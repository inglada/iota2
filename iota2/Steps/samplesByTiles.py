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


class samplesByTiles(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "samplesSelection_tiles"
        super(samplesByTiles, self).__init__(cfg, cfg_resources_file,
                                             resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.tile_name_pos = 0

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Split pixels selected to learn models by tiles")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from iota2.Common.FileUtils import FileSearch_AND
        sample_sel_directory = os.path.join(
            SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath'),
            "samplesSelection")
        sampled_vectors = FileSearch_AND(sample_sel_directory, True,
                                         "selection.sqlite")
        tiles = []
        for sampled_vector in sampled_vectors:
            tile_name = os.path.splitext(os.path.basename(
                sampled_vector))[0].split("_")[self.tile_name_pos]
            if not tile_name in tiles and tile_name != "samples":
                tiles.append(tile_name)
        tiles = sorted(tiles)
        return tiles

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from iota2.Sampling import SamplesSelection
        step_function = lambda x: SamplesSelection.prepare_selection(
            os.path.join(self.output_path, "samplesSelection"), x, self.
            workingDirectory)
        return step_function

    def step_outputs(self):
        """
        """
        pass
