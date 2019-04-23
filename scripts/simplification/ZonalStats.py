#!/usr/bin/python
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

import os, sys, argparse
from collections import OrderedDict
import osgeo
import ogr
import gdal
import pandas as pad
import geopandas as gpad
from skimage.measure import label
from skimage.measure import regionprops
import numpy as np

try:
    from VectorTools import vector_functions as vf
    from VectorTools import BufferOgr as bfo
    from VectorTools import splitByArea as sba
    from Common import FileUtils as fut
    from Common import Utils    
    from simplification import nomenclature
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
    for root, dirs, files in os.walk(path):
        for filein in files:
            if ".shp" in filein:
                listfiles.append(os.path.join(root, filein))

    return listfiles

def countPixelByClass(databand, fid=0, band=0):
    """Compute rates of unique values of a categorical raster and store them in a Pandas DataFrame:

    Parameters
    ----------
    databand : gdal raster file or osgeo.gdal.Dataset
        categorical raster

    fid : int
        FID value of feature of zonal vector (DataFrame storage)

    band : int
        band number of databand input parameter

    Return
    ------
    classStats
        Pandas DataFrame

    classmaj
        integer value of the majority class

    posclassmaj
        numpy array of position of majority class
    """

    if databand:
        if isinstance(databand, str):
            if os.path.exists(databand):
                rastertmp = gdal.Open(databand, 0)
            else:
                raise Exception('Raster file %s not exist'%(databand))
        elif isinstance(databand, osgeo.gdal.Dataset):
            rastertmp = databand
        else:
            raise Exception('Type of raster dataset not handled')

        banddata = rastertmp.GetRasterBand(band)
        data = banddata.ReadAsArray()
        img = label(data)
        counts = []

        col_names = ['value', 'count']

        if len(np.unique(img)) != 1 or np.unique(img)[0] != 0:
            res = rastertmp.GetGeoTransform()[1]
            try:
                dataclean = data[data != 0]
                npcounts = np.array(np.unique(dataclean, return_counts=True)).T
                counts = npcounts.tolist()
            except:
                for reg in regionprops(img, data):
                    counts.append([[x for x in np.unique(reg.intensity_image) if x != 0][0], reg.area])

            if len(counts[0]):
                # test si counts a des valeurs !
                listlab = pad.DataFrame(data=counts, columns=col_names)
                # pourcentage
                listlab['rate'] = listlab['count'] / listlab['count'].sum()

                # classmaj
                classmaj = listlab[listlab['rate'] == max(listlab['rate'])]['value']
                classmaj = classmaj.iloc[0]

                posclassmaj = np.where(data == int(classmaj))

                # Transposition pour jointure directe
                listlabT = listlab.T
                classStats = pad.DataFrame(data=[listlabT.loc['rate'].values], index=[fid], columns=[str(int(x)) for x in listlabT.loc['value']])

        listlab = listlabT = data = None

    else:
        raise Exception("Raster does not exist")

    return classStats, classmaj, posclassmaj

