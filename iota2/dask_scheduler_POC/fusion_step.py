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


class fusion_step(step):
    """simulate classification stage"""
    def __init__(self, running_directory: str):
        super(fusion_step, self).__init__()
        self.running_directory = running_directory
        self.log_dir = os.path.join(self.running_directory, "logs")
        if not os.path.exists(self.log_dir):
            os.mkdir(self.log_dir)
        # is the step can be run locally ("local") or must send to a cluster ("cluster")
        self.execution_mode = "cluster"
        self.step_resources = {"cpu": 1, "ram": "5Gb", "walltime": "06:00:00"}
        # useful to get last tasks to triggered
        self.step_tasks = []

        step_params_from_tile_name = {
            "T31TCJ": {
                "f":
                self.fusion,
                "classifications": [],
                "out_classif_file":
                os.path.join(self.running_directory, "classif_T31TCJ_FUS.txt"),
                "sleeping_time":
                1
            },
            "T31TDJ": {
                "f":
                self.fusion,
                "classifications": [],
                "out_classif_file":
                os.path.join(self.running_directory, "classif_T31TDJ_FUS.txt"),
                "sleeping_time":
                1
            }
        }
        for tile in self.list_tiles:
            task = self.i2_task(
                task_name=f"fusion_{tile}",
                log_dir=self.log_dir,
                execution_mode=self.execution_mode,
                task_parameters=step_params_from_tile_name[tile],
                task_resources=self.step_resources)

            # build dependencies we need, a list of strings
            tile_model_couples = []
            for model_name, model_meta in self.list_models.items():
                for tile_name in model_meta["tiles"]:
                    if tile_name == tile:
                        tile_model_couples.append(f"{tile}_{model_name}")

            task_in_graph = self.add_task_to_i2_processing_graph(
                task,
                task_group="tile_tasks",
                task_sub_group=tile,
                task_dep_group="tile_model",
                task_dep_sub_group=tile_model_couples)
            self.step_tasks.append(task_in_graph)

    def fusion(self,
               classifications: List[str],
               out_classif_file: str,
               sleeping_time: Optional[int] = 5,
               logger=LOGGER):
        """simulate the classification of one tile
        """
        import time
        for classif in classifications:
            if not os.path.exists(classif):
                raise IOError(f"{classif} does not exists")

        logger.warning(
            f"generating classificaiton fusion : {out_classif_file}")
        if os.path.exists(out_classif_file):
            os.remove(out_classif_file)
        with open(out_classif_file, "w") as out_file:
            out_file.write(f"clasificaton fusion")
        time.sleep(sleeping_time)
        LOGGER.warning(f"classification fusion : {out_classif_file} DONE")
