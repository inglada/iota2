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
import datetime
import time
import csv
from itertools import groupby
import ogr
import gdal
import pandas as pad
import geopandas as gpad
from skimage.measure import label
from skimage.measure import regionprops
import numpy as np

try:
    from VectorTools import vector_functions as vf
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


def CountPixelByClass(databand, fid):
    # TODO : 1 méthode pour les statistiques qualitatives (parts de valeur de pixel)
    # TODO : 1 méthode pour les statistiques quantitatives (mean, std, max, min)    
    # np.array(np.unique(x, return_counts=True)).T

    if os.path.exists(databand):
        rastertmp = gdal.Open(databand, 0)
        data = rastertmp.ReadAsArray()
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
                    print reg.intensity_image
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
                classStats = pad.DataFrame(data=[listlabT.loc['rate'].values], index=[fid], columns=[int(x) for x in listlabT.loc['value']])

        listlab = listlabT = data = None
        
    else:
        raise Exception("Raster does not exist")
    
    return classStats, classmaj, posclassmaj

def RasterStats(band, posclassmaj=None):

    if os.path.exists(band):
        rastertmp = gdal.Open(band, 0)
        data = rastertmp.ReadAsArray()
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
            [cols.append(x) for x, y, w, z in desclasses]
        elif paramstats[param] == "stats":
            [cols.append(x) for x in ["meanb%s"%(param), "stdb%s"%(param), "maxb%s"%(param), "minb%s"%(param)]]
        elif paramstats[param] == "statsmaj":        
            [cols.append(x) for x in ["meanmajb%s"%(param), "stdmajb%s"%(param), "maxmajb%s"%(param), "minmajb%s"%(param)]]
        elif "stats_" in paramstats[param]:
            cl = paramstats[param].split('_')[1]            
            [cols.append(x) for x in ["meanb%sc%s"%(param, cl), "stdb%sc%s"%(param, cl), "maxb%sc%s"%(param, cl), "minb%sc%s"%(param, cl)]]
        else:
            raise Exception("The method %s is not implemented")%(paramstats[param])
        
    return pad.DataFrame(np.nan, index=idvals, columns=cols)
    
