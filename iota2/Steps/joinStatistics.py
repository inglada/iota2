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

class joinStatistics(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "join"
        super(joinStatistics, self).__init__(cfg, cfg_resources_file, resources_block_name)

        # step variables
        self.RAM = 1024.0 * get_RAM(self.resources["ram"])
        self.CPU = self.resources["cpu"]
        self.workingDirectory = workingDirectory
        self.outputPath = SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath')
        self.outprefix = SCF.serviceConfigFile(self.cfg).getParam('Simplification', 'outprefix')
        self.dozip = SCF.serviceConfigFile(self.cfg).getParam('Simplification', 'dozip')

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Join shapefile and statistics")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from simplification import computeStats as cs
        csvfilestojoin = os.path.join(self.outputPath, 'final', 'simplification',
                                      'vectors')
        return cs.getStatsList(csvfilestojoin)

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from simplification import computeStats as cs

        tmpdir = self.workingDirectory
        if tmpdir is None:
            tmpdir = os.path.join(self.outputPath, 'final', 'simplification',
                                  'tmp')
        outfilevecttojoin = os.path.join(self.outputPath, 'final', 'simplification',
                                         'vectors', '%s_.shp'%(self.outprefix))
        step_function = lambda x: cs.computeStats(outfilevecttojoin,
                                                  x,
                                                  tmpdir,
                                                  self.dozip)
        return step_function

    def step_outputs(self):
        """
        """
        pass
