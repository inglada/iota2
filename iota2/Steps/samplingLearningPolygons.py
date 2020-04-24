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

from iota2.Steps import IOTA2Step
from iota2.Common import ServiceConfigFile as SCF
from iota2.Sampling import SamplesSelection


class samplingLearningPolygons(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "samplesSelection"
        super(samplingLearningPolygons, self).__init__(cfg, cfg_resources_file,
                                                       resources_block_name)

        # step variables
        self.working_directory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.enable_cross_validation = SCF.serviceConfigFile(
            self.cfg).getParam('chain', 'enableCrossValidation')
        self.execution_mode = "cluster"
        self.nb_runs = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'runs')
        epsg = SCF.serviceConfigFile(self.cfg).getParam('GlobChain', 'proj')
        parameters = dict(
            SCF.serviceConfigFile(self.cfg).getParam('argTrain',
                                                     'sampleSelection'))
        data_field = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'dataField').lower()
        random_seed = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'random_seed')
        for model_name, model_meta in self.spatial_models_distribution.items():
            for seed in range(self.nb_runs):
                target_model = f"model_{model_name}_seed_{seed}"
                task = self.i2_task(
                    task_name=f"s_sel_{target_model}",
                    log_dir=self.log_step_dir,
                    execution_mode=self.execution_mode,
                    task_parameters={
                        "f":
                        SamplesSelection.samples_selection,
                        "model":
                        os.path.join(
                            self.output_path, "samplesSelection",
                            f"samples_region_{model_name}_seed_{seed}.shp"),
                        "working_directory":
                        self.working_directory,
                        "output_path":
                        self.output_path,
                        "runs":
                        self.nb_runs,
                        "epsg":
                        epsg,
                        "masks_name":
                        "MaskCommunSL.tif",
                        "parameters":
                        parameters,
                        "data_field":
                        data_field,
                        "random_seed":
                        random_seed
                    },
                    task_resources=self.resources)
                self.add_task_to_i2_processing_graph(
                    task,
                    task_group="region_tasks",
                    task_sub_group=target_model,
                    task_dep_group="tile_tasks_model",
                    task_dep_sub_group=[
                        f"{tile}_{model_name}_{seed}"
                        for tile in model_meta["tiles"]
                    ])

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Select pixels in learning polygons by models")
        return description
