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

import argparse
import os
import logging
from Common import ServiceConfigFile as SCF

# import shutil
# import ast
# from config import Config
# from Common import FileUtils as fu
# from Common import OtbAppBank

logger = logging.getLogger(__name__)


def str2bool(v):
    """
    usage : use in argParse as function to parse options

    IN:
    v [string]
    out [bool]
    """
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


def generateFeatures(
    pathWd, tile, cfg, writeFeatures=False, mode="usually", customFeatures=False
):
    """
    usage : Function use to compute features according to a configuration file.

    IN

    OUT

    AllFeatures [OTB Application object] : otb object ready to Execute()
    feat_labels [list] : list of strings, labels for each output band
    dep [list of OTB Applications]
    """
    from Sensors.Sensors_container import Sensors_container
    from Common.OtbAppBank import CreateConcatenateImagesApplication
    from Common.OtbAppBank import getInputParameterOutput
    from Common.rasterUtils import apply_function
    from functools import partial
    from Common.customNumpyFeatures import customNumpyFeatures
    import otbApplication as otb

    logger.info("prepare features for tile : " + tile)
    wMode = cfg.getParam("GlobChain", "writeOutputs")
    sar_optical_post_fusion = cfg.getParam("argTrain", "dempster_shafer_SAR_Opt_fusion")

    config_path = cfg.pathConf
    sensor_tile_container = Sensors_container(config_path, tile, working_dir=pathWd)
    feat_labels = []
    dep = []
    feat_app = []
    if mode == "usually" and sar_optical_post_fusion is False:
        sensors_features = sensor_tile_container.get_sensors_features(
            available_ram=1000
        )
        for (
            sensor_name,
            ((sensor_features, sensor_features_dep), features_labels),
        ) in sensors_features:
            sensor_features.Execute()
            feat_app.append(sensor_features)
            dep.append(sensor_features_dep)
            feat_labels = feat_labels + features_labels
    elif mode == "usually" and sar_optical_post_fusion is True:
        sensor_tile_container.remove_sensor("Sentinel1")
        sensors_features = sensor_tile_container.get_sensors_features(
            available_ram=1000
        )
        for (
            sensor_name,
            ((sensor_features, sensor_features_dep), features_labels),
        ) in sensors_features:
            sensor_features.Execute()
            feat_app.append(sensor_features)
            dep.append(sensor_features_dep)
            feat_labels = feat_labels + features_labels
    elif mode == "SAR":
        sensor = sensor_tile_container.get_sensor("Sentinel1")
        (sensor_features, sensor_features_dep), feat_labels = sensor.get_features(
            ram=1000
        )
        sensor_features.Execute()
        feat_app.append(sensor_features)
        dep.append(sensor_features_dep)

    dep.append(feat_app)

    features_name = "{}_Features.tif".format(tile)
    features_dir = os.path.join(
        cfg.getParam("chain", "outputPath"), "features", tile, "tmp"
    )
    features_raster = os.path.join(features_dir, features_name)

    if len(feat_app) > 1:
        AllFeatures = CreateConcatenateImagesApplication(
            {"il": feat_app, "out": features_raster}
        )
    else:
        AllFeatures = sensor_features
        output_param_name = getInputParameterOutput(sensor_features)
        AllFeatures.SetParameterString(output_param_name, features_raster)
    if customFeatures:
        cust = customNumpyFeatures(config_path)
        function_partial = partial(cust.process)
        labels_features_name = ""  # TODO : how to feel labels_features_name ?
        # TODO: change chunck size and ram ?
        test_array, new_labels, _, _, _ = apply_function(
            otb_pipeline=AllFeatures,
            labels=labels_features_name,
            working_dir=pathWd,
            function=function_partial,
            output_path=features_raster,
            chunck_size_x=5,
            chunck_size_y=5,
            ram=128,
        )
        otbImage = AllFeatures.ExportImage(output_param_name)
        # Boom ?
        otbImage["array"] = test_array[:]
        bandMath = otb.Registry.CreateApplication("BandMathX")
        bandMath.ImportVectorImage("il", otbImage)
        bandMath.SetParameterString("out", features_raster)
        bandMath.SetParameterString("exp", "im1")
        AllFeatures = bandMath
    return AllFeatures, feat_labels, dep


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=("Computes a time series" " of features")
    )
    parser.add_argument(
        "-wd",
        dest="pathWd",
        help="path to the working directory",
        default=None,
        required=False,
    )
    parser.add_argument(
        "-tile", dest="tile", help="tile to be processed", required=True
    )
    parser.add_argument(
        "-conf",
        dest="pathConf",
        help="path to the configuration file (mandatory)",
        required=True,
    )
    parser.add_argument(
        "-writeFeatures",
        type=str2bool,
        dest="writeFeatures",
        Shelp="path to the working directory",
        default=False,
        required=False,
    )
    args = parser.parse_args()

    # load configuration file
    cfg = SCF.serviceConfigFile(args.pathConf)

    generateFeatures(args.pathWd, args.tile, cfg, args.writeFeatures)