def rasterStats(band, nbband=0, posclassmaj=None, posToRead=None):
    """Compute descriptive statistics of a numpy array or a gdal raster:

    Parameters
    ----------
    band : gdal raster file or osgeo.gdal.Dataset
        raster on which compute statistics

    nbband : int
        band number of band input parameter

    posclassmaj
        numpy array of position of majority class

    posToRead : tuple
        col / row coordinates on which extract pixel value

    Return
    ------
    mean, std, max, min
        float

    pixel value
        float
    """
    if band:
        if isinstance(band, str):
            if os.path.exists(band):
                rastertmp = gdal.Open(band, 0)
            else:
                raise Exception('Raster file %s not exist'%(band))
        elif isinstance(band, osgeo.gdal.Dataset):
            rastertmp = band
        else:
            raise Exception('Type of raster dataset not handled')

        banddata = rastertmp.GetRasterBand(nbband)

        if not posToRead:
            data = banddata.ReadAsArray()
            img = label(data)
            # TODO : when data is empty (else) ?
            if len(np.unique(img)) != 1 or np.unique(img)[0] != 0:
                mean = round(np.mean(data[posclassmaj]), 2)
                std = round(np.std(data[posclassmaj]), 2)
                maxval = round(np.max(data[posclassmaj]), 2)
                minval = round(np.min(data[posclassmaj]), 2)

            stats = (mean, std, maxval, minval)
        else:
            stats = np.float(banddata.ReadAsArray()[posToRead[1], posToRead[0]])

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
            if classes != "":
                nomenc = nomenclature.Iota2Nomenclature(classes, 'cfg')
                desclasses = nomenc.HierarchicalNomenclature.get_level_values(nomenc.getLevelNumber() - 1)
                [cols.append(str(x)) for x, y, w, z in desclasses]
        elif paramstats[param] == "stats":
            [cols.append(x) for x in ["meanb%s"%(param), "stdb%s"%(param), "maxb%s"%(param), "minb%s"%(param)]]
        elif paramstats[param] == "statsmaj":        
            [cols.append(x) for x in ["meanmajb%s"%(param), "stdmajb%s"%(param), "maxmajb%s"%(param), "minmajb%s"%(param)]]
        elif "stats_" in paramstats[param]:
            cl = paramstats[param].split('_')[1]            
            [cols.append(x) for x in ["meanb%sc%s"%(param, cl), "stdb%sc%s"%(param, cl), "maxb%sc%s"%(param, cl), "minb%sc%s"%(param, cl)]]
        elif "val" in paramstats[param]:
            [cols.append("valb%s"%(param))]
        else:
            raise Exception("The method %s is not implemented")%(paramstats[param])


    statsgpad = gpad.GeoDataFrame(np.nan, index=idvals, columns=cols)
    geoframe = gpad.GeoDataFrame(pad.concat([geoframe, statsgpad], axis=1), geometry=geoframe['geometry'], crs=geoframe.crs)
    
    return geoframe

def checkmethodstats(method):

    if 'stats_' in method:
        method = 'stats'

    return method in ('stats', 'statsmaj', 'rate', 'val')

