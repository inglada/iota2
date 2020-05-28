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
from iota2.Validation import GenConfusionMatrix as GCM
from iota2.Cluster import get_RAM


class confusionCmd(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "gen_confusionMatrix"
        super(confusionCmd, self).__init__(cfg, cfg_resources_file,
                                           resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.runs = SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs')
        self.data_field = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'dataField')
        self.execution_mode = "cluster"
        for seed in range(self.runs):
            for tile in self.tiles:
                task = self.i2_task(
                    task_name=f"confusion_{tile}_seed_{seed}",
                    log_dir=self.log_step_dir,
                    execution_mode=self.execution_mode,
                    task_parameters={
                        "f":
                        GCM.gen_conf_matrix,
                        "in_classif":
                        os.path.join(self.output_path, "final",
                                     f"Classif_Seed_{seed}.tif"),
                        "out_csv":
                        os.path.join(self.output_path, "final", "TMP",
                                     f"{tile}_seed_{seed}.csv"),
                        "data_field":
                        self.data_field,
                        "ref_vector":
                        os.path.join(self.output_path, "dataAppVal",
                                     f"{tile}_seed_{seed}_val.sqlite"),
                        "ram":
                        1024.0 * get_RAM(self.resources["ram"])
                    },
                    task_resources=self.resources)
                self.add_task_to_i2_processing_graph(
                    task,
                    task_group="tile_tasks_seed",
                    task_sub_group=f"{tile}_{seed}",
                    task_dep_dico={"mosaic": ["mosaic"]})

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("generate confusion matrix by tiles")
        return description
