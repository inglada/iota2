#!/usr/bin/env python3
#-*- coding: utf-8 -*-

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

import os
import sys
import argparse
import shutil
from collections import OrderedDict
from zipfile import ZipFile
import logging
import osgeo
import gdal
import pandas as pad
import geopandas as gpad
from skimage.measure import label
from skimage.measure import regionprops
import rasterio
import fiona
from rasterio.mask import mask
import numpy as np
LOGGER = logging.getLogger(__name__)

try:
    from iota2.VectorTools import vector_functions as vf
    from iota2.VectorTools import checkGeometryAreaThreshField as checkGeom
    from iota2.VectorTools import BufferOgr as bfo
    from iota2.VectorTools import splitByArea as sba
    from iota2.VectorTools import MergeFiles as mf
    from iota2.Common import FileUtils as fut
    from iota2.Common import Utils
    from iota2.simplification import nomenclature
except ImportError:
    raise ImportError('Iota2 not well configured / installed')


def getFidList(vect):

    shape = vf.openToRead(vect)
    lyr = shape.GetLayer()
    fidlist = []
    for feat in lyr:
        fidlist.append(feat.GetFID())

    return list(set(fidlist))


def getVectorsList(path):

    listfiles = []
    for root, _, files in os.walk(path):
        for filein in files:
            if ".shp" in filein:
                listfiles.append(os.path.join(root, filein))

    return listfiles


def countPixelByClass(databand, fid=0, band=0, nodata=0):
    """Compute rates of unique values of a categorical raster and store them in a Pandas DataFrame:


    ----------
    databand : gdal raster file or osgeo.gdal.Dataset
        categorical raster

    fid : int
        FID value of feature of zonal vector (DataFrame storage)

    band : int
        band number of databand input parameter

    nodata : int
        nodata value of the raster / band

    Return
    ------
    classStats
        Pandas DataFrame

    classmaj
        integer value of the majority class

    posclassmaj
        ndarray of position of majority class
    """

    if isinstance(databand, np.ndarray):
        if databand.size != 0:
            data = databand
        else:
            raise Exception('Empty data of wrapped raster')

    else:
        if databand:
            if isinstance(databand, str):
                if os.path.exists(databand):
                    rastertmp = gdal.Open(databand, 0)
                else:
                    raise Exception('Raster file %s not exist' % (databand))

            elif isinstance(databand, osgeo.gdal.Dataset):
                rastertmp = databand

            else:
                raise Exception('Type of raster dataset not handled')

            banddata = rastertmp.GetRasterBand(band)
            data = banddata.ReadAsArray()

        else:
            raise Exception('Empty data of wrapped raster')

    img = label(data)
    counts = []

    col_names = ['value', 'count']

    if len(np.unique(img)) != 1 or np.unique(img)[0] != 0:
        try:
            dataclean = data[data != nodata]
            npcounts = np.array(np.unique(dataclean, return_counts=True)).T
            counts = npcounts.tolist()
        except:
            for reg in regionprops(img, data):
                counts.append([[
                    x for x in np.unique(reg.intensity_image) if x != nodata
                ][0], reg.area])

        if len(counts[0]):
            # test si counts a des valeurs !
            listlab = pad.DataFrame(data=counts, columns=col_names)
            # pourcentage
            listlab['rate'] = listlab['count'] / listlab['count'].sum()

            # classmaj
            classmaj = listlab[listlab['rate'] == max(
                listlab['rate'])]['value']
            classmaj = classmaj.iloc[0]

            posclassmaj = np.where(data == int(classmaj))

            # Transposition pour jointure directe
            listlabT = listlab.T
            classStats = pad.DataFrame(
                data=[listlabT.loc['rate'].values],
                index=[fid],
                columns=[str(int(x)) for x in listlabT.loc['value']])

    else:
        classStats = pad.DataFrame(index=[fid], columns=[])
        classmaj = 0
        posclassmaj = 0

    listlab = listlabT = data = None

    return classStats, classmaj, posclassmaj


def rasterStats(band, nbband=0, posclassmaj=None, posToRead=None, nodata=0):
    """Compute descriptive statistics of a numpy array or a gdal raster:

    Parameters
    ----------
    band : gdal raster file or osgeo.gdal.Dataset
        raster on which compute statistics

    nbband : int
        band number of band input parameter

    posclassmaj : ndarray
        numpy array of position of majority class

    posToRead : tuple
        col / row coordinates on which extract pixel value

    nodata : int
        nodata value of the raster / band

    Return
    ------
    mean, std, max, min
        float

    pixel value
        float
    """

    if isinstance(band, np.ndarray):
        if band.size != 0:
            data = band
        else:
            raise Exception('Empty data of wrapped raster')

    else:
        if band:
            if isinstance(band, str):
                if os.path.exists(band):
                    rastertmp = gdal.Open(band, 0)
                else:
                    raise Exception('Raster file %s not exist' % (band))

            elif isinstance(band, osgeo.gdal.Dataset):
                rastertmp = band

            else:
                raise Exception('Type of raster dataset not handled')

            banddata = rastertmp.GetRasterBand(band)
            data = banddata.ReadAsArray()

        else:
            raise Exception('Empty data of wrapped raster')

    if not posToRead:
        img = label(data)

        if len(np.unique(img)) != 1 or np.unique(img)[0] != 0:
            data = data[posclassmaj]
            mean = round(np.mean(data[data != nodata]), 2)
            std = round(np.std(data[data != nodata]), 2)
            maxval = round(np.max(data[data != nodata]), 2)
            minval = round(np.min(data[data != nodata]), 2)

            stats = (mean, std, maxval, minval)
        else:
            stats = (0, 0, 0, 0)

    else:
        stats = np.float(data[posToRead[1], posToRead[0]])

    return stats


