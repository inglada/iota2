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
from itertools import chain
import datetime
import time
import csv
from itertools import groupby
#from osgeo.gdal import Dataset
import osgeo
import ogr
import gdal
import pandas as pad
import geopandas as gpad
import fiona
from shapely import wkt
from skimage.measure import label
from skimage.measure import regionprops
import numpy as np

try:
    from VectorTools import vector_functions as vf
    from VectorTools import BufferOgr as bfo
    from Common import FileUtils as fut
    from simplification import nomenclature
    from Common import Utils
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

def getUniqueId(csvpath):
    
    df = pad.read_csv(csvpath, header=None)
    
    return list(set(df.groupby(0).groups))


def countPixelByClass(databand, fid, band=0):

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

        col_names =  ['value', 'count']
        statsdf  = pad.DataFrame(columns = col_names)
        
        if len(np.unique(img)) != 1 or np.unique(img)[0] != 0:
            res = rastertmp.GetGeoTransform()[1]
            try:
                dataclean = data[data!=0]
                npcounts = np.array(np.unique(dataclean, return_counts=True)).T
                counts = npcounts.tolist()
            except:
                for reg in regionprops(img, data):
                    counts.append([[x for x in np.unique(reg.intensity_image) if x != 0][0], reg.area])
                
            if len(counts[0]) != 0:
                # test si counts a des valeurs !
                listlab = pad.DataFrame(data=counts, columns = col_names)
                # pourcentage
                listlab['rate'] = listlab['count'] / listlab['count'].sum()
                
                # classmaj
                classmaj = listlab[listlab['rate'] == max(listlab['rate'])]['value']       
                classmaj = classmaj.iloc[0]

                posclassmaj = np.where(data==int(classmaj))                

                # Transposition pour jointure directe
                listlabT = listlab.T
                classStats = pad.DataFrame(data=[listlabT.loc['rate'].values], index=[fid], columns=[str(int(x)) for x in listlabT.loc['value']])                

        listlab = listlabT = data = None
        
    else:
        raise Exception("Raster does not exist")
    
    return classStats, classmaj, posclassmaj

def rasterStats(band, nbband=0, posclassmaj=None):

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
        data = banddata.ReadAsArray()
        img = label(data)
        if len(np.unique(img)) != 1 or np.unique(img)[0] != 0:
                mean = round(np.mean(data[posclassmaj]), 2)
                std = round(np.std(data[posclassmaj]), 2)
                max = round(np.max(data[posclassmaj]), 2)
                min = round(np.min(data[posclassmaj]), 2)
                
        return mean, std, max, min


def definePandasDf(idvals, paramstats={1:'rate', 2:'statsmaj', 3:'stats_11'}, classes="/home/qt/thierionv/iota2/iota2/scripts/simplification/nomenclature17.cfg"):

    cols = []

    for param in paramstats:
        if paramstats[param] == "rate": 
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
        else:
            raise Exception("The method %s is not implemented")%(paramstats[param])

    cols.append('geometry')

    return gpad.GeoDataFrame(np.nan, index=idvals, columns=cols)        
    
