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
from config import Config
import numpy as np
from Common import FileUtils as fu
from osgeo import ogr
from Common import ServiceConfigFile as SCF

def buildObiaTrainCmd(sample, classif, options, dataField, out, feats, stat):
    """ Compute command line for model creation (one per region and run)

    Parameters
    ----------
    sample : strings
       path to learning samples layer
    classif : string
        name of classifier
    options : string
        string of every options of the classifier, ex : '-rf.max X -rf.min Y -rf.nbtrees Z'
    dataField : string
        field name of ground truth class
    out : string
        output model path
    feats : string
        string of fields to use, ex : 'T1F1D1 T1F1D2 T1F2D1 T1F2D2'
    stat : string
        path to the xml stats (unskew model step)

    Note
    ------
    """
    cmd = "otbcli_TrainVectorClassifier -io.vd"
    cmd += " {} -classifier {} {} -cfield {} -feat {} -io.out {}".format(sample,
                                                          classif,
                                                          options,
                                                          dataField,
                                                          feats,
                                                          out)
    if stat != None :
        cmd += " -io.stats {}".format(stat)
    return cmd

def launchObiaTrainModel(cfg, dataField, region_seed_tile, pathToCmdTrain, outfolder, pathWd = None):
    """ Compute command line for model creation (one per region and run)

    Parameters
    ----------
    cfg : serviceConfig obj
        configuration object for parameters
    dataField : string
        field name of ground truth class
    region_seed_tile : list
        list [region, tiles, seed], cf. Sampling/SamplesMerge
    pathToCmdTrain : string
        path to the cmd folder
    outfolder : string
        path to the model folder
    pathWd : string
        path to the working directory

    Note
    ------
    """
    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)

    classif = cfg.getParam('argTrain', 'classifier')
    options = cfg.getParam('argTrain', 'options')
    iota2_directory = cfg.getParam('chain', 'outputPath')
    lsamples_directory = os.path.join(iota2_directory, "learningSamples")
    stats_directory = os.path.join(iota2_directory, "stats")
    wd = stats_directory
    if pathWd != None :
        wd = pathWd

    cmd_list = []
    # Construct every cmd
    for region, tiles, seed in region_seed_tile :
        sample = os.path.join(lsamples_directory, "learn_samples_region_{}_seed_{}_stats.shp".format(region, seed))
        stat = os.path.join(stats_directory, "features_stats_region_{}_seed_{}.xml".format(region, seed))
        if os.path.exists(stat) == False:
            stat = None
        feats = open(os.path.join(lsamples_directory, "learn_samples_region_{}_seed_{}_stats_label.txt".format(region,seed))).read().replace('\n',' ')
        output = os.path.join(outfolder,"model_region_{}_seed_{}.txt".format(region, seed))
        cmd = buildObiaTrainCmd(sample, classif, options, dataField, output, feats, stat)
        cmd_list.append(cmd)
    # Save these cmd to a txt file
    fu.writeCmds(pathToCmdTrain + "/train.txt", cmd_list)
    return cmd_list
