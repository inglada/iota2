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
from iota2.Common import FileUtils as fut
from iota2.Classification import undecision_management as UM
from iota2.Common import ServiceConfigFile as SCF


class fusionsIndecisions(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, working_directory=None):
        # heritage init

        resources_block_name = "noData"
        super(fusionsIndecisions, self).__init__(cfg, cfg_resources_file,
                                                 resources_block_name)

        # step variables
        self.working_directory = working_directory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.field_region = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'regionField')
        self.shape_region = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'regionPath')
        self.runs = SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs')
        self.no_label = SCF.serviceConfigFile(self.cfg).getParam(
            'argClassification', 'noLabelManagement')
        self.features = SCF.serviceConfigFile(self.cfg).getParam(
            "GlobChain", "features")
        self.user_feat_path = SCF.serviceConfigFile(self.cfg).getParam(
            "chain", "userFeatPath")
        self.pixtype = fut.getOutputPixType(
            SCF.serviceConfigFile(self.cfg).getParam('chain',
                                                     'nomenclaturePath'))
        self.region_vec = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'regionPath')
        self.patterns = SCF.serviceConfigFile(self.cfg).getParam(
            "userFeat", "patterns")
        self.sar_opt_fusion = SCF.serviceConfigFile(self.cfg).getParam(
            'argTrain', 'dempster_shafer_SAR_Opt_fusion')
        self.path_to_img = os.path.join(self.output_path, "features")
        self.execution_mode = "cluster"

        for model_name, model_meta in self.spatial_models_distribution_no_sub_splits.items(
        ):
            for seed in range(self.runs):
                for tile in model_meta["tiles"]:
                    fusion_img = os.path.join(
                        self.output_path, "classif",
                        f"{tile}_FUSION_model_{model_name}_seed_{seed}.tif")
                    task = self.i2_task(
                        task_name=
                        f"manage_undecision_{tile}_model_{model_name}_seed_{seed}",
                        log_dir=self.log_step_dir,
                        execution_mode=self.execution_mode,
                        task_parameters={
                            "f": UM.undecision_management,
                            "path_test": self.output_path,
                            "path_fusion": fusion_img,
                            "field_region": self.field_region,
                            "path_to_img": self.path_to_img,
                            "path_to_region": self.shape_region,
                            "no_label_management": self.no_label,
                            "path_wd": self.working_directory,
                            "list_indices": list(self.features),
                            "user_feat_path": self.user_feat_path,
                            "pix_type": self.pixtype,
                            "region_vec": self.region_vec,
                            "user_feat_pattern": self.patterns,
                            "ds_sar_opt": self.sar_opt_fusion
                        },
                        task_resources=self.resources)
                    if model_meta["nb_sub_model"] > 1:
                        self.add_task_to_i2_processing_graph(
                            task,
                            task_group="tile_tasks_model",
                            task_sub_group=f"{tile}_{model_name}_{seed}",
                            task_dep_dico={
                                "tile_tasks_model":
                                [f"{tile}_{model_name}_{seed}"]
                            })

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Manage indecisions in classification's fusion")
        return description
