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
from iota2.Common import FileUtils as fut


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

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        return "Manage indecisions in classification's fusion"

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from iota2.Common import FileUtils as fut
        return fut.FileSearch_AND(os.path.join(self.output_path, "classif"),
                                  True, "_FUSION_")

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from iota2.Classification import undecision_management as UM
        return lambda x: UM.undecision_management(
            self.output_path, x, self.field_region, self.path_to_img, self.
            shape_region, self.no_label, self.working_directory,
            list(self.features), self.user_feat_path, self.pixtype, self.
            region_vec, self.patterns, self.sar_opt_fusion)

    def step_outputs(self):
        """
        """
        pass
