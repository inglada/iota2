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


class PBS_scheduler:
    def __init__(self, cfg_resources_file):

        resources_block_name = "iota2_chain"
        self.resources = self.parse_resource_file(
            resources_block_name, cfg_resources_file
        )

        self.RAM = self.resources["ram"]
        self.cpu = self.resources["cpu"]
        self.walltime = self.resources["walltime"]

        self.name = self.resources["name"]

    def build_step_name(self):
        """
        strategy to build step name
        the name define logging ouput files and resources access
        """
        return self.__class__.__name__

    def parse_resource_file(self, step_name, cfg_resources_file):
        """
        parse a configuration file dedicated to reserve resources to HPC
        """
        from config import Config

        default_name = "IOTA2"
        default_cpu = 1
        default_ram = "5gb"
        default_walltime = "01:00:00"
        default_process_min = 1
        default_process_max = -1

        cfg_resources = None
        if cfg_resources_file and os.path.exists(cfg_resources_file):
            cfg_resources = Config(cfg_resources_file)

        resource = {}
        cfg_step_resources = getattr(cfg_resources, str(step_name), {})
        resource["name"] = getattr(cfg_step_resources, "name", default_name)
        resource["cpu"] = getattr(cfg_step_resources, "nb_cpu", default_cpu)
        resource["ram"] = getattr(cfg_step_resources, "ram", default_ram)
        resource["walltime"] = getattr(
            cfg_step_resources, "walltime", default_walltime
        )
        resource["process_min"] = getattr(
            cfg_step_resources, "process_min", default_process_min
        )
        resource["process_max"] = getattr(
            cfg_step_resources, "process_max", default_process_max
        )

        return resource
