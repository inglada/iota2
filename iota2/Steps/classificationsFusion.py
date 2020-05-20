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
from iota2.Classification import Fusion as FUS
from iota2.Common import ServiceConfigFile as SCF
from iota2.Common import FileUtils as fu


class classificationsFusion(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "fusion"
        super(classificationsFusion, self).__init__(cfg, cfg_resources_file,
                                                    resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.runs = SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs')
        self.execution_mode = "cluster"
        self.dempster_shafer_SAR_Opt_fusion = SCF.serviceConfigFile(
            self.cfg).getParam('argTrain', 'dempster_shafer_SAR_Opt_fusion')
        pix_type = fu.getOutputPixType(
            SCF.serviceConfigFile(self.cfg).getParam('chain',
                                                     'nomenclaturePath'))
        for model_name, model_meta in self.spatial_models_distribution_no_sub_splits.items(
        ):
            for seed in range(self.runs):
                for tile in model_meta["tiles"]:
                    classif_to_merge = [
                        os.path.join(
                            self.output_path, "classif",
                            f"Classif_{tile}_model_{model_name}f{submodel_num + 1}_seed_{seed}.tif"
                        ) for submodel_num in range(model_meta["nb_sub_model"])
                    ]

                    if self.dempster_shafer_SAR_Opt_fusion:
                        classif_to_merge = [
                            elem.replace(".tif", "_DS.tif")
                            for elem in classif_to_merge
                        ]
                    task = self.i2_task(
                        task_name=
                        f"classification_fusion_{tile}_model_{model_name}_seed_{seed}",
                        log_dir=self.log_step_dir,
                        execution_mode=self.execution_mode,
                        task_parameters={
                            "f":
                            FUS.fusion,
                            "in_classif":
                            classif_to_merge,
                            "fusion_options":
                            SCF.serviceConfigFile(self.cfg).getParam(
                                'argClassification', 'fusionOptions'),
                            "out_classif":
                            os.path.join(
                                self.output_path, "classif",
                                f"{tile}_FUSION_model_{model_name}_seed_{seed}.tif"
                            ),
                            "out_pix_type":
                            pix_type
                        },
                        task_resources=self.resources)
                    if model_meta["nb_sub_model"] > 1:
                        task_dep_group = "tile_tasks_model_mode"
                        task_dep_sub_group = [
                            f"{tile}_{model_name}f{sub_model+1}_{seed}_usually"
                            for sub_model in range(model_meta["nb_sub_model"])
                        ]

                        if self.dempster_shafer_SAR_Opt_fusion:
                            task_dep_group = "tile_tasks_model"
                            task_dep_sub_group = [
                                f"{tile}_model_{model_name}f{sub_model+1}_seed_{seed}"
                                for sub_model in range(
                                    model_meta["nb_sub_model"])
                            ]
                        self.add_task_to_i2_processing_graph(
                            task,
                            task_group="tile_tasks_model",
                            task_sub_group=f"{tile}_{model_name}_{seed}",
                            task_dep_dico={task_dep_group: task_dep_sub_group})

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Fusion of classifications")
        return description
