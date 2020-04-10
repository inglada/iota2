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

from iota2.Steps import IOTA2Step
from iota2.Cluster import get_RAM
from iota2.Common import ServiceConfigFile as SCF
from iota2.Sampling import SamplesMerge as samples_merge


class learningSamplesZonalStatistics(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, working_directory=None):
        # heritage init
        resources_block_name = "learningSamplesZonalStatistics"
        super(learningSamplesZonalStatistics,
              self).__init__(cfg, cfg_resources_file, resources_block_name)

        # step variables
        self.working_directory = working_directory
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
        description = ("compute zonalstatistics for learning samples")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        region_seed_tile = samples_merge.get_models(
            os.path.join(self.output_path, "formattingVectors"),
            self.field_region, self.nb_runs)
        return region_seed_tile

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from iota2.Sampling import SamplesZonalStatistics
        tile = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'listTile').split(" ")[0]
        sensors_parameters = SCF.iota2_parameters(
            self.cfg).get_sensors_parameters(tile)
        return (
            lambda x: SamplesZonalStatistics.learning_samples_zonal_statistics(
                iota2_directory=self.output_path,
                region_seed_tile=x,
                sensors_parameters=sensors_parameters,
                working_directory=self.working_directory))

    def step_outputs(self):
        """
        """
        pass
