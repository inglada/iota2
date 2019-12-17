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
from Cluster import get_RAM
from Common import ServiceConfigFile as SCF
from Common import IOTA2Directory as IOTA2_dir


class Sentinel1PreProcess(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = None
        super(Sentinel1PreProcess, self).__init__(
            cfg, cfg_resources_file, resources_block_name
        )

        # step variables
        self.workingDirectory = workingDirectory
        self.Sentinel1 = SCF.serviceConfigFile(cfg).getParam("chain", "S1Path")

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = "Sentinel-1 pre-processing"
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from Common import ServiceConfigFile as SCF

        tiles = (
            SCF.serviceConfigFile(self.cfg)
            .getParam("chain", "listTile")
            .split(" ")
        )
        return tiles

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from Sensors.SAR import S1Processor as SAR

        def step_function(x):
            return SAR.S1PreProcess(self.Sentinel1, x, self.workingDirectory)

        return step_function

    def step_outputs(self):
        """
        """
        pass
