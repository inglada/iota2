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

class classification(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "classifications"
        super(classification, self).__init__(cfg, cfg_resources_file, resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath')
        self.data_field = SCF.serviceConfigFile(self.cfg).getParam('chain', 'dataField')
        self.enable_autoContext = SCF.serviceConfigFile(self.cfg).getParam('chain', 'enable_autoContext')
        self.RAM = 1024.0 * get_RAM(self.resources["ram"])

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Generate classifications")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from Common import FileUtils as fut
        from Classification.ImageClassifier import autoContext_classification_param
        if self.enable_autoContext is True:
            parameter_list = autoContext_classification_param(self.output_path,
                                                              self.data_field)
        else :
            parameter_list = fut.parseClassifCmd(os.path.join(self.output_path, "cmd", "cla", "class.txt"))
        return parameter_list

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from Classification.ImageClassifier import autoContext_launch_classif
        from Classification import ImageClassifier as imageClassifier
        from MPI import launch_tasks as tLauncher

        if self.enable_autoContext is False:
            launchPythonCmd = tLauncher.launchPythonCmd
            step_function = lambda x: launchPythonCmd(imageClassifier.launchClassification, *x)
        else:
            step_function = lambda x: autoContext_launch_classif(x, self.cfg, self.RAM, self.workingDirectory)
        return step_function

    def step_outputs(self):
        """
        """
        pass
