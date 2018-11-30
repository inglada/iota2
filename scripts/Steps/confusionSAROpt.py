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
from Cluster import get_RAM

class confusionSAROpt(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        super(confusionSAROpt, self).__init__(cfg, cfg_resources_file)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath')
        self.data_field = SCF.serviceConfigFile(self.cfg).getParam('chain', 'dataField')
        self.sar_opt_conf_ram = 1024.0 * get_RAM(self.resources["ram"])
        
    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Evaluate SAR vs optical performance")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from Validation import GenConfusionMatrix as GCM
        return GCM.confusion_sar_optical_parameter(self.output_path)

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from Validation import GenConfusionMatrix as GCM
        step_function = lambda x: GCM.confusion_sar_optical(x,
                                                            self.data_field,
                                                            self.sar_opt_conf_ram)
        return step_function

    def step_outputs(self):
        """
        """
        pass
