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
from iota2.Validation import ConfusionFusion


class confusionsMerge(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "confusionMatrixFusion"
        super(confusionsMerge, self).__init__(cfg, cfg_resources_file,
                                              resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.data_field = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'dataField')
        self.ground_truth = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'groundTruth')
        self.runs = SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs')
        self.execution_mode = "cluster"

        task = self.i2_task(task_name=f"merge_confusions",
                            log_dir=self.log_step_dir,
                            execution_mode=self.execution_mode,
                            task_parameters={
                                "f":
                                ConfusionFusion.confusion_fusion,
                                "input_vector":
                                self.ground_truth,
                                "data_field":
                                self.data_field,
                                "csv_out":
                                os.path.join(self.output_path, "final", "TMP"),
                                "txt_out":
                                os.path.join(self.output_path, "final", "TMP"),
                                "csv_path":
                                os.path.join(self.output_path, "final", "TMP"),
                                "runs":
                                SCF.serviceConfigFile(self.cfg).getParam(
                                    'chain', 'runs'),
                                "crop_mix":
                                SCF.serviceConfigFile(self.cfg).getParam(
                                    'argTrain', 'cropMix'),
                                "annual_crop":
                                SCF.serviceConfigFile(self.cfg).getParam(
                                    'argTrain', 'annualCrop'),
                                "annual_crop_label_replacement":
                                (SCF.serviceConfigFile(self.cfg).getParam(
                                    'argTrain',
                                    'ACropLabelReplacement').data)[0]
                            },
                            task_resources=self.resources)
        self.add_task_to_i2_processing_graph(
            task,
            task_group="confusion_merge",
            task_sub_group="confusion_merge",
            task_dep_dico={
                "tile_tasks_seed": [
                    f"{tile}_{seed}" for seed in range(self.runs)
                    for tile in self.tiles
                ]
            })

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Merge all confusions")
        return description
