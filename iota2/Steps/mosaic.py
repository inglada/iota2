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

    def step_description(self):
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
        step_function = lambda x: CS.ClassificationShaping(
            x, self.runs, os.path.join(self.output_path, "final"), self.
            workingDirectory, classif_mode, self.output_path,
            ds_fusion_sar_opt, proj, nomenclature_path, output_statistics,
            spatial_res, enable_proba_map, region_path, self.color_table)
        return step_function

    def step_outputs(self):
        """
        """
        pass
