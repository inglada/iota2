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


class splitSamples(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "split_samples"
        super(splitSamples, self).__init__(cfg, cfg_resources_file,
                                           resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        return "split learning polygons and Validation polygons in sub-sample if necessary"

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
        from iota2.Sampling import SplitSamples as splitS
        from iota2.Common import ServiceConfigFile as SCF

        return lambda x: splitS.split_samples(
            SCF.serviceConfigFile(x).getParam("chain", "outputPath"),
            SCF.serviceConfigFile(x).getParam("chain", "dataField"),
            SCF.serviceConfigFile(x).getParam("chain", "enableCrossValidation"
                                              ),
            SCF.serviceConfigFile(x).getParam("chain",
                                              "mode_outside_RegionSplit"),
            SCF.serviceConfigFile(x).getParam("chain", "regionField"),
            SCF.serviceConfigFile(x).getParam("chain", "ratio"),
            SCF.serviceConfigFile(x).getParam("chain", "random_seed"),
            SCF.serviceConfigFile(x).getParam("chain", "runs"),
            SCF.serviceConfigFile(x).getParam("GlobChain", "proj"), self.
            workingDirectory)

    def step_outputs(self):
        """
        """
        pass