def zonalstats(path, rasters, params, output, paramstats, classes="", bufferDist=None, gdalpath="", res=10, write_ouput=False, gdalcachemax="9000"):
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

    write_ouput : boolean
        if True, wrapped raster are stored in working dir

    gdalcachemax : string
        gdal cache for wrapping operation (in Mb)

    """
    # Get vector file and FID list
    vector, idvals = params

    # Get bands or raster number
    if len(rasters) != 1:
        nbbands = len(rasters)
    else:
        nbbands = fut.getRasterNbands(rasters[0])

    # Format requested statistics
    if isinstance(paramstats, list):
        # List of methods (bash)
        if ':' in paramstats[0]:
            paramstats = dict([(x.split(':')[0], x.split(':')[1]) for x in paramstats])

        # Unique method without band / raster number
        elif len(paramstats) == 1:
            # Build statistics method dictionary
            tmpdict = {}
            for idx in nbbands:
                tmpdict[idx + 1] = str(paramstats[0])
            paramstats = tmpdict

    # Check statistics methods validity
    for keys in paramstats:
        if not checkmethodstats(paramstats[keys]):
            raise Exception('The method %s is not implemented'%(paramstats[0]))

    # check inputs integrity
    # same extent and resolution ?
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

    # requested stats and band number ?
    maxband = max([int(x) for x in paramstats.keys()])
    if len(rasters) != 1:
        if nbbands < maxband:
            raise Exception("Band ids in requested stats and number of input rasters "\
                            "or bands number of input raster do not correspond")

    res = abs(fut.getRasterResolution(rasters[0])[0])

    # if no vector subsetting (all features)
    if not idvals:
        idvals = getFidList(vector)

    # vector open and iterate features and/or buffer geom
    vectorname = os.path.splitext(os.path.basename(vector))[0]
    vectorgeomtype = vf.getGeomType(vector)
    vectorbuff = None

    # Value extraction
    if not bufferDist and vectorgeomtype in (1, 4, 1001, 1004):
        if 'val' in paramstats.values():
            if vectorgeomtype == 1:
                schema = {'geometry': 'Point', 'properties' : {}}
            elif vectorgeomtype == 4:
                schema = {'geometry': 'MultiPoint', 'properties' : {}}
        else:
            raise Exception("Only pixel value extraction available "\
                            "when Point geometry without buffer distance is provided")

    # Stats extraction
    else:
        # Point geometry
        if vectorgeomtype in (1, 4, 1001, 1004):
            if vectorgeomtype == 1:
                schema = {'geometry': 'Point', 'properties' : {}}
            elif vectorgeomtype == 4:
                schema = {'geometry': 'MultiPoint', 'properties' : {}}
            vectorbuff = vectorname + "buff.shp"
            _ = bfo.bufferPoly(vector, vectorbuff, bufferDist=bufferDist)

        # Polygon geometry
        elif vectorgeomtype in (3, 6, 1003, 1006):
            if vectorgeomtype == 3:
                schema = {'geometry': 'Polygon', 'properties' : {}}
            elif vectorgeomtype == 6:
                schema = {'geometry': 'MultiPolygon', 'properties' : {}}
        else:
            raise Exception("Geometry type of vector file not handled")


    # Vector reading
    vectgpad = gpad.read_file(vector)

    dataset = vf.openToRead(vector)
    lyr = dataset.GetLayer()
    spatialRef = lyr.GetSpatialRef().ExportToProj4()

    # Prepare stats DataFrame
    stats = definePandasDf(vectgpad, idvals, paramstats, classes)

    # Iterate FID list
    for idval in idvals:
        if vectorgeomtype in (1, 4, 1001, 1004):
            lyr.SetAttributeFilter("FID=" + str(idval))
            for feat in lyr:
                geom = feat.GetGeometryRef()
                if geom:
                    xpt, ypt, _ = geom.GetPoint()

        if vectorbuff:
            vector = vectorbuff

        # creation of wrapped rasters
        if gdalpath != "" and gdalpath is not None:
            gdalpath = gdalpath + "/"
        else:
            gdalpath = ""

        bands = []
        success = True
        for idx, raster in enumerate(rasters):

            # Value extraction
            if 'val' in paramstats.values():
                if vectorgeomtype not in (1, 4, 1001, 1004):
                    raise Exception("Type of input vector %s must be "\
                                    "'Point' for pixel value extraction"%(vector))
                else:
                    bands.append(raster)
                    tmpfile = raster

            # Stats Extraction
            else:
                tmpfile = os.path.join(path, 'rast_%s_%s_%s'%(vectorname, str(idval), idx))
                try:
                    # TODO : test gdal version : >= 2.2.4
                    if write_ouput:
                        cmd = '%sgdalwarp -tr %s %s -tap -q -overwrite -cutline %s '\
                              '-crop_to_cutline --config GDAL_CACHEMAX %s -wm %s '\
                              '-wo "NUM_THREADS=ALL_CPUS" -wo "CUTLINE_ALL_TOUCHED=YES" "\
                              "-cwhere "FID=%s" %s %s -ot Float32'%(gdalpath, \
                                                                    res, \
                                                                    res, \
                                                                    vector, \
                                                                    gdalcachemax, \
                                                                    gdalcachemax, \
                                                                    idval, \
                                                                    raster, \
                                                                    tmpfile)
                        Utils.run(cmd)
                    else:
                        gdal.SetConfigOption("GDAL_CACHEMAX", gdalcachemax)
                        tmpfile = gdal.Warp('', raster, xRes=res, \
                                            yRes=res, targetAlignedPixels=True, \
                                            cutlineDSName=vector, cropToCutline=True, \
                                            cutlineWhere="FID=%s"%(idval), format='MEM', \
                                            warpMemoryLimit=gdalcachemax, \
                                            warpOptions=[["NUM_THREADS=ALL_CPUS"], ["CUTLINE_ALL_TOUCHED=YES"]])

                    bands.append(tmpfile)
                    success = True
                except:
                    success = False

        if success:
            for param in paramstats:
                # Multi-raster / Multi-band data preparation
                if len(rasters) != 1:
                    band = bands[int(param) - 1]
                    nbband = 1
                else:
                    band = tmpfile
                    nbband = int(param)

                # Statistics extraction
                if band:
                    methodstat = paramstats[param]
                    
                    ### Categorical statistics ###
                    if methodstat == 'rate':
                        classStats, classmaj, posclassmaj = countPixelByClass(band, idval, nbband)
                        stats.update(classStats)

                        # Add columns when pixel values are not identified in nomenclature file
                        if list(classStats.columns) != list(stats.columns):
                            newcols = list(set(list(classStats.columns)).difference(set(list(stats.columns))))
                            pad.concat([stats, classStats[newcols]], axis=1)

                    elif methodstat == 'stats':

                        cols = ["meanb%s"%(int(param)), "stdb%s"%(int(param)), \
                                "maxb%s"%(int(param)), "minb%s"%(int(param))]
                        
                        stats.update(pad.DataFrame(data=[rasterStats(band, nbband)], \
                                                   index=[idval], \
                                                   columns=cols))

                    ### Descriptive statistics for majority class ###
                    elif methodstat == 'statsmaj':
                        if not classmaj:
                            if "rate" in paramstats.values():
                                idxbdclasses = [x for x in paramstats if paramstats[x] == "rate"][0]
                                if len(rasters) != 1:
                                    bandrate = bands[idxbdclasses - 1]
                                    nbbandrate = 0
                                else:
                                    bandrate = band
                                    nbbandrate = idxbdclasses - 1
                            else:
                                raise Exception("No classification raster provided "\
                                                "to check position of majority class")

                            classStats, classmaj, posclassmaj = countPixelByClass(bandrate, idval, nbbandrate)
                            classStats = None

                        cols = ["meanmajb%s"%(int(param)), "stdmajb%s"%(int(param)), \
                                "maxmajb%s"%(int(param)), "minmajb%s"%(int(param))]
                        stats.update(pad.DataFrame(data=[rasterStats(band, nbband, posclassmaj)], \
                                                   index=[idval], \
                                                   columns=cols))

                    ### Descriptive statistics for one class ###
                    elif "stats_" in methodstat:
                        if "rate" in paramstats.values():
                            
                            # get positions of class in categorical raster
                            reqclass = paramstats[param].split('_')[1]
                            # find index band / raster of categorical raster
                            idxbdclasses = [x for x in paramstats if paramstats[x] == "rate"][0]
                            # get positions array
                            rastertmp = gdal.Open(bands[idxbdclasses - 1], 0)
                            data = rastertmp.ReadAsArray()
                            posclass = np.where(data == int(reqclass))
                            data = None
                        else:
                            raise Exception("No classification raster provided "\
                                            "to check position of requested class")

                        cols = ["meanb%sc%s"%(int(param), reqclass), "stdb%sc%s"%(int(param), reqclass), \
                                "maxb%sc%s"%(int(param), reqclass), "minb%sc%s"%(int(param), reqclass)]

                        stats.update(pad.DataFrame(data=[rasterStats(band, nbband, posclass)], \
                                                   index=[idval], \
                                                   columns=cols))
                    ### Pixel value extraction ###
                    elif "val" in methodstat:
                        colpt, rowpt = fut.geoToPix(band, xpt, ypt)
                        cols = "valb%s"%(param)
                        stats.update(pad.DataFrame(data=[rasterStats(band, nbband, None, (colpt, rowpt))], \
                                                   index=[idval], \
                                                   columns=[cols]))
                    else:
                        print("The method %s is not implemented"%(paramstats[param]))

                band = None

            if write_ouput:
                os.remove(tmpfile)

        else:
            print("gdalwarp problem for feature %s (geometry error, too small area, etc.)"%(idval))

    # replace NAN values by zero
    stats.fillna(0, inplace=True)

    # change column names if rate stats expected and nomenclature file is provided
    if "rate" in paramstats and classes != "":
        # get multi-level nomenclature
        nomenc = nomenclature.Iota2Nomenclature(classes, 'cfg')
        desclasses = nomenc.HierarchicalNomenclature.get_level_values(nomenc.getLevelNumber() - 1)
        cols = [(str(x), str(z)) for x, y, w, z in desclasses]

        # rename columns with alias
        for col in cols:
            stats.rename(columns={col[0]:col[1].decode('utf8')}, inplace=True)

    # change columns type
    schema['properties'] = OrderedDict([(x, 'float:10.2') for x in list(stats.columns) \
                                        if x != 'geometry'])

    # exportation
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
        raise Exception("The output format '%s' is not handled"%(outformat[1:]))

    if not convert:
        stats.to_file(output, driver=driver, schema=schema, encoding='utf-8')
    else:
        outputinter = os.path.splitext(output)[0] + '.shp'
        stats.to_file(outputinter, driver=driver, schema=schema, encoding='utf-8')
        output = os.path.splitext(output)[0] + '.sqlite'
        Utils.run('ogr2ogr -f SQLite %s %s'%(output, outputinter))

def splitVectorFeatures(vectorpath, chunk=1, byarea=False):
    """Split FID list of a list of vector files in equal groups:

    Parameters
    ----------
    vectorpath : string
        vector file or folder of vector files

    chunk : integer
        number of FID groups

    byarea : boolean
        split vector features where each split's sum tends to be the same

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
                listid = sba.getFidArea(vect)
                statsclasses = sba.getFeaturesFolds(listid, chunk)
                listfid = []
                for elt in statsclasses[0][1]:
                    listfid.append([x[0] for x in elt])
            else:
                listfid = [listfid[i::chunk] for i in range(chunk)]
                
            for fidlist in listfid:
                params.append((vect, fidlist))
    else:
        vect = vectorpath
        listfid = getFidList(vectorpath)
        listfid = [listfid[i::chunk] for i in range(chunk)]
        for fidlist in listfid:
            params.append((vect, fidlist))

    return params

