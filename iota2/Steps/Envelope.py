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


class Envelope(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "envelope"
        super(Envelope, self).__init__(cfg, cfg_resources_file,
                                       resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.outputPath = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.proj = int(
            SCF.serviceConfigFile(self.cfg).getParam('GlobChain',
                                                     'proj').split(":")[-1])

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        return "Generate tile's envelope"

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        return [self.outputPath]

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from iota2.Sampling import TileEnvelope as env

        tiles = SCF.serviceConfigFile(self.cfg).getParam('chain',
                                                         'listTile').split(" ")
        return lambda x: env.generate_shape_tile(
            tiles, self.workingDirectory, x, self.proj)

    def step_outputs(self):
        """
        """
        pass
