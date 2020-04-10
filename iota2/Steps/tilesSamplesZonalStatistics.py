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


class tilesSamplesZonalStatistics(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "tilesSamplesZonalStatistics"
        super(tilesSamplesZonalStatistics,
              self).__init__(cfg, cfg_resources_file, resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.cfg = cfg
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            "chain", "outputPath")
        self.first_tile = SCF.serviceConfigFile(self.cfg).getParam(
            "chain", "listTile").split(" ")[0]
        self.region_path = SCF.serviceConfigFile(self.cfg).getParam(
            "chain", "regionPath")

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("compute zonal statistics for segments")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        tiles = SCF.serviceConfigFile(self.cfg).getParam('chain',
                                                         'listTile').split(' ')
        return tiles

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from iota2.Sampling import SamplesZonalStatistics
        sensors_parameters = SCF.iota2_parameters(
            self.cfg).get_sensors_parameters(self.first_tile)
        return (lambda x: SamplesZonalStatistics.tile_samples_zonal_statistics(
            iota2_directory=self.output_path,
            tile=x,
            sensors_parameters=sensors_parameters,
            region_path=self.region_path,
            working_directory=self.workingDirectory))

    def step_outputs(self):
        """
        """
        pass
