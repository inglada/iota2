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


class copySamples(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "samplesManagement"
        super(copySamples, self).__init__(cfg, cfg_resources_file,
                                          resources_block_name)
        self.execution_mode = "cluster"
        self.working_directory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.dataField = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'dataField')
        self.sampleManagement = SCF.serviceConfigFile(self.cfg).getParam(
            'argTrain', 'sampleManagement')
        nb_runs = SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs')
        self.suffix_list = ["usually"]
        if SCF.serviceConfigFile(self.cfg).getParam(
                'argTrain', 'dempster_shafer_SAR_Opt_fusion') is True:
            self.suffix_list.append("SAR")

        #inputs
        models_by_seeds = {}
        for seed in range(nb_runs):
            models_by_seeds[seed] = {"dep": [], "files": []}
            for suffix in self.suffix_list:
                for model_name, _ in self.spatial_models_distribution.items():
                    models_by_seeds[seed]["dep"].append(
                        f"model_{model_name}_seed_{seed}_{suffix}")
                    if suffix == "SAR":
                        models_by_seeds[seed]["files"].append(
                            os.path.join(
                                self.output_path, "learningSamples",
                                f"Samples_region_{model_name}_seed{seed}_learn_SAR.sqlite"
                            ))
                    else:
                        models_by_seeds[seed]["files"].append(
                            os.path.join(
                                self.output_path, "learningSamples",
                                f"Samples_region_{model_name}_seed{seed}_learn.sqlite"
                            ))
        for seed in range(nb_runs):
            task = self.i2_task(task_name=f"transfert_samples_seed_{seed}",
                                log_dir=self.log_step_dir,
                                execution_mode=self.execution_mode,
                                task_parameters={
                                    "f":
                                    DataAugmentation.DataAugmentationByCopy,
                                    "dataField": self.dataField.lower(),
                                    "csv_path": self.sampleManagement,
                                    "samplesSet":
                                    models_by_seeds[seed]["files"],
                                    "workingDirectory": self.working_directory
                                },
                                task_resources=self.resources)
            self.add_task_to_i2_processing_graph(
                task,
                task_group="seed_tasks",
                task_sub_group=seed,
                task_dep_dico={"region_tasks": models_by_seeds[seed]["dep"]})

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Copy samples between models according to user request")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from Sampling import DataAugmentation
        return DataAugmentation.GetDataAugmentationByCopyParameters(
            os.path.join(self.output_path, "learningSamples"))

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from Sampling import DataAugmentation
        step_function = lambda x: DataAugmentation.DataAugmentationByCopy(
            self.dataField.lower(), self.sampleManagement, x, self.
            workingDirectory)
        return step_function

    def step_outputs(self):
        """
        """
        pass
