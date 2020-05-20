# !/usr/bin/env python3
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

from iota2.Steps import IOTA2Step
from iota2.Cluster import get_RAM
from iota2.Common import ServiceConfigFile as SCF
from iota2.Sensors import ProcessLauncher


class PixelValidity(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "get_pixValidity"
        super(PixelValidity, self).__init__(cfg, cfg_resources_file,
                                            resources_block_name)

        # step variables
        self.ram = 1024.0 * get_RAM(self.resources["ram"])
        self.working_directory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        cloud_threshold = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'cloud_threshold')
        self.execution_mode = "cluster"

        for tile in self.tiles:
            task = self.i2_task(task_name=f"validity_raster_{tile}",
                                log_dir=self.log_step_dir,
                                execution_mode=self.execution_mode,
                                task_parameters={
                                    "f": ProcessLauncher.validity,
                                    "tile_name": tile,
                                    "config_path": self.cfg,
                                    "output_path": self.output_path,
                                    "maskOut_name":
                                    f"CloudThreshold_{cloud_threshold}.shp",
                                    "view_threshold": cloud_threshold,
                                    "workingDirectory": self.working_directory,
                                    "RAM": self.ram
                                },
                                task_resources=self.resources)
            self.add_task_to_i2_processing_graph(
                task,
                task_group="tile_tasks",
                task_sub_group=tile,
                task_dep_dico={"tile_tasks": [tile]})

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Compute validity raster by tile")
        return description
