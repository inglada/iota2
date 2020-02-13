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
    from Sensors.Sensors_container import sensors_container

    remoteSensor_container = Sensors_container(config_path,
                                               tile_name,
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
    import os
    from Sensors.Sensors_container import Sensors_container
    from Common.Utils import run
    from Common.FileUtils import ensure_dir

    remoteSensor_container = Sensors_container(config_path,
                                               tile_name,
                                               working_dir=working_directory)
    common_mask, _ = remoteSensor_container.get_common_sensors_footprint(
        available_ram=RAM)
    common_mask_raster = common_mask.GetParameterValue("out")

    if not os.path.exists(common_mask_raster):
        ensure_dir(os.path.split(common_mask_raster)[0], raise_exe=False)
        common_mask.ExecuteAndWriteOutput()

    common_mask_vector = common_mask_raster.replace(".tif", ".shp")
    common_mask_vector_cmd = "gdal_polygonize.py -f \"ESRI Shapefile\" -mask {} {} {}".format(
        common_mask_raster, common_mask_raster, common_mask_vector)
    run(common_mask_vector_cmd)


def validity(tile_name,
             config_path,
             maskOut_name,
             view_threshold,
             workingDirectory=None,
             RAM=128):
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
    from Sensors.Sensors_container import Sensors_container
    from Common.OtbAppBank import CreateConcatenateImagesApplication
    from Common.OtbAppBank import CreateBandMathApplication
    from Common import ServiceConfigFile as SCF
    from Common.Utils import run
    from Common.FileUtils import erodeShapeFile
    from Common.FileUtils import removeShape
    from Common.FileUtils import ensure_dir

    cfg = SCF.serviceConfigFile(config_path)
    features_dir = os.path.join(cfg.getParam("chain", "outputPath"),
                                "features", tile_name)
    validity_name = "nbView.tif"

    validity_out = os.path.join(features_dir, validity_name)
    validity_processing = validity_out
    if workingDirectory:
        ensure_dir(os.path.join(workingDirectory, tile_name))
        validity_processing = os.path.join(workingDirectory, tile_name,
                                           validity_name)

    remote_sensor_container = Sensors_container(config_path,
                                                tile_name,
                                                working_dir=workingDirectory)
    sensors_time_series_masks = remote_sensor_container.get_sensors_time_series_masks(
        available_ram=RAM)
    sensors_masks_size = []
    sensors_masks = []
    for sensor_name, (time_series_masks, time_series_dep,
                      nb_bands) in sensors_time_series_masks:
        if sensor_name.lower() == "sentinel1":
            for sensor_mode, time_series_masks_app in list(
                    time_series_masks.items()):
                time_series_masks_app.Execute()
                sensors_masks.append(time_series_masks_app)
        else:
            time_series_masks.Execute()
            sensors_masks.append(time_series_masks)
        sensors_masks_size.append(nb_bands)

    total_dates = sum(sensors_masks_size)
    merge_masks = CreateConcatenateImagesApplication({
        "il": sensors_masks,
        "ram": str(RAM)
    })
    merge_masks.Execute()

    validity_app = CreateBandMathApplication({
        "il":
        merge_masks,
        "exp":
        "{}-({})".format(
            total_dates,
            "+".join(["im1b{}".format(i + 1) for i in range(total_dates)])),
        "ram":
        str(0.7 * RAM),
        "pixType":
        "uint8" if total_dates < 255 else "uint16",
        "out":
        validity_processing
    })
    if not os.path.exists(os.path.join(features_dir, validity_name)):
        validity_app.ExecuteAndWriteOutput()
        if workingDirectory:
            shutil.copy(validity_processing,
                        os.path.join(features_dir, validity_name))
    threshold_raster_out = os.path.join(features_dir,
                                        maskOut_name.replace(".shp", ".tif"))
    threshold_vector_out_tmp = os.path.join(
        features_dir, maskOut_name.replace(".shp", "_TMP.shp"))
    threshold_vector_out = os.path.join(features_dir, maskOut_name)

    input_threshold = validity_processing if os.path.exists(
        validity_processing) else validity_out

    threshold_raster = CreateBandMathApplication({
        "il":
        input_threshold,
        "exp":
        "im1b1>={}?1:0".format(view_threshold),
        "ram":
        str(0.7 * RAM),
        "pixType":
        "uint8",
        "out":
        threshold_raster_out
    })
    threshold_raster.ExecuteAndWriteOutput()
    cmd_poly = "gdal_polygonize.py -mask {} {} -f \"ESRI Shapefile\" {} {} cloud".format(
        threshold_raster_out, threshold_raster_out, threshold_vector_out_tmp,
        os.path.splitext(os.path.basename(threshold_vector_out_tmp))[0])
    run(cmd_poly)

    erodeShapeFile(threshold_vector_out_tmp, threshold_vector_out, 0.1)
    os.remove(threshold_raster_out)
    removeShape(threshold_vector_out_tmp.replace(".shp", ""),
                [".prj", ".shp", ".dbf", ".shx"])
