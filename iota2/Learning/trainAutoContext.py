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


def train_autoContext_parameters(iota2_directory):
    """
    Parameters
    ----------
    iota2_directory : string
        path to iota²'s running directory

    Return
    ------
    parameters : list
    """
    from collections import OrderedDict
    from Common.FileUtils import FileSearch_AND
    from Common.FileUtils import sortByFirstElem

    sample_selection_directory = os.path.join(iota2_directory, "samplesSelection")
    
    tile_position = 0
    model_position = 3
    seed_position = 5

    parameters = []

    sample_sel_content = FileSearch_AND(sample_selection_directory, False, "_samples_region_", "selection.sqlite")
    selection_models = [((c_file.split("_")[model_position],
                          int(c_file.split("_")[seed_position])),
                          c_file) for c_file in sample_sel_content]
    selection_models = sortByFirstElem(selection_models)

    for (model_name, seed_num), selection_files in selection_models:
        tiles = [selection_file.split("_")[tile_position] for selection_file in selection_files]
        
        assert len(set(tiles)) == len(selection_files)
        
        tiles_slic = []
        for tile in tiles : 
            tiles_slic.append(FileSearch_AND(os.path.join(iota2_directory,
                                             "features", tile, "tmp"),
                                             True, "SLIC", ".tif")[0])
        parameters.append({"model_name": model_name,
                           "seed": seed_num,
                           "list_selection": ["{}.sqlite".format(os.path.join(sample_selection_directory, selection_file)) for selection_file in selection_files],
                           "list_tiles": tiles,
                           "list_slic":tiles_slic})
    return parameters
    
def train_autoContext(parameter_dict, config_path, RAM=128, WORKING_DIR=None, LOGGER=logger):
    """
    """
    import shutil
    from Common.GenerateFeatures import generateFeatures
    from Common import ServiceConfigFile as SCF
    from Common.OtbAppBank import CreateTrainAutoContext
    from Common.FileUtils import ensure_dir
    
    cfg = SCF.serviceConfigFile(config_path)
    
    tiles = parameter_dict["list_tiles"]
    model_name = parameter_dict["model_name"]
    seed_num = parameter_dict["seed"]
    slic = parameter_dict["list_slic"]
    data_ref = parameter_dict["list_selection"]
    field = cfg.getParam("chain", "dataField").lower()
    iota2_run = cfg.getParam("chain", "outputPath")
    
    features = []
    dependencies = []
    for tile in tiles :
       features_tile, feat_labels, dep = generateFeatures(WORKING_DIR, tile, cfg)
       features_tile.Execute()
       features.append(features_tile)
       dependencies.append(dep)

    models_path = os.path.join(iota2_run, "model")
    model_path = os.path.join(models_path, "model_{}_seed_{}".format(model_name, seed_num))
    ensure_dir(model_path)

    if WORKING_DIR is None:
        tmp_dir = os.path.join(model_path, "tmp")
    else : 
        tmp_dir = os.path.join(WORKING_DIR, "model_{}_seed_{}_tmp".format(model_name, seed_num))
    ensure_dir(tmp_dir)

    train_autoContext = CreateTrainAutoContext({"il" : features,
                                                "inseg": slic,
                                                "tmpdir": "{}/".format(tmp_dir),
                                                "refdata": data_ref,
                                                "field": field,
                                                "out": "{}/".format(model_path),
                                                "ram": RAM})
    LOGGER.info("Start training autoContext, produce model {}, seed {}".format(model_name, seed_num))
    train_autoContext.ExecuteAndWriteOutput()
    LOGGER.info("training autoContext DONE")
    shutil.rmtree(tmp_dir)