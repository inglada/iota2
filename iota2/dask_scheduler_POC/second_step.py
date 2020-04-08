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
import logging
from typing import Optional

from iota2_step import step

LOGGER = logging.getLogger(__name__)


class second_step(step):
    def __init__(self, running_directory: str):
        super(second_step, self).__init__()
        self.running_directory = running_directory
        self.log_dir = os.path.join(self.running_directory, "logs")
        if not os.path.exists(self.log_dir):
            os.mkdir(self.log_dir)
        self.execution_mode = "cluster"
        self.step_resources = {"cpu": 1, "ram": "5Gb", "walltime": "02:00:00"}
        # useful to get last tasks to triggered
        self.step_tasks = []

        # can comes from a dedicated function
        step_params_from_tile_name = {
            "T31TCJ": {
                "f":
                self.preprocess,
                "check_file":
                os.path.join(self.running_directory, "dask_fonction_a.txt"),
                "tile_name":
                "T31TCJ",
                "output_file":
                os.path.join(self.running_directory, "dask_fonction_b1.txt"),
                "sleeping_time":
                1
            },
            "T31TDJ": {
                "f":
                self.preprocess,
                "check_file":
                os.path.join(self.running_directory, "dask_fonction_a.txt"),
                "tile_name":
                "T31TDJ",
                "output_file":
                os.path.join(self.running_directory, "dask_fonction_b2.txt"),
                "sleeping_time":
                10
            }
        }
        # then build dep tree
        for tile in self.list_tiles:
            task = self.i2_task(
                task_name=f"prepro_{tile}",
                log_dir=self.log_dir,
                execution_mode=self.execution_mode,
                task_parameters=step_params_from_tile_name[tile],
                task_resources=self.step_resources)
            task_in_graph = self.add_task_to_i2_processing_graph(
                task,
                task_group="tile_tasks",
                task_sub_group=tile,
                task_dep_group="first_task")
            self.step_tasks.append(task_in_graph)

    def preprocess(self,
                   check_file: str,
                   output_file: str,
                   tile_name: str,
                   sleeping_time: Optional[int] = 5,
                   LOGGER=LOGGER):
        """simulate the sensors preprocess by tiles
        """
        import time
        if not os.path.exists(check_file):
            raise IOError(f"the file {check_file} does not exists")
        LOGGER.warning(
            f"preprocess a sensor tile {tile_name} writing results at {output_file} in {sleeping_time} seconds"
        )
        if os.path.exists(output_file):
            os.remove(output_file)
        with open(output_file, "w") as out_file:
            out_file.write(f"{tile_name} preprocessing")
        time.sleep(sleeping_time)
        LOGGER.warning(f"preprocessing of {tile_name} done")
