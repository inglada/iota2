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
        self.execution_mode = "cluster"
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.data_field = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'dataField')
        self.nb_runs = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'runs')
        for model_name, model_meta in self.spatial_models_distribution.items():
            for seed in range(self.nb_runs):
                for tile in model_meta["tiles"]:
                    target_model = f"{model_name}_S_{seed}_T_{tile}"
                    task = self.i2_task(task_name=f"stats_{target_model}",
                                        log_dir=self.log_step_dir,
                                        execution_mode=self.execution_mode,
                                        task_parameters={
                                            "f":
                                            SamplesStat.samples_stats,
                                            "region_seed_tile":
                                            (model_name, str(seed), tile),
                                            "iota2_directory":
                                            self.output_path,
                                            "data_field":
                                            self.data_field,
                                            "working_directory":
                                            self.workingDirectory
                                        },
                                        task_resources=self.resources)
                    self.add_task_to_i2_processing_graph(
                        task,
                        task_group="tile_tasks_model",
                        task_sub_group=f"{tile}_{model_name}_{seed}",
                        task_dep_dico={
                            "region_tasks":
                            [f"model_{model_name}_seed_{seed}"]
                        })

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Generate samples statistics by models")
        return description
