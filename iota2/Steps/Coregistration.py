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
from iota2.Common.Tools import CoRegister


class Coregistration(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "coregistration"
        super(Coregistration, self).__init__(cfg, cfg_resources_file,
                                             resources_block_name)

        # step variables
        self.RAM = 1024.0 * get_RAM(self.resources["ram"])
        self.workingDirectory = workingDirectory
        self.execution_mode = "cluster"

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

        for tile in self.tiles:
            task = self.i2_task(
                task_name=f"coreg_{tile}",
                log_dir=self.log_step_dir,
                execution_mode=self.execution_mode,
                task_parameters={
                    "f":
                    CoRegister.launch_coregister,
                    "working_directory":
                    self.workingDirectory,
                    "inref":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'coregistration', 'VHRPath'),
                    "bandsrc":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'coregistration', 'bandSrc'),
                    "bandref":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'coregistration', 'bandRef'),
                    "resample":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'coregistration', 'resample'),
                    "step":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'coregistration', 'step'),
                    "minstep":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'coregistration', 'minstep'),
                    "minsiftpoints":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'coregistration', 'minshiftpoints'),
                    "iterate":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'coregistration', 'iterate'),
                    "prec":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'coregistration', 'prec'),
                    "mode":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'coregistration', 'mode'),
                    "output_path":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'chain', 'outputPath'),
                    "date_vhr":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'coregistration', 'dateVHR'),
                    "dates_src":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'coregistration', 'dateSrc'),
                    "list_tiles":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'chain', 'listTile'),
                    "ipath_l5":
                    l5_path,
                    "ipath_l8":
                    l8_path,
                    "ipath_s2":
                    s2_path,
                    "ipath_s2_s2c":
                    s2_s2c_path,
                    "corregistration_pattern":
                    correg_pattern,
                    "launch_mask":
                    True,
                    "sensors_parameters":
                    sensors_parameters.get_sensors_parameters(tile)
                },
                task_resources=self.resources)
            self.add_task_to_i2_processing_graph(task,
                                                 task_group="tile_tasks",
                                                 task_sub_group=tile,
                                                 task_dep_group="first_task")

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Time series coregistration on a VHR reference")
        return description
