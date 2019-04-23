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
import GetModel as GM
from Common import FileUtils as fu
from Common import ServiceConfigFile as SCF

def launchUnskew(region_seed_tile, cfg):
    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)
    iota2_directory = cfg.getParam('chain', 'outputPath')
    lsamples_directory = os.path.join(iota2_directory, "learningSamples")
    stats_directory = os.path.join(iota2_directory, "stats")

    cmd_list=[]
    for region, tiles, seed in region_seed_tile :
        shp = os.path.join(lsamples_directory, "learn_samples_region_{}_seed_{}_stats.shp".format(region, seed))
        output = os.path.join(stats_directory, "features_stats_region_{}_seed_{}.xml".format(region, seed))
        ft_file = os.path.join(lsamples_directory, "learn_samples_region_{}_seed_{}_stats_label.txt".format(region, seed))
        feats = open(ft_file).read().replace('\n',' ')
        cmd = "otbcli_ComputeVectorFeaturesStatistics -io.vd {} -io.stats {} -feat {}".format(shp, output, feats)
        cmd_list.append(cmd)
    return cmd_list


