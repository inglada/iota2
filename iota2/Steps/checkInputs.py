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
from typing import Optional
from Steps import IOTA2Step
from Common import ServiceConfigFile as serviceConf


class CheckInputs(IOTA2Step.Step):
    def __init__(self,
                 cfg: str,
                 cfg_resources_file: str,
                 working_directory: Optional[str] = None) -> None:
        """set up the step
        """
        # heritage init
        resources_block_name = "checkInputs"
        super(CheckInputs, self).__init__(cfg, cfg_resources_file, resources_block_name)

        # step variables
        self.execution_dir = serviceConf.serviceConfigFile(self.cfg).getParam('chain', 'outputPath')

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("check iota2 input provided in the configuration file")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        return [self.cfg]

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from Common.verifyInputs import check_iota2_inputs

        def step_function(x):
            return check_iota2_inputs(x)

        return step_function

    def step_outputs(self):
        """
        """
        pass
