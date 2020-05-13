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

from iota2.Steps import IOTA2Step
from iota2.Common import ServiceConfigFile as SCF
from iota2.Common import IOTA2Directory as IOTA2_dir


class features_maps_dir_tree(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file):
        # heritage init
        resources_block_name = "iota2_dir"
        super(features_maps_dir_tree, self).__init__(cfg, cfg_resources_file,
                                                     resources_block_name)

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Construct features maps output directories")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        return [
            SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath')
        ]

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        return lambda x: IOTA2_dir.generate_features_maps_directories(x)

    def step_outputs(self):
        outputPath = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        return os.path.exists(outputPath)
