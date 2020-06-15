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

class simplification(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "vectorisation"
        super(simplification, self).__init__(cfg, cfg_resources_file, resources_block_name)

        # step variables
        self.RAM = 1024.0 * get_RAM(self.resources["ram"])
        self.workingDirectory = workingDirectory
        self.outputPath = SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath')
        self.mmu = SCF.serviceConfigFile(self.cfg).getParam('Simplification', 'mmu')
        self.douglas = SCF.serviceConfigFile(self.cfg).getParam('Simplification', 'douglas')
        self.hermite = SCF.serviceConfigFile(self.cfg).getParam('Simplification', 'hermite')
        self.angle = SCF.serviceConfigFile(self.cfg).getParam('Simplification', 'angle')
        self.grasslib = SCF.serviceConfigFile(self.cfg).getParam('Simplification', 'grasslib')

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        return "Vectorisation and simplification of classification"

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        outfilereg = os.path.join(self.outputPath, 'final', 'simplification',
                                  'classif_regul.tif')
        return [outfilereg]

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from simplification import VectAndSimp as vas

        tmpdir = os.path.join(self.outputPath, 'final', 'simplification', 'tmp')
        if self.workingDirectory:
            tmpdir = self.workingDirectory
        outfilevectsimp = os.path.join(self.outputPath, 'final', 'simplification',
                                       'classif.shp')
        return lambda x: vas.simplification(tmpdir,
                                                     x,
                                                     self.grasslib,
                                                     outfilevectsimp,
                                                     self.douglas,
                                                     self.hermite,
                                                     self.mmu,
                                                     self.angle)

    def step_outputs(self):
        """
        """
        pass
