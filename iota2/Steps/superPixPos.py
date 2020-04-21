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
from iota2.Sampling.SuperPixelsSelection import merge_ref_super_pix


class superPixPos(IOTA2Step.Step):
    def __init__(self,
                 cfg: str,
                 cfg_resources_file: str,
                 workingDirectory: Optional[str] = None) -> None:
        """set up the step
        """
        from Common.FileUtils import FileSearch_AND

        # heritage init
        resources_block_name = "superPixPos"
        super(superPixPos, self).__init__(cfg, cfg_resources_file,
                                          resources_block_name)

        # step variables
        self.execution_mode = "cluster"
        self.step_tasks = []
        self.working_directory = workingDirectory
        self.execution_dir = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.superPix_field = "superpix"
        self.superPix_belong_field = "is_super_pix"
        self.region_field = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'regionField')
        self.data_field = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'dataField')
        self.ram = 1024.0 * get_RAM(self.resources["ram"])
        self.nb_runs = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'runs')
        self.sampling_labels_from_raster = {}
        if (SCF.serviceConfigFile(self.cfg).getParam('argTrain', 'cropMix')
                and SCF.serviceConfigFile(self.cfg).getParam(
                    'argTrain', 'samplesClassifMix')):
            source_dir = SCF.serviceConfigFile(self.cfg).getParam(
                'argTrain', 'annualClassesExtractionSource')

            annual_labels = SCF.serviceConfigFile(self.cfg).getParam(
                'argTrain', 'annualCrop')
            classification_raster = os.path.join(source_dir, "final",
                                                 "Classif_Seed_0.tif")
            validity_raster = os.path.join(source_dir, "final",
                                           "PixelsValidity.tif")
            val_thresh = SCF.serviceConfigFile(self.cfg).getParam(
                'argTrain', 'validityThreshold')
            region_mask_dir = os.path.join(self.execution_dir, "shapeRegion")
            self.sampling_labels_from_raster = {
                "annual_labels": annual_labels,
                "classification_raster": classification_raster,
                "validity_raster": validity_raster,
                "region_mask_directory": region_mask_dir,
                "val_threshold": val_thresh
            }
        for model_name, model_meta in self.spatial_models_distribution.items():
            for seed in range(self.nb_runs):
                for tile in model_meta["tiles"]:
                    target_model = f"model_{model_name}_seed_{seed}"
                    task = self.i2_task(
                        task_name=f"SP_{target_model}_{tile}",
                        log_dir=self.log_step_dir,
                        execution_mode=self.execution_mode,
                        task_parameters={
                            "f": merge_ref_super_pix,
                            "data": {
                                "SLIC":
                                os.path.join(self.execution_dir, "features",
                                             tile, "tmp", f"SLIC_{tile}.tif"),
                                "selection_samples":
                                os.path.join(
                                    self.execution_dir, "samplesSelection",
                                    f"{tile}_samples_region_{model_name}_seed_{seed}_selection.sqlite"
                                )
                            },
                            "DATAREF_FIELD_NAME": self.data_field,
                            "SP_FIELD_NAME": self.superPix_field,
                            "SP_BELONG_FIELD_NAME": self.superPix_belong_field,
                            "REGION_FIELD_NAME": self.region_field,
                            "sampling_labels_from_raster":
                            self.sampling_labels_from_raster,
                            "workingDirectory": self.working_directory,
                            "ram": self.ram
                        },
                        task_resources=self.resources)
                    task_in_graph = self.add_task_to_i2_processing_graph(
                        task,
                        task_group="tile_tasks_model",
                        task_sub_group=f"{tile}_{model_name}_{seed}",
                        task_dep_group="region_tasks",
                        task_dep_sub_group=[target_model])
                    self.step_tasks.append(task_in_graph)

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Add superPixels positions to reference data")
        return description
