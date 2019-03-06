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

class Clump(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "clump"
        super(Clump, self).__init__(cfg, cfg_resources_file, resources_block_name)

        # step variables
        self.RAM = 1024.0 * get_RAM(self.resources["ram"])
        self.workingDirectory = workingDirectory
        self.outputPath = SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath')
        self.lib64bit = SCF.serviceConfigFile(self.cfg).getParam('Simplification', 'lib64bit')

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Clump of regularized classification raster")
        return description

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
        from simplification import ClumpClassif as clump
        outfileclp = os.path.join(self.outputPath, 'final', 'simplification',
                                  'classif_regul_clump.tif')
        tmpdir = os.path.join(self.outputPath, 'final', 'simplification', 'tmp')
        if self.workingDirectory:
            tmpdir = self.workingDirectory
        use64bit = False if self.lib64bit is not None else False
        step_function = lambda x: clump.clumpAndStackClassif(tmpdir,
                                                             x,
                                                             outfileclp,
                                                             str(self.RAM),
                                                             use64bit,
                                                             self.lib64bit)
        return step_function

    def step_outputs(self):
        """
        """
        pass
