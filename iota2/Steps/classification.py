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
        self.use_scikitlearn = SCF.serviceConfigFile(self.cfg).getParam('scikit_models_parameters', 'model_type') is not None
        
        # ~ TODO : find a smarted way to determine the attribute self.scikit_tile_split
        self.scikit_tile_split = 50

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
        parameters = fut.parseClassifCmd(os.path.join(self.output_path, "cmd", "cla", "class.txt"))
        if self.enable_autoContext is True:
            parameters = autoContext_classification_param(self.output_path,
                                                          self.data_field)
        elif self.use_scikitlearn:
            parameters = [{"mask": param[1],
                           "model": param[2],
                           "stat": param[3],
                           "out_classif": param[4],
                           "out_confidence": param[5],
                           "out_proba": None,
                           "working_dir": param[6],
                           "configuration_file": param[7],
                           "pixel_type": param[8],
                           "number_of_chunks": self.scikit_tile_split,
                           "targeted_chunk": target_chunk,
                           "ram": param[10]} for param in parameters for target_chunk in range(self.scikit_tile_split)]
        return parameters

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
        from Classification import skClassifier
        from MPI import launch_tasks as tLauncher

        if self.enable_autoContext is False and self.use_scikitlearn is False:
            launchPythonCmd = tLauncher.launchPythonCmd
            step_function = lambda x: launchPythonCmd(imageClassifier.launchClassification, *x)
        elif self.enable_autoContext is True and self.use_scikitlearn is False:
            step_function = lambda x: autoContext_launch_classif(x, self.cfg, self.RAM, self.workingDirectory)
        elif self.enable_autoContext is False and self.use_scikitlearn is True:
            step_function = lambda x: skClassifier.predict(**x)

        return step_function

    def step_outputs(self):
        """
        """
        pass
