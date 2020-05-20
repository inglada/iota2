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
from iota2.Sampling import TileEnvelope as env


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
        self.execution_mode = "cluster"

        task = self.i2_task(task_name=f"tiles_envelopes",
                            log_dir=self.log_step_dir,
                            execution_mode=self.execution_mode,
                            task_parameters={
                                "f": env.generate_shape_tile,
                                "tiles": self.tiles,
                                "pathWd": self.workingDirectory,
                                "output_path": self.outputPath,
                                "proj": self.proj
                            },
                            task_resources=self.resources)
        self.add_task_to_i2_processing_graph(
            task,
            task_group="vector",
            task_sub_group="vector",
            task_dep_dico={"tile_tasks": self.tiles})

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Generate tile's envelope")
        return description
