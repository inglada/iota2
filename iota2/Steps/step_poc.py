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
from typing import Dict

from iota2.Steps import IOTA2Step
from iota2.Cluster import get_RAM
from iota2.Common import ServiceConfigFile as SCF

from iota2.Learning.TrainingCmd import config_model
from iota2.Learning.TrainSkLearn import cast_config_cv_parameters

from iota2.Learning.launch_learning import learn_otb_model
from iota2.Learning.launch_learning import learn_scikitlearn_model
from iota2.Learning.launch_learning import learn_autocontext_model


class poc_multi_step_dep(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "training"
        super(poc_multi_step_dep, self).__init__(cfg, cfg_resources_file,
                                                 resources_block_name)
        self.execution_mode = "cluster"

        task = self.i2_task(task_name="poc_poc",
                            log_dir=self.log_step_dir,
                            execution_mode=self.execution_mode,
                            task_parameters={"f": ""},
                            task_resources=self.resources)

        self.add_task_to_i2_processing_graph(task,
                                             task_group="poc",
                                             task_sub_group="poc_task",
                                             task_dep_dico={
                                                 "tile_tasks_prepro":
                                                 ["T31TCJ"],
                                                 "tile_tasks_cm": ["T30TXN"]
                                             })

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("multi dep poc")
        return description
