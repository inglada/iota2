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

from iota2.Steps import IOTA2Step
from iota2.Common import ServiceConfigFile as SCF
from iota2.Cluster import get_RAM
from iota2.Common import write_features_map as wfm


class merge_features_maps(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "mergeMaps"
        super(merge_features_maps, self).__init__(cfg, cfg_resources_file,
                                                  resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.ram_extraction = 1024.0 * get_RAM(self.resources["ram"])
        # read config file to init custom features and check validity
        self.custom_features = SCF.serviceConfigFile(
            self.cfg).checkCustomFeature()
        if self.custom_features:
            self.number_of_chunks = SCF.serviceConfigFile(self.cfg).getParam(
                'external_features', "number_of_chunks")
            self.chunk_size_mode = SCF.serviceConfigFile(self.cfg).getParam(
                'external_features', "chunk_size_mode")

        # implement tests for check if custom features are well provided
        # so the chain failed during step init
    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Extract pixels values by tiles")
        return description

    def step_inputs(self):

        output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')

        return [output_path]

    def step_execute(self):
        """ 
        Return
        ------
        lambda
        """
        output_name = SCF.serviceConfigFile(self.cfg).getParam(
            'external_features', 'output_name')
        res = SCF.serviceConfigFile(self.cfg).getParam('chain',
                                                       'spatialResolution')

        return lambda x: wfm.merge_features_maps(x, output_name, res)

    def step_outputs(self):
        """
        """
        pass
