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

from iota2.Steps import IOTA2Step
from iota2.Common import ServiceConfigFile as SCF


class additionalStatisticsMerge(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "mergeOutStats"
        super(additionalStatisticsMerge,
              self).__init__(cfg, cfg_resources_file, resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.runs = SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs')

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        return "Merge additional statistics"

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        return [self.output_path]

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from iota2.Validation import MergeOutStats as MOutS
        return lambda x: MOutS.merge_output_statistics(x, self.runs)

    def step_outputs(self):
        """
        """
        pass