def zonalstats(path, rasters, params, gdalpath = "", res = 10):
    
    vector, idvals, csvstore, clipvalue = params

    stats = []
    # vector open and iterate features
    vectorname = os.path.splitext(os.path.basename(vector))[0]
    ds = vf.openToRead(vector)
    lyr = ds.GetLayer()

    # Prepare stats DataFrame
    paramstats = {2:'statsmaj', 1:'rate', 3:'stats'}
    stats = definePandasDf(idvals, paramstats)

    for idval in idvals:        
    
        lyr.SetAttributeFilter("FID=" + str(idval))
        for feat in lyr:
            geom = feat.GetGeometryRef()
            area = geom.GetArea()

        # rasters  creation
        if gdalpath != "" and gdalpath is not None:
            gdalpath = gdalpath + "/"
        else:
            gdalpath = ""

        bands = []
        success = True

        for idx, raster in enumerate(rasters):
            tmpfile = os.path.join(path, 'rast_%s_%s_%s'%(vectorname, str(idval), idx))
            bands.append(tmpfile)

            try:
                cmd = '%sgdalwarp -tr %s %s -tap -q -overwrite -cutline %s '\
                      '-crop_to_cutline --config GDAL_CACHEMAX 9000 -wm 9000 '\
                      '-wo NUM_THREADS=ALL_CPUS -cwhere "FID=%s" %s %s'%(gdalpath, res, res, vector, idval, raster, tmpfile)        
                Utils.run(cmd)
                success = True
            except:
                success = False            
                pass


        if success:
            # analyze raster
            idxband  = 0
            
            # issues sur frama : 1. nouveau : pour Zonal stats 2. modif : nomenclature => modification du fichier de configuration 
            # exemple de paramétrage de statistiques
            # paramstats = {1:"rate", 2:"statsmaj", 3:"statsmaj", 4:"stats", 2:stats_cl}
            # stats : mean_b, std_b, max_b, min_b
            # statsmaj : meanmaj, stdmaj, maxmaj, minmaj of majority class
            # rate : rate of each pixel value (classe names)
            # stats_cl : mean_cl, std_cl, max_cl, min_cl of one class
            # for param in params:
            #     ...
            #for band in bands:
            for param in paramstats:
                band = bands[int(param) - 1]
                if os.path.exists(band):
                    methodstat = paramstats[param]
                    if methodstat == 'rate':
                        classStats, classmaj, posclassmaj = CountPixelByClass(band, idval)
                        stats.update(classStats)
                    elif methodstat == 'stats':
                        cols = ["meanb%s"%(int(param)), "stdb%s"%(int(param)), "maxb%s"%(int(param)), "minb%s"%(int(param))]
                        stats.update(pad.DataFrame(data=[RasterStats(band)], index=[idval], columns = cols))
                    elif methodstat == 'statsmaj':
                        if not classmaj:                            
                            if "rate" in paramstats.values():
                                idxbdclasses = [x for x in paramstats if paramstats[x] == "rate"][0]
                                classStats, classmaj, posclassmaj = CountPixelByClass(bands[idxbdclasses - 1], idval)
                            else:
                                raise Exception("No classification raster provided")
                            
                        cols = ["meanmajb%s"%(int(param)), "stdmajb%s"%(int(param)), "maxmajb%s"%(int(param)), "minmajb%s"%(int(param))]
                        stats.update(pad.DataFrame(data=[RasterStats(band, posclassmaj)], index=[idval], columns = cols))
                        
                    elif "stats_" in methodstat:                        
                        if "rate" in paramstats.values():
                            # get positions of class
                            cl = paramstats[param].split('_')[1]
                            idxbdclasses = [x for x in paramstats if paramstats[x] == "rate"][0]
                            rastertmp = gdal.Open(bands[idxbdclasses - 1], 0)
                            data = rastertmp.ReadAsArray()
                            posclass = np.where(data==int(cl))
                        else:
                            raise Exception("No classification raster provided")

                        cols = ["meanb%sc%s"%(int(param), cl), "stdb%sc%s"%(int(param), cl), "maxb%sc%s"%(int(param), cl), "minb%sc%s"%(int(param), cl)]                        
                        stats.update(pad.DataFrame(data=[RasterStats(band, posclass)], index=[idval], columns = cols))

                        data = band = None
                    else:
                        print "The method %s is not implemented"%(paramstats[param])
                            
                    '''
                    rastertmp = gdal.Open(band, 0)
                    data = rastertmp.ReadAsArray()
                    img = label(data)
                    listlab = []
                    if len(np.unique(img)) != 1 or np.unique(img)[0] != 0:

                            
                            res = rastertmp.GetGeoTransform()[1]
                            try:
                                for reg in regionprops(img, data):
                                    listlab.append([[x for x in np.unique(reg.intensity_image) if x != 0][0], reg.area])
                            except:
                                elts, cptElts = np.unique(data, return_counts=True)
                                for idx, elts in enumerate(elts):
                                    if elts != 0:
                                        listlab.append([elts, cptElts[idx]])


                            if len(listlab) != 0:                
                                classmaj = [y for y in listlab if y[1] == max([x[1] for x in listlab])][0][0]
                                posclassmaj = np.where(data==classmaj)
                                results = []

                                for i, g in groupby(sorted(listlab), key = lambda x: x[0]):
                                    results.append([i, sum(v[1] for v in g)])

                                sumpix = sum([x[1] for x in results])
                                for elt in [[int(w), round(((float(z) * float(res) * float(res)) /float(sumpix)), 2)] for w, z in results]:
                                    results_final.append([idval, 'classif', 'part'] + elt)

                        if idxband != 1:
                            if idxband == 2:
                                results_final.append([idval, 'confidence', 'mean', int(classmaj), round(np.mean(data[posclassmaj]), 2)])
                            elif idxband == 3:
                                results_final.append([idval, 'validity', 'mean', int(classmaj), round(np.mean(data[posclassmaj]), 2)])
                                results_final.append([idval, 'validity', 'std', int(classmaj), round(np.std(data[posclassmaj]), 2)])                
                    else:
                        if idxband == 1:
                            results_final.append([idval, 'classif', 'part', 0, 0])
                        elif idxband == 2:
                            results_final.append([idval, 'confidence', 'mean', 0, 0])
                        elif idxband == 3:                        
                            results_final.append([idval, 'validity', 'mean', 0, 0])
                            results_final.append([idval, 'validity', 'std', 0, 0])

                    data = img = None

                    '''
                print stats
                #Utils.run("rm %s"%(band))

                #rastertmp = None
                #stats.append(results_final)
        else:
            print "gdal problem"
            '''
            results_final.append([[idval, 'classif', 'part', 0, 0], [idval, 'confidence', 'mean', 0, 0], [idval, 'validity', 'mean', 0, 0],[idval, 'validity', 'std', 0, 0]])
            print "Feature with FID = %s of shapefile %s with null stats (maybe its size is too small)"%(idval, vector)
            stats.append(results_final[0])
            '''
    '''
    with open(csvstore, 'a') as myfile:
        writer = csv.writer(myfile)
        writer.writerows(stats)
    '''
    
def getParameters(vectorpath, csvstorepath, chunk=1):
    
    listvectors = getVectorsList(vectorpath)
    params = []
    if os.path.isdir(vectorpath):
        for vect in listvectors:
            listfid = getFidList(vect)
            clipvalue = os.path.splitext(os.path.basename(vect))[0]
            csvstore = os.path.join(csvstorepath, "stats_%s"%(clipvalue))
            # prepare list of fids to remove in listfid before chunk 
            #TODO : split in chunks with sum of feature areas quite equal
            listfid = [listfid[i::chunk] for i in xrange(chunk)]
            for fidlist in listfid:                 
                params.append((vect, fidlist, csvstore, clipvalue))
    else:
        clipvalue = os.path.splitext(os.path.basename(vectorpath))[0]
        listfid = getFidList(vectorpath)
        csvstore = os.path.join(csvstorepath, "stats_%s"%(clipvalue))
        listfid = [listfid[i::chunk] for i in xrange(chunk)]        
        for fidlist in listfid:                 
            params.append((vect, fidlist, csvstore, clipvalue))

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
