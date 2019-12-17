#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =========================================================================
#   Program:   iota2
#
#   Copyright (c) CESBIO. All rights reserved.
#
#   See LICENSE for details.
#
#   This software is distributed WITHOUT ANY WARRANTY; without even
#   the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the above copyright notices for more information.
#
# =========================================================================

import os, sys, argparse
import shutil
import gdal
import multiprocessing as mp

try:
    from Common import FileUtils as fut
    from Common import OtbAppBank
    from Common.OtbAppBank import executeApp
    from simplification import nomenclature
except ImportError:
    raise ImportError("Iota2 not well configured / installed")


def getMaskRegularisation(classes):

    nomenc = nomenclature.Iota2Nomenclature(classes, "cfg")
    df = nomenc.HierarchicalNomenclature.to_frame().groupby(level=0)
    masks = []
    for idx, key in enumerate(df.groups.keys()):

        exp = "(im1b1=="
        listclasses = []
        for elt in df.groups[key].to_frame().groupby(level=1).groups.keys():
            listclasses.append(str(elt[0]))

        exp += " || im1b1==".join(listclasses)
        exp += ")?im1b1:0"
        output = "mask_%s.tif" % (idx)

        masks.append([idx, exp, output, len(df.groups[key]) != 1])

    return masks


def prepareBandRasterDataset(raster):

    if isinstance(raster, str):
        data = gdal.Open(raster)
    elif isinstance(raster, gdal.Dataset):
        data = raster
    else:
        raise Exception("Input raster file not managed")

    transform = data.GetGeoTransform()
    proj = data.GetProjection()
    drv = gdal.GetDriverByName("MEM")
    dst_ds = drv.Create("", data.RasterXSize, data.RasterYSize, 1, gdal.GDT_Byte)
    dst_ds.SetGeoTransform(transform)
    dst_ds.SetProjection(proj)
    dstband = dst_ds.GetRasterBand(1)

    return dst_ds, dstband


def rastToVectRecode(
    path,
    classif,
    vector,
    outputName,
    ram="10000",
    dtype="uint8",
    valvect=255,
    valrastout=255,
):

    """
    Convert vector in raster file and change background value 

    Parameters
    ----------
    path : string
        working directory
    classif : string
        path to landcover classification
    vector : string
        vector file to rasterize
    outputName : string
        output filename and path
    ram : string
        ram for OTB applications
    dtype : string
        pixel type of the output raster
    valvect : integer
        value of vector to search
    valrastout : integer
        value to use to recode
    """

    # Empty raster
    tmpclassif = os.path.join(path, "temp.tif")
    bmapp = OtbAppBank.CreateBandMathApplication(
        {
            "il": [classif],
            "exp": "im1b1*0",
            "ram": str(1 * float(ram)),
            "pixType": dtype,
            "out": tmpclassif,
        }
    )

    p = mp.Process(target=executeApp, args=[bmapp])
    p.start()
    p.join()

    # Burn
    tifMasqueMerRecode = os.path.join(path, "masque_mer_recode.tif")
    rastApp = OtbAppBank.CreateRasterizationApplication(
        {
            "in": vector,
            "im": os.path.join(path, "temp.tif"),
            "background": 1,
            "pixType": dtype,
            "out": tifMasqueMerRecode,
        }
    )

    p = mp.Process(target=executeApp, args=[rastApp])
    p.start()
    p.join()

    # Differenciate inland water and sea water
    exp = "im1b1==%s?im2b1:%s" % (int(valvect), int(valrastout))
    bandMathAppli = OtbAppBank.CreateBandMathApplication(
        {
            "il": [tifMasqueMerRecode, classif],
            "exp": exp,
            "ram": str(1 * float(ram)),
            "pixType": dtype,
            "out": outputName,
        }
    )

    p = mp.Process(target=executeApp, args=[bandMathAppli])
    p.start()
    p.join()

    os.remove(tifMasqueMerRecode)
    os.remove(tmpclassif)


