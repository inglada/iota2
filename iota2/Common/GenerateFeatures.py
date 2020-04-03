#!/usr/bin/env python3
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
"""Module dedicated to generate the whole iota2 feature pipeline
"""
import argparse
import os
import logging
from typing import Dict, Union, List, Optional
from rasterio.plot import reshape_as_image
from iota2.Common import FileUtils as fu
LOGGER = logging.getLogger(__name__)

sensors_params = Dict[str, Union[str, List[str], int]]


def generate_features(pathWd: str,
                      tile: str,
                      sar_optical_post_fusion: bool,
                      output_path: str,
                      sensors_parameters: sensors_params,
                      custom_features: Optional[bool] = False,
                      module_name: Optional[str] = None,
                      list_functions: Optional[List[str]] = None,
                      targeted_chunk: Optional[int] = None,
                      number_of_chunks: Optional[int] = 50,
                      force_standard_labels: Optional[bool] = False,
                      mode: Optional[str] = "usually",
                      logger: Optional[logging.Logger] = LOGGER):
    """
    usage : Function use to compute features according to a configuration file
    Parameters
    ----------
    pathWd : str
        path to a working directory
    tile : str
        tile's name
    sar_optical_post_fusion : bool
        flag use to remove SAR data from features
    mode : str
        'usually' / 'SAR' used to get only sar features
    Return
    ------
    AllFeatures [OTB Application object] : otb object ready to Execute()
    feat_labels [list] : list of strings, labels for each output band
    dep [list of OTB Applications]
    """
    from iota2.Sensors.Sensors_container import sensors_container
    from iota2.Common.OtbAppBank import CreateConcatenateImagesApplication
    from iota2.Common.OtbAppBank import getInputParameterOutput
    from iota2.Common.rasterUtils import apply_function
    from functools import partial
    from iota2.Common.customNumpyFeatures import custom_numpy_features
    import otbApplication as otb

    logger.info(f"prepare features for tile : {tile}")

    sensor_tile_container = sensors_container(tile, pathWd, output_path,
                                              **sensors_parameters)

    feat_labels = []
    dep = []
    feat_app = []
    if mode == "usually" and sar_optical_post_fusion is False:
        sensors_features = sensor_tile_container.get_sensors_features(
            available_ram=1000)
        for _, ((sensor_features, sensor_features_dep),
                features_labels) in sensors_features:
            sensor_features.Execute()
            feat_app.append(sensor_features)
            dep.append(sensor_features_dep)
            feat_labels = feat_labels + features_labels
    elif mode == "usually" and sar_optical_post_fusion is True:
        sensor_tile_container.remove_sensor("Sentinel1")
        sensors_features = sensor_tile_container.get_sensors_features(
            available_ram=1000)
        for _, ((sensor_features, sensor_features_dep),
                features_labels) in sensors_features:
            sensor_features.Execute()
            feat_app.append(sensor_features)
            dep.append(sensor_features_dep)
            feat_labels = feat_labels + features_labels
    elif mode == "SAR":
        sensor = sensor_tile_container.get_sensor("Sentinel1")
        (sensor_features,
         sensor_features_dep), feat_labels = sensor.get_features(ram=1000)
        sensor_features.Execute()
        feat_app.append(sensor_features)
        dep.append(sensor_features_dep)
    dep.append(feat_app)

    features_name = "{}_Features.tif".format(tile)
    features_dir = os.path.join(output_path, "features", tile, "tmp")
    features_raster = os.path.join(features_dir, features_name)
    if len(feat_app) > 1:
        all_features = CreateConcatenateImagesApplication({
            "il":
            feat_app,
            "out":
            features_raster
        })
    else:
        all_features = sensor_features
        output_param_name = getInputParameterOutput(sensor_features)
        all_features.SetParameterString(output_param_name, features_raster)
    if custom_features:
        cust = custom_numpy_features(tile, output_path, sensors_parameters,
                                     module_name, list_functions)
        function_partial = partial(cust.process)
        labels_features_name = ""
        # TODO : how to feel labels_features_name ?
        # The output path is empty to ensure the image was not writed
        feat_array, new_labels, out_transform, _, _, otbimage = apply_function(
            otb_pipeline=all_features,
            labels=labels_features_name,
            working_dir=pathWd,
            chunk_size_mode="split_number",
            function=function_partial,
            targeted_chunk=targeted_chunk,
            number_of_chunks=number_of_chunks,
            ram=128,
        )
        # rasterio shape [bands, row, cols] OTB shape [row, cols, bands]
        # use rasterio reshape_as_image function to move axis
        otbimage["array"] = reshape_as_image(feat_array)
        logger.debug("Numpy image inserted in otb pipeline: "
                     f"{fu.memory_usage_psutil()} MB")
        # get the chunk size
        size = otbimage["array"].shape
        # get the chunk origin
        origin = out_transform * (0, 0)
        # add a demi pixel size to origin
        # offset between rasterio (gdal) and OTB
        otbimage["origin"].SetElement(0,
                                      origin[0] + (otbimage["spacing"][0] / 2))
        otbimage["origin"].SetElement(1,
                                      origin[1] + (otbimage["spacing"][1] / 2))
        # Set buffer image region
        # Mandatory to keep the projection in OTB pipeline
        otbimage["region"].SetIndex(0, 0)
        otbimage["region"].SetIndex(1, 0)
        otbimage["region"].SetSize(0, size[1])
        otbimage["region"].SetSize(1, size[0])
        # TODO: remove this bandmath and return an OTB image
        bandmath = otb.Registry.CreateApplication("BandMathX")
        bandmath.ImportVectorImage("il", otbimage)
        bandmath.SetParameterString("out", features_raster)
        bandmath.SetParameterString("exp", "im1")
        # bandmath.SetParameterString("ram", "200000")
        all_features = bandmath
        dep.append(bandmath)
        dep.append(otbimage)
        # new_labels can never be empty
        feat_labels += new_labels

    if force_standard_labels:
        feat_labels = [f"value_{i}" for i in range(len(feat_labels))]
    return all_features, feat_labels, dep


if __name__ == "__main__":

    from iota2.Common import ServiceConfigFile as SCF
    from iota2.Common.ServiceConfigFile import iota2_parameters
    PARSER = argparse.ArgumentParser(
        description="Computes a time series of features")
    PARSER.add_argument("-wd",
                        dest="pathWd",
                        help="path to the working directory",
                        default=None,
                        required=False)
    PARSER.add_argument("-tile",
                        dest="tile",
                        help="tile to be processed",
                        required=True)
    PARSER.add_argument("-conf",
                        dest="pathConf",
                        help="path to the configuration file (mandatory)",
                        required=True)
    ARGS = PARSER.parse_args()

    # load configuration file
    CFG = SCF.serviceConfigFile(ARGS.pathConf)
    PARAMS = iota2_parameters(ARGS.pathConf)
    SEN_PARAM = PARAMS.get_sensors_parameters(ARGS.tile)

    generate_features(ARGS.pathWd,
                      ARGS.tile,
                      sar_optical_post_fusion=False,
                      output_path=CFG.getParam("chain", "outputPath"),
                      sensors_parameters=SEN_PARAM)
