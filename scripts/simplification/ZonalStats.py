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
from skimage.measure import label
from skimage.measure import regionprops
import numpy as np

try:
    from VectorTools import vector_functions as vf
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

def zonalstats(path, rasters, params, gdalpath = "", res = 10):
    
    vector, idvals, csvstore = params

    stats = []
    # vector open and iterate features
    vectorname = os.path.splitext(os.path.basename(vector))[0]
    ds = vf.openToRead(vector)
    lyr = ds.GetLayer()
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

        results_final = []
        if success:
            # analyze raster
            idxband  = 0
            for band in bands:
                if os.path.exists(band):
                    idxband += 1
                    rastertmp = gdal.Open(band, 0)
                    data = rastertmp.ReadAsArray()
                    img = label(data)
                    listlab = []
                    if len(np.unique(img)) != 1 or np.unique(img)[0] != 0:
                        if idxband == 1:
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

                Utils.run("rm %s"%(band))

                rastertmp = None
                stats.append(results_final)
        else:
            results_final.append([[idval, 'classif', 'part', 0, 0], [idval, 'confidence', 'mean', 0, 0], [idval, 'validity', 'mean', 0, 0],[idval, 'validity', 'std', 0, 0]])
            print "Feature with FID = %s of shapefile %s with null stats (maybe its size is too small)"%(idval, vector)
            stats.append(results_final[0])

    with open(csvstore, 'a') as myfile:
        writer = csv.writer(myfile)
        writer.writerows(stats)

def getParameters(vectorpath, csvstorepath, chunk=1):
    
    listvectors = getVectorsList(vectorpath)
    params = []
    if os.path.isdir(vectorpath):
        for vect in listvectors:
            listfid = getFidList(vect)
            csvstore = os.path.join(csvstorepath, "stats_%s"%(os.path.splitext(os.path.basename(vect))[0]))
            #TODO : split in chunks with sum of feature areas quite equal
            listfid = [listfid[i::chunk] for i in xrange(chunk)]
            for fidlist in listfid:                 
                params.append((vect, fidlist, csvstore))
    else:
        listfid = getFidList(vectorpath)
        csvstore = os.path.join(csvstorepath, "stats_%s"%(os.path.splitext(os.path.basename(vectorpath))[0]))
        listfid = [listfid[i::chunk] for i in xrange(chunk)]        
        for fidlist in listfid:                 
            params.append((vect, fidlist, csvstore))

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
