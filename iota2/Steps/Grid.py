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


class Grid(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "grid"
        super(Grid, self).__init__(cfg, cfg_resources_file,
                                   resources_block_name)

        # step variables
        self.RAM = 1024.0 * get_RAM(self.resources["ram"])
        self.workingDirectory = workingDirectory
        self.outputPath = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.gridsize = SCF.serviceConfigFile(self.cfg).getParam(
            'Simplification', 'gridsize')
        self.epsg = int(
            SCF.serviceConfigFile(self.cfg).getParam('GlobChain',
                                                     'proj').split(":")[-1])

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        return "Generation of grid for serialisation"

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        outfileclp = os.path.join(self.outputPath, 'final', 'simplification',
                                  'classif_regul_clump.tif')
        return [outfileclp]

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from simplification import GridGenerator as gridg

        outfilegrid = os.path.join(self.outputPath, 'final', 'simplification',
                                   'grid.shp')
        return lambda x: gridg.grid_generate(
            outfilegrid, self.gridsize, int(self.epsg.split(':')[1]), x)

    def step_outputs(self):
        """
        """
        pass
