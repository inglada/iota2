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
import os

from Steps import IOTA2Step
from Common import ServiceConfigFile as SCF


class VectorFormatting(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "samplesFormatting"
        super(VectorFormatting, self).__init__(
            cfg, cfg_resources_file, resources_block_name
        )

        # step variables
        self.workingDirectory = workingDirectory
        self.outputPath = SCF.serviceConfigFile(self.cfg).getParam(
            "chain", "outputPath"
        )

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = "Prepare samples"
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        tiles = SCF.serviceConfigFile(self.cfg).getParam("chain", "listTile").split(" ")
        return tiles

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from Sampling import VectorFormatting as VF

        def step_function(x):
            return VF.VectorFormatting(self.cfg, x, self.workingDirectory)

        return step_function

    def step_outputs(self):
        """
        """
        pass
