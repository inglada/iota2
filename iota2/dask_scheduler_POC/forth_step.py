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

#from iota2_step import step
from iota2.dask_scheduler_POC import iota2_step

LOGGER = logging.getLogger(__name__)


class forth_step(iota2_step.step):
    def __init__(self, running_directory: str):
        super(forth_step, self).__init__()
        self.running_directory = running_directory
        self.log_dir = os.path.join(self.running_directory, "logs")
        if not os.path.exists(self.log_dir):
            os.mkdir(self.log_dir)
        self.execution_mode = "cluster"
        self.step_resources = {"cpu": 1, "ram": "5Gb", "walltime": "04:00:00"}

        # useful to get last tasks to triggered
        self.step_tasks = []

        # can comes from a dedicated function
        step_params_from_model_name = {
            "1": {
                "f":
                self.generate_database,
                "region_name":
                "1",
                "check_file_1":
                os.path.join(self.running_directory, "dask_fonction_c1.txt"),
                "check_file_2":
                os.path.join(self.running_directory, "dask_fonction_c2.txt"),
                "output_file":
                os.path.join(self.running_directory, "dask_fonction_d1.txt"),
                "sleeping_time":
                10
            },
            "2": {
                "f":
                self.generate_database,
                "region_name":
                "2",
                "check_file_1":
                os.path.join(self.running_directory, "dask_fonction_c1.txt"),
                "check_file_2":
                os.path.join(self.running_directory, "dask_fonction_c2.txt"),
                "output_file":
                os.path.join(self.running_directory, "dask_fonction_d2.txt"),
                "sleeping_time":
                10
            }
        }
        # then, build dependency tree
        for model_name, model_meta in self.list_models.items():
            task = self.i2_task(
                task_name=f"learn_model_{model_name}",
                log_dir=self.log_dir,
                execution_mode=self.execution_mode,
                task_parameters=step_params_from_model_name[model_name],
                task_resources=self.step_resources)
            task_in_graph = self.add_task_to_i2_processing_graph(
                task,
                task_group="region_task",
                task_sub_group=model_name,
                task_dep_group="tile_tasks",
                task_dep_sub_group=model_meta["tiles"])
            self.step_tasks.append(task_in_graph)

    def generate_database(self,
                          region_name: str,
                          check_file_1: str,
                          check_file_2: str,
                          output_file: str,
                          sleeping_time: Optional[int] = 1,
                          LOGGER=LOGGER):
        """
        """
        import time
        if not os.path.exists(check_file_1) and not os.path.exists(
                check_file_2):
            raise IOError(f"{check_file_1} or {check_file_2} is missing")
        LOGGER.warning(
            f"simulation database generation of model {region_name} in {sleeping_time} seconds, write resulsts in {output_file}"
        )
        if os.path.exists(output_file):
            os.remove(output_file)
        with open(output_file, "w") as database_file:
            database_file.write("samples done")
        time.sleep(sleeping_time)
        LOGGER.warning(f"database generated")
