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
""" The CommonMasks step"""
from iota2.Steps import IOTA2Step
from iota2.Cluster import get_RAM
from iota2.Common import ServiceConfigFile as SCF
from iota2.Sensors import ProcessLauncher


class CommonMasks(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "get_common_mask"
        super(CommonMasks, self).__init__(cfg, cfg_resources_file,
                                          resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.RAM = 1024.0 * get_RAM(self.resources["ram"])
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.execution_mode = "cluster"
        sensors_params = SCF.iota2_parameters(self.cfg)
        for tile in self.tiles:
            task = self.i2_task(
                task_name=f"common_mask_{tile}",
                log_dir=self.log_step_dir,
                execution_mode=self.execution_mode,
                task_parameters={
                    "f":
                    ProcessLauncher.commonMasks,
                    "tile_name":
                    tile,
                    "output_path":
                    self.output_path,
                    "sensors_parameters":
                    sensors_params.get_sensors_parameters(tile),
                    "working_directory":
                    self.workingDirectory,
                    "RAM":
                    self.RAM
                },
                task_resources=self.resources)
            self.add_task_to_i2_processing_graph(task,
                                                 task_group="tile_tasks",
                                                 task_sub_group=tile,
                                                 task_dep_group="tile_tasks",
                                                 task_dep_sub_group=[tile])

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Generate a common masks for each sensors")
        return description
