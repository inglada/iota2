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

from iota2.Steps import IOTA2Step
from iota2.Common import ServiceConfigFile as SCF
from iota2.Common.FileUtils import sortByFirstElem
from iota2.Sampling import SamplesSelection


class samplesByTiles(IOTA2Step.Step):
    def __init__(self,
                 cfg,
                 cfg_resources_file,
                 enable_autocontext,
                 workingDirectory=None):
        # heritage init
        resources_block_name = "samplesSelection_tiles"
        super(samplesByTiles, self).__init__(cfg, cfg_resources_file,
                                             resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.nb_runs = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'runs')
        self.execution_mode = "cluster"

        tiles_model_distribution_tmp = []
        for model_name, model_meta in self.spatial_models_distribution.items():
            for tile in model_meta["tiles"]:
                tiles_model_distribution_tmp.append((tile, model_name))
        tiles_model_distribution_tmp = sortByFirstElem(
            tiles_model_distribution_tmp)

        tiles_model_distribution = {}
        for tile_name, model_list in tiles_model_distribution_tmp:
            tiles_model_distribution[tile_name] = [
                f"{tile_name}_{model_name}_{seed}" for model_name in model_list
                for seed in range(self.nb_runs)
            ]
        model_distribution = {}
        for tile_name, model_list in tiles_model_distribution_tmp:
            model_distribution[tile_name] = [
                f"model_{model_name}_seed_{seed}" for model_name in model_list
                for seed in range(self.nb_runs)
            ]
        for tile in self.tiles:
            task = self.i2_task(task_name=f"merge_samples_{tile}",
                                log_dir=self.log_step_dir,
                                execution_mode=self.execution_mode,
                                task_parameters={
                                    "f":
                                    SamplesSelection.prepare_selection,
                                    "sample_sel_directory":
                                    os.path.join(self.output_path,
                                                 "samplesSelection"),
                                    "tile_name":
                                    tile,
                                    "workingDirectory":
                                    self.workingDirectory
                                },
                                task_resources=self.resources)
            dep_key = "tile_tasks_model" if enable_autocontext else "region_tasks"
            dep_values = tiles_model_distribution[
                tile] if enable_autocontext else model_distribution[tile]
            self.add_task_to_i2_processing_graph(
                task,
                task_group="tile_tasks",
                task_sub_group=tile,
                task_dep_dico={dep_key: dep_values})

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Split pixels selected to learn models by tiles")
        return description