def definePandasDf(geoframe, idvals, paramstats={}, classes=""):
    """Define DataFrame (columns and index values) based on expected statistics and zonal vector

    Parameters
    ----------
    geoframe : geopandas.GeoDataFrame
        dataframe of input vector file
 
    idvals : list
        list of FID to analyse (DataFrame storage)

    paramstats : dict
        list of statistics to compute (e.g. {1:'stats', 2:'rate'})

    classes : nomenclature file
        nomenclature

    Return
    ------
    geopandas.GeoDataFrame

    """

    cols = []
    for param in paramstats:
        if paramstats[param] == "rate":
            if classes != "" and classes is not None:
                nomenc = nomenclature.Iota2Nomenclature(classes, 'cfg')
                desclasses = nomenc.HierarchicalNomenclature.get_level_values(
                    int(nomenc.getLevelNumber() - 1))
                [cols.append(str(x)) for x, y, w, z in desclasses]
        elif paramstats[param] == "stats":
            [
                cols.append(x) for x in [
                    "meanb%s" % (param),
                    "stdb%s" % (param),
                    "maxb%s" % (param),
                    "minb%s" % (param)
                ]
            ]
        elif paramstats[param] == "statsmaj":
            [
                cols.append(x) for x in [
                    "meanmajb%s" % (param),
                    "stdmajb%s" % (param),
                    "maxmajb%s" % (param),
                    "minmajb%s" % (param)
                ]
            ]
        elif "stats_" in paramstats[param]:
            cl = paramstats[param].split('_')[1]
            [
                cols.append(x) for x in [
                    "meanb%sc%s" % (param, cl),
                    "stdb%sc%s" % (param, cl),
                    "maxb%sc%s" % (param, cl),
                    "minb%sc%s" % (param, cl)
                ]
            ]
        elif "val" in paramstats[param]:
            [cols.append("valb%s" % (param))]
        else:
            raise Exception("The method %s is not implemented") % (
                paramstats[param])

    statsgpad = gpad.GeoDataFrame(np.nan, index=idvals, columns=cols)
    geoframe = gpad.GeoDataFrame(pad.concat([geoframe, statsgpad], axis=1),
                                 geometry=geoframe['geometry'],
                                 crs=geoframe.crs)

    return geoframe


def checkmethodstats(rasters, paramstats, nbbands):
    """Store list of requested statistics in dict and check validity of in put rasters

    Parameters
    ----------

    rasters : list
        list of rasters to analyse

    paramstats : list
        list of statistics to compute (e.g. [[1,'stats'], [2, 'rate']] or ['val'])

    nbbands : int
        number of input rasters or bands of input raster

    Return
    ----------
    paramstats : dict
        list of statistics to compute (e.g. {1:'stats', 2:'rate'})

    """

    # Format requested statistics
    if isinstance(paramstats, list):
        # List of methods (bash)
        if ':' in paramstats[0]:
            paramstats = dict([(x.split(':')[0], x.split(':')[1])
                               for x in paramstats])

        # Unique method without band / raster number
        elif len(paramstats) == 1:
            # Build statistics method dictionary
            tmpdict = {}
            for idx in range(nbbands):
                tmpdict[idx + 1] = str(paramstats[0])
            paramstats = tmpdict

    # Check statistics methods validity
    for keys in paramstats:
        if 'stats_' in paramstats[keys]:
            paramstats[keys] = 'stats'

        if paramstats[keys] not in ('stats', 'statsmaj', 'rate', 'val'):
            raise Exception('The method %s is not implemented' %
                            (paramstats[0]))

    # requested stats and band number ?
    maxband = max([int(x) for x in list(paramstats.keys())])
    if len(rasters) != 1:
        if nbbands < maxband:
            raise Exception("Band ids in requested stats and number of input rasters "\
                            "or bands number of input raster do not correspond")

    # same extent and resolution of input rasters ?
    listres = []
    listextent = []
    if len(rasters) != 1:
        for raster in rasters:
            listres.append(abs(fut.getRasterResolution(raster)[0]))
            listextent.append(fut.getRasterExtent(raster))

    if listextent[1:] != listextent[:-1]:
        raise Exception("Input rasters must have same extent")

    if listres[1:] != listres[:-1]:
        raise Exception("Input rasters must have same spatial resolution")

    return paramstats


