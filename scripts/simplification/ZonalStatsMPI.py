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
import traceback
import datetime
import time
import dill
from mpi4py import MPI
import csv
from itertools import groupby
import logging
logger = logging.getLogger(__name__)
import ogr
import gdal
from skimage.measure import label
from skimage.measure import regionprops
import numpy as np

try:
    from VectorTools import vector_functions as vf
    from Common import FileUtils as fut
    from simplification import extractAndConcatRaster as ecr
    from Common import Utils
except ImportError:
    raise ImportError('Iota2 not well configured / installed')


# This is needed in order to be able to send pyhton objects throug MPI send
MPI.pickle.dumps = dill.dumps
MPI.pickle.loads = dill.loads

class MPIService():
    """
    Class for storing the MPI context
    """
    def __init__(self):
        self.comm = MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        self.size = self.comm.Get_size()


class JobArray():
    """
    Class for storing a function to be applied to an array of parameters.
    - job is a callable object like a lambda expression; it takes a single parameter
    - param_array is a list of the parameters for each call to job
    """
    def __init__(self, job, param_array):
        self.job = job
        self.param_array = param_array


def kill_slaves(mpi_service):
    """
    kill slaves
    :param mpi_service
    """
    for i in range(1, mpi_service.size):
        print "Kill signal to slave " + str(i), "debug"
        mpi_service.comm.send(None, dest=i, tag=1)


def mpi_schedule_job_array(csvstore, job_array, mpi_service=MPIService()):
    """
    A simple MPI scheduler to execute jobs in parallel.
    """
    param_array = job_array.param_array
    job = job_array.job
    try:
        if mpi_service.rank == 0:
            # master
            results = []
            nb_completed_tasks = 0
            nb_tasks = len(param_array)
            for i in range(1, mpi_service.size):
                if len(param_array) > 0:
                    task_param = param_array.pop(0)
                    mpi_service.comm.send([job, task_param], dest=i, tag=0)
            while nb_completed_tasks < nb_tasks:
                [slave_rank, [start, end, result]] = mpi_service.comm.recv(source=MPI.ANY_SOURCE, tag=0)
                results += result
                with open(csvstore, 'a') as myfile:
                    writer = csv.writer(myfile)
                    writer.writerows(result)
                nb_completed_tasks += 1
                if len(param_array) > 0:
                    task_param = param_array.pop(0)
                    mpi_service.comm.send([job, task_param], dest=slave_rank, tag=0)
            print "All tasks sent"
            try:
                kill_slaves(mpi_service)
            except Exception as inst:
                print inst
            print "All tasks completed"
        else:
            # slave
            mpi_status = MPI.Status()
            while 1:
                # waiting sending works by master
                print 'Slave ' + str(mpi_service.rank) + ' is ready...'
                [task_job, task_param] = mpi_service.comm.recv(source=0, tag=MPI.ANY_TAG, status=mpi_status)
                if mpi_status.Get_tag() == 1:
                    print 'Closed rank ' + str(mpi_service.rank)
                    break
                start_date = datetime.datetime.now()
                result = task_job(task_param)

                end_date = datetime.datetime.now()
                print mpi_service.rank, "ended"
                mpi_service.comm.send([mpi_service.rank, [start_date, end_date, result]], dest=0, tag=0)

    except:
        if mpi_service.rank == 0:
            print "Something went wrong, we should log errors."
            traceback.print_exc()
            kill_slaves(mpi_service)
            sys.exit(1)

def getFidList(vect):
    
    shape = vf.openToRead(vect)
    lyr = shape.GetLayer()
    fidlist = []
    for feat in lyr:
        fidlist.append(feat.GetFID())
        
    return fidlist

def getVectorsList(path):

    listfiles = []
    for root, dirs, files in os.walk(path):
        for filein in files:
            if ".shp" in filein:
                listfiles.append(os.path.join(root, filein))    

    return listfiles

