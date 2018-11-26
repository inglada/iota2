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
from Cluster import get_RAM
from Common import ServiceConfigFile as SCF 
from Common import IOTA2Directory as IOTA2_dir

class PixelValidity(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        super(PixelValidity, self).__init__(cfg, cfg_resources_file)

        # step variables
        self.workingDirectory = workingDirectory

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Compute validity raster by tile")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from Common import ServiceConfigFile as SCF
        tiles = SCF.serviceConfigFile(self.cfg).getParam('chain', 'listTile').split(" ")
        outputPath = SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath')
        pathTilesFeat = os.path.join(outputPath, "features")
        
        return [os.path.join(pathTilesFeat, tile) for tile in tiles]

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from Common import FileUtils as fut
        from Sensors import NbView

        cloud_threshold = SCF.serviceConfigFile(self.cfg).getParam('chain', 'cloud_threshold')
        cloud_threshold_name = "CloudThreshold_{}.shp".format(cloud_threshold)
        step_function = lambda x: NbView.genNbView(x, cloud_threshold_name, cloud_threshold, self.cfg, self.workingDirectory)
        return step_function

    def step_outputs(self):
        """
        """
        pass
        