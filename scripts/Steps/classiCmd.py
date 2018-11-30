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

class classiCmd(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        super(classiCmd, self).__init__(cfg, cfg_resources_file)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath')
        self.field_region = SCF.serviceConfigFile(self.cfg).getParam('chain', 'regionField')
        self.runs = SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs')
        self.region_path = SCF.serviceConfigFile(self.cfg).getParam('chain', 'regionPath')
        self.ram_classification = 1024.0 * get_RAM(self.resources["ram"])

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

        return [self.field_region]

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from Classification import ClassificationCmd as CC
        step_function = lambda x: CC.launchClassification(os.path.join(self.output_path, "model"),
                                                          self.cfg,
                                                          os.path.join(self.output_path, "stats"),
                                                          os.path.join(self.output_path, "shapeRegion"),
                                                          os.path.join(self.output_path, "features"),
                                                          self.region_path,
                                                          x,
                                                          self.runs,
                                                          os.path.join(self.output_path, "cmd", "cla"),
                                                          os.path.join(self.output_path, "classif"),
                                                          self.ram_classification,
                                                          self.workingDirectory)
        return step_function

    def step_outputs(self):
        """
        """
        pass
