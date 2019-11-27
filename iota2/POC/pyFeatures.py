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

from functools import partial
import argparse

from iota2.Sensors.Sensors_container import Sensors_container
from iota2.Common.GenerateFeatures import generateFeatures
from iota2.Common import ServiceConfigFile as SCF
from iota2.Common import IOTA2Directory

import rasterUtils


def smart_scientific_function(array, increment, *args, **kwargs):
    """do important scientific stuff, publishing in progress
    """
    return array + increment


def compute_features(config_path, output_raster, tile_name, working_dir,
                     function=smart_scientific_function) -> None:
    """Use a python function to generate features through the use of numpy arrays

    Parameters
    ----------
    config_path : str
        configuration file path
    output_raster : str
        output raster path
    tile_name : str
        tile to compute
    function : function
        function to apply on iota²' stack
    """

    # first, generate the full iota2 stack.
    IOTA2Directory.GenerateDirectories(config_path)
    sensors = Sensors_container(config_path, tile_name, working_dir)
    cfg = SCF.serviceConfigFile(config_path)

    feat_stack, feat_labels, _ = generateFeatures(working_dir, tile_name, cfg)

    # Then compute new features
    function = partial(function, increment=1)
    feat_stack_array, feat_labels = rasterUtils.apply_function(feat_stack,
                                                               feat_labels,
                                                               working_dir,
                                                               function,
                                                               output_raster,
                                                               chunck_size_x=10,
                                                               chunck_size_y=10,
                                                               ram=128)


if __name__ == "__main__":
    description = ("Use a python function to generate new features, "
                   "through the use of numpy arrays")
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-config", dest="config",
                        help="configuration file path", default=None,
                        required=True)
    parser.add_argument("-output", dest="output", help="output raster",
                        default=None, required=True)
    parser.add_argument("-tile", dest="tile_name", help="tile's name",
                        default=None, required=True)
    parser.add_argument("-working_dir", dest="working_dir", help="tile's name",
                        default=None, required=True)
    args = parser.parse_args()

    compute_features(args.config, args.output, args.tile_name,
                     args.working_dir)