def setPandasSchema(paramstats, vectorgeomtype, bufferDist=""):
    """Store list of raster or multi-band raster in a ndarray

    Parameters
    ----------

    paramstats : dict
        list of statistics to compute (e.g. {1:'stats', 2:'rate'})

    vectorgeomtype : int
        Type of geometry of input/output vector (http://portal.opengeospatial.org/files/?artifact_id=25355)

    bufferDist : int
        buffer size around Point vetor geometry


    Return
    ----------
    schema : dict / Fiona schema
        schema giving geometry type 

    """

    # Value extraction
    if not bufferDist and vectorgeomtype in (1, 4, 1001, 1004):
        if 'val' in list(paramstats.values()):
            if vectorgeomtype == 1:
                schema = {'geometry': 'Point', 'properties': {}}
            elif vectorgeomtype == 4:
                schema = {'geometry': 'MultiPoint', 'properties': {}}
        else:
            raise Exception("Only pixel value extraction available "\
                            "when Point geometry without buffer distance is provided")

    # Stats extraction
    else:
        # Point geometry
        if vectorgeomtype in (1, 4, 1001, 1004):
            if vectorgeomtype == 1:
                schema = {'geometry': 'Point', 'properties': {}}
            elif vectorgeomtype == 4:
                schema = {'geometry': 'MultiPoint', 'properties': {}}

        # Polygon geometry
        elif vectorgeomtype in (3, 6, 1003, 1006):
            if vectorgeomtype == 3:
                schema = {'geometry': 'Polygon', 'properties': {}}
            elif vectorgeomtype == 6:
                schema = {'geometry': 'MultiPolygon', 'properties': {}}
        else:
            raise Exception("Geometry type of vector file not handled")

    return schema


def storeRasterInArray(rasters):
    """Store list of raster or multi-band raster in a ndarray

    Parameters
    ----------

    rasters : list
        list of rasters to analyse

    Return
    ----------
    ndarray

    """

    # get raster size with first raster file
    data = fut.readRaster(rasters[0], False)

    # get rasters or bands number
    if len(rasters) == 1:
        nbbands = fut.getRasterNbands(rasters[0])

    elif len(rasters) > 1:
        nbbands = len(rasters)

    # Set a empty ndarrays with same dimension as input rasters
    outdata = np.zeros([data[1], data[0], nbbands])

    # Populate output ndarrays
    if len(rasters) == 1:
        for nbband in range(nbbands):
            outdata[:, :, nbband] = fut.readRaster(rasters[0], True,
                                                   nbband + 1)[0]

    elif len(rasters) > 1:
        for idx, raster in enumerate(rasters):
            outdata[:, :, idx] = fut.readRaster(raster, True)[0]
    else:
        raise Exception("No input raster provided to store in Numpy array")

    return outdata


def extractRasterArray(rasters,
                       paramstats,
                       vector,
                       vectorgeomtype,
                       fid,
                       gdalpath="",
                       gdalcachemax="9000",
                       systemcall=True,
                       path=""):
    """Clip raster and store in ndarrays

    Parameters
    ----------

    rasters : list
        list of rasters to analyse

    paramstats : dict
        list of statistics to compute (e.g. {1:'stats', 2:'rate'})

    vector : string
        vector file for cutline opetation

    vectorgeomtype : int
        Type of geometry of input/output vector (http://portal.opengeospatial.org/files/?artifact_id=25355)

    fid : integer
        FID value to clip raster (cwhere parameter of gdalwarp)

    gdalpath : string
        gdal binaries path

    gdalcachemax : string
        gdal cache for wrapping operation (in Mb)

    systemcall : boolean
        if True, use os system call to execute gdalwarp (usefull to control gdal binaries version - gdalpath parameter)

    path : string
        temporary path to store temporary date if systemcall is True

    Return
    ----------
    boolean
        if True, wrap operation well terminated    

    ndarray ndarrays
        
    """

    bands = []
    todel = []
    success = True
    # Get rasters resolution
    res = abs(fut.getRasterResolution(rasters[0])[0])
    # Get vector name
    vectorname = os.path.splitext(os.path.basename(vector))[0]
    for idx, raster in enumerate(rasters):

        # Value extraction
        if 'val' in list(paramstats.values()):
            if vectorgeomtype not in (1, 4, 1001, 1004):
                raise Exception("Type of input vector %s must be "\
                                "'Point' for pixel value extraction"%(vector))
            else:
                bands.append(raster)
                todel = []
                ndbands = storeRasterInArray(bands)

        # Stats Extraction
        else:
            errormsg = ""

            try:
                # TODO : test gdal version : >= 2.2.4
                if systemcall:
                    tmpfile = os.path.join(
                        path, 'rast_%s_%s_%s' % (vectorname, str(fid), idx))
                    cmd = '%sgdalwarp -tr %s %s -tap -q -overwrite -cutline %s '\
                          '-crop_to_cutline --config GDAL_CACHEMAX %s -wm %s '\
                          '-wo "NUM_THREADS=ALL_CPUS" -wo "CUTLINE_ALL_TOUCHED=YES" '\
                          '-cwhere "FID=%s" %s %s -ot Float32'%(os.path.join(gdalpath, ''), \
                                                                res, \
                                                                res, \
                                                                vector, \
                                                                gdalcachemax, \
                                                                gdalcachemax, \
                                                                fid, \

                                                                raster, \
                                                                tmpfile)
                    Utils.run(cmd)
                    todel.append(tmpfile)
                else:
                    gdal.SetConfigOption("GDAL_CACHEMAX", gdalcachemax)
                    tmpfile = gdal.Warp('', raster, xRes=res, \
                                        yRes=res, targetAlignedPixels=True, \
                                        cutlineDSName=vector, cropToCutline=True, \
                                        cutlineWhere="FID=%s"%(fid), format='MEM', \
                                        warpMemoryLimit=gdalcachemax, \
                                        warpOptions=[["NUM_THREADS=ALL_CPUS"], ["CUTLINE_ALL_TOUCHED=YES"]])

                bands.append(tmpfile)
                todel = []

                # store rasters in ndarray
                ndbands = storeRasterInArray(bands)

            except RuntimeError as err:
                errormsg = err
                success = False

    # Remove tmp rasters
    for filtodel in todel:
        os.remove(filtodel)

    if not success:

        with fiona.open(vector) as src:
            filtered = filter(lambda f: f['id'] == str(fid), src)
            feature = next(filtered)
            geometry = feature["geometry"]

        with rasterio.open(raster) as rast:
            ndbands, out_transform = mask(rast, [geometry], crop=True)

    return success, ndbands, errormsg