def computZonalStats(path, inr, shape, params, output, classes="", buffer="", gdalpath="", chunk=1, cache="1000", write_outputs=False):

    chunks = splitVectorFeatures(shape, chunk)

    for block in chunks:
        zonalstats(path, inr, block, output, params, classes, buffer, gdalpath, write_outputs, cache)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        PROG = os.path.basename(sys.argv[0])
        print('      '+sys.argv[0]+' [options]')
        print("     Help : ", PROG, " --help")
        print("        or : ", PROG, " -h")
        sys.exit(-1)
    else:
        USAGE = "usage: %prog [options] "
        PARSER = argparse.ArgumentParser(description="Extract shapefile records")
        PARSER.add_argument("-wd", dest="path", action="store",\
                            help="working dir",\
                            required=True)
        PARSER.add_argument("-inr", dest="inr", nargs='+',\
                            help="input rasters list (classification, validity and confidence)",\
                            required=True)
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
        PARSER.add_argument("-params", dest="params", nargs='+',\
                            help="1:rate 2:statsmaj 3:statsmaj 4:stats, 2:stats_cl"\
                            "left side value corresponds to band or raster number"\
                            "right side value corresponds to the type of statistics"\
                            "stats: statistics of the band (mean_b, std_b, max_b, min_b)" \
                            "statsmaj: statistics of the band for pixel corresponding to the majority class "\
                            "(meanmaj, stdmaj, maxmaj, minmaj). Need to provide a categorical raster (rate statistics)" \
                            "rate: rate of each pixel value (classe names)" \
                            "stats_cl: statistics of the band for pixel corresponding to the required class "\
                            "(mean_cl, std_cl, max_cl, min_cl). Need to provide a categorical raster (rate statistics)" \
                            "val: value of corresponding pixel (only for Point geom)", default='1:stats')
        PARSER.add_argument("-classes", dest="classes", action="store",\
                            help="", default="")
        PARSER.add_argument("-buffer", dest="buffer", action="store",\
                            help="", default="")
        PARSER.add_argument("-write_outputs", action='store_true',\
                            help="", default=False)
        PARSER.add_argument("-gdal_cache", dest="cache", action="store",\
                            help="", default="1000")

        args = PARSER.parse_args()
        computZonalStats(args.path, args.inr, args.shape, args.params, args.output, args.classes, args.buffer, args.gdal, args.chunk, args.cache, args.write_outputs)
