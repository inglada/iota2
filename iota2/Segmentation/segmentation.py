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
import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

def slicSegmentation(tile_name, config_path, ram=128, working_dir=None, LOGGER=logger):
    """generate segmentation using SLIC algorithm

    Parameters
    ----------
    tile_name : string
        tile's name
    config_path : string
        configuration file path
    ram : int
        available ram
    working_dir : string
        directory to store temporary data
    LOGGER : logging
        root logger
    """
    import shutil
    from Common.GenerateFeatures import generateFeatures
    from Common import ServiceConfigFile as SCF
    from Common.OtbAppBank import CreateSLICApplication
    from Common.OtbAppBank import getInputParameterOutput
    from Common.FileUtils import ensure_dir
    
    SLIC_NAME = "SLIC_{}.tif".format(tile_name)

    cfg = SCF.serviceConfigFile(config_path)
    all_features, feat_labels, dep = generateFeatures(working_dir, tile_name, cfg)
    all_features.Execute()

    spx, _ = all_features.GetImageSpacing(getInputParameterOutput(all_features))

    tmp_dir = working_dir
    if working_dir is None:
        tmp_dir = os.path.join(cfg.getParam("chain", "outputPath"),
                               "features",
                               tile_name,
                               "tmp",
                               "SLIC_TMPDIR")
    else:
        tmp_dir = os.path.join(working_dir, tile_name)

    ensure_dir(tmp_dir)

    slic_seg_path = os.path.join(cfg.getParam("chain", "outputPath"),
                                 "features",
                                 tile_name,
                                 "tmp",
                                 SLIC_NAME)
    slic_parameters = {"in": all_features,
                       "tmpdir": tmp_dir,
                       "spw": int(spx),
                       "tiling.auto.ram": ram,
                       "out": slic_seg_path}
    SLIC_seg = CreateSLICApplication(slic_parameters)
    LOGGER.info("Processing SLIC segmentation : {}\n\t\t\
                 with parameters : {}".format(tile_name, slic_parameters))
    SLIC_seg.ExecuteAndWriteOutput()
    if working_dir is None:
        shutil.rmtree(tmp_dir)