def getClassMaj(bands, methodstat, idxcatraster):
    """Extract statistics on numpy array and store them on a GeoPandas / Pandas dataframe

    Parameters
    ----------
    bands : ndarray
        raster bands or raster files store in numpy array

    methodstats : string
        statistics method ('statsmaj' or 'stats_*')

    idxcatraster : integer
        indice of the categorical raster to find class positions

    Return
    ----------
    ndarray or tuple of ndarrays
        
    """
    if methodstat == 'statsmaj':

        # Get band of categorical raster
        nbbandrate = int(idxcatraster - 1)
        bandrate = bands[nbbandrate]

        # Find majority class and return positions array
        _, _, posclass = countPixelByClass(bandrate, "", nbbandrate)

    elif 'stats_' in methodstat:

        # get class value to check
        reqclass = 'statsmaj'.split('_')[1]

        # get positions array of the class
        rastertmp = gdal.Open(bands[idxcatraster - 1], 0)
        data = rastertmp.ReadAsArray()
        posclass = np.where(data == int(reqclass))
        data = None

    return posclass


def computeStats(bands, paramstats, dataframe, idval, nodata=0):
    """Extract statistics on numpy array and store them on a GeoPandas / Pandas dataframe

    Parameters
    ----------
    bands : ndarray
        raster bands or raster files store in numpy array

    paramstats : dict
        list of statistics to compute (e.g. {1:'stats', 2:'rate'})

    dataframe : Pandas Dataframe
        Pandas Dataframe

    idval : integer
        index value to store in dataframe
    
    nodata : float
        nodata value of input rasters

    multiraster : boolean
        True, if several input rasters, False if one input raster

    Return
    ----------
    GeoPandas or Pandas DataFrame
        
    """

    for param in paramstats:

        band = bands[:, :, int(param) - 1]
        nbband = int(param)

        # Statistics extraction
        if band.size != 0:
            methodstat = paramstats[param]

            ### Categorical statistics ###
            if methodstat == 'rate':
                classStats, classmaj, posclassmaj = countPixelByClass(
                    band, idval, nbband)
                dataframe.update(classStats)

                # Get majority class and add it in columns "majority"
                try:
                    classStats["majority"] = classStats.idxmax(axis=1)
                except:
                    classStats["majority"] = None

                # Add columns when pixel values are not identified in nomenclature file
                if list(classStats.columns) != list(dataframe.columns):
                    newcols = list(
                        set(list(classStats.columns)).difference(
                            set(list(dataframe.columns))))
                    dataframe = pad.concat([dataframe, classStats[newcols]],
                                           axis=1)

                dataframe.fillna(np.nan, inplace=True)

            elif methodstat == 'stats':

                cols = ["meanb%s"%(int(param)), "stdb%s"%(int(param)), \
                        "maxb%s"%(int(param)), "minb%s"%(int(param))]

                dataframe.update(pad.DataFrame(data=[rasterStats(band, nbband)], \
                                           index=[idval], \
                                           columns=cols))

            ### Descriptive statistics for majority class ###
            elif methodstat == 'statsmaj':
                if not classmaj:
                    if "rate" in list(paramstats.values()):
                        idxbdclasses = [
                            x for x in paramstats if paramstats[x] == "rate"
                        ][0]
                        posclassmaj = getClassMaj(bands, methodstat,
                                                  idxbdclasses)
                    else:
                        raise Exception("No classification raster provided "\
                                        "to check position of majority class")

                cols = ["meanmajb%s"%(int(param)), "stdmajb%s"%(int(param)), \
                        "maxmajb%s"%(int(param)), "minmajb%s"%(int(param))]

                dataframe.update(pad.DataFrame(data=[rasterStats(band, nbband, posclassmaj, nodata)], \
                                           index=[idval], \
                                           columns=cols))

            ### Descriptive statistics for one class ###
            elif "stats_" in methodstat:
                if "rate" in list(paramstats.values()):
                    idxbdclasses = [
                        x for x in paramstats if paramstats[x] == "rate"
                    ][0]
                    posclass = getClassMaj(bands, methodstat, idxbdclasses)
                else:
                    raise Exception("No classification raster provided "\
                                    "to check position of majority class")

                cols = ["meanb%sc%s"%(int(param), reqclass), "stdb%sc%s"%(int(param), reqclass), \
                        "maxb%sc%s"%(int(param), reqclass), "minb%sc%s"%(int(param), reqclass)]

                dataframe.update(pad.DataFrame(data=[rasterStats(band, nbband, posclass, nodata)], \
                                           index=[idval], \
                                           columns=cols))
            band = None

    return dataframe


