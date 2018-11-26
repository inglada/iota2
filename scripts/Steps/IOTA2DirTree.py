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
from Common import IOTA2Directory as IOTA2_dir

class IOTA2DirTree(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file):
        # heritage init
        super(IOTA2DirTree, self).__init__(cfg, cfg_resources_file)

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Construct IOTA² output directories")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        return [self.cfg]

    def step_execute(self, workingDirectory=None):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        step_function = lambda x: IOTA2_dir.GenerateDirectories(x)
        return step_function

    def step_outputs(self):
        from Common import ServiceConfigFile as SCF
        outputPath = SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath')
        return os.path.exists(outputPath)

    


        