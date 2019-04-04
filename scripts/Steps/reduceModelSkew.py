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
from Sampling import SamplesMerge as samples_merge

class reduceModelSkew(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "reduceModelSkew"
        super(reduceModelSkew, self).__init__(cfg, cfg_resources_file, resources_block_name)

        # step variables
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath')
        self.field_region = SCF.serviceConfigFile(self.cfg).getParam('chain', 'regionField')
        self.nb_runs = SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs')
    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("reduce model skew")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from Learning import ModelUnskew
        region_seed_tile = samples_merge.get_models(os.path.join(self.output_path, "formattingVectors"), self.field_region, self.nb_runs)
        cmd_list = ModelUnskew.launchUnskew(region_seed_tile,self.cfg)
        return cmd_list

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