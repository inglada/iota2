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
import os
from typing import Dict

from iota2.Steps import IOTA2Step
from iota2.Cluster import get_RAM
from iota2.Common import ServiceConfigFile as SCF

from iota2.Learning.TrainingCmd import config_model
from iota2.Learning.TrainSkLearn import cast_config_cv_parameters

from iota2.Learning.launch_learning import learn_otb_model
from iota2.Learning.launch_learning import learn_scikitlearn_model
from iota2.Learning.launch_learning import learn_autocontext_model


class learnModel(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "training"
        super(learnModel, self).__init__(cfg, cfg_resources_file,
                                         resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.data_field = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'dataField')

        self.region_field = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'regionField')
        self.ground_truth = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'groundTruth')
        self.runs = SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs')

        self.enable_autoContext = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'enable_autoContext')
        self.autoContext_iterations = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'autoContext_iterations')
        self.superpix_data_field = "superpix"
        self.tiles = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'listTile').split("_")
        self.available_ram = 1024.0 * get_RAM(self.resources["ram"])
        self.use_scikitlearn = SCF.serviceConfigFile(self.cfg).getParam(
            'scikit_models_parameters', 'model_type') is not None

        self.classifier = SCF.serviceConfigFile(self.cfg).getParam(
            'argTrain', 'classifier')
        self.classifier_options = SCF.serviceConfigFile(self.cfg).getParam(
            'argTrain', 'options')

        self.apply_standardization = SCF.serviceConfigFile(self.cfg).getParam(
            "scikit_models_parameters", "standardization")
        self.cross_valid_params = cast_config_cv_parameters(
            SCF.serviceConfigFile(self.cfg).getParam(
                "scikit_models_parameters", "cross_validation_parameters"))
        self.cross_val_grouped = SCF.serviceConfigFile(self.cfg).getParam(
            "scikit_models_parameters", "cross_validation_grouped")
        self.folds_number = SCF.serviceConfigFile(self.cfg).getParam(
            "scikit_models_parameters", "cross_validation_folds")
        self.sk_model_parameters = dict(
            SCF.serviceConfigFile(
                self.cfg).getSection("scikit_models_parameters"))

        self.sensors_parameters = ""

        self.sk_model_name = self.sk_model_parameters['model_type']
        del self.sk_model_parameters['model_type']
        del self.sk_model_parameters['standardization']
        del self.sk_model_parameters['cross_validation_grouped']
        del self.sk_model_parameters['cross_validation_folds']
        del self.sk_model_parameters['cross_validation_parameters']

        self.execution_mode = "cluster"

        self.suffix_list = ["usually"]
        if SCF.serviceConfigFile(self.cfg).getParam(
                'argTrain', 'dempster_shafer_SAR_Opt_fusion') is True:
            self.suffix_list.append("SAR")
        for suffix in self.suffix_list:
            for model_name, model_meta in self.spatial_models_distribution.items(
            ):
                for seed in range(self.runs):
                    target_model = f"model_{model_name}_seed_{seed}_{suffix}"
                    task_name = f"learning_model_{model_name}_seed_{seed}"
                    vector_file = os.path.join(
                        self.output_path, "learningSamples",
                        f"Samples_region_{model_name}_seed{seed}_learn.sqlite")
                    output_model = os.path.join(
                        self.output_path, "model",
                        f"model_{model_name}_seed_{seed}.txt")
                    if suffix == "SAR":
                        task_name += f"_{suffix}"
                        vector_file = vector_file.replace(
                            ".sqlite", "_SAR.sqlite")
                        output_model = output_model.replace(".txt", "_SAR.txt")

                    task_params = self.get_learning_i2_task_parameters(
                        vector_file, output_model, model_name, seed)

                    task = self.i2_task(task_name=task_name,
                                        log_dir=self.log_step_dir,
                                        execution_mode=self.execution_mode,
                                        task_parameters=task_params,
                                        task_resources=self.resources)
                    self.add_task_to_i2_processing_graph(
                        task,
                        task_group="region_tasks",
                        task_sub_group=f"{target_model}",
                        task_dep_group="region_tasks"
                        if self.enable_autoContext is False else
                        "tile_tasks_model",
                        task_dep_sub_group=[target_model]
                        if self.enable_autoContext is False else [
                            f"{tile}_{model_name}_seed_{seed}_{suffix}"
                            for tile in model_meta["tiles"]
                        ])

    def get_learning_i2_task_parameters(self, vector_file: str,
                                        output_model: str, model_name: str,
                                        seed: int) -> Dict:
        """
        """
        task_params = {}
        if self.use_scikitlearn is True and self.enable_autoContext is True:
            raise ValueError(
                "scikit-learn and autoContext modes are not compatibles")
        if self.use_scikitlearn is True and self.enable_autoContext is False:
            task_params = {
                'f': learn_scikitlearn_model,
                "samples_file": vector_file,
                "output_model": output_model,
                "data_field": self.data_field,
                "sk_model_name": self.sk_model_name,
                "apply_standardization": self.apply_standardization,
                "cross_valid_params": self.cross_valid_params,
                "cross_val_grouped": self.cross_val_grouped,
                "folds_number": self.folds_number,
                "available_ram": self.available_ram,
                "sk_model_params": self.sk_model_parameters
            }

        elif self.enable_autoContext is True:
            model_tiles = self.spatial_models_distribution[model_name]["tiles"]
            suffix_learning_samples = ".sqlite"
            if "_SAR.sqlite" in vector_file:
                suffix_learning_samples = "_SAR.sqlite"
            list_learning_samples = [
                os.path.join(
                    self.output_path, "learningSamples",
                    f'{tile}_region_{model_name}_seed{seed}_Samples_learn{suffix_learning_samples}'
                ) for tile in model_tiles
            ]
            list_super_pixel_samples = [
                os.path.join(
                    self.output_path, "learningSamples",
                    f'{tile}_region_{model_name}_seed{seed}_Samples_SP.sqlite')
                for tile in model_tiles
            ]
            list_slic = [
                os.path.join(self.output_path, "features", tile, "tmp",
                             f'SLIC_{tile}.tif') for tile in model_tiles
            ]
            task_params = {
                "f": learn_autocontext_model,
                "model_name": model_name,
                "output_path": self.output_path,
                "superpix_data_field": self.superpix_data_field,
                "seed": seed,
                "list_learning_samples": list_learning_samples,
                "list_superPixel_samples": list_super_pixel_samples,
                "list_slic": list_slic,
                "data_field": self.data_field,
                "iterations": self.autoContext_iterations,
                "ram": self.available_ram,
                "working_directory": self.workingDirectory
            }
        else:
            task_params = {
                "f": learn_otb_model,
                "samples_file": vector_file,
                "output_model": output_model,
                "data_field": self.data_field,
                "classifier": self.classifier,
                "classifier_options": self.classifier_options,
                "i2_running_dir": self.output_path,
                "model_name": model_name,
                "seed": seed,
                "region_field": self.region_field,
                "ground_truth": self.ground_truth
            }
        return task_params

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Learn model")
        return description
