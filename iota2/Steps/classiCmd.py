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

from iota2.Steps import IOTA2Step
from iota2.Cluster import get_RAM
from iota2.Common import ServiceConfigFile as SCF


class classiCmd(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "cmdClassifications"
        super(classiCmd, self).__init__(cfg, cfg_resources_file,
                                        resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.field_region = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'regionField')
        self.runs = SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs')
        self.region_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'regionPath')
        self.ram_classification = 1024.0 * get_RAM(self.resources["ram"])

    @classmethod
    def step_description(cls):
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
        from iota2.Classification import ClassificationCmd as CC
        step_function = lambda x: CC.write_classification_command(
            os.path.join(self.output_path, "model"), self.cfg, self.
            output_path,
            SCF.serviceConfigFile(self.cfg).getParam('argTrain', 'classifier'),
            SCF.serviceConfigFile(self.cfg).getParam('argClassification',
                                                     'classifMode'),
            SCF.serviceConfigFile(self.cfg).getParam('chain',
                                                     'nomenclaturePath'),
            os.path.join(self.output_path, "stats"),
            os.path.join(self.output_path, "shapeRegion"),
            os.path.join(self.output_path, "features"), self.region_path, x,
            os.path.join(self.output_path, "cmd", "cla"),
            os.path.join(self.output_path, "classif"
                         ), self.ram_classification, self.workingDirectory)
        return step_function

    def step_outputs(self):
        """
        """
        pass
