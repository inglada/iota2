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
from iota2.Cluster import get_RAM
from iota2.Common import ServiceConfigFile as SCF
from iota2.Segmentation import segmentation
from iota2.Common.ServiceConfigFile import iota2_parameters


class slicSegmentation(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "slic_segmentation"
        super(slicSegmentation, self).__init__(cfg, cfg_resources_file,
                                               resources_block_name)

        # step variables
        self.RAM = 1024.0 * get_RAM(self.resources["ram"])
        self.workingDirectory = workingDirectory
        self.execution_mode = "cluster"
        self.step_tasks = []
        running_parameters = iota2_parameters(self.cfg)

        for tile in self.tiles:
            task = self.i2_task(
                task_name=f"slic_segmentation_{tile}",
                log_dir=self.log_step_dir,
                execution_mode=self.execution_mode,
                task_parameters={
                    "f":
                    segmentation.slicSegmentation,
                    "tile_name":
                    tile,
                    "output_path":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'chain', 'outputPath'),
                    "sensors_parameters":
                    running_parameters.get_sensors_parameters(tile),
                    "ram":
                    self.RAM,
                    "working_dir":
                    self.workingDirectory
                },
                task_resources=self.resources)
            task_in_graph = self.add_task_to_i2_processing_graph(
                task,
                task_group="tile_tasks",
                task_sub_group=tile,
                task_dep_group="tile_tasks",
                task_dep_sub_group=[tile])
            self.step_tasks.append(task_in_graph)

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Compute SLIC segmentation by tile")
        #~ About SLIC segmentation implementation :
        #~     https://ieeexplore.ieee.org/document/8606448
        return description
