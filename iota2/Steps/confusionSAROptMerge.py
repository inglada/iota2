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
from Common import ServiceConfigFile as SCF
from Cluster import get_RAM


class confusionSAROptMerge(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "SAROptConfusionMatrixFusion"
        super(confusionSAROptMerge, self).__init__(cfg, cfg_resources_file,
                                                   resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.data_field = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'dataField')

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        return "Fusion of confusion matrix"

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from iota2.Validation import ConfusionFusion as confFus
        return confFus.confusion_models_merge_parameters(self.output_path)

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from iota2.Validation import ConfusionFusion as confFus
        return lambda x: confFus.confusion_models_merge(x)

    def step_outputs(self):
        """
        """
        pass
