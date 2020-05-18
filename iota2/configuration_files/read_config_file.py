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
"""
Generic module to read any configuration file
"""
from iota2.configuration_files.base_read_config_file import base_config_file


class load_config_file(base_config_file):
    """
    This class read a config file and init the different section
    according to the detected builder
    """
    def __init__(self, path_conf):
        super(load_config_file).__init__(path_conf)
        builder_mode = self.cfg.getParam("builder", "mode")
        if builder_mode == "classification":
            from iota2.sequence_builders.i2_classification import i2_classification as builder
        elif builder_mode == "features_map":
            from iota2.sequence_builders.i2_features_map import i2_features_map as builder
        else:
            raise NotImplementedError
        builder.load_default_parameters(self.cfg)

    def init_config(self, params):
        print(params)
