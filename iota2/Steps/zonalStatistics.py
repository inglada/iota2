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

from Steps import IOTA2Step
from Cluster import get_RAM
from Common import ServiceConfigFile as SCF

class zonalStatistics(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "statistics"
        super(zonalStatistics, self).__init__(cfg, cfg_resources_file, resources_block_name)

        # step variables
        self.RAM = 1024.0 * get_RAM(self.resources["ram"])
        self.workingDirectory = workingDirectory
        self.outputPath = SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath')
        
        self.rastclass = SCF.serviceConfigFile(self.cfg).getParam('Simplification', 'classification')
        self.rastconf = SCF.serviceConfigFile(self.cfg).getParam('Simplification', 'confidence')
        self.rastval = SCF.serviceConfigFile(self.cfg).getParam('Simplification', 'validity')
        self.seed = SCF.serviceConfigFile(self.cfg).getParam('Simplification', 'seed')
        self.bingdal = SCF.serviceConfigFile(self.cfg).getParam('Simplification', 'bingdal')

        if self.rastclass is None:
            if self.seed is not None:
                self.rastclass = os.path.join(self.outputPath, 'final', 'Classif_Seed_{}.tif'.format(self.seed))
                if self.rastconf is None:
                    self.rastconf = os.path.join(self.outputPath, 'final', 'Confidence_Seed_{}.tif'.format(self.seed))
            else:
                if os.path.exists(os.path.join(self.outputPath, 'final', 'Classifications_fusion.tif')):
                    self.rastclass = os.path.join(self.outputPath, 'final', 'Classifications_fusion.tif')
                else:
                    self.rastclass = os.path.join(self.outputPath, 'final', 'Classif_Seed_0.tif')
                # Pas de fusion de confidence ?
        if self.rastval is None:
            self.rastval = os.path.join(self.outputPath, 'final', 'PixelsValidity.tif') 
        if self.rastconf is None:
            self.rastconf = os.path.join(self.outputPath, 'final', 'Confidence_Seed_0.tif')

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Compute statistics for each polygon of the classification")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from simplification import ZonalStats as zs
        outfilesvectpath = os.path.join(self.outputPath, 'final', 'simplification', 'vectors')
        return zs.getParameters(outfilesvectpath, outfilesvectpath)


    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from simplification import ZonalStats as zs

        tmpdir = os.path.join(self.outputPath, 'final', 'simplification', 'tmp')
        if self.workingDirectory:
            tmpdir = self.workingDirectory

        step_function = lambda x: zs.zonalstats(tmpdir,
                                                [self.rastclass, self.rastconf, self.rastval],
                                                x,
                                                self.bingdal)

        return step_function

    def step_outputs(self):
        """
        """
        pass