def extractPixelValue(rasters, bands, paramstats, xpt, ypt, dataframe,
                      idval=0):
    """Extract pixel value and store it on a Pandas dataframe

    Parameters
    ----------
    rasters : list
        list of rasters to analyse

    bands : ndarray
        raster bands or raster files store in numpy array

    paramstats : dict
        list of statistics to compute (e.g. {1:'stats', 2:'rate'})

    xpt : float
        Point x coordinates 

    ypt : float
        Point y coordinates 

    dataframe : Pandas Dataframe
        Pandas Dataframe

    idval : integer
        index value to store in dataframe

    Return
    ----------
    GeoPandas or Pandas DataFrame
        
    """

    for param in paramstats:

        band = bands[:, :, int(param) - 1]
        nbband = int(param)

        ### Pixel value extraction ###
        if band.size != 0:
            methodstat = paramstats[param]
            if "val" in methodstat:
                colpt, rowpt = fut.geoToPix(rasters[0], xpt, ypt)
                cols = "valb%s" % (param)
                dataframe.update(pad.DataFrame(data=[rasterStats(band, nbband, None, (colpt, rowpt))], \
                                           index=[idval], \
                                           columns=[cols]))

            band = None

    return dataframe


def formatDataFrame(geodataframe,
                    schema,
                    fidToDel,
                    categorical=False,
                    classes="",
                    floatdec=2,
                    intsize=10):
    """Format columns name and format of a GeoPandas DataFrame

    Parameters
    ----------
    geodataframe : GeoPandas DataFrame
        GeoPandas DataFrame

    schema : dict / Fiona schema
        schema giving colums name and format

    categorical : boolean
        if True, use a input nomenclature (Iota2Nomenclature) to use alias renaming

    classes : Iota2Nomenclature
        Nomencalture description (see nomenclature class for input)

    floatdec : integer
        length of decimal part of columns values

    intsize : integer
        length of integer part of columns values

    Return
    ----------
    GeoPandas DataFrame

    GeoPandas schema

    """

    # change column names if rate stats expected and nomenclature file is provided
    if categorical:
        # get multi-level nomenclature
        # TODO : several type of input nomenclature (cf. nomenclature class)
        nomenc = nomenclature.Iota2Nomenclature(classes, 'cfg')
        desclasses = nomenc.HierarchicalNomenclature.get_level_values(
            int(nomenc.getLevelNumber() - 1))
        cols = [(str(x), str(z)) for x, y, w, z in desclasses]

        # rename columns with alias
        for col in cols:
            #geodataframe.rename(columns={col[0]:col[1].decode('utf8')}, inplace=True)
            geodataframe.rename(columns={col[0]: col[1]}, inplace=True)

    # change columns type
    schema['properties'] = OrderedDict([(x, 'float:%s.%s'%(intsize, floatdec)) for x in list(geodataframe.columns) \
                                        if x != 'geometry'])

    # drop unused index
    geodataframe.drop(fidToDel, inplace=True)

    return geodataframe, schema


def dataframeExport(geodataframe, output, schema):
    """Export a GeoPandas DataFrame as a vector file (shapefile, sqlite and geojson)

    Parameters
    ----------
    geodataframe : GeoPandas DataFrame
        GeoPandas DataFrame

    output : string
        output vector file

    schema : dict / Fiona schema
        schema giving colums name and format

    """

    # TODO Export format depending on columns number (shapefile, sqlite, geojson) # Check Issue on framagit
    convert = False
    outformat = os.path.splitext(output)[1]
    if outformat == ".shp":
        driver = "ESRI Shapefile"
    elif outformat == ".geojson":
        driver = "GeoJSON"
    elif outformat == ".sqlite":
        driver = "ESRI Shapefile"
        convert = True
    else:
        raise Exception("The output format '%s' is not handled" %
                        (outformat[1:]))

    if not convert:
        geodataframe.to_file(output,
                             driver=driver,
                             schema=schema,
                             encoding='utf-8')
    else:
        outputinter = os.path.splitext(output)[0] + '.shp'
        geodataframe.to_file(outputinter,
                             driver=driver,
                             schema=schema,
                             encoding='utf-8')
        output = os.path.splitext(output)[0] + '.sqlite'
        Utils.run('ogr2ogr -f SQLite %s %s' % (output, outputinter))


