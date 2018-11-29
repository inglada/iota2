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
from Sampling import VectorSamplesMerge as VSM

class samplesByModels(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file):
        # heritage init
        super(samplesByModels, self).__init__(cfg, cfg_resources_file)

        # step variables
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath')

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Merge samples dedicated to the same model")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        return VSM.tile_vectors_to_models(os.path.join(self.output_path, "learningSamples"),
                                          SCF.serviceConfigFile(self.cfg).getParam('argTrain', 'dempster_shafer_SAR_Opt_fusion'))

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        step_function = lambda x: VSM.vectorSamplesMerge(self.cfg, x)
        return step_function

    def step_outputs(self):
        """
        """
        pass
