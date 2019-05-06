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
from Cluster import get_RAM
from Common import ServiceConfigFile as SCF

class obiaClassification(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "cmdClassifications"
        super(obiaClassification, self).__init__(cfg, cfg_resources_file, resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.cfg = cfg
        self.runs = SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs')
        if cfg_resources_file != None :
            self.nb_cpu = SCF.serviceConfigFile(cfg_resources_file).getParam(resources_block_name,'nb_cpu')
        else :
            self.nb_cpu = 1

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Generate classification commands")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        runs = [run for run in range(0, self.runs)]
        return runs

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from Classification import ObiaClassification as OCC
        step_function = lambda x: OCC.launchObiaClassification(x, self.nb_cpu, self.cfg, self.workingDirectory)
        return step_function

    def step_outputs(self):
        """
        """
        pass