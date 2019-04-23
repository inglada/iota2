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

import argparse
import os
import glob
import shutil
from config import Config
from osgeo import gdal, ogr, osr
from Common import FileUtils as fu
from Common import ServiceConfigFile as SCF
from Common.Utils import run
from MPI import launch_tasks


def launchObiaClassification(run, nb_cpu, cfg, pathWd):

    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)
    cfield = cfg.getParam('chain', 'dataField')
    outputPath = cfg.getParam('chain', 'outputPath')
    tsamples_dir = os.path.join(outputPath, "tilesSamples")
    lsamples_dir = os.path.join(outputPath, "learningSamples")
    model_dir = os.path.join(outputPath, "model")
    stats_dir = os.path.join(outputPath, "stats")
    classif_dir = os.path.join(outputPath, "classif")
    AllCmd = []

    models = glob.glob(os.path.join(model_dir, 'model_region_*_seed_{}.txt'.format(run)))

    for model in models :
        region = os.path.splitext(os.path.basename(model))[0].split('_')[2]
        features_stats = os.path.join(stats_dir, "features_stats_region_{}_seed_{}.xml".format(region,run))
        samples_list = glob.glob(os.path.join(tsamples_dir,"*","*_region_{}_*_stats.shp".format(region)))
        for samples in samples_list :
            tile = samples.split('/')[-2]
            if os.path.exists(os.path.join(classif_dir,tile)) == False :
                os.mkdir(os.path.join(classif_dir,tile))
            part = samples.split('_')[-2]
            ft_file = os.path.join(lsamples_dir, "learn_samples_region_{}_seed_{}_stats_label.txt".format(region, run))
            feats = open(ft_file).read().replace('\n',' ')
            out = os.path.join(classif_dir,tile,"{}_model_{}_seed_{}_part_{}.shp".format(tile,region,run,part))
            cmd = "otbcli_VectorClassifier -in {} -instat {} -model {} -cfield {} -feat {} -out {} -confmap 1".format(samples,features_stats, model, cfield, feats, out)
            AllCmd.append(cmd)
    launch_tasks.queuedProcess(AllCmd,N_processes=nb_cpu,shell=True)
    return 

def reassembleParts(run,nb_cpu,cfg, pathWd):
    from Common.Tools import ExtractROIRaster

    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)
    cfield = cfg.getParam('chain', 'dataField')
    tiles = cfg.getParam('chain', 'listTile').split(' ')
    runs = [run for run in range(0,cfg.getParam('chain', 'runs'))]
    outputPath = cfg.getParam('chain', 'outputPath')
    seg_dir = os.path.join(outputPath, 'segmentation')
    model_dir = os.path.join(outputPath, "model")
    classif_dir = os.path.join(outputPath, "classif")

    im_ref = cfg.getParam('chain', 'OBIA_segmentation_path')
    spx, spy = ExtractROIRaster.getRasterResolution(im_ref)

    models = glob.glob(os.path.join(model_dir, 'model_region_*_seed_{}.txt'.format(run)))

    for model in models :
        region = os.path.splitext(os.path.basename(model))[0].split('_')[2]
        for tile in tiles :
            parts = glob.glob(os.path.join(classif_dir,tile,"{}_model_{}_seed_{}_part_*.shp".format(tile,region,run)))
            out_parts = ''
            out_parts_conf = ''
            AllCmd = []
            for part in parts:
                out = os.path.splitext(part)[0]+'.tif'
                p = os.path.splitext(out)[0].split('_')[-1]
                out_parts += ' '+out
                out_confmap = os.path.join(classif_dir,tile,"{}_model_{}_confidence_seed_{}_part_{}.tif".format(tile, region, run, p))
                out_parts_conf += ' '+out_confmap
                cmd = 'otbcli_Rasterization -in {} -out {} -mode attribute -mode.attribute.field {} -spx {} -spy {}'.format(part, out, cfield, spx, spy)
                AllCmd.append(cmd)
                cmd = 'otbcli_Rasterization -in {} -out {} -mode attribute -mode.attribute.field confidence -spx {} -spy {}'.format(part, out_confmap, spx, spy)
                AllCmd.append(cmd)
            launch_tasks.queuedProcess(AllCmd,N_processes=nb_cpu,shell=True)
            out_merge = os.path.join(classif_dir,"Classif_{}_model_{}_seed_{}.tif".format(tile,region,run))
            out_conf_merge = os.path.join(classif_dir,"{}_model_{}_confidence_seed_{}.tif".format(tile,region,run))
            cmd = 'gdal_merge.py -o {} -ot Int32 -co COMPRESS=DEFLATE -n 0 -a_nodata 0 {}'.format(out_merge,out_parts)
            launch_tasks.launchBashCmd(cmd)
            cmd = 'gdal_merge.py -o {} -co COMPRESS=DEFLATE -n 0 -a_nodata 0 {}'.format(out_conf_merge,out_parts_conf)
            launch_tasks.launchBashCmd(cmd)
