#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
from Common import ServiceConfigFile as SCF


class Envelope(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "envelope"
        super(
            Envelope,
            self).__init__(
            cfg,
            cfg_resources_file,
            resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.outputPath = SCF.serviceConfigFile(
            self.cfg).getParam(
            'chain', 'outputPath')

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Generate tile's envelope")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        pathEnvelope = os.path.join(self.outputPath, "envelope")
        return [pathEnvelope]

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from Sampling import TileEnvelope as env

        tiles = SCF.serviceConfigFile(
            self.cfg).getParam(
            'chain', 'listTile').split(" ")
        pathTilesFeat = os.path.join(self.outputPath, "features")

        def step_function(x): return env.GenerateShapeTile(tiles, pathTilesFeat,
                                                           x, self.workingDirectory,
                                                           self.cfg)
        return step_function

    def step_outputs(self):
        """
        """
        pass
