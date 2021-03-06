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
from iota2.Common import ServiceConfigFile as SCF


class genRegionVector(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "regionShape"
        super(genRegionVector, self).__init__(cfg, cfg_resources_file,
                                              resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.outputPath = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Generate a region vector")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        shapeRegion = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'regionPath')
        return [shapeRegion]

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from iota2.Sampling import TileArea as area

        pathEnvelope = os.path.join(self.outputPath, "envelope")
        field_Region = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'regionField')

        step_function = lambda x: area.generate_region_shape(
            pathEnvelope, x, field_Region, self.outputPath, self.
            workingDirectory)
        return step_function

    def step_outputs(self):
        """
        """
        pass
