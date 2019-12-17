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
from Common import ServiceConfigFile as SCF
from Cluster import get_RAM
from Sampling import VectorSampler as vs


class samplesExtraction(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "vectorSampler"
        super(samplesExtraction, self).__init__(
            cfg, cfg_resources_file, resources_block_name
        )

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            "chain", "outputPath"
        )
        self.ram_extraction = 1024.0 * get_RAM(self.resources["ram"])

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = "Extract pixels values by tiles"
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        return vs.get_vectors_to_sample(
            os.path.join(self.output_path, "formattingVectors"),
            SCF.serviceConfigFile(self.cfg).getParam(
                "argTrain", "dempster_shafer_SAR_Opt_fusion"
            ),
        )

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """

        def step_function(x):
            return vs.generateSamples(
                x, self.workingDirectory, self.cfg, self.ram_extraction
            )

        return step_function

    def step_outputs(self):
        """
        """
        pass
