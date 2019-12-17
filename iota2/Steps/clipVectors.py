#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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


class clipVectors(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "clipvectors"
        super(clipVectors, self).__init__(
            cfg, cfg_resources_file, resources_block_name
        )

        # step variables
        self.RAM = 1024.0 * get_RAM(self.resources["ram"])
        self.workingDirectory = workingDirectory
        self.outputPath = SCF.serviceConfigFile(self.cfg).getParam(
            "chain", "outputPath"
        )
        self.grasslib = SCF.serviceConfigFile(self.cfg).getParam(
            "Simplification", "grasslib"
        )
        self.clipfile = SCF.serviceConfigFile(self.cfg).getParam(
            "Simplification", "clipfile"
        )
        self.clipfield = SCF.serviceConfigFile(self.cfg).getParam(
            "Simplification", "clipfield"
        )
        self.outprefix = SCF.serviceConfigFile(self.cfg).getParam(
            "Simplification", "outprefix"
        )
        self.outmos = os.path.join(
            self.outputPath, "final", "simplification", "mosaic"
        )
        self.outfilevect = os.path.join(
            self.outputPath, "final", "simplification", "vectors"
        )

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = (
            "Clip vector files for each feature of clipfile parameters"
        )
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from simplification import MergeTileRasters as mtr

        return mtr.getListVectToClip(
            self.outmos, self.clipfield, self.outfilevect
        )

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from simplification import VectAndSimp as vas

        tmpdir = os.path.join(
            self.outputPath, "final", "simplification", "tmp"
        )
        if self.workingDirectory:
            tmpdir = self.workingDirectory

        step_function = lambda x: vas.clipVectorfile(
            tmpdir,
            x[0],
            self.clipfile,
            self.clipfield,
            x[1],
            prefix=self.outprefix,
            outpath=self.outfilevect,
        )

        return step_function

    def step_outputs(self):
        """
        """
        pass
