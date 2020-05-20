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
from iota2.Validation import ClassificationShaping as CS


class mosaic(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "classifShaping"
        super(mosaic, self).__init__(cfg, cfg_resources_file,
                                     resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.runs = SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs')
        self.enable_cross_validation = SCF.serviceConfigFile(
            self.cfg).getParam('chain', 'enableCrossValidation')
        if self.enable_cross_validation:
            self.runs = self.runs - 1
        self.fieldEnv = "FID"
        self.color_table = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'colorTable')
        self.execution_mode = "cluster"
        ds_sar_opt = SCF.serviceConfigFile(cfg).getParam(
            'argTrain', 'dempster_shafer_SAR_Opt_fusion')
        classif_mode = SCF.serviceConfigFile(cfg).getParam(
            'argClassification', 'classifMode')
        shape_region = SCF.serviceConfigFile(cfg).getParam(
            'chain', 'regionPath')
        task = self.i2_task(task_name=f"mosaic",
                            log_dir=self.log_step_dir,
                            execution_mode=self.execution_mode,
                            task_parameters={
                                "f":
                                CS.classification_shaping,
                                "path_classif":
                                os.path.join(self.output_path, "classif"),
                                "runs":
                                self.runs,
                                "path_out":
                                os.path.join(self.output_path, "final"),
                                "path_wd":
                                self.workingDirectory,
                                "classif_mode":
                                SCF.serviceConfigFile(self.cfg).getParam(
                                    "argClassification", "classifMode"),
                                "path_test":
                                self.output_path,
                                "ds_sar_opt":
                                ds_sar_opt,
                                "proj":
                                int(
                                    SCF.serviceConfigFile(self.cfg).getParam(
                                        'GlobChain', 'proj').split(":")[-1]),
                                "nomenclature_path":
                                SCF.serviceConfigFile(self.cfg).getParam(
                                    "chain", "nomenclaturePath"),
                                "output_statistics":
                                SCF.serviceConfigFile(self.cfg).getParam(
                                    'chain', 'outputStatistics'),
                                "spatial_resolution":
                                SCF.serviceConfigFile(self.cfg).getParam(
                                    "chain", "spatialResolution"),
                                "proba_map_flag":
                                SCF.serviceConfigFile(self.cfg).getParam(
                                    "argClassification",
                                    "enable_probability_map"),
                                "region_shape":
                                SCF.serviceConfigFile(self.cfg).getParam(
                                    'chain', 'regionPath'),
                                "color_path":
                                self.color_table
                            },
                            task_resources=self.resources)

        dependencies = {}
        for model_name, model_meta in self.spatial_models_distribution_no_sub_splits.items(
        ):
            for seed in range(self.runs):
                model_subdivisions = model_meta["nb_sub_model"]
                dep_group = "tile_tasks_model"
                if model_subdivisions == 1:
                    dep_group = "tile_tasks_model_mode"
                if ds_sar_opt:
                    dep_group = "tile_tasks_model"
                if not dep_group in dependencies:
                    dependencies[dep_group] = []
                for tile in model_meta["tiles"]:
                    if dep_group == "tile_tasks_model_mode":
                        dependencies[dep_group].append(
                            f"{tile}_{model_name}_{seed}_usually")
                    else:
                        dependencies[dep_group].append(
                            f"{tile}_{model_name}_{seed}")
        self.add_task_to_i2_processing_graph(task,
                                             task_group="mosaic",
                                             task_sub_group=f"mosaic",
                                             task_dep_dico=dependencies)

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Mosaic")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        return [os.path.join(self.output_path, "classif")]

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from iota2.Validation import ClassificationShaping as CS
        region_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'regionPath')
        classif_mode = SCF.serviceConfigFile(self.cfg).getParam(
            "argClassification", "classifMode")
        ds_fusion_sar_opt = SCF.serviceConfigFile(self.cfg).getParam(
            "argTrain", "dempster_shafer_SAR_Opt_fusion")
        proj = int(
            SCF.serviceConfigFile(self.cfg).getParam('GlobChain',
                                                     'proj').split(":")[-1])
        nomenclature_path = SCF.serviceConfigFile(self.cfg).getParam(
            "chain", "nomenclaturePath")
        enable_proba_map = SCF.serviceConfigFile(self.cfg).getParam(
            "argClassification", "enable_probability_map")
        spatial_res = SCF.serviceConfigFile(self.cfg).getParam(
            "chain", "spatialResolution")
        output_statistics = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputStatistics')
        step_function = lambda x: CS.classification_shaping(
            x, self.runs, os.path.join(self.output_path, "final"), self.
            workingDirectory, classif_mode, self.output_path,
            ds_fusion_sar_opt, proj, nomenclature_path, output_statistics,
            spatial_res, enable_proba_map, region_path, self.color_table)
        return step_function

    def step_outputs(self):
        """
        """
        pass
