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

from iota2.Steps import IOTA2Step
from iota2.Common import ServiceConfigFile as SCF
from iota2.Sampling.SplitSamplesForOBIA import split_segmentation_by_tiles


class splitSegmentationByTiles(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, working_directory=None):
        # heritage init
        resources_block_name = "splitSegmentationByTiles"
        super(splitSegmentationByTiles, self).__init__(cfg, cfg_resources_file,
                                                       resources_block_name)

        # step variables
        self.working_directory = working_directory
        self.segmentation = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'OBIA_segmentation_path')
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            "chain", "outputPath")
        self.epsg = int(
            SCF.serviceConfigFile(self.cfg).getParam("GlobChain",
                                                     "proj").split(":")[-1])
        self.region_path = SCF.serviceConfigFile(self.cfg).getParam(
            "chain", "regionPath")
        self.tiles = SCF.serviceConfigFile(self.cfg).getParam(
            "chain", "listTile").split(" ")

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

        return [self.segmentation]

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """

        return lambda x: split_segmentation_by_tiles(
            iota2_directory=self.output_path,
            tiles=self.tiles,
            segmentation=x,
            epsg=self.epsg,
            region_path=self.region_path,
            working_dir=self.working_directory)

    def step_outputs(self):
        """
        """
        pass
