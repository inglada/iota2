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
from iota2.Sampling import DimensionalityReduction as DR


class samplesDimReduction(IOTA2Step.Step):
    def __init__(self,
                 cfg,
                 cfg_resources_file,
                 seed_granularity,
                 workingDirectory=None):
        # heritage init
        resources_block_name = "dimensionalityReduction"
        super(samplesDimReduction, self).__init__(cfg, cfg_resources_file,
                                                  resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.nb_runs = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'runs')
        self.targetDimension = SCF.serviceConfigFile(self.cfg).getParam(
            'dimRed', 'targetDimension')
        self.reductionMode = SCF.serviceConfigFile(self.cfg).getParam(
            'dimRed', 'reductionMode')
        self.execution_mode = "cluster"
        self.suffix_list = ["usually"]
        if SCF.serviceConfigFile(self.cfg).getParam(
                'argTrain', 'dempster_shafer_SAR_Opt_fusion') is True:
            self.suffix_list.append("SAR")
        for suffix in self.suffix_list:
            for model_name, _ in self.spatial_models_distribution.items():
                for seed in range(self.nb_runs):
                    if suffix == "SAR":
                        samples_file = os.path.join(
                            self.output_path, "learningSamples",
                            f"Samples_region_{model_name}_seed{seed}_learn_SAR.sqlite"
                        )
                    else:
                        samples_file = os.path.join(
                            self.output_path, "learningSamples",
                            f"Samples_region_{model_name}_seed{seed}_learn.sqlite"
                        )
                    target_model = f"model_{model_name}_seed_{seed}_{suffix}"
                    task = self.i2_task(
                        task_name=f"data_reduction_{target_model}",
                        log_dir=self.log_step_dir,
                        execution_mode=self.execution_mode,
                        task_parameters={
                            "f":
                            DR.sample_dimensionality_reduction,
                            "io_file_pair":
                            (samples_file,
                             samples_file.replace(".sqlite",
                                                  "_reduced.sqlite")),
                            "iota2_output":
                            self.output_path,
                            "target_dimension":
                            self.targetDimension,
                            "reduction_mode":
                            self.reductionMode
                        },
                        task_resources=self.resources)
                    dep_key = "region_tasks" if not seed_granularity else "seed_tasks"
                    dep_values = [target_model
                                  ] if not seed_granularity else [seed]
                    self.add_task_to_i2_processing_graph(
                        task,
                        task_group="region_tasks",
                        task_sub_group=f"{target_model}",
                        task_dep_dico={dep_key: dep_values})

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Dimensionality reduction")
        return description
