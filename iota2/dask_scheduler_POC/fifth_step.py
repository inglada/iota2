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


class fifth_step(step):
    """simulate classification stage"""
    def __init__(self, running_directory: str):
        super(fifth_step, self).__init__()
        self.running_directory = running_directory
        self.log_dir = os.path.join(self.running_directory, "logs")
        if not os.path.exists(self.log_dir):
            os.mkdir(self.log_dir)
        self.execution_mode = "cluster"
        self.step_resources = {"cpu": 1, "ram": "5Gb", "walltime": "05:00:00"}
        # useful to get last tasks to triggered
        self.step_tasks = []

        step_params_from_tile_model = {
            "T31TCJ_1": {
                "f":
                self.classification,
                "in_model_file":
                os.path.join(self.running_directory, "dask_fonction_d1.txt"),
                "out_classif_file":
                os.path.join(self.running_directory, "classif_T31TCJ_m1.txt"),
                "sleeping_time":
                1
            },
            "T31TDJ_1": {
                "f":
                self.classification,
                "in_model_file":
                os.path.join(self.running_directory, "dask_fonction_d1.txt"),
                "out_classif_file":
                os.path.join(self.running_directory, "classif_T31TDJ_m1.txt"),
                "sleeping_time":
                1
            },
            "T31TDJ_2": {
                "f":
                self.classification,
                "in_model_file":
                os.path.join(self.running_directory, "dask_fonction_d2.txt"),
                "out_classif_file":
                os.path.join(self.running_directory, "classif_T31TDJ_m2.txt"),
                "sleeping_time":
                1
            }
        }
        for model_name, model_meta in self.list_models.items():
            for tile in model_meta["tiles"]:
                task = self.i2_task(
                    task_name=f"classif_m{model_name}_{tile}",
                    log_dir=self.log_dir,
                    execution_mode=self.execution_mode,
                    task_parameters=step_params_from_tile_model[
                        f"{tile}_{model_name}"],
                    task_resources=self.step_resources)
                task_in_graph = self.add_task_to_i2_processing_graph(
                    task,
                    task_group="tile_model",
                    task_sub_group=f"{tile}_{model_name}",
                    task_dep_group="region_task",
                    task_dep_sub_group=model_name)
                self.step_tasks.append(task_in_graph)

    def classification(self,
                       in_model_file: str,
                       out_classif_file: str,
                       sleeping_time: Optional[int] = 5,
                       logger=LOGGER):
        """simulate the classification of one tile
        """
        import time
        if not os.path.exists(in_model_file):
            raise IOError(
                f"model file {in_model_file} does not exists, cannot generate classification {out_classif_file}"
            )
        logger.warning(
            f"generating classificaiton : {out_classif_file} thanks to model {in_model_file}"
        )
        if os.path.exists(out_classif_file):
            os.remove(out_classif_file)
        with open(out_classif_file, "w") as out_file:
            out_file.write(f"clasificaton with many interesting classes")
        time.sleep(sleeping_time)
        LOGGER.warning(f"classification of {out_classif_file} DONE")
