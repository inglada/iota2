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

from Steps import IOTA2Step
from Common import ServiceConfigFile as SCF


class mergeSeedClassifications(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "merge_final_classifications"
        super(mergeSeedClassifications, self).__init__(cfg, cfg_resources_file, resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath')
        self.data_field = SCF.serviceConfigFile(self.cfg).getParam('chain', 'dataField')
        self.nomenclature = SCF.serviceConfigFile(self.cfg).getParam('chain', 'nomenclaturePath')
        self.color_table = SCF.serviceConfigFile(self.cfg).getParam('chain', 'colorTable')
        self.runs = SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs')
        self.undecidedlabel = SCF.serviceConfigFile(self.cfg).getParam('chain', 'merge_final_classifications_undecidedlabel')
        self.dempstershafer_mob = SCF.serviceConfigFile(self.cfg).getParam('chain', 'dempstershafer_mob')
        self.keep_runs_results = SCF.serviceConfigFile(self.cfg).getParam('chain', 'keep_runs_results')
        self.enableCrossValidation = SCF.serviceConfigFile(self.cfg).getParam('chain', 'enableCrossValidation')
        self.ground_truth = SCF.serviceConfigFile(cfg).getParam('chain', 'groundTruth')
        self.fusionClaAllSamplesVal = SCF.serviceConfigFile(cfg).getParam('chain', 'fusionOfClassificationAllSamplesValidation')
        self.merge_final_classifications_method = SCF.serviceConfigFile(cfg).getParam('chain', 'merge_final_classifications_method')

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        return "Merge final classifications"

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        return [self.output_path]

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from Common import FileUtils as fut
        from Classification import MergeFinalClassifications as mergeCl

        pixType = fut.getOutputPixType(self.nomenclature)
        validation_shape = None
        if self.fusionClaAllSamplesVal is True:
            validation_shape = self.ground_truth
        return lambda x: mergeCl.mergeFinalClassifications(
            x,
            self.data_field,
            self.nomenclature,
            self.color_table,
            self.runs,
            pixType,
            self.merge_final_classifications_method,
            self.undecidedlabel,
            self.dempstershafer_mob,
            self.keep_runs_results,
            self.enableCrossValidation,
            validation_shape,
            self.workingDirectory,
        )

    def step_outputs(self):
        """
        """
        pass
