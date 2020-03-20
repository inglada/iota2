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

from iota2.Steps import IOTA2Step
from iota2.Cluster import get_RAM
from iota2.Common import ServiceConfigFile as SCF


class classification(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "classifications"

        super(classification, self).__init__(cfg, cfg_resources_file,
                                             resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.data_field = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'dataField')
        self.enable_autoContext = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'enable_autoContext')
        self.RAM = 1024.0 * get_RAM(self.resources["ram"])
        self.use_scikitlearn = SCF.serviceConfigFile(self.cfg).getParam(
            'scikit_models_parameters', 'model_type') is not None
        self.custom_features_flag = SCF.serviceConfigFile(
            self.cfg).checkCustomFeature()
        if self.custom_features_flag:
            self.number_of_chunks = SCF.serviceConfigFile(self.cfg).getParam(
                "Features", "number_of_chunks")
        else:
            self.number_of_chunks = None

        # ~ TODO : find a smarted way to determine the attribute self.scikit_tile_split
        self.scikit_tile_split = 50

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = "Generate classifications"
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from iota2.Common import FileUtils as fut
        from iota2.Classification.ImageClassifier import autoContext_classification_param
        from iota2.Common.ServiceConfigFile import iota2_parameters

        if self.enable_autoContext is False and self.use_scikitlearn is False:
            parameters = fut.parseClassifCmd(
                os.path.join(self.output_path, "cmd", "cla", "class.txt"),
                self.custom_features_flag, self.number_of_chunks)
            input(f"input param {parameters}")
        elif self.enable_autoContext is True:
            parameters = autoContext_classification_param(
                self.output_path, self.data_field)
        elif self.use_scikitlearn:
            parameters = fut.parseClassifCmd(
                os.path.join(self.output_path, "cmd", "cla", "class.txt"))
            running_parameters = iota2_parameters(self.cfg)
            parameters = [{
                "mask":
                param[1],
                "model":
                param[2],
                "stat":
                param[3],
                "out_classif":
                param[4],
                "out_confidence":
                param[5],
                "out_proba":
                None,
                "working_dir":
                param[6],
                "tile_name":
                param[8],
                "sar_optical_post_fusion":
                SCF.serviceConfigFile(self.cfg).getParam(
                    'argTrain', 'dempster_shafer_SAR_Opt_fusion'),
                "output_path":
                SCF.serviceConfigFile(self.cfg).getParam(
                    'chain', 'outputPath'),
                "sensors_parameters":
                running_parameters.get_sensors_parameters(tile_name=param[8]),
                "pixel_type":
                param[17],
                "number_of_chunks":
                self.scikit_tile_split,
                "targeted_chunk":
                target_chunk,
                "ram":
                param[19]
            } for param in parameters
                          for target_chunk in range(self.scikit_tile_split)]
        return parameters

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from iota2.Classification.ImageClassifier import autoContext_launch_classif
        from iota2.Classification import ImageClassifier as imageClassifier
        from iota2.Common.ServiceConfigFile import iota2_parameters
        from iota2.Classification import skClassifier
        from iota2.MPI import launch_tasks as tLauncher

        if self.enable_autoContext is False and self.use_scikitlearn is False:
            launch_py_cmd = tLauncher.launchPythonCmd
            step_function = lambda x: launch_py_cmd(
                imageClassifier.launchClassification, *x)
        elif self.enable_autoContext is True and self.use_scikitlearn is False:
            running_parameters = iota2_parameters(self.cfg)

            step_function = lambda x: autoContext_launch_classif(
                x,
                SCF.serviceConfigFile(self.cfg).getParam(
                    'argTrain', 'classifier'), x["tile"],
                SCF.serviceConfigFile(self.cfg).getParam(
                    'argClassification', 'enable_probability_map'),
                SCF.serviceConfigFile(self.cfg).getParam('dimRed', 'dimRed'),
                SCF.serviceConfigFile(self.cfg).getParam('chain', 'dataField'),
                SCF.serviceConfigFile(self.cfg).getParam(
                    'GlobChain', 'writeOutputs'),
                SCF.serviceConfigFile(self.cfg).getParam(
                    'dimRed', 'reductionMode'),
                SCF.serviceConfigFile(self.cfg).getParam(
                    'chain', 'outputPath'),
                SCF.serviceConfigFile(self.cfg).getParam(
                    'argTrain', 'dempster_shafer_SAR_Opt_fusion'),
                SCF.serviceConfigFile(self.cfg).getParam(
                    'chain', 'nomenclaturePath'),
                running_parameters.get_sensors_parameters(x["tile"]), self.RAM,
                self.workingDirectory)
        elif self.enable_autoContext is False and self.use_scikitlearn is True:
            step_function = lambda x: skClassifier.predict(**x)

        return step_function

    def step_outputs(self):
        """
        """
        pass
