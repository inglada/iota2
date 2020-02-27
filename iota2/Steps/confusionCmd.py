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

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Prepare confusion matrix commands")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        return [os.path.join(self.output_path, "final")]

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from iota2.Validation import GenConfusionMatrix as GCM
        step_function = lambda x: GCM.gen_conf_matrix(
            x, os.path.join(self.output_path, "dataAppVal"), self.runs, self.
            data_field, os.path.join(self.output_path, "cmd", "confusion"
                                     ), self.workingDirectory,
            SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath'),
            SCF.serviceConfigFile(self.cfg).getParam('chain',
                                                     'spatialResolution'),
            SCF.serviceConfigFile(self.cfg).getParam('chain', 'listTile'),
            SCF.serviceConfigFile(self.cfg).getParam('chain',
                                                     'enableCrossValidation'))
        return step_function

    def step_outputs(self):
        """
        """
        pass
