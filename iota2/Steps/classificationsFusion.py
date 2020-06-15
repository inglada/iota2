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


class classificationsFusion(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "fusion"
        super(classificationsFusion, self).__init__(cfg, cfg_resources_file,
                                                    resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        return "Fusion of classifications"

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from iota2.Classification import Fusion as FUS
        return FUS.fusion(
            os.path.join(self.output_path, "classif"),
            SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs'),
            SCF.serviceConfigFile(self.cfg).getParam('chain',
                                                     'listTile').split(" "),
            SCF.serviceConfigFile(self.cfg).getParam('argClassification',
                                                     'fusionOptions'),
            SCF.serviceConfigFile(self.cfg).getParam('chain',
                                                     'nomenclaturePath'),
            SCF.serviceConfigFile(self.cfg).getParam('chain', 'regionPath'),
            SCF.serviceConfigFile(self.cfg).getParam(
                'argTrain', 'dempster_shafer_SAR_Opt_fusion'), None)

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from iota2.MPI import launch_tasks as tLauncher
        bash_launcher_function = tLauncher.launchBashCmd
        return lambda x: bash_launcher_function(x)

    def step_outputs(self):
        """
        """
        pass
