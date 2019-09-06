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
from Cluster import get_RAM
from Common import ServiceConfigFile as SCF

class learnModel(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "training"
        super(learnModel, self).__init__(cfg, cfg_resources_file, resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath')
        self.data_field = SCF.serviceConfigFile(self.cfg).getParam('chain', 'dataField')
        self.regionField = SCF.serviceConfigFile(self.cfg).getParam('chain', 'regionField')
        self.runs = SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs')
        self.enable_autoContext = SCF.serviceConfigFile(self.cfg).getParam('chain', 'enable_autoContext')
        self.RAM = 1024.0 * get_RAM(self.resources["ram"])

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
        from Learning.trainAutoContext import train_autoContext_parameters
        if self.enable_autoContext:
            parameter_list = train_autoContext_parameters(self.output_path, 
                                                          self.regionField)
        else:
            parameter_list = TC.launchTraining(self.cfg,
                                               self.data_field,
                                               os.path.join(self.output_path + "stats"),
                                               self.runs,
                                               os.path.join(self.output_path, "cmd", "train"),
                                               os.path.join(self.output_path, "model"),
                                               self.workingDirectory)
        return parameter_list

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        if self.enable_autoContext:
            from Learning.trainAutoContext import train_autoContext
            step_function = lambda x: train_autoContext(x, self.cfg, self.RAM, self.workingDirectory)
        else:
            from MPI import launch_tasks as tLauncher
            bashLauncherFunction = tLauncher.launchBashCmd
            step_function = lambda x: bashLauncherFunction(x)
        return step_function

    def step_outputs(self):
        """
        """
        pass
