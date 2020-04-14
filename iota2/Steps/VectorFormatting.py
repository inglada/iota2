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
from iota2.Sampling import VectorFormatting as VF


class VectorFormatting(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "samplesFormatting"
        super(VectorFormatting, self).__init__(cfg, cfg_resources_file,
                                               resources_block_name)

        # step variables
        self.working_directory = workingDirectory
        self.execution_mode = "cluster"
        self.step_tasks = []
        # parameters
        output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        ground_truth_vec = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'groundTruth')
        data_field = (SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'dataField')).lower()

        cloud_threshold = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'cloud_threshold')
        ratio = SCF.serviceConfigFile(self.cfg).getParam('chain', 'ratio')
        random_seed = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'random_seed')
        enable_cross_validation = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'enableCrossValidation')
        enable_split_ground_truth = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'splitGroundTruth')
        fusion_merge_all_validation = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'fusionOfClassificationAllSamplesValidation')
        runs = SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs')
        epsg = int(
            (SCF.serviceConfigFile(self.cfg).getParam('GlobChain',
                                                      'proj')).split(":")[-1])
        region_vec = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'regionPath')
        region_field = (SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'regionField')).lower()
        if not region_vec:
            region_vec = os.path.join(
                SCF.serviceConfigFile(self.cfg).getParam(
                    "chain", "outputPath"), "MyRegion.shp")

        merge_final_classifications = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'merge_final_classifications')
        merge_final_classifications_ratio = SCF.serviceConfigFile(
            self.cfg).getParam('chain', 'merge_final_classifications_ratio')

        for tile in self.tiles:
            task = self.i2_task(
                task_name=f"vector_form_{tile}",
                log_dir=self.log_step_dir,
                execution_mode=self.execution_mode,
                task_parameters={
                    "f": VF.vector_formatting,
                    "tile_name": tile,
                    "output_path": output_path,
                    "ground_truth_vec": ground_truth_vec,
                    "data_field": data_field,
                    "cloud_threshold": cloud_threshold,
                    "ratio": ratio,
                    "random_seed": random_seed,
                    "enable_cross_validation": enable_cross_validation,
                    "enable_split_ground_truth": enable_split_ground_truth,
                    "fusion_merge_all_validation": fusion_merge_all_validation,
                    "runs": runs,
                    "epsg": epsg,
                    "region_field": region_field,
                    "merge_final_classifications": merge_final_classifications,
                    "merge_final_classifications_ratio":
                    merge_final_classifications_ratio,
                    "region_vec": region_vec,
                    "working_directory": self.working_directory
                },
                task_resources=self.resources)
            task_in_graph = self.add_task_to_i2_processing_graph(
                task,
                task_group="tile_tasks",
                task_sub_group=tile,
                task_dep_group="vector",
                task_dep_sub_group=["vector"])
            self.step_tasks.append(task_in_graph)

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Prepare samples")
        return description