def zonalstats(path, rasters, params, paramstats={}, bufferDist=None, gdalpath="", res=10, write_ouput=False, gdalcachemax="9000"):

    # issues sur frama : 1. nouveau : pour Zonal stats 2. modif : nomenclature => modification du fichier de configuration 
    # exemple de paramétrage de statistiques
    # paramstats = {1:"rate", 2:"statsmaj", 3:"statsmaj", 4:"stats", 2:stats_cl}
    # stats : mean_b, std_b, max_b, min_b
    # statsmaj : meanmaj, stdmaj, maxmaj, minmaj of majority class
    # rate : rate of each pixel value (classe names)
    # stats_cl : mean_cl, std_cl, max_cl, min_cl of one class    

    vector, idvals = params
    
    # if no vector subsetting (all features)
    if not idvals:
        idvals = getFidList(vector)
    
    # vector open and iterate features and/or buffer geom
    vectorname = os.path.splitext(os.path.basename(vector))[0]
    vectorgeomtype = vf.getGeomType(vector)
    if vectorgeomtype in (1, 4, 1001, 1004):
        if vectorgeomtype == 1:
            schema = {'geometry': 'Point', 'properties' : {}}
        elif vectorgeomtype == 4:
            schema = {'geometry': 'MultiPoint', 'properties' : {}}
            
        if not bufferDist:
            bufferDist = res / 2
        vectorbuff = vectorname + "buff.shp"
        lyr = bfo.bufferPoly(vector, vectorbuff, bufferDist=bufferDist)
    elif vectorgeomtype in (3, 6, 1003, 1006):
        if vectorgeomtype == 3:
            schema = {'geometry': 'Polygon', 'properties' : {}}
        elif vectorgeomtype == 6:
            schema = {'geometry': 'MultiPolygon', 'properties' : {}}
            
    else:
        raise Exception("Geometry type of vector file not handled")
    
    ds = vf.openToRead(vector)
    lyr = ds.GetLayer()
    spatialRef = lyr.GetSpatialRef().ExportToProj4()
    
    # Prepare stats DataFrame
    paramstats = {2:'statsmaj', 1:'rate', 3:'stats'}
    stats = definePandasDf(idvals, paramstats)

    # Iterate FID list
    for idval in idvals:        
    
        lyr.SetAttributeFilter("FID=" + str(idval))
        for feat in lyr:
            geom = feat.GetGeometryRef()
            if geom:
                geomdf = pad.DataFrame(index=[idval], columns=["geometry"], data=[str(geom.ExportToWkt())])
                stats.update(geomdf)

        if vectorbuff:vector=vectorbuff
                
        # rasters  creation
        if gdalpath != "" and gdalpath is not None:
            gdalpath = gdalpath + "/"
        else:
            gdalpath = ""

        bands = []
        success = True
        for idx, raster in enumerate(rasters):
            if write_ouput:
                tmpfile = os.path.join(path, 'rast_%s_%s_%s'%(vectorname, str(idval), idx))            
            try:
                if write_ouput:
                    cmd = '%sgdalwarp -tr %s %s -tap -q -overwrite -cutline %s '\
                          '-crop_to_cutline --config GDAL_CACHEMAX %s -wm %s '\
                          '-wo NUM_THREADS=ALL_CPUS -cwhere "FID=%s" %s %s'%(gdalpath, res, res, vector, gdalcachemax, gdalcachemax, idval, raster, tmpfile)
                    Utils.run(cmd)
                else:                    
                    gdal.SetConfigOption("GDAL_CACHEMAX", gdalcachemax)
                    tmpfile = gdal.Warp('', raster, xRes = res, yRes = res, targetAlignedPixels = True, cutlineDSName = vector, cropToCutline = True, \
                                        cutlineWhere = "FID=%s"%(idval), format = 'MEM', warpMemoryLimit=gdalcachemax, warpOptions = ["NUM_THREADS=ALL_CPUS"])
                
                bands.append(tmpfile)

                success = True
            except:
                success = False            
                pass

        if success:
            for param in paramstats:
                # Multi-raster / Multi-band
                if len(rasters) != 1:
                    band = bands[int(param) - 1]
                    nbband = 1
                else:
                    band = tmpfile
                    nbband = int(param)                                    
                    
                if band:                    
                    methodstat = paramstats[param]

                    if methodstat == 'rate':
                        classStats, classmaj, posclassmaj = countPixelByClass(band, idval, nbband)
                        stats.update(classStats)

                    elif methodstat == 'stats':
                        cols = ["meanb%s"%(int(param)), "stdb%s"%(int(param)), "maxb%s"%(int(param)), "minb%s"%(int(param))]
                        stats.update(pad.DataFrame(data=[rasterStats(band, nbband)], index=[idval], columns = cols))
                        
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
                                raise Exception("No classification raster provided")
                            
                            classStats, classmaj, posclassmaj = countPixelByClass(bandrate, idval, nbbandrate)
                            classStats = None

                        cols = ["meanmajb%s"%(int(param)), "stdmajb%s"%(int(param)), "maxmajb%s"%(int(param)), "minmajb%s"%(int(param))]
                        stats.update(pad.DataFrame(data=[rasterStats(band, nbband, posclassmaj)], index=[idval], columns = cols))
                        
                    elif "stats_" in methodstat:                        
                        if "rate" in paramstats.values():
                            # get positions of class
                            cl = paramstats[param].split('_')[1]
                            idxbdclasses = [x for x in paramstats if paramstats[x] == "rate"][0]
                            rastertmp = gdal.Open(bands[idxbdclasses - 1], 0)
                            data = rastertmp.ReadAsArray()
                            posclass = np.where(data==int(cl))
                            data = None                            
                        else:
                            raise Exception("No classification raster provided")

                        cols = ["meanb%sc%s"%(int(param), cl), "stdb%sc%s"%(int(param), cl), "maxb%sc%s"%(int(param), cl), "minb%sc%s"%(int(param), cl)]                        
                        stats.update(pad.DataFrame(data=[rasterStats(band, nbband, posclass)], index=[idval], columns = cols))

                    else:
                        print "The method %s is not implemented"%(paramstats[param])

                band = None            
        else:
            print "gdalwarp problem for feature %s (geometry error, too small area, etc.)"%(idval)

            
    # Export
    stats["geometry"] = stats["geometry"].apply(wkt.loads)
    statsfinal = gpad.GeoDataFrame(stats, geometry="geometry")
    statsfinal.fillna(0, inplace=True)
    statsfinal.crs = {'init':'proj4:%s'%(spatialRef)}

    # change column names
    # get multi-level nomenclature
    classes="/home/qt/thierionv/iota2/iota2/scripts/simplification/nomenclature17.cfg"
    nomenc = nomenclature.Iota2Nomenclature(classes, 'cfg')    
    desclasses = nomenc.HierarchicalNomenclature.get_level_values(nomenc.getLevelNumber() - 1)
    cols = [(str(x), str(z)) for x, y, w, z in desclasses]

    for col in cols:
        statsfinal.rename(columns={col[0]:col[1].decode('utf8')}, inplace=True)

    # change columns type
    schema['properties'] = OrderedDict([(x, 'float:10.2') for x in list(statsfinal.columns) if x != 'geometry'])    

    # exportation
    statsfinal.to_file("/home/qt/thierionv/teststats3.shp", driver="ESRI Shapefile", schema=schema, encoding='utf-8')
    # Export depending on columns number (shapefile, sqlite, geojson) # Check Issue on framagit
    
