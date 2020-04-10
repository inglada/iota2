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

from iota2.Steps import IOTA2Step
from iota2.Cluster import get_RAM
from iota2.Common import ServiceConfigFile as SCF


class reassembleTileParts(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "reassembleTileParts"
        super(reassembleTileParts, self).__init__(cfg, cfg_resources_file,
                                                  resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.cfg = cfg
        self.runs = SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs')
        self.tiles = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'listTile').split(" ")
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.data_field = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'dataField')
        self.im_ref = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'OBIA_segmentation_path')
        if cfg_resources_file is not None:
            self.nb_cpu = SCF.serviceConfigFile(cfg_resources_file).getParam(
                resources_block_name, 'nb_cpu')
        else:
            self.nb_cpu = 1

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Reassemble parts of tiles")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        runs = [run for run in range(0, self.runs)]
        return runs

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from iota2.Classification import ObiaClassification as OCC
        return lambda x: OCC.reassembleParts(seed=x,
                                             nb_cpu=self.nb_cpu,
                                             tiles=self.tiles,
                                             data_field=self.data_field,
                                             output_path=self.output_path,
                                             im_ref=self.im_ref,
                                             path_wd=self.workingDirectory)

    def step_outputs(self):
        """
        """
        pass
