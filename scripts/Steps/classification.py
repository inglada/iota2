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

class classification(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        super(classification, self).__init__(cfg, cfg_resources_file)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath')

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
        return fut.parseClassifCmd(os.path.join(self.output_path, "cmd", "cla", "class.txt"))

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from Classification import ImageClassifier as imageClassifier
        from MPI import launch_tasks as tLauncher

        launchPythonCmd = tLauncher.launchPythonCmd
        step_function = lambda x: launchPythonCmd(imageClassifier.launchClassification, *x)
        return step_function

    def step_outputs(self):
        """
        """
        pass
