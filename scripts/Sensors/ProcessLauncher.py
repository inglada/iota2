# -*- coding: utf-8 -*-

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

def preprocess(tile_name, config_path, working_directory=None, RAM=128):
    """
    preprocessing input rasters data by tile
    
    Parameters
    ----------
    tile_name [string]
        tile's name
    config_path [string]
        absolute path to the configuration file
    working_directory [string]
        absolute path to a working directory
    RAM [int]
        pipeline's size (Mo)
    """
    from Sensors_container import Sensors_container

    remoteSensor_container = Sensors_container(config_path, tile_name,
                                               working_dir=working_directory)
    remoteSensor_container.sensors_preprocess(available_ram=RAM)

def commonMasks(tile_name, config_path, working_directory=None, RAM=128):
    """
    compute common mask considering all sensors by tile
    
    Parameters
    ----------
    tile_name [string]
        tile's name
    config_path [string]
        absolute path to the configuration file
    working_directory [string]
        absolute path to a working directory
    RAM [int]
        pipeline's size (Mo)
    """
    from Sensors_container import Sensors_container

    remoteSensor_container = Sensors_container(config_path, tile_name,
                                               working_dir=working_directory)
    commonMask, _ = remoteSensor_container.get_common_sensors_footprint(available_ram=RAM)
    commonMask.ExecuteAndWriteOutput()

def validity(tile_name, config_path, maskOut_name, view_threshold, workingDirectory=None, RAM=128):
    """
    function dedicated to compute validity raster/vector by tile

    Parameters
    ----------
    
    tile_name [string]
        tile's name
    config_path [string]
        absolute path to the configuration file
    maskOut_name [string]
        output vector mask's name
    view_threshold [int]
        threshold
    working_directory [string]
        absolute path to a working directory
    RAM [int]
        pipeline's size (Mo)
    """
    import os
    import shutil
    from Sensors_container import Sensors_container
    from Common.OtbAppBank import CreateConcatenateImagesApplication
    from Common.OtbAppBank import CreateBandMathApplication
    from Common import ServiceConfigFile as SCF

    cfg = SCF.serviceConfigFile(config_path)
    features_dir = os.path.join(cfg.getParam("chain", "outputPath"),
                                "features", tile_name)
    validity_name = "nbView.tif"

    validity_out = os.path.join(features_dir, validity_name)
    validity_processing = validity_out
    if workingDirectory:
        validity_processing = os.path.join(workingDirectory, validity_name)

    remoteSensor_container = Sensors_container(config_path, tile_name,
                                               working_dir=workingDirectory)
    sensors_time_series_masks = remoteSensor_container.get_sensors_time_series_masks(available_ram=RAM)
    sensors_masks_size = []
    sensors_masks = []
    for sensor_name, (time_series_masks, time_series_dep, nb_bands) in sensors_time_series_masks:
        time_series_masks.Execute()
        sensors_masks.append(time_series_masks)
        sensors_masks_size.append(nb_bands)

    total_dates = sum(sensors_masks_size)
    merge_masks = CreateConcatenateImagesApplication({"il": sensors_masks,
                                                      "ram": str(RAM)})
    merge_masks.Execute()

    validity_app = CreateBandMathApplication({"il": merge_masks,
                                              "exp": "{}-({})".format(total_dates,
                                                                      "+".join(["im1b{}".format(i + 1) for i in range(total_dates)])),
                                              "ram": str(RAM),
                                              "pixType": "uint8" if total_dates < 255 else "uint16",
                                              "out": validity_processing})
    validity_app.ExecuteAndWriteOutput()
    if workingDirectory:
        shutil.copy(validity_processing, os.path.join(features_dir, validity_name))