#!/usr/bin/python
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

import IOTA2Step
from Common import ServiceConfigFile as SCF
from Sampling.SplitTrainSamplesForOBIA import split_segmentation_by_tiles

class splitSegmentationByTiles(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "splitSegmentationByTiles"
        super(splitSegmentationByTiles, self).__init__(cfg, cfg_resources_file, resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("split segmentation by tiles")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        tiles = SCF.serviceConfigFile(self.cfg).getParam('chain', 'listTile').split(" ")
        return tiles

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        step_function = lambda x: split_segmentation_by_tiles(self.cfg, x, self.workingDirectory)
        return step_function

    def step_outputs(self):
        """
        """
        pass
