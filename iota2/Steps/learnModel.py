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
from iota2.Learning.TrainingCmd import config_model


class learnModel(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "training"
        super(learnModel, self).__init__(cfg, cfg_resources_file,
                                         resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.data_field = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'dataField')

        self.region_field = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'regionField')
        self.runs = SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs')

        self.enable_autoContext = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'enable_autoContext')
        self.autoContext_iterations = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'autoContext_iterations')
        self.RAM = 1024.0 * get_RAM(self.resources["ram"])
        self.superpix_data_field = "superpix"
        self.tiles = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'listTile').split("_")
        self.available_ram = 1024.0 * get_RAM(self.resources["ram"])
        self.use_scikitlearn = SCF.serviceConfigFile(self.cfg).getParam(
            'scikit_models_parameters', 'model_type') is not None

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = "Learn model"
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from iota2.Learning import TrainingCmd as TC
        from iota2.Learning import TrainSkLearn
        from iota2.Learning.trainAutoContext import train_autoContext_parameters
        parameters = []

        pathToModelConfig = os.path.join(self.output_path, "config_model",
                                         "configModel.cfg")
        configModel = config_model(self.output_path, self.region_field)
        if not os.path.exists(pathToModelConfig):
            with open(pathToModelConfig, "w") as configFile:
                configFile.write(configModel)
        if self.use_scikitlearn is True and self.enable_autoContext is True:
            raise ValueError(
                "scikit-learn and autoContext modes are not compatibles")
        elif self.use_scikitlearn is True and self.enable_autoContext is False:
            parameters = TrainSkLearn.get_learning_samples(
                os.path.join(self.output_path, "learningSamples"), self.cfg)
        elif self.enable_autoContext is True:
            parameters = train_autoContext_parameters(self.output_path,
                                                      self.region_field)
        else:
            parameters = TC.launch_training(
                classifier_name=SCF.serviceConfigFile(self.cfg).getParam(
                    "argTrain", "classifier"),
                classifier_options=SCF.serviceConfigFile(self.cfg).getParam(
                    "argTrain", "options"),
                output_path=self.output_path,
                ground_truth=SCF.serviceConfigFile(self.cfg).getParam(
                    "chain", "groundTruth"),
                data_field=self.data_field,
                region_field=SCF.serviceConfigFile(self.cfg).getParam(
                    "chain", "regionField"),
                path_to_cmd_train=os.path.join(self.output_path, "cmd",
                                               "train"),
                out=os.path.join(self.output_path, "model"))
        return parameters

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from iota2.MPI import launch_tasks as tLauncher
        from iota2.Learning import TrainSkLearn
        from iota2.Learning.TrainSkLearn import cast_config_cv_parameters
        from iota2.Learning.trainAutoContext import train_autoContext
        from iota2.Common.ServiceConfigFile import iota2_parameters

        if self.use_scikitlearn is True and self.enable_autoContext is False:
            model_parameters = SCF.serviceConfigFile(
                self.cfg).getSection("scikit_models_parameters")
            sk_model = model_parameters['model_type']
            del model_parameters['model_type']
            del model_parameters['standardization']
            del model_parameters['cross_validation_grouped']
            del model_parameters['cross_validation_folds']
            del model_parameters['cross_validation_parameters']

            cv_params = SCF.serviceConfigFile(self.cfg).getParam(
                "scikit_models_parameters", "cross_validation_parameters")
            cv_params = cast_config_cv_parameters(cv_params)

            step_function = lambda x: TrainSkLearn.sk_learn(
                x["learning_file"], x["feat_labels"], x[
                    "model_path"], self.data_field, sk_model,
                SCF.serviceConfigFile(self.cfg).getParam(
                    "scikit_models_parameters", "standardization"), cv_params,
                SCF.serviceConfigFile(self.cfg).getParam(
                    "scikit_models_parameters", "cross_validation_grouped"),
                SCF.serviceConfigFile(self.cfg).getParam(
                    "scikit_models_parameters", "cross_validation_folds"), self
                .available_ram, **model_parameters)
        elif self.enable_autoContext is True:
            running_parameters = iota2_parameters(self.cfg)
            step_function = lambda x: train_autoContext(
                x,
                SCF.serviceConfigFile(self.cfg).getParam("chain", "dataField"
                                                         ), self.output_path,
                running_parameters.get_sensors_parameters(self.tiles[
                    0]), self.superpix_data_field, self.autoContext_iterations,
                self.RAM, self.workingDirectory)
        else:
            bashLauncherFunction = tLauncher.launchBashCmd
            step_function = lambda x: bashLauncherFunction(x)

        return step_function

    def step_outputs(self):
        """
        """
        pass
