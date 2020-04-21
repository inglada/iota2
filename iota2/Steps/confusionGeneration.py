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


class confusionGeneration(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "confusionMatrix"
        super(confusionGeneration, self).__init__(cfg, cfg_resources_file,
                                                  resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Generate confusions matrix by tiles")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from Common import FileUtils as fut
        return fut.getCmd(
            os.path.join(self.output_path, "cmd", "confusion",
                         "confusion.txt"))

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
