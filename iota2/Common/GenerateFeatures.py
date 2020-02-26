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
"""Module dedicated to generate the whole iota2 feature pipeline
"""
import argparse
import os
import logging
from typing import Dict, Union, List, Optional

LOGGER = logging.getLogger(__name__)

sensors_params = Dict[str, Union[str, List[str], int]]


def generateFeatures(pathWd: str,
                     tile: str,
                     sar_optical_post_fusion: bool,
                     output_path: str,
                     sensors_parameters: sensors_params,
                     mode: Optional[str] = "usually"):
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
    """
    from iota2.Common.OtbAppBank import getInputParameterOutput
    from iota2.Sensors.Sensors_container import sensors_container
    from iota2.Common.OtbAppBank import CreateConcatenateImagesApplication

    LOGGER.info(f"prepare features for tile : {tile}")

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

    generateFeatures(ARGS.pathWd,
                     ARGS.tile,
                     sar_optical_post_fusion=False,
                     output_path=CFG.getParam("chain", "outputPath"),
                     sensors_parameters=SEN_PARAM)