def maskOTBBandMathOutput(path, raster, exp, ram, output, dstnodata=0):

    outbm = os.path.join(path, "mask.tif")
    bandMathAppli = OtbAppBank.CreateBandMathApplication(
        {"il": raster, "exp": exp, "ram": str(ram), "pixType": "uint8", "out": outbm}
    )

    p = mp.Process(target=executeApp, args=[bandMathAppli])
    p.start()
    p.join()

    gdal.Warp(
        output,
        outbm,
        dstNodata=dstnodata,
        multithread=True,
        format="GTiff",
        warpOptions=[["NUM_THREADS=ALL_CPUS"], ["OVERWRITE=TRUE"]],
    )

    os.remove(outbm)

    return output


def sieveRasterMemory(raster, threshold, output="", dstnodata=0, pixelConnection=8):

    # input band
    if isinstance(raster, str):
        data = gdal.Open(raster)
    elif isinstance(raster, gdal.Dataset):
        data = raster
    else:
        raise Exception("Input raster file not managed")

    srcband = data.GetRasterBand(1)

    # output band
    dst_ds, dstband = prepareBandRasterDataset(raster)

    gdal.SieveFilter(srcband, None, dstband, threshold, pixelConnection)

    outformat = "MEM"
    if os.path.splitext(output)[1] == ".tif":
        outformat = "GTiff"

    sievedRaster = gdal.Warp(
        output,
        dst_ds,
        dstNodata=dstnodata,
        multithread=True,
        format=outformat,
        warpOptions=[["NUM_THREADS=ALL_CPUS"], ["OVERWRITE=TRUE"]],
    )
    return sievedRaster


def adaptRegularization(path, raster, output, ram, rule, threshold):

    mask = os.path.join(path, rule[2])
    outpath = os.path.dirname(output)

    if not os.path.exists(mask):
        mask = maskOTBBandMathOutput(path, raster, rule[1], ram, mask)

        if rule[3]:
            tmpsieve8 = sieveRasterMemory(mask, threshold, "", 0, 8)
            tmpsieve4 = sieveRasterMemory(tmpsieve8, threshold, mask, 0, 4)
            tmpsieve8 = tmpsieve4 = None

    shutil.copy(mask, outpath)
    return mask


def mergeRegularization(
    path, rasters, threshold, output, ram, resample=None, water=None
):

    if not os.path.exists(output):

        outpath = os.path.dirname(output)

        exp = "+".join(["im%sb1" % (idx + 1) for idx, x in enumerate(rasters)])

        merge = os.path.join(path, "merge.tif")
        merge = maskOTBBandMathOutput(path, rasters, exp, ram, merge)

        sieve8 = sieveRasterMemory(merge, threshold, "", 0, 8)

        outtmp = os.path.join(path, "class4.tif")

        if resample:
            sieve4 = sieveRasterMemory(sieve8, threshold, "", 0, 4)

            if water:
                tmprewater = gdal.Warp(
                    outtmp,
                    sieve4,
                    targetAlignedPixels=True,
                    resampleAlg="mode",
                    xRes=resample,
                    yRes=resample,
                    dstNodata=0,
                    multithread=True,
                    format="GTiff",
                    warpOptions=[["NUM_THREADS=ALL_CPUS"], ["OVERWRITE=TRUE"]],
                )
                rastToVectRecode(path, outtmp, water, output)
                os.remove(outtmp)
                tmprewater = sieve4 = None

            else:
                tmpre = gdal.Warp(
                    output,
                    sieve4,
                    targetAlignedPixels=True,
                    resampleAlg="mode",
                    xRes=resample,
                    yRes=resample,
                    dstNodata=0,
                    multithread=True,
                    format="GTiff",
                    warpOptions=[["NUM_THREADS=ALL_CPUS"], ["OVERWRITE=TRUE"]],
                )
                tmpre = sieve4 = None
        else:
            if water:
                sieve4 = sieveRasterMemory(sieve8, threshold, outtmp, 0, 4)
                sieve4 = sieve8 = None
                rastToVectRecode(path, outtmp, water, output)
                os.remove(outtmp)

            else:
                sieve4 = sieveRasterMemory(sieve8, threshold, output, 0, 4)
                sieve4 = sieve8 = None
                try:
                    shutil.copy(output, outpath)
                except:
                    print("Output file %s already exists" % (output))
                    pass

        os.remove(merge)

    else:
        print("Output file %s already exists" % (output))
