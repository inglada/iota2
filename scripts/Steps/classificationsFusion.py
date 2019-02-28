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


class classificationsFusion(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "fusion"
        super(classificationsFusion, self).__init__(cfg, cfg_resources_file, resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath')
        
    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Fusion of classifications")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from Classification import Fusion as FUS
        return FUS.fusion(os.path.join(self.output_path, "classif"), self.cfg, None)

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from MPI import launch_tasks as tLauncher
        bashLauncherFunction = tLauncher.launchBashCmd
        step_function = lambda x: bashLauncherFunction(x)
        return step_function

    def step_outputs(self):
        """
        """
        pass
