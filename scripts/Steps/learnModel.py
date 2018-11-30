#!/usr/bin/python
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

import IOTA2Step
from Common import ServiceConfigFile as SCF

class learnModel(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        super(learnModel, self).__init__(cfg, cfg_resources_file)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath')
        self.data_field = SCF.serviceConfigFile(self.cfg).getParam('chain', 'dataField')
        self.runs = SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs')
    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Learn model")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from Learning import TrainingCmd as TC
        return TC.launchTraining(self.cfg,
                                 self.data_field,
                                 os.path.join(self.output_path + "stats"),
                                 self.runs,
                                 os.path.join(self.output_path, "cmd", "train"),
                                 os.path.join(self.output_path, "model"),
                                 self.workingDirectory)

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