def genPBSfile(path, rasters, pypath, pathvectors, jobpath, csvstore, gdal, ram, cpu):
    pypath = "/home/qt/thierionv/workiota/iota2/scripts/"

    listcmd = []

    for root, dirs, files in os.walk(pathvectors):
        for filein in files:
            if ".shp" in filein:
                shapefile = os.path.join(root, filein)
                idxval = os.path.splitext(shapefile)[0].split("_")[len(os.path.splitext(shapefile)[0].split("_")) - 1]
                dircsvstore = os.path.dirname(csvstore)
                outpbs = os.path.join(jobpath, "vectorstats" + str(idxval) + '.pbs')

                jobFile = open(outpbs, "w")
                jobFile.write('#!/bin/bash\n\
#PBS -N stats%s\n\
#PBS -l select=6:ncpus=%s:mem=%s:mpiprocs=1:os=rh7\n\
#PBS -l walltime=60:00:00\n\
#PBS -o %s/logs/computeStats_out%s.log\n\
#PBS -e %s/logs/computeStats_err%s.log\n\
\n\
module use /work/OT/theia/oso/modulefiles\n\
module load release_66\n\
export GDAL_CACHEMAX=128\n\
export PYTHONPATH=$PYTHONPATH:%s\n\
cd %s\n\
\n\
cp %s $TMPDIR\n\
cp %s $TMPDIR\n\
cp %s $TMPDIR\n\
\n\
mpirun -x ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=%s -np 6 python ZonalStatsMPI.py -wd $TMPDIR -inr $TMPDIR/%s $TMPDIR/%s $TMPDIR/%s -ins %s -csv $TMPDIR/%s -gdal %s\n\
\n\
cp $TMPDIR/%s %s\n\
                '%(idxval, cpu, ram, path, idxval, path, idxval, pypath, os.path.join(pypath, "simplification"), \
                   rasters[0], rasters[1], rasters[2], \
                   cpu, \
                   os.path.basename(rasters[0]), \
                   os.path.basename(rasters[1]), \
                   os.path.basename(rasters[2]), \
                   shapefile, os.path.basename(csvstore), gdal, \
                   os.path.basename(csvstore), os.path.join(dircsvstore, os.path.splitext(os.path.basename(csvstore))[0] + '_' + str(idxval) + ".csv"))
                )
                
                listcmd.append("qsub -W block=true %s\n"%(outpbs))

    return listcmd
        
def zonalstats(params):
    
    #raster, vector, idfield, idval = params
    path, raster, vector, idval, gdalpath, res = params

    # vector open
    ds = vf.openToRead(vector)
    lyr = ds.GetLayer()
    lyr.SetAttributeFilter("FID=" + str(idval))
    for feat in lyr:
        geom = feat.GetGeometryRef()
        area = geom.GetArea()
        
    # rast  creation
    tmpfile = os.path.join(path, 'rast_' + str(idval))
    
    if gdalpath != "" and gdalpath is not None:
        gdalpath = gdalpath + "/"
    else:
        gdalpath = ""

    #try:
    cmd = '%sgdalwarp -q -overwrite -cutline %s -crop_to_cutline --config GDAL_CACHEMAX 9000 -wm 9000 -wo NUM_THREADS=ALL_CPUS -cwhere "FID=%s" %s %s'%(gdalpath, vector, idval, raster, tmpfile)
    print cmd
    Utils.run(cmd)
    #except: pass
    
    # analyze raster
    results_final = []
    if os.path.exists(tmpfile):
        rastertmp = gdal.Open(tmpfile, 0)

        for band in range(rastertmp.RasterCount):
            band += 1
            raster_band = rastertmp.GetRasterBand(band)
            data = raster_band.ReadAsArray()
            img = label(data)
            listlab = []

            if band == 1:
                try:
                    for reg in regionprops(img, data):
                        listlab.append([[x for x in np.unique(reg.intensity_image) if x != 0][0], reg.area])
                except:
                    elts, cptElts = np.unique(data, return_counts=True)
                    for idx, elts in enumerate(elts):
                        if elts != 0:
                            listlab.append([elts, cptElts[idx]])

                print listlab
                if len(listlab) != 0:                
                    classmaj = [y for y in listlab if y[1] == max([x[1] for x in listlab])][0][0]
                    posclassmaj = np.where(data==classmaj)
                    results = []
                    
                    for i, g in groupby(sorted(listlab), key = lambda x: x[0]):
                        results.append([i, sum(v[1] for v in g)])

                    sumpix = sum([x[1] for x in results])
                    for elt in [[int(w), round(((float(z) * float(res) * float(res)) /float(sumpix)), 2)] for w, z in results]:
                        results_final.append([idval, 'classif', 'part'] + elt)

            if band != 1:
                if band == 2:
                    results_final.append([idval, 'confidence', 'mean', int(classmaj), round(np.mean(data[posclassmaj]), 2)])
                elif band == 3:
                    results_final.append([idval, 'validity', 'mean', int(classmaj), round(np.mean(data[posclassmaj]), 2)])
                    results_final.append([idval, 'validity', 'std', int(classmaj), round(np.std(data[posclassmaj]), 2)])                

            raster_band = data = img = None

        Utils.run("rm %s"%(tmpfile))

        rastertmp = None

    return results_final

