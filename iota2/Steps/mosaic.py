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

from Steps import IOTA2Step
from Common import ServiceConfigFile as SCF


class mosaic(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "classifShaping"
        super(
            mosaic,
            self).__init__(
            cfg,
            cfg_resources_file,
            resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(
            self.cfg).getParam(
            'chain', 'outputPath')
        self.runs = SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs')
        self.enable_cross_validation = SCF.serviceConfigFile(
            self.cfg).getParam('chain', 'enableCrossValidation')
        if self.enable_cross_validation:
            self.runs = self.runs - 1
        self.fieldEnv = "FID"
        self.color_table = SCF.serviceConfigFile(
            self.cfg).getParam(
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
        from Validation import ClassificationShaping as CS

        def step_function(x): return CS.ClassificationShaping(x,
                                                              os.path.join(
                                                                  self.output_path, "envelope"),
                                                              os.path.join(
                                                                  self.output_path, "features"),
                                                              self.fieldEnv,
                                                              self.runs,
                                                              os.path.join(
                                                                  self.output_path, "final"),
                                                              self.workingDirectory,
                                                              self.cfg,
                                                              self.color_table)
        return step_function

    def step_outputs(self):
        """
        """
        pass
