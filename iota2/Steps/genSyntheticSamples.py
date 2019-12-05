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


class genSyntheticSamples(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "samplesAugmentation"
        super(
            genSyntheticSamples,
            self).__init__(
            cfg,
            cfg_resources_file,
            resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(
            self.cfg).getParam(
            'chain', 'outputPath')
        self.ground_truth = SCF.serviceConfigFile(
            self.cfg).getParam(
            'chain', 'groundTruth')
        self.data_field = SCF.serviceConfigFile(
            self.cfg).getParam(
            'chain', 'dataField')
        self.sample_augmentation = SCF.serviceConfigFile(
            self.cfg).getParam('argTrain', 'sampleAugmentation')

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Generate synthetic samples")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from Sampling import DataAugmentation
        return DataAugmentation.GetDataAugmentationSyntheticParameters(
            self.output_path)

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from Sampling import DataAugmentation

        def step_function(x): return DataAugmentation.DataAugmentationSynthetic(x,
                                                                                self.ground_truth,
                                                                                self.data_field.lower(),
                                                                                self.sample_augmentation,
                                                                                self.workingDirectory)
        return step_function

    def step_outputs(self):
        """
        """
        pass
