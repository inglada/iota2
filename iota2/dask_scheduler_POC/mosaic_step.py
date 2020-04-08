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
from typing import Optional, List

from iota2_step import step

LOGGER = logging.getLogger(__name__)


class mosaic_step(step):
    """simulate classification stage"""
    def __init__(self, running_directory: str):
        super(mosaic_step, self).__init__()
        self.running_directory = running_directory
        self.log_dir = os.path.join(self.running_directory, "logs")
        if not os.path.exists(self.log_dir):
            os.mkdir(self.log_dir)
        # is the step can be run locally ("local") or must send to a cluster ("cluster")
        self.execution_mode = "cluster"
        self.step_resources = {"cpu": 1, "ram": "5Gb", "walltime": "07:00:00"}
        # useful to get last tasks to triggered
        self.step_tasks = []

        task = self.i2_task(task_name="mosaic",
                            log_dir=self.log_dir,
                            execution_mode=self.execution_mode,
                            task_parameters={
                                "f":
                                self.mosaic,
                                "classifications": [],
                                "out_mosaic":
                                os.path.join(self.running_directory,
                                             "final_mosaic.txt")
                            },
                            task_resources=self.step_resources)

        task_in_graph = self.add_task_to_i2_processing_graph(
            task,
            task_group="final",
            task_sub_group="mosaic",
            task_dep_group="tile_tasks",
            task_dep_sub_group=self.list_tiles)
        self.step_tasks.append(task_in_graph)

    def mosaic(self,
               classifications: List[str],
               out_mosaic: str,
               sleeping_time: Optional[int] = 5,
               logger=LOGGER):
        """simulate the classification of one tile
        """
        import time
        for classif in classifications:
            if not os.path.exists(classif):
                raise IOError(f"{classif} does not exists")

        logger.warning(f"generating mosaic : {out_mosaic}")
        if os.path.exists(out_mosaic):
            os.remove(out_mosaic)
        with open(out_mosaic, "w") as out_file:
            out_file.write("mosaic")
        time.sleep(sleeping_time)
        LOGGER.warning(f"mosaic : {out_mosaic} DONE")
