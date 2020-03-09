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


class prodVectors(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "prodVectors"
        super(prodVectors, self).__init__(cfg, cfg_resources_file,
                                          resources_block_name)

        # step variables
        self.RAM = 1024.0 * get_RAM(self.resources["ram"])
        self.workingDirectory = workingDirectory
        self.outputPath = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.nomenclature = SCF.serviceConfigFile(self.cfg).getParam(
            'Simplification', 'nomenclature')

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = (
            "Merge statistics and format output vectors for OSO production")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from simplification import ZonalStats as zs

        tmpdir = os.path.join(self.outputPath, 'final', 'simplification',
                              'tmp')

        return zs.getVectorsChunks(tmpdir)

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from simplification import ZonalStats as zs

        outpath = os.path.join(self.outputPath, 'final', 'vectors')

        step_function = lambda x: zs.mergeSubVector(
            x, outpath, self.nomenclature, oso=True, outbase="departement_")

        return step_function

    def step_outputs(self):
        """
        """
        pass

    def step_clean(self):
        """
        """
        pass