def getParameters(vectorpath, csvstorepath="", chunk=1):
    
    listvectors = getVectorsList(vectorpath)
    params = []
    if os.path.isdir(vectorpath):
        for vect in listvectors:
            listfid = getFidList(vect)
            # prepare list of fids to remove in listfid before chunk
            
            #TODO : split in chunks with sum of feature areas quite equal
            listfid = [listfid[i::chunk] for i in xrange(chunk)]
            for fidlist in listfid:                 
                params.append((vect, fidlist))
    else:
        listfid = getFidList(vectorpath)
        listfid = [listfid[i::chunk] for i in xrange(chunk)]        
        for fidlist in listfid:                 
            params.append((vect, fidlist))

    return params

def computZonalStats(path, inr, shape, csvstore, gdal, chunk=1):

    #TODO : optimize chunk with real-time HPC ressources
    params = getParameters(shape, csvstore, chunk)

    for parameters in params:
        zonalstats(path, inr, parameters, gdal, chunk)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        PROG = os.path.basename(sys.argv[0])
        print '      '+sys.argv[0]+' [options]'
        print "     Help : ", PROG, " --help"
        print "        or : ", PROG, " -h"
        sys.exit(-1)
    else:
        USAGE = "usage: %prog [options] "
        PARSER = argparse.ArgumentParser(description="Extract shapefile records")
        PARSER.add_argument("-wd", dest="path", action="store",\
                            help="working dir",\
                            required=True)
        PARSER.add_argument("-inr", dest="inr", nargs ='+',\
                            help="input rasters list (classification, validity and confidence)",\
                            required=True)
        PARSER.add_argument("-shape", dest="shape", action="store",\
                            help="shapefiles path",\
                            required=True)
        PARSER.add_argument("-csvpath", dest="csvpath", action="store",\
                            help="stats output path",\
                            required=True)        
        PARSER.add_argument("-gdal", dest="gdal", action="store",\
                            help="gdal 2.2.4 binaries path (problem of very small features with lower gdal version)", default = "")
        PARSER.add_argument("-chunk", dest="chunk", action="store",\
                            help="number of feature groups", default=1)        
        
        args = PARSER.parse_args()

        computZonalStats(args.path, args.inr, args.shape, args.csvpath, args.gdal, args.chunk)
