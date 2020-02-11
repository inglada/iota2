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
from iota2.Common import ServiceConfigFile as SCF

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


def generateFeatures(pathWd,
                     tile,
                     cfg,
                     writeFeatures=False,
                     mode="usually",
                     customFeatures=False,
                     force_standard_labels=False):
    """
    usage : Function use to compute features according to a configuration file.

    IN

    OUT

    AllFeatures [OTB Application object] : otb object ready to Execute()
    feat_labels [list] : list of strings, labels for each output band
    dep [list of OTB Applications]
    """
    from iota2.Sensors.Sensors_container import Sensors_container
    from iota2.Common.OtbAppBank import CreateConcatenateImagesApplication
    from iota2.Common.OtbAppBank import getInputParameterOutput
    from iota2.Common.rasterUtils import apply_function
    from functools import partial
    from iota2.Common.customNumpyFeatures import customNumpyFeatures
    import otbApplication as otb
    import numpy as np

    logger.info("prepare features for tile : " + tile)
    # wMode = cfg.getParam("GlobChain", "writeOutputs")
    sar_optical_post_fusion = cfg.getParam("argTrain",
                                           "dempster_shafer_SAR_Opt_fusion")

    config_path = cfg.pathConf
    sensor_tile_container = Sensors_container(config_path,
                                              tile,
                                              working_dir=pathWd)
    feat_labels = []
    dep = []
    feat_app = []
    if mode == "usually" and sar_optical_post_fusion is False:
        sensors_features = sensor_tile_container.get_sensors_features(
            available_ram=1000)
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
            available_ram=1000)
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
        (sensor_features,
         sensor_features_dep), feat_labels = sensor.get_features(ram=1000)
        sensor_features.Execute()
        feat_app.append(sensor_features)
        dep.append(sensor_features_dep)

    dep.append(feat_app)

    features_name = "{}_Features.tif".format(tile)
    features_dir = os.path.join(cfg.getParam("chain", "outputPath"),
                                "features", tile, "tmp")
    features_raster = os.path.join(features_dir, features_name)
    if len(feat_app) > 1:
        AllFeatures = CreateConcatenateImagesApplication({
            "il": feat_app,
            "out": features_raster
        })
    else:
        AllFeatures = sensor_features
        output_param_name = getInputParameterOutput(sensor_features)
        AllFeatures.SetParameterString(output_param_name, features_raster)
    if customFeatures:
        cust = customNumpyFeatures(config_path)
        function_partial = partial(cust.process)
        labels_features_name = ""
        # TODO : how to feel labels_features_name ?
        # The output path is empty to ensure the image was not writed
        test_array, new_labels, _, _, _ = apply_function(
            otb_pipeline=AllFeatures,
            labels=labels_features_name,
            working_dir=pathWd,
            function=function_partial,
            chunck_size_x=5,
            chunck_size_y=5,
            ram=128,
        )
        AllFeatures.Execute()
        otbImage = AllFeatures.ExportImage(output_param_name)
        # rasterio shape [bands, row, cols] OTB shape [row, cols, bands]
        # use move axis for OTB
        arr_resh = np.moveaxis(test_array, [0, 1, 2], [2, 0, 1])
        # ensure c order in memory
        # for OTB application
        arr_2 = np.copy(arr_resh, order="C")
        otbImage["array"] = arr_2
        bandMath = otb.Registry.CreateApplication("BandMathX")
        bandMath.ImportVectorImage("il", otbImage)
        bandMath.SetParameterString("out", features_raster)
        bandMath.SetParameterString("exp", "im1")
        AllFeatures = bandMath
        # new_labels can never be empty
        feat_labels += new_labels
        if force_standard_labels:
            feat_labels = [f"value_{i}" for i in range(len(feat_labels))]
    return AllFeatures, feat_labels, dep


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description=("Computes a time series"
                                                  " of features"))
    parser.add_argument(
        "-wd",
        dest="pathWd",
        help="path to the working directory",
        default=None,
        required=False,
    )
    parser.add_argument("-tile",
                        dest="tile",
                        help="tile to be processed",
                        required=True)
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
