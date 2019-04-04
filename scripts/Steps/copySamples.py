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

class copySamples(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "samplesManagement"
        super(copySamples, self).__init__(cfg, cfg_resources_file, resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath')
        self.dataField = SCF.serviceConfigFile(self.cfg).getParam('chain', 'dataField')
        self.sampleManagement = SCF.serviceConfigFile(self.cfg).getParam('argTrain', 'sampleManagement')

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Copy samples between models according to user request")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from Sampling import DataAugmentation
        return DataAugmentation.GetDataAugmentationByCopyParameters(os.path.join(self.output_path, "learningSamples"))

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from Sampling import DataAugmentation
        step_function = lambda x: DataAugmentation.DataAugmentationByCopy(self.dataField.lower(),
                                                                          self.sampleManagement,
                                                                          x, self.workingDirectory)
        return step_function

    def step_outputs(self):
        """
        """
        pass
