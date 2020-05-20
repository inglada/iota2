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
from iota2.Cluster import get_RAM
from iota2.Validation import GenConfusionMatrix as GCM


class confusionSAROpt(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "SAROptConfusionMatrix"
        super(confusionSAROpt, self).__init__(cfg, cfg_resources_file,
                                              resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.data_field = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'dataField')
        self.sar_opt_conf_ram = 1024.0 * get_RAM(self.resources["ram"])
        self.execution_mode = "cluster"
        self.runs = SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs')

        self.suffix_list = ["usually"]
        if SCF.serviceConfigFile(self.cfg).getParam(
                'argTrain', 'dempster_shafer_SAR_Opt_fusion') is True:
            self.suffix_list.append("SAR")

        for suffix in self.suffix_list:
            for model_name, model_meta in self.spatial_models_distribution.items(
            ):
                for seed in range(self.runs):
                    for tile in model_meta["tiles"]:
                        task_name = f"confusion_{tile}_model_{model_name}_seed_{seed}"
                        ref_vector = os.path.join(
                            self.output_path, "dataAppVal", "bymodels",
                            f"{tile}_region_{model_name}_seed_{seed}_samples_val.shp"
                        )
                        classification = os.path.join(
                            self.output_path, "classif",
                            f"Classif_{tile}_model_{model_name}_seed_{seed}.tif"
                        )
                        if suffix == "SAR":
                            task_name = f"{task_name}_SAR"
                            classification = classification.replace(
                                ".tif", "_SAR.tif")
                        task = self.i2_task(task_name=task_name,
                                            log_dir=self.log_step_dir,
                                            execution_mode=self.execution_mode,
                                            task_parameters={
                                                "f":
                                                GCM.confusion_sar_optical,
                                                "ref_vector":
                                                (ref_vector, classification),
                                                "data_field":
                                                self.data_field,
                                                "ram":
                                                self.sar_opt_conf_ram
                                            },
                                            task_resources=self.resources)
                        self.add_task_to_i2_processing_graph(
                            task,
                            task_group="tile_tasks_model_mode",
                            task_sub_group=
                            f"{tile}_{model_name}_{seed}_{suffix}",
                            task_dep_dico={
                                "tile_tasks_model_mode":
                                [f"{tile}_{model_name}_{seed}_{suffix}"]
                            })

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = (
            "Evaluate SAR vs optical classification's performance by tiles and models"
        )
        return description
