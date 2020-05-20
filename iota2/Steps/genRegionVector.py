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
from iota2.Sampling import TileArea as area


class genRegionVector(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "regionShape"
        super(genRegionVector, self).__init__(cfg, cfg_resources_file,
                                              resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.outputPath = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.execution_mode = "cluster"
        task = self.i2_task(task_name=f"region_generation",
                            log_dir=self.log_step_dir,
                            execution_mode=self.execution_mode,
                            task_parameters={
                                "f":
                                area.generate_region_shape,
                                "envelope_directory":
                                os.path.join(self.outputPath, "envelope"),
                                "output_region_file":
                                SCF.serviceConfigFile(self.cfg).getParam(
                                    'chain', 'regionPath'),
                                "out_field_name":
                                SCF.serviceConfigFile(self.cfg).getParam(
                                    'chain', 'regionField'),
                                "i2_output_path":
                                self.outputPath,
                                "working_directory":
                                self.workingDirectory
                            },
                            task_resources=self.resources)
        self.add_task_to_i2_processing_graph(
            task,
            task_group="vector",
            task_sub_group="vector",
            task_dep_dico={"vector": ["vector"]})

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Generate a region vector")
        return description
