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


class crownSearch(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "crownsearch"
        super(crownSearch, self).__init__(cfg, cfg_resources_file,
                                          resources_block_name)

        # step variables
        self.RAM = 1024.0 * get_RAM(self.resources["ram"])
        self.CPU = self.resources["cpu"]
        self.workingDirectory = workingDirectory
        self.outputPath = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.gridsize = SCF.serviceConfigFile(self.cfg).getParam(
            'Simplification', 'gridsize')

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Search crown entities for serialization process")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """

        return list(range(self.gridsize * self.gridsize))

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from simplification import searchCrownTile as sct
        tmpdir = os.path.join(self.outputPath, 'final', 'simplification',
                              'tmp')
        if self.workingDirectory:
            tmpdir = self.workingDirectory
        outfileclp = os.path.join(self.outputPath, 'final', 'simplification',
                                  'classif_regul_clump.tif')
        inclump = os.path.join(self.outputPath, 'final', 'simplification',
                               'clump32bits.tif')
        outfilegrid = os.path.join(self.outputPath, 'final', 'simplification',
                                   'grid.shp')
        outseria = os.path.join(self.outputPath, 'final', 'simplification',
                                'tiles')
        step_function = lambda x: sct.searchCrownTile(
            tmpdir, outfileclp, inclump, self.RAM, outfilegrid, outseria, self.
            CPU, x)
        return step_function

    def step_outputs(self):
        """
        """
        pass
