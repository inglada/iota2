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
from typing import Dict, Union, List
from functools import partial
import argparse

from iota2.Common.GenerateFeatures import generateFeatures
from iota2.Common import IOTA2Directory
from iota2.Common import rasterUtils

sensors_params = Dict[str, Union[str, List[str], int]]


def smart_scientific_function(array, increment, *args, **kwargs):
    """do important scientific stuff, publishing in progress
    """
    return array + increment


def compute_features(output_path: str,
                     sensors_parameters: sensors_params,
                     output_raster: str,
                     tile_name: str,
                     working_dir: str,
                     function=smart_scientific_function) -> None:
    """Use a python function to generate features through the use of numpy arrays

    Parameters
    ----------
    output_path : str
        output directory
    sensors_parameters : dict
        sensors parameters description
    output_raster : str
        output raster path
    tile_name : str
        tile to compute
    function : function
        function to apply on iota²' stack
    """
    IOTA2Directory.generate_directories(output_path, check_inputs=False)
    feat_stack, feat_labels, _ = generateFeatures(
        working_dir,
        tile_name,
        sar_optical_post_fusion=False,
        output_path=output_path,
        sensors_parameters=sensors_parameters)

    # Then compute new features
    function = partial(function, increment=1)
    feat_stack_array, feat_labels = rasterUtils.apply_function(
        feat_stack,
        feat_labels,
        working_dir,
        function,
        output_raster,
        chunck_size_x=10,
        chunck_size_y=10,
        ram=128)


if __name__ == "__main__":
    from iota2.Common import ServiceConfigFile as SCF
    from iota2.Common.ServiceConfigFile import iota2_parameters
    DESCRIPTION = ("Use a python function to generate new features, "
                   "through the use of numpy arrays")
    PARSER = argparse.ArgumentParser(description=DESCRIPTION)
    PARSER.add_argument("-config",
                        dest="config",
                        help="configuration file path",
                        default=None,
                        required=True)
    PARSER.add_argument("-output",
                        dest="output",
                        help="output raster",
                        default=None,
                        required=True)
    PARSER.add_argument("-tile",
                        dest="tile_name",
                        help="tile's name",
                        default=None,
                        required=True)
    PARSER.add_argument("-working_dir",
                        dest="working_dir",
                        help="tile's name",
                        default=None,
                        required=True)
    ARGS = PARSER.parse_args()
    # load configuration file
    CFG = SCF.serviceConfigFile(ARGS.pathConf)
    PARAMS = iota2_parameters(ARGS.pathConf)
    SEN_PARAM = PARAMS.get_sensors_parameters(ARGS.tile)
    OUTPUT_PATH = CFG.getParam("chain", "outputPath")

    compute_features(OUTPUT_PATH, SEN_PARAM, ARGS.output, ARGS.tile_name,
                     ARGS.working_dir)
