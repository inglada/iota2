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
from iota2.Common import IOTA2Directory as IOTA2_dir


class IOTA2DirTree(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file):
        # heritage init
        resources_block_name = "iota2_dir"
        super(IOTA2DirTree, self).__init__(cfg, cfg_resources_file,
                                           resources_block_name)

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Construct IOTA² output directories")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        return [
            SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath')
        ]

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from iota2.Sensors.Sensors_container import sensors_container
        from iota2.Common.ServiceConfigFile import iota2_parameters

        check_inputs = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'check_inputs')
        tiles = SCF.serviceConfigFile(self.cfg).getParam('chain',
                                                         'listTile').split(" ")
        output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        running_parameters = iota2_parameters(
            SCF.serviceConfigFile(self.cfg).pathConf)
        sensors_parameters = running_parameters.get_sensors_parameters(
            tiles[0])
        sensor_tile_container = sensors_container(tiles[0], None, output_path,
                                                  **sensors_parameters)

        sensor_path = sensor_tile_container.get_enabled_sensors_path()[0]
        step_function = lambda x: IOTA2_dir.generate_directories(
            x, check_inputs,
            SCF.serviceConfigFile(self.cfg).getParam(
                'chain', 'merge_final_classifications'),
            SCF.serviceConfigFile(self.cfg).getParam('chain', 'groundTruth'),
            SCF.serviceConfigFile(self.cfg).getParam('chain', 'regionPath'),
            SCF.serviceConfigFile(self.cfg).getParam('chain', 'dataField'),
            SCF.serviceConfigFile(self.cfg).getParam('chain', 'regionField'),
            int(
                SCF.serviceConfigFile(self.cfg).getParam('GlobChain', 'proj').
                split(":")[-1]), sensor_path, tiles)
        return step_function

    def step_outputs(self):
        from iota2.Common import ServiceConfigFile as SCF
        outputPath = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        return os.path.exists(outputPath)
