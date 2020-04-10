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

from Steps import IOTA2Step
from Common import ServiceConfigFile as SCF
from Sampling import SamplesMerge as samples_merge


class obiaLearning(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, working_directory=None):
        # heritage init
        resources_block_name = "obiaLearning"
        super(obiaLearning, self).__init__(cfg, cfg_resources_file,
                                           resources_block_name)

        # step variables
        self.workingDirectory = working_directory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.data_field = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'dataField')
        self.field_region = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'regionField')
        self.nb_runs = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'runs')
        self.classifier = SCF.serviceConfigFile(self.cfg).getParam(
            'argTrain', 'classifier')
        self.options = SCF.serviceConfigFile(self.cfg).getParam(
            'argTrain', 'options')

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("learn model for obia")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from iota2.Learning import ObiaTrainingCmd
        region_seed_tile = samples_merge.get_models(
            os.path.join(self.output_path, "formattingVectors"),
            self.field_region, self.nb_runs)
        cmd_list = ObiaTrainingCmd.launch_obia_train_model(
            iota2_directory=self.output_path,
            data_field=self.data_field,
            region_seed_tile=region_seed_tile,
            path_to_cmd_train=os.path.join(self.output_path, "cmd", "train"),
            out_folder=os.path.join(self.output_path, "model"),
            classifier=self.classifier,
            options=self.options)
        return cmd_list

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
