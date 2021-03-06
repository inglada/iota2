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
""" The CommonMasks step"""
from iota2.Steps import IOTA2Step
from iota2.Cluster import get_RAM
from iota2.Common import ServiceConfigFile as SCF


class CommonMasks(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "get_common_mask"
        super(CommonMasks, self).__init__(cfg, cfg_resources_file,
                                          resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.RAM = 1024.0 * get_RAM(self.resources["ram"])
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Generate a common masks for each sensors")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from iota2.Common import ServiceConfigFile as SCF
        tiles = SCF.serviceConfigFile(self.cfg).getParam('chain',
                                                         'listTile').split(" ")
        return tiles

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from Sensors import ProcessLauncher
        from iota2.Common import ServiceConfigFile as SCF
        sensors_params = SCF.iota2_parameters(self.cfg)
        step_function = lambda x: ProcessLauncher.commonMasks(
            x, self.output_path, sensors_params.get_sensors_parameters(x), self
            .workingDirectory, self.RAM)
        return step_function

    def step_outputs(self):
        """
        """
        pass
