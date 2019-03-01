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

class samplesDimReduction(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        super(samplesDimReduction, self).__init__(cfg, cfg_resources_file)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath')
        self.targetDimension = SCF.serviceConfigFile(self.cfg).getParam('dimRed', 'targetDimension')
        self.reductionMode = SCF.serviceConfigFile(self.cfg).getParam('dimRed', 'reductionMode')

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Dimensionality reduction")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from Sampling import DimensionalityReduction as DR
        return DR.BuildIOSampleFileLists(self.output_path)

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from Sampling import DimensionalityReduction as DR
        step_function = lambda x: DR.SampleDimensionalityReduction(x,
                                                                   self.output_path,
                                                                   self.targetDimension,
                                                                   self.reductionMode)
        return step_function

    def step_outputs(self):
        """
        """
        pass