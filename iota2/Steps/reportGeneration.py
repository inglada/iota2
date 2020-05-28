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
from iota2.Validation import GenResults as GR


class reportGeneration(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "reportGen"
        super(reportGeneration, self).__init__(cfg, cfg_resources_file,
                                               resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.nomenclature = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'nomenclaturePath')

        self.execution_mode = "cluster"

        task = self.i2_task(task_name=f"final_report",
                            log_dir=self.log_step_dir,
                            execution_mode=self.execution_mode,
                            task_parameters={
                                "f": GR.genResults,
                                "pathRes":
                                os.path.join(self.output_path, "final"),
                                "pathNom": self.nomenclature
                            },
                            task_resources=self.resources)
        self.add_task_to_i2_processing_graph(
            task,
            task_group="final_report",
            task_sub_group="final_report",
            task_dep_dico={"confusion_merge": ["confusion_merge"]})

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Generate final report")
        return description
