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
from iota2.Sampling import SamplesStat


class statsSamplesModel(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "samplesStatistics"
        super(statsSamplesModel, self).__init__(cfg, cfg_resources_file,
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
        return "Generate samples statistics by models"

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        return SamplesStat.region_tile(
            os.path.join(self.output_path, "samplesSelection"))

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """

        return lambda x: SamplesStat.samples_stats(
            x, self.output_path, self.data_field, self.workingDirectory)

    def step_outputs(self):
        """
        """
        pass
