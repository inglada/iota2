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


class PixelValidity(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "get_pixValidity"
        super(PixelValidity, self).__init__(
            cfg, cfg_resources_file, resources_block_name
        )

        # step variables
        self.RAM = 1024.0 * get_RAM(self.resources["ram"])
        self.workingDirectory = workingDirectory

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = "Compute validity raster by tile"
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
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
        from Sensors import ProcessLauncher

        cloud_threshold = SCF.serviceConfigFile(self.cfg).getParam(
            "chain", "cloud_threshold"
        )

        def step_function(x):
            return ProcessLauncher.validity(
                x,
                self.cfg,
                "CloudThreshold_{}.shp".format(cloud_threshold),
                cloud_threshold,
                self.workingDirectory,
                self.RAM,
            )

        return step_function

    def step_outputs(self):
        """
        """
        pass
