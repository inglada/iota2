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
from iota2.Classification import Fusion as FUS


class SAROptFusion(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "SAROptFusion"
        super(SAROptFusion, self).__init__(cfg, cfg_resources_file,
                                           resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.enable_proba_map = SCF.serviceConfigFile(self.cfg).getParam(
            'argClassification', 'enable_probability_map')
        self.runs = SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs')
        self.execution_mode = "cluster"

        for model_name, model_meta in self.spatial_models_distribution.items():
            for seed in range(self.runs):
                for tile in model_meta["tiles"]:
                    task = self.i2_task(
                        task_name=
                        f"fusion_Optical_SAR_{tile}_model_{model_name}_seed_{seed}",
                        log_dir=self.log_step_dir,
                        execution_mode=self.execution_mode,
                        task_parameters={
                            "f": FUS.dempster_shafer_fusion,
                            "iota2_dir": self.output_path,
                            "fusion_dic": {
                                "sar_classif":
                                os.path.join(
                                    self.output_path, "classif",
                                    f"Classif_{tile}_model_{model_name}_seed_{seed}_SAR.tif"
                                ),
                                "opt_classif":
                                os.path.join(
                                    self.output_path, "classif",
                                    f"Classif_{tile}_model_{model_name}_seed_{seed}.tif"
                                ),
                                "sar_model":
                                os.path.join(
                                    self.output_path, "dataAppVal", "bymodels",
                                    f"model_{model_name}_seed_{seed}_SAR.csv"),
                                "opt_model":
                                os.path.join(
                                    self.output_path, "dataAppVal", "bymodels",
                                    f"model_{model_name}_seed_{seed}.csv")
                            },
                            "proba_map_flag": self.enable_proba_map
                        },
                        task_resources=self.resources)
                    self.add_task_to_i2_processing_graph(
                        task,
                        task_group="tile_tasks_model",
                        task_sub_group=f"{tile}_{model_name}_{seed}",
                        task_dep_dico={
                            "region_tasks": [
                                f"model_{model_name}_seed_{seed}_usually",
                                f"model_{model_name}_seed_{seed}_SAR"
                            ]
                        })

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("SAR and optical post-classifications fusion")
        return description