def zonalstats(path,
               rasters,
               params,
               output,
               paramstats,
               classes="",
               bufferDist=None,
               nodata=0,
               gdalpath="",
               systemcall=False,
               gdalcachemax="9000",
               logger=LOGGER):
    """Compute zonal statistitics (descriptive and categorical)
       on multi-band raster or multi-rasters
       based on Point (buffered or not) or Polygon zonal vector

    Parameters
    ----------
    path : string
        working directory

    rasters : list
        list of rasters to analyse

    params : list
        list of fid list and vector file

    output : vector file (sqlite, shapefile and geojson)
        vector file to store statistitics

    paramstats : list
        list of statistics to compute (e.g. {1:'stats', 2:'rate'})

            - paramstats = {1:"rate", 2:"statsmaj", 3:"statsmaj", 4:"stats", 2:stats_cl}
            - stats : mean_b, std_b, max_b, min_b
            - statsmaj : meanmaj, stdmaj, maxmaj, minmaj of majority class
            - rate : rate of each pixel value (classe names)
            - stats_cl : mean_cl, std_cl, max_cl, min_cl of one class
            - val : value of corresponding pixel (only for Point geometry and without other stats)

    classes : nomenclature file
        nomenclature

    bufferDist : int
        in case of point zonal vector : buffer size

    gdalpath : string
        path of gdal binaries (for system execution)

    systemcall : boolean
        if True, wrapped raster are stored in working dir

    gdalcachemax : string
        gdal cache for wrapping operation (in Mb)

    """

    LOGGER.info("Begin to compute zonal statistics for vector file %s" %
                (output))

    if systemcall and not gdalpath:
        LOGGER.info(
            "Please provide gdal binaries path when systemcall is set to true")
        sys.exit()

    if os.path.exists(output):
        return

    # Get bands or raster number
    if len(rasters) != 1:
        nbbands = len(rasters)
    else:
        nbbands = fut.getRasterNbands(rasters[0])

    # Prepare and check validity of statistics methods and input raster
    paramstats = checkmethodstats(rasters, paramstats, nbbands)

    # Get vector file and FID list
    if len(params) > 1:
        vector, idvals = params
    else:
        vector = params[0][0]
        idvals = params[0][1]

    # if no vector subsetting (all features)
    fullfid = getFidList(vector)
    if not idvals:
        idvals = fullfid
        novals = []
    else:
        novals = [x for x in fullfid if x not in idvals]

    # vector open and iterate features and/or buffer geom
    vectorname = os.path.splitext(os.path.basename(vector))[0]
    vectorgeomtype = vf.getGeomType(vector)
    vectorbuff = None

    # Prepare schema of output geopandas dataframe (geometry type and columns formatting)
    schema = setPandasSchema(paramstats, vectorgeomtype, bufferDist)

    # Buffer Point vector file
    if bufferDist and vectorgeomtype in (1, 4, 1001, 1004):
        vectorbuff = os.path.join(path, vectorname + "buff.shp")
        _ = bfo.bufferPoly(vector, vectorbuff, bufferDist=bufferDist)
        vectorgeomtype = vf.getGeomType(vectorbuff)

    # Store input vector in output geopandas dataframe
    vectgpad = gpad.read_file(vector)

    # Prepare statistics columns of output geopandas dataframe
    stats = definePandasDf(vectgpad, idvals, paramstats, classes)

    # Iterate FID list
    dataset = vf.openToRead(vector)
    lyr = dataset.GetLayer()

    if "fid" in [x.lower() for x in vf.getFields(vector)]:
        raise ValueError(
            "FID field not allowed. This field name is reserved by gdal binary."
        )

    for idval in idvals:
        if vectorgeomtype in (1, 4, 1001, 1004):
            if 'val' in list(paramstats.values()):
                lyr.SetAttributeFilter("FID=" + str(idval))
                for feat in lyr:
                    geom = feat.GetGeometryRef()
                    if geom:
                        if vectorgeomtype == 4:
                            point = geom.GetGeometryRef(0)
                            xpt = point.GetX()
                            ypt = point.GetY()
                        else:
                            xpt, ypt, _ = geom.GetPoint()

            # Switch to buffered vector (Point and bufferDist)
            if bufferDist:
                if vectorbuff:
                    vector = vectorbuff

        # creation of wrapped rasters
        success, bands, err = extractRasterArray(rasters, paramstats, vector,
                                                 vectorgeomtype, idval,
                                                 gdalpath, gdalcachemax,
                                                 systemcall, path)

        if success:
            if 'val' in list(paramstats.values()):
                stats = extractPixelValue(rasters, bands, paramstats, xpt, ypt,
                                          stats, idval)
            else:
                stats = computeStats(bands, paramstats, stats, idval, nodata)

        else:
            print(
                "gdalwarp problem for feature %s (%s) : statistic computed with rasterio"
                % (idval, err))

    # Prepare columns name and format of output dataframe
    if "rate" in list(paramstats.values()) and classes != "":
        stats, schema = formatDataFrame(stats, schema, novals, True, classes)
    else:
        stats, schema = formatDataFrame(stats, schema, novals)

    # exportation
    dataframeExport(stats, output, schema)

    LOGGER.info("End to compute zonal statistics for vector file %s" %
                (output))


