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
from typing import Optional

from iota2.Steps import IOTA2Step
from iota2.Common import ServiceConfigFile as SCF
from iota2.Sampling import SamplesMerge as samples_merge


class samplesMerge(IOTA2Step.Step):
    def __init__(self,
                 cfg: str,
                 cfg_resources_file: str,
                 workingDirectory: Optional[str] = None,
                 huge_models: Optional[bool] = False):
        # heritage init
        resources_block_name = "samplesMerge"
        super(samplesMerge, self).__init__(cfg, cfg_resources_file,
                                           resources_block_name)
        self.execution_mode = "cluster"
        self.step_tasks = []
        # step variables
        self.working_directory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.field_region = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'regionField')
        self.nb_runs = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'runs')
        for model_name, model_meta in self.spatial_models_distribution.items():
            for seed in range(self.nb_runs):
                target_model = f"model_{model_name}_seed_{seed}"
                task = self.i2_task(
                    task_name=f"merge_{target_model}",
                    log_dir=self.log_step_dir,
                    execution_mode=self.execution_mode,
                    task_parameters={
                        "f":
                        samples_merge.samples_merge,
                        "region_tiles_seed":
                        (model_name, model_meta["tiles"], seed),
                        "output_path":
                        self.output_path,
                        "region_field":
                        self.field_region,
                        "runs":
                        self.nb_runs,
                        "enable_cross_validation":
                        SCF.serviceConfigFile(self.cfg).getParam(
                            'chain', 'enableCrossValidation'),
                        "ds_sar_opt_flag":
                        SCF.serviceConfigFile(self.cfg).getParam(
                            'argTrain', 'dempster_shafer_SAR_Opt_fusion'),
                        "working_directory":
                        self.working_directory
                    },
                    task_resources=self.resources)
                task_in_graph = self.add_task_to_i2_processing_graph(
                    task,
                    task_group="region_tasks",
                    task_sub_group=target_model,
                    task_dep_group="vector" if huge_models else "tile_tasks",
                    task_dep_sub_group=["vector"]
                    if huge_models else model_meta["tiles"])
                self.step_tasks.append(task_in_graph)

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("merge samples by models")
        return description
