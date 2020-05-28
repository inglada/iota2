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
from iota2.Classification import MergeFinalClassifications as mergeCl
from iota2.Common import FileUtils as fut


class mergeSeedClassifications(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "merge_final_classifications"
        super(mergeSeedClassifications, self).__init__(cfg, cfg_resources_file,
                                                       resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.data_field = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'dataField')
        self.nomenclature = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'nomenclaturePath')
        self.color_table = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'colorTable')
        self.runs = SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs')
        self.undecidedlabel = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'merge_final_classifications_undecidedlabel')
        self.dempstershafer_mob = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'dempstershafer_mob')
        self.keep_runs_results = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'keep_runs_results')
        self.enableCrossValidation = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'enableCrossValidation')
        self.ground_truth = SCF.serviceConfigFile(cfg).getParam(
            'chain', 'groundTruth')
        self.fusionClaAllSamplesVal = SCF.serviceConfigFile(cfg).getParam(
            'chain', 'fusionOfClassificationAllSamplesValidation')
        self.merge_final_classifications_method = SCF.serviceConfigFile(
            cfg).getParam('chain', 'merge_final_classifications_method')

        self.execution_mode = "cluster"
        pixType = fut.getOutputPixType(self.nomenclature)
        validation_shape = None
        if self.fusionClaAllSamplesVal is True:
            validation_shape = self.ground_truth

        task = self.i2_task(task_name=f"final_report",
                            log_dir=self.log_step_dir,
                            execution_mode=self.execution_mode,
                            task_parameters={
                                "f": mergeCl.mergeFinalClassifications,
                                "iota2_dir": self.output_path,
                                "dataField": self.data_field,
                                "nom_path": self.nomenclature,
                                "colorFile": self.color_table,
                                "runs": self.runs,
                                "pixType": pixType,
                                "method":
                                self.merge_final_classifications_method,
                                "undecidedlabel": self.undecidedlabel,
                                "dempstershafer_mob": self.dempstershafer_mob,
                                "keep_runs_results": self.keep_runs_results,
                                "enableCrossValidation":
                                self.enableCrossValidation,
                                "validationShape": validation_shape,
                                "workingDirectory": self.workingDirectory
                            },
                            task_resources=self.resources)
        self.add_task_to_i2_processing_graph(
            task,
            task_group="merge_final_classifications",
            task_sub_group="merge_final_classifications",
            task_dep_dico={"final_report": ["final_report"]})

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Merge final classifications")
        return description
