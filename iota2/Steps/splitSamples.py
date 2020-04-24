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
from iota2.Sampling import SplitSamples as splitS


class splitSamples(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "split_samples"
        super(splitSamples, self).__init__(cfg, cfg_resources_file,
                                           resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.execution_mode = "cluster"

        task = self.i2_task(
            task_name=f"models_subdivision",
            log_dir=self.log_step_dir,
            execution_mode=self.execution_mode,
            task_parameters={
                "f":
                splitS.split_samples,
                "output_path":
                SCF.serviceConfigFile(self.cfg).getParam(
                    "chain", "outputPath"),
                "data_field":
                SCF.serviceConfigFile(self.cfg).getParam("chain", "dataField"),
                "enable_cross_validation":
                SCF.serviceConfigFile(self.cfg).getParam(
                    "chain", "enableCrossValidation"),
                "region_threshold":
                SCF.serviceConfigFile(self.cfg).getParam(
                    "chain", "mode_outside_RegionSplit"),
                "region_field":
                SCF.serviceConfigFile(self.cfg).getParam(
                    "chain", "regionField"),
                "ratio":
                SCF.serviceConfigFile(self.cfg).getParam("chain", "ratio"),
                "random_seed":
                SCF.serviceConfigFile(self.cfg).getParam(
                    "chain", "random_seed"),
                "runs":
                SCF.serviceConfigFile(self.cfg).getParam("chain", "runs"),
                "epsg":
                SCF.serviceConfigFile(self.cfg).getParam("GlobChain", "proj"),
                "workingDirectory":
                self.workingDirectory
            },
            task_resources=self.resources)
        self.add_task_to_i2_processing_graph(task,
                                             task_group="vector",
                                             task_sub_group="vector",
                                             task_dep_group="tile_tasks",
                                             task_dep_sub_group=self.tiles)

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = (
            "split learning polygons and Validation polygons in sub-sample if necessary"
        )
        return description
