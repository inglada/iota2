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
from iota2.Cluster import get_RAM
from iota2.Common import ServiceConfigFile as SCF


class sensorsPreprocess(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "preprocess_data"
        super(sensorsPreprocess, self).__init__(cfg, cfg_resources_file,
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
        return "Sensors pre-processing"

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from iota2.Common import ServiceConfigFile as SCF
        return SCF.serviceConfigFile(self.cfg).getParam('chain',
                                                         'listTile').split(" ")

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from iota2.Sensors import ProcessLauncher
        return lambda x: ProcessLauncher.preprocess(
            x, self.cfg, self.output_path, self.workingDirectory, self.RAM)

    def step_outputs(self):
        """
        """
        pass