def osoFormatting(invector, classes, outvector=""):
    def Sort(sub_li):
        sub_li.sort(key=lambda x: x[0])
        return sub_li

    nomenc = nomenclature.Iota2Nomenclature(classes, 'cfg')
    desclasses = nomenc.HierarchicalNomenclature.get_level_values(
        int(nomenc.getLevelNumber() - 1))
    cols = [[x, str(z)] for x, y, w, z in desclasses]
    sortalias = [x[1] for x in Sort(cols)]

    exp = ""
    for name in sortalias:
        exp += "CAST(%s AS NUMERIC(6,2)) AS %s, " % (name, name)

    layerin = os.path.splitext(os.path.basename(invector))[0]
    if outvector == "":
        layerin = os.path.splitext(os.path.basename(invector))[0]
        outvector = os.path.splitext(invector)[0] + '_tmp.shp'
        layerout = layerin + "_tmp"
    else:
        layerin = os.path.splitext(os.path.basename(invector))[0]
        layerout = os.path.splitext(os.path.basename(outvector))[0]

    command = "ogr2ogr -lco ENCODING=UTF-8 -overwrite -q -f 'ESRI Shapefile' -nln %s -sql "\
              "'SELECT CAST(cat AS INTEGER(4)) AS Classe, "\
              "CAST(meanmajb3 AS INTEGER(4)) AS Validmean, "\
              "CAST(stdmajb3 AS NUMERIC(6,2)) AS Validstd, "\
              "CAST(meanmajb2 AS INTEGER(4)) AS Confidence, %s"\
              "CAST(area AS NUMERIC(10,2)) AS Aire "\
              "FROM %s' "\
              "%s %s"%(layerout, exp, layerin, outvector, invector)

    Utils.run(command)


def splitVectorFeatures(vectorpath, outputPath, chunk=1, byarea=False):
    """Split FID list of a list of vector files in equal groups:

    Parameters
    ----------
    vectorpath : string
        vector file or folder of vector files

    outputPath : string
        path to chunked vector files

    chunk : integer
        number of FID groups

    byarea : boolean
        split vector features where sum of areas of each split tends to be the same

    Return
    ----------
    list of FID list and vector file

    """

    listvectors = getVectorsList(vectorpath)
    params = []
    if os.path.isdir(vectorpath):
        for vect in listvectors:

            listfid = getFidList(vect)
            #TODO : split in chunks with sum of feature areas quite equal
            if byarea:
                vectorgeomtype = vf.getGeomType(vect)

                if vectorgeomtype in (3, 6, 1003, 1006):
                    listid = sba.getFidArea(vect)
                else:
                    raise Exception(
                        'Geometry type is not adapted to compute features areas'
                    )
                statsclasses = sba.getFeaturesFolds(listid, chunk)
                listfid = []
                for elt in statsclasses[0][1]:
                    listfid.append([x[0] for x in elt])
            else:
                listfid = [listfid[i::chunk] for i in range(chunk)]
                listfid = list(filter(None, listfid))

            if len(listfid) == 1:
                outfile = os.path.splitext(
                    os.path.basename(vect))[0] + "_stats.shp"
                params.append(
                    (vect, listfid[0], os.path.join(outputPath, outfile)))
            else:
                for idchunk, fidlist in enumerate(listfid):
                    outfile = os.path.splitext(os.path.basename(
                        vect))[0] + '_chk' + str(idchunk) + ".shp"
                    params.append(
                        (vect, fidlist, os.path.join(outputPath, outfile)))
    else:
        vect = vectorpath
        listfid = getFidList(vectorpath)
        listfid = [listfid[i::chunk] for i in range(chunk)]
        for fidlist in listfid:
            params.append((vect, fidlist))

    return params


def computZonalStats(path,
                     inr,
                     shape,
                     params,
                     output,
                     classes="",
                     bufferdist="",
                     nodata=0,
                     gdalpath="",
                     chunk=1,
                     byarea=False,
                     cache="1000",
                     systemcall=True,
                     oso=True):

    # clean geometries of input vector file
    if vf.getGeomType(shape) not in (1, 4, 1001, 1004):
        if os.path.splitext(shape)[1] == ".shp":
            tmp = os.path.join(path, "tmp.shp")

            checkGeom.checkGeometryAreaThreshField(shape, 1, 0, tmp)

            for ext in ['.shp', '.dbf', '.shx', '.prj', '.cpg']:
                try:
                    shutil.copy(
                        os.path.splitext(tmp)[0] + ext,
                        os.path.splitext(shape)[0] + ext)
                    os.remove(os.path.splitext(tmp)[0] + ext)
                except:
                    pass

        else:
            raise Exception("Only shapefile allowed for input vector file")

    chunks = splitVectorFeatures(shape, path, chunk, byarea)

    for block in chunks:
        zonalstats(path, inr, block, output, params, classes, bufferdist,
                   nodata, gdalpath, systemcall, cache)

    if oso:
        osoFormatting(output, classes)


