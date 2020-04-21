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
from iota2.Sampling import DataAugmentation


class genSyntheticSamples(IOTA2Step.Step):
    def __init__(self,
                 cfg,
                 cfg_resources_file,
                 transfert_samples,
                 workingDirectory=None):
        # heritage init
        resources_block_name = "samplesAugmentation"
        super(genSyntheticSamples, self).__init__(cfg, cfg_resources_file,
                                                  resources_block_name)

        # step variables
        self.working_directory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.ground_truth = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'groundTruth')
        self.data_field = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'dataField')
        self.sample_augmentation = SCF.serviceConfigFile(self.cfg).getParam(
            'argTrain', 'sampleAugmentation')
        self.nb_runs = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'runs')

        self.execution_mode = "cluster"
        self.step_tasks = []

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
                        task_name=f"data_augmentation_{target_model}",
                        log_dir=self.log_step_dir,
                        execution_mode=self.execution_mode,
                        task_parameters={
                            "f": DataAugmentation.DataAugmentationSynthetic,
                            "samples": samples_file,
                            "groundTruth": self.ground_truth,
                            "dataField": self.data_field.lower(),
                            "strategies": self.sample_augmentation,
                            "workingDirectory": self.working_directory
                        },
                        task_resources=self.resources)
                    task_in_graph = self.add_task_to_i2_processing_graph(
                        task,
                        task_group="region_tasks",
                        task_sub_group=f"{target_model}",
                        task_dep_group="seed_tasks"
                        if transfert_samples else "region_tasks",
                        task_dep_sub_group=[seed]
                        if transfert_samples else [target_model])
                    self.step_tasks.append(task_in_graph)

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Generate synthetic samples")
        return description
