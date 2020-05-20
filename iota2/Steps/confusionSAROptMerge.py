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
from iota2.Validation import ConfusionFusion as confFus


class confusionSAROptMerge(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "SAROptConfusionMatrixFusion"
        super(confusionSAROptMerge, self).__init__(cfg, cfg_resources_file,
                                                   resources_block_name)

        # step variables
        self.execution_mode = "cluster"
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.data_field = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'dataField')
        self.runs = SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs')

        self.suffix_list = ["usually"]
        if SCF.serviceConfigFile(self.cfg).getParam(
                'argTrain', 'dempster_shafer_SAR_Opt_fusion') is True:
            self.suffix_list.append("SAR")
        for suffix in self.suffix_list:
            for model_name, model_meta in self.spatial_models_distribution.items(
            ):
                for seed in range(self.runs):
                    csv_files_to_merge = self.get_csv_files(
                        suffix, model_name, model_meta["tiles"], seed)
                    task_name_fusion = f"confusion_fusion_model_{model_name}_seed_{seed}"
                    if suffix == "SAR":
                        task_name_fusion = f"{task_name_fusion}_SAR"
                    task = self.i2_task(task_name=task_name_fusion,
                                        log_dir=self.log_step_dir,
                                        execution_mode=self.execution_mode,
                                        task_parameters={
                                            "f":
                                            confFus.confusion_models_merge,
                                            "csv_list": csv_files_to_merge
                                        },
                                        task_resources=self.resources)
                    self.add_task_to_i2_processing_graph(
                        task,
                        task_group="region_tasks",
                        task_sub_group=
                        f"model_{model_name}_seed_{seed}_{suffix}",
                        task_dep_dico={
                            "tile_tasks_model_mode": [
                                f"{tile}_{model_name}_{seed}_{suffix}"
                                for tile in model_meta["tiles"]
                            ]
                        })

    def get_csv_files(self, suffix, model_name, tiles, seed):
        csv_files = []
        for tile in tiles:
            if suffix == "SAR":
                csv_files.append(
                    os.path.join(
                        self.output_path, "dataAppVal", "bymodels",
                        f"{tile}_region_{model_name}_seed_{seed}_samples_val_SAR.csv"
                    ))
            else:
                csv_files.append(
                    os.path.join(
                        self.output_path, "dataAppVal", "bymodels",
                        f"{tile}_region_{model_name}_seed_{seed}_samples_val.csv"
                    ))
        return csv_files

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Fusion of confusion matrix")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from iota2.Validation import ConfusionFusion as confFus
        return confFus.confusion_models_merge_parameters(self.output_path)

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from iota2.Validation import ConfusionFusion as confFus
        step_function = lambda x: confFus.confusion_models_merge(x)
        return step_function

    def step_outputs(self):
        """
        """
        pass
