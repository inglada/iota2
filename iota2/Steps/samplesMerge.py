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

from iota2.Steps import IOTA2Step
from iota2.Common import ServiceConfigFile as SCF
from iota2.Sampling import SamplesMerge as samples_merge


class samplesMerge(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "samplesMerge"
        super(samplesMerge, self).__init__(cfg, cfg_resources_file,
                                           resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.field_region = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'regionField')
        self.nb_runs = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'runs')

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("merge samples by models")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        return samples_merge.get_models(
            os.path.join(self.output_path, "formattingVectors"),
            self.field_region, self.nb_runs)

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        step_function = lambda x: samples_merge.samples_merge(
            x,
            SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath'),
            SCF.serviceConfigFile(self.cfg).getParam('chain', 'regionField'),
            SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs'),
            SCF.serviceConfigFile(self.cfg).getParam('chain',
                                                     'enableCrossValidation'),
            SCF.serviceConfigFile(self.cfg).getParam(
                'argTrain', 'dempster_shafer_SAR_Opt_fusion'), self.
            workingDirectory)
        return step_function

    def step_outputs(self):
        """
        """
        pass
