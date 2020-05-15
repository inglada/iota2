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
from typing import List, Dict
from iota2.Steps import IOTA2Step
from iota2.Common import ServiceConfigFile as SCF
from iota2.Sampling import VectorSamplesMerge as VSM


class samplesByModels(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file):
        # heritage init
        resources_block_name = "mergeSample"
        super(samplesByModels, self).__init__(cfg, cfg_resources_file,
                                              resources_block_name)

        # step variables
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.nb_runs = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'runs')
        self.execution_mode = "cluster"
        self.suffix_list = ["usually"]
        if SCF.serviceConfigFile(self.cfg).getParam(
                'argTrain', 'dempster_shafer_SAR_Opt_fusion') is True:
            self.suffix_list.append("SAR")

        self.custom_features = SCF.serviceConfigFile(
            self.cfg).checkCustomFeature()
        self.number_of_chunks = SCF.serviceConfigFile(self.cfg).getParam(
            'external_features', "number_of_chunks")

        dico_model_samples_files = self.expected_files_to_merge()
        for suffix in self.suffix_list:
            for model_name, model_meta in self.spatial_models_distribution.items(
            ):
                for seed in range(self.nb_runs):
                    target_model = f"model_{model_name}_seed_{seed}_{suffix}"
                    task = self.i2_task(
                        task_name=f"merge_{target_model}",
                        log_dir=self.log_step_dir,
                        execution_mode=self.execution_mode,
                        task_parameters={
                            "f": VSM.vector_samples_merge,
                            "vector_list":
                            dico_model_samples_files[target_model],
                            "output_path": self.output_path
                        },
                        task_resources=self.resources)
                    dependencies = [
                        f"{tile}_{suffix}" for tile in model_meta["tiles"]
                    ]
                    if self.custom_features:
                        dependencies = [
                            f"{tile}_chunk_{chunk_num}_{suffix}"
                            for tile in model_meta["tiles"]
                            for chunk_num in range(self.number_of_chunks)
                        ]
                    self.add_task_to_i2_processing_graph(
                        task,
                        task_group="region_tasks",
                        task_sub_group=f"{target_model}",
                        task_dep_group="tile_tasks",
                        task_dep_sub_group=dependencies)

    def expected_files_to_merge(self) -> Dict[str, List[str]]:
        """
        """
        files_to_merge = {}
        for suffix in self.suffix_list:
            for seed in range(self.nb_runs):
                for model_name, model_meta in self.spatial_models_distribution.items(
                ):
                    file_list = []
                    for tile in model_meta["tiles"]:
                        file_name = f"{tile}_region_{model_name}_seed{seed}_Samples_learn.sqlite"
                        if suffix == "SAR":
                            file_name = f"{tile}_region_{model_name}_seed{seed}_Samples_SAR_learn.sqlite"
                        if self.custom_features:
                            for chunk in range(self.number_of_chunks):
                                file_name = f"{tile}_region_{model_name}_seed{seed}_{chunk}_Samples_learn.sqlite"
                                file_list.append(
                                    os.path.join(self.output_path,
                                                 "learningSamples", file_name))
                        else:
                            file_list.append(
                                os.path.join(self.output_path,
                                             "learningSamples", file_name))
                    files_to_merge[
                        f"model_{model_name}_seed_{seed}_{suffix}"] = file_list
        return files_to_merge

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Merge samples dedicated to the same model")
        return description
