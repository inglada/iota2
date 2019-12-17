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


class confusionsMerge(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "confusionMatrixFusion"
        super(confusionsMerge, self).__init__(
            cfg, cfg_resources_file, resources_block_name
        )

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            "chain", "outputPath"
        )
        self.data_field = SCF.serviceConfigFile(self.cfg).getParam("chain", "dataField")
        self.ground_truth = SCF.serviceConfigFile(self.cfg).getParam(
            "chain", "groundTruth"
        )

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = "Merge all confusions"
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        return [self.ground_truth]

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from Validation import ConfusionFusion as confFus

        def step_function(x):
            return confFus.confFusion(
                x,
                self.data_field,
                os.path.join(self.output_path, "final", "TMP"),
                os.path.join(self.output_path, "final", "TMP"),
                os.path.join(self.output_path, "final", "TMP"),
                self.cfg,
            )

        return step_function

    def step_outputs(self):
        """
        """
        pass
