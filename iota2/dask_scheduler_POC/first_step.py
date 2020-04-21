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


class first_step(iota2_step.step):
    def __init__(self, running_directory: str):
        super(first_step, self).__init__()
        self.running_directory = running_directory
        self.log_dir = os.path.join(self.running_directory, "logs")
        if not os.path.exists(self.log_dir):
            os.mkdir(self.log_dir)
        self.execution_mode = "cluster"
        self.step_resources = {"cpu": 1, "ram": "5Gb", "walltime": "01:00:00"}

        # useful to get last tasks to triggered
        self.step_tasks = []

        dir_task = self.i2_task(task_name="gen_dir",
                                log_dir=self.log_dir,
                                execution_mode=self.execution_mode,
                                task_parameters={
                                    "f":
                                    self.generate_directories,
                                    "output_file":
                                    os.path.join(self.running_directory,
                                                 "dask_fonction_a.txt"),
                                    "sleeping_time":
                                    1
                                },
                                task_resources=self.step_resources)

        # then build dep tree
        task_in_graph = self.add_task_to_i2_processing_graph(
            dir_task, "first_task")
        self.step_tasks.append(task_in_graph)

    def generate_directories(self,
                             output_file: str,
                             sleeping_time: Optional[int] = 5,
                             LOGGER=LOGGER):
        """simulating iota2 directories generation
        """
        import time
        LOGGER.warning(
            f"simulating directories generation by writing {output_file} in {sleeping_time} seconds"
        )
        if os.path.exists(output_file):
            os.remove(output_file)
        with open(output_file, "w") as out_file:
            out_file.write("ecriture du fichier par premiere_fonction")
        time.sleep(sleeping_time)
        LOGGER.warning(f"TMPDIR = {os.environ.get('TMPDIR')}")
        LOGGER.warning("directories generation simulation done")
