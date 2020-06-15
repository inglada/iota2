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
"""
The coregistration step
"""
from iota2.Steps import IOTA2Step
from iota2.Cluster import get_RAM
from iota2.Common import ServiceConfigFile as SCF


class Coregistration(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "coregistration"
        super(Coregistration, self).__init__(cfg, cfg_resources_file,
                                             resources_block_name)

        # step variables
        self.RAM = 1024.0 * get_RAM(self.resources["ram"])
        self.workingDirectory = workingDirectory

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        return "Time series coregistration on a VHR reference"

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        return SCF.serviceConfigFile(self.cfg).getParam('chain',
                                                         'listTile').split(" ")

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from iota2.Common.Tools import CoRegister
        cfg = SCF.serviceConfigFile(self.cfg)

        l5_path = None
        l8_path = None
        s2_path = None
        s2_s2c_path = None
        correg_pattern = None
        if cfg.getParam('chain', 'L5Path_old').lower() != "none":
            l5_path = cfg.getParam('chain', 'L5Path_old')
        if cfg.getParam('chain', 'S2Path').lower() != "none":
            l8_path = cfg.getParam('chain', 'L8Path_old')
        if cfg.getParam('chain', 'S2Path').lower() != "none":
            s2_path = cfg.getParam('chain', 'S2Path')
        if cfg.getParam('chain', 'S2_S2C_Path').lower() != "none":
            s2_s2c_path = cfg.getParam('chain', 'S2_S2C_Path')
        if cfg.getParam('coregistration', 'pattern').lower != "none":
            correg_pattern = cfg.getParam('coregistration', 'pattern')
        sensors_parameters = SCF.iota2_parameters(self.cfg)
        return lambda x: CoRegister.launch_coregister(
            x, self.workingDirectory, cfg.getParam('coregistration', 'VHRPath'
                                                   ),
            cfg.getParam('coregistration', 'bandSrc'),
            cfg.getParam('coregistration', 'bandRef'),
            cfg.getParam('coregistration', 'resample'),
            cfg.getParam('coregistration', 'step'),
            cfg.getParam('coregistration', 'minstep'),
            cfg.getParam('coregistration', 'minsiftpoints'),
            cfg.getParam('coregistration', 'iterate'),
            cfg.getParam('coregistration', 'prec'),
            cfg.getParam('coregistration', 'mode'),
            cfg.getParam("chain", "outputPath"),
            cfg.getParam('coregistration', 'dateVHR'),
            cfg.getParam('coregistration', 'dateSrc'),
            cfg.getParam('chain', 'listTile'), l5_path, l8_path, s2_path,
            s2_s2c_path, correg_pattern, True,
            sensors_parameters.get_sensors_parameters(x))
        # return step_function

    def step_outputs(self):
        """
        """
        pass
