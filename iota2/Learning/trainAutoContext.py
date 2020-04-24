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
from typing import List, Dict, Union, Optional

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())

SENSORS_PARAMS = Dict[str, Union[str, List[str], int]]
Param = Dict[str, Union[str, List[str], int]]


def train_autoContext_parameters(iota2_directory: str,
                                 regionField: str) -> List[Param]:
    """feed train_autoContext function

    Parameters
    ----------
    iota2_directory : string
        path to iota²'s running directory
    regionField : string
        region's field
    Return
    ------
    parameters : list
        dictionary describing input parameters
    """
    from iota2.Common.FileUtils import FileSearch_AND
    from iota2.Common.FileUtils import sortByFirstElem
    from iota2.Learning.TrainingCmd import config_model

    parameters = []

    pathToModelConfig = os.path.join(iota2_directory, "config_model",
                                     "configModel.cfg")
    configModel = config_model(iota2_directory, regionField)
    if not os.path.exists(pathToModelConfig):
        with open(pathToModelConfig, "w") as configFile:
            configFile.write(configModel)

    learningSamples_directory = os.path.join(iota2_directory,
                                             "learningSamples")
    tile_position = 0
    model_position = 2
    seed_position = 3

    learning_samples = FileSearch_AND(learningSamples_directory, False,
                                      "_Samples_learn.sqlite")

    learning_models = [
        ((c_file.split("_")[model_position],
          int(c_file.split("_")[seed_position].replace("seed", ""))), c_file)
        for c_file in learning_samples
    ]

    learning_models = sortByFirstElem(learning_models)

    for (model_name, seed_num), learning_files in learning_models:
        tiles = [
            learning_file.split("_")[tile_position]
            for learning_file in learning_files
        ]

        assert len(set(tiles)) == len(learning_files)

        tiles_slic = []
        for tile in tiles:
            tiles_slic.append(
                FileSearch_AND(
                    os.path.join(iota2_directory, "features", tile, "tmp"),
                    True, "SLIC", ".tif")[0])
        learning_files_path = [
            "{}.sqlite".format(
                os.path.join(learningSamples_directory, learning_file))
            for learning_file in learning_files
        ]
        SP_files_path = []
        for learning_file_path in learning_files_path:
            SP_file = learning_file_path.replace("learn.sqlite", "SP.sqlite")
            if not os.path.exists(SP_file):
                raise FileNotFoundError("{} not found".format(SP_file))
            SP_files_path.append(SP_file)

        parameters.append({
            "model_name": model_name,
            "seed": seed_num,
            "list_learning_samples": learning_files_path,
            "list_superPixel_samples": SP_files_path,
            "list_tiles": tiles,
            "list_slic": tiles_slic
        })
    return parameters


def train_autoContext(parameter_dict: Param,
                      data_field: str,
                      output_path: str,
                      sensors_parameters: SENSORS_PARAMS,
                      superpix_data_field: Optional[str] = "superpix",
                      iterations: Optional[int] = 3,
                      RAM: Optional[int] = 128,
                      WORKING_DIR: Optional[str] = None,
                      logger: Optional[logging.Logger] = LOGGER):
    """launch autoContext training

    Parameters
    ----------
    parameter_dict : dict
        dictionnary containing autoContext's input parameters
        {"model_name": string,
         "seed": integer,
         "list_learning_samples": list,
         "list_tiles": list,
         "list_slic": list,
         "list_superPixel_samples": list}
    config_path : string
        path to the configuration file
    iterations : int
        number of auto-context iterations
    RAM : integer
        available ram
    WORKING_DIR : string
        path to store temporary data
    logger : logging
        root logger
    """
    import shutil
    from iota2.Sampling import GenAnnualSamples
    from iota2.Common.GenerateFeatures import generateFeatures
    from iota2.Common.OtbAppBank import CreateTrainAutoContext
    from iota2.Common.FileUtils import ensure_dir

    tiles = parameter_dict["list_tiles"]
    model_name = parameter_dict["model_name"]
    seed_num = parameter_dict["seed"]
    data_ref = parameter_dict["list_learning_samples"]
    data_segmented = parameter_dict["list_superPixel_samples"]

    field = data_field.lower()

    models_path = os.path.join(output_path, "model")
    model_path = os.path.join(models_path,
                              "model_{}_seed_{}".format(model_name, seed_num))
    ensure_dir(model_path)

    if WORKING_DIR is None:
        tmp_dir = os.path.join(model_path, "tmp")
    else:
        tmp_dir = os.path.join(
            WORKING_DIR, "model_{}_seed_{}_tmp".format(model_name, seed_num))
    ensure_dir(tmp_dir)

    _, feat_labels, _ = generateFeatures(pathWd=WORKING_DIR,
                                         tile=tiles[0],
                                         sar_optical_post_fusion=False,
                                         output_path=output_path,
                                         sensors_parameters=sensors_parameters)

    feat_labels = [elem.lower() for elem in feat_labels]

    train_autoContext_app = CreateTrainAutoContext({
        "refdata":
        data_ref,
        "reffield":
        field,
        "superpixdata":
        data_segmented,
        "superpixdatafield":
        superpix_data_field,
        "feat":
        feat_labels,
        "nit":
        iterations,
        "out":
        "{}/".format(model_path)
    })
    logger.info("Start training autoContext, produce model {}, seed {}".format(
        model_name, seed_num))
    train_autoContext_app.ExecuteAndWriteOutput()
    logger.info("training autoContext DONE")
    shutil.rmtree(tmp_dir)
