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


class slicSegmentation(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "slic_segmentation"
        super(slicSegmentation, self).__init__(cfg, cfg_resources_file,
                                               resources_block_name)

        # step variables
        self.RAM = 1024.0 * get_RAM(self.resources["ram"])
        self.workingDirectory = workingDirectory

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Compute SLIC segmentation by tile")
        #~ About SLIC segmentation implementation :
        #~     https://ieeexplore.ieee.org/document/8606448
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
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
        from iota2.Segmentation import segmentation
        from iota2.Common.ServiceConfigFile import iota2_parameters

        running_parameters = iota2_parameters(self.cfg)

        step_function = lambda x: segmentation.slicSegmentation(
            x,
            SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath'),
            running_parameters.get_sensors_parameters(x), self.RAM, self.
            workingDirectory)
        return step_function

    def step_outputs(self):
        """
        """
        pass
