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


class SAROptFusion(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "SAROptFusion"
        super(SAROptFusion, self).__init__(cfg, cfg_resources_file, resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath')
        self.enable_proba_map = SCF.serviceConfigFile(self.cfg).getParam('argClassification',
                                                                         'enable_probability_map')
        
    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("SAR and optical post-classifications fusion")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from Classification import Fusion as FUS
        return FUS.dempster_shafer_fusion_parameters(self.output_path)

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from Classification import Fusion as FUS
        step_function = lambda x: FUS.dempster_shafer_fusion(self.output_path,
                                                             x,
                                                             proba_map_flag=self.enable_proba_map,
                                                             workingDirectory=self.workingDirectory)
        return step_function

    def step_outputs(self):
        """
        """
        pass
