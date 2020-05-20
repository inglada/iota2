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
from typing import Optional, TypeVar, Generic

from iota2.Steps import IOTA2Step
from iota2.Common import ServiceConfigFile as SCF
from iota2.Cluster import get_RAM
from iota2.Sampling.SplitSamples import split_superpixels_and_reference


class superPixSplit(IOTA2Step.Step):
    def __init__(self,
                 cfg: str,
                 cfg_resources_file: str,
                 workingDirectory: Optional[str] = None) -> None:
        """set up the step
        """
        # heritage init
        resources_block_name = "superPixSplit"
        super(superPixSplit, self).__init__(cfg, cfg_resources_file,
                                            resources_block_name)

        # step variables
        self.working_directory = workingDirectory
        self.execution_dir = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.is_superPix_field = "is_super_pix"
        self.region_field = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'regionField')
        self.nb_runs = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'runs')
        self.ram = 1024.0 * get_RAM(self.resources["ram"])
        self.execution_mode = "cluster"

        suffix_list = ["usually"]
        if SCF.serviceConfigFile(self.cfg).getParam(
                'argTrain', 'dempster_shafer_SAR_Opt_fusion') is True:
            suffix_list.append("SAR")
        for suffix in suffix_list:
            for model_name, model_meta in self.spatial_models_distribution.items(
            ):
                for seed in range(self.nb_runs):
                    for tile in model_meta["tiles"]:
                        in_file_name = f"{tile}_region_{model_name}_seed{seed}_Samples_learn.sqlite"
                        if suffix == "SAR":
                            in_file_name = f"{tile}_region_{model_name}_seed{seed}_Samples_SAR_learn.sqlite"
                        task = self.i2_task(
                            task_name=
                            f"superpix_split_{tile}_{model_name}_seed_{seed}_{suffix}",
                            log_dir=self.log_step_dir,
                            execution_mode=self.execution_mode,
                            task_parameters={
                                "f":
                                split_superpixels_and_reference,
                                "vector_file":
                                os.path.join(self.execution_dir,
                                             "learningSamples", in_file_name),
                                "superpix_column":
                                self.is_superPix_field,
                                "working_dir":
                                self.working_directory
                            },
                            task_resources=self.resources)
                        self.add_task_to_i2_processing_graph(
                            task,
                            task_group="tile_tasks_model",
                            task_sub_group=
                            f"{tile}_{model_name}_seed_{seed}_{suffix}",
                            task_dep_dico={"tile_tasks": [f"{tile}_{suffix}"]})

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = (
            "Generate two data sets, one dedicated to superpixels one to reference data"
        )
        return description