def getVectorsChunks(inpath, inbase="dept_"):

    if not fut.FileSearch_AND(inpath, True, inbase, ".shp", "chk"):
        listout = fut.FileSearch_AND(inpath, True, inbase, ".shp", "stats")
    else:
        listout = fut.FileSearch_AND(inpath, True, inbase, ".shp", "chk")

    listofchkofzones = fut.sortByFirstElem([
        ("_".join(x.split('_')[0:len(x.split('_')) - 1]), x) for x in listout
    ])

    return listofchkofzones


def mergeSubVector(listofchkofzones,
                   outpath,
                   classes="",
                   outbase="departement_",
                   outzip=True,
                   oso=True,
                   logger=LOGGER):

    zoneval = listofchkofzones[0].split(
        '_')[len(listofchkofzones[0].split('_')) -
             1:len(listofchkofzones[0].split('_'))]
    outfile = os.path.join(outpath, outbase + zoneval[0] + '.shp')

    LOGGER.info("Production of vector file %s" % (outfile))

    mf.mergeVectors(listofchkofzones[1], outfile)

    if os.path.exists(outfile):
        for subzone in listofchkofzones[1]:
            for ext in ['.shp', '.dbf', '.shx', '.prj', '.cpg']:
                try:
                    os.remove(os.path.splitext(subzone)[0] + ext)
                except:
                    pass
        if oso:
            osoFormatting(outfile, classes, outfile)

        if outzip:
            outzip = os.path.splitext(outfile)[0] + '.zip'
            compressShape(outfile, outzip)


def compressShape(shapefile, outzip):

    with ZipFile(outzip, 'w') as myzip:
        for ext in ['.shp', '.dbf', '.shx', '.prj', '.cpg']:
            try:
                myzip.write(
                    os.path.splitext(shapefile)[0] + ext,
                    os.path.basename(os.path.splitext(shapefile)[0] + ext))
            except:
                pass


if __name__ == "__main__":
    if len(sys.argv) == 1:
        PROG = os.path.basename(sys.argv[0])
        print('      ' + sys.argv[0] + ' [options]')
        print("     Help : ", PROG, " --help")
        print("        or : ", PROG, " -h")
        sys.exit(-1)
    else:
        USAGE = "usage: %prog [options] "
        PARSER = argparse.ArgumentParser(
            description="Extract shapefile records",
            formatter_class=argparse.RawTextHelpFormatter)
        PARSER.add_argument("-wd", dest="path", action="store",\
                            help="working dir",\
                            required=True)
        PARSER.add_argument("-inr", dest="inr", nargs='+',\
                            help="input rasters list (classification, validity and confidence)",\
                            required=True)
        PARSER.add_argument("-nodata", dest="nodata", action="store",\
                            help="nodata value of input raster(s)", default=0)
        PARSER.add_argument("-shape", dest="shape", action="store",\
                            help="shapefiles path",\
                            required=True)
        PARSER.add_argument("-output", dest="output", action="store",\
                            help="vector output with statistics",\
                            required=True)
        PARSER.add_argument("-gdal", dest="gdal", action="store",\
                            help="gdal 2.2.4 binaries path "\
                            "(problem of very small features with lower gdal version)", \
                            default="")
        PARSER.add_argument("-chunk", dest="chunk", action="store",\
                            help="number of feature groups", default=1)
        PARSER.add_argument("-byarea", action='store_true',\
                            help="split vector features where sum of areas of each split tends to be the same", default=False)
        PARSER.add_argument("-params", dest="params", nargs='+', \
                            help="1:rate 2:statsmaj 3:statsmaj 4:stats, 2:stats_cl \n"\
                            "left side value corresponds to band or raster number \n"\
                            "right side value corresponds to the type of statistics \n"\
                            "stats: statistics of the band (mean_b, std_b, max_b, min_b) \n" \
                            "statsmaj: statistics of the band for pixel corresponding to the majority class \n"\
                            "(meanmaj, stdmaj, maxmaj, minmaj). Need to provide a categorical raster (rate statistics) \n" \
                            "rate: rate of each pixel value (classe names) \n" \
                            "stats_cl: statistics of the band for pixel corresponding to the required class \n"\
                            "(mean_cl, std_cl, max_cl, min_cl). Need to provide a categorical raster (rate statistics) \n" \
                            "val: value of corresponding pixel (only for Point geom)", default='1:stats')
        PARSER.add_argument("-classes", dest="classes", action="store",\
                            help="", default="")
        PARSER.add_argument("-buffer", dest="buff", action="store",\
                            help="", default="")
        PARSER.add_argument("-syscall", action='store_true',\
                            help="If True, use system call of gdalwrap binary", default=False)
        PARSER.add_argument("-gdal_cache", dest="cache", action="store",\
                            help="", default="1000")
        PARSER.add_argument("-oso", action='store_true',\
                            help="If True, format output vector for production", default=False)

        args = PARSER.parse_args()
        computZonalStats(args.path, args.inr, args.shape, args.params,
                         args.output, args.classes, args.buff, args.nodata,
                         args.gdal, args.chunk, args.byarea, args.cache,
                         args.syscall, args.iota2)