def computZonalStats(path, rasters, vector, csvstore, nbcore = 1, outtype = "uint8", inputlistfid = "", mpi = True, gdalpath = "", logger = logger):

    begintime = time.time()
    raster = os.path.join(path, "concat.tif")    

    if mpi: 
        listfid = []
        mpi_service=MPIService()
        if mpi_service.rank == 0:
            ecr.extractAndConcat(path, vector, rasters, raster, nbcore, outtype)

            rastin = gdal.Open(raster, 0)
            resraster = rastin.GetGeoTransform()[1]
            if os.path.exists(csvstore):
                os.remove(csvstore)
            if inputlistfid == None:
                listfid = getFidList(vector)
            else:
                with open(inputlistfid, "r") as ffid:
                    for line in ffid.readlines():
                        listfid.append(line[:-2])

        param_list = []
        for i in range(len(listfid)):
            param_list.append((path, raster, vector, listfid[i], gdalpath, resraster))

        ja = JobArray(lambda x: zonalstats(x), param_list)    
        results = mpi_schedule_job_array(csvstore, ja, mpi_service=MPIService())
        
    else:
        idxval = os.path.splitext(os.path.basename(vector))[0].split('_')[1]
        csvstore = os.path.splitext(csvstore)[0] + '_' + str(idxval) + '.csv'        

        if os.path.exists(csvstore):
            os.remove(csvstore)
            
        ecr.extractAndConcat(path, vector, rasters, raster, nbcore, outtype)
        timempi = time.time()
        logger.info(" ".join([" : ".join(["Concatenate rasters", str(round(timempi - begintime, 2))]), "seconds"]))

        results = []
        listfid = getFidList(vector)
        rastin = gdal.Open(raster, 0)
        resraster = rastin.GetGeoTransform()[1]
        for fid in listfid:
            paramlist = (path, raster, vector, fid, gdalpath, resraster)
            res = zonalstats(paramlist)
            results.append(res)

        with open(csvstore, 'w') as myfile:
            for row in results:
                writer = csv.writer(myfile)
                writer.writerows(row)

        endtime = time.time()
        logger.info(" ".join([" : ".join(["Compute stats", str(round(endtime - timempi, 2))]), "seconds"]))

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
        PARSER.add_argument("-ins", dest="ins", action="store",\
                            help="input shapefile",\
                            required=True)
        PARSER.add_argument("-csv", dest="csv", action="store",\
                            help="csv file to store results", required=True)
        PARSER.add_argument("-gdal", dest="gdal", action="store",\
                            help="gdal 2.2.4 binaries path (problem of very small features with lower gdal version)", default = "")
        PARSER.add_argument("-nompi", action="store_false",\
                            help="mode mpi for run", default = True)
        PARSER.add_argument("-listfid", dest="inputlistfid",\
                            help="list of fid to treate")                
        PARSER.add_argument("-pixtype", dest="pixtype", action="store", \
                            help="output raster", default="uint8")
        PARSER.add_argument("-nbcore", dest="nbcore", action="store", \
                            help="thread number for concatenate operation", default="1")                            
        
        args = PARSER.parse_args()
        computZonalStats(args.path, args.inr, args.ins, args.csv, args.nbcore, args.pixtype, args.inputlistfid, args.nompi, args.gdal)
