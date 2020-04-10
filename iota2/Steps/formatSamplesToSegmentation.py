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

from Steps import IOTA2Step
from Common import ServiceConfigFile as SCF
from Sampling import SamplesMerge as samples_merge


class formatSamplesToSegmentation(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "formatSamplesToSegmentation"
        super(formatSamplesToSegmentation,
              self).__init__(cfg, cfg_resources_file, resources_block_name)

        # step variables
        self.working_directory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.field_region = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'regionField')
        self.nb_runs = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'runs')
        self.region_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'regionPath')

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("intersect samples with segments")
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
        from iota2.Sampling.SplitSamplesForOBIA import format_sample_to_segmentation
        return lambda x: format_sample_to_segmentation(
            iota2_directory=self.output_path,
            region_tiles_seed=x,
            working_dir=self.working_directory,
            region_path=self.region_path)

    def step_outputs(self):
        """
        """
        pass
