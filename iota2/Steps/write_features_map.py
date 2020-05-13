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
import iota2.Common.write_features_map as wfm


class write_features_map(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "writeMaps"
        super(write_features_map, self).__init__(cfg, cfg_resources_file,
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
        # found all shapes

        # Initialize the sensors dictionnary with the first tile found
        # Sensors are the same for all tiles
        tiles = SCF.serviceConfigFile(self.cfg).getParam("chain",
                                                         "listTile").split(" ")

        params = {
            "working_directory":
            self.workingDirectory,
            "output_path":
            SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath'),
            "sar_optical_post_fusion":
            SCF.serviceConfigFile(self.cfg).getParam(
                'argTrain', 'dempster_shafer_SAR_Opt_fusion'),
            "module_path":
            SCF.serviceConfigFile(self.cfg).getParam('external_features',
                                                     'module'),
            "list_functions":
            SCF.serviceConfigFile(self.cfg).getParam('external_features',
                                                     'functions').split(" "),
            "force_standard_labels":
            SCF.serviceConfigFile(self.cfg).getParam('chain',
                                                     'force_standard_labels'),
            "number_of_chunks":
            self.number_of_chunks,
            "chunk_size_mode":
            self.chunk_size_mode,
            "concat_mode":
            SCF.serviceConfigFile(self.cfg).getParam('external_features',
                                                     "concat_mode")
        }

        parameters = []
        for tile in tiles:
            sensors_params = SCF.iota2_parameters(
                self.cfg).get_sensors_parameters(tile)

            for i in range(self.number_of_chunks):
                param_t = params.copy()
                param_t["tile"] = tile
                param_t["targeted_chunk"] = i
                param_t["sensors_parameters"] = sensors_params
                parameters.append(param_t)
        return parameters

    def step_execute(self):
        """ 
        Return
        ------
        lambda
        """
        return lambda x: wfm.write_features_by_chunk(**x)

    def step_outputs(self):
        """
        """
        pass
