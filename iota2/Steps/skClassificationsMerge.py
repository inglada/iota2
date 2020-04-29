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
from typing import Tuple, List
from iota2.Steps import classification
from iota2.Steps import IOTA2Step
from iota2.Common import ServiceConfigFile
from iota2.Classification.skClassifier import merge_sk_classifications


class ScikitClassificationsMerge(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, working_directory=None):
        # heritage init
        resources_block_name = "mergeClassifications"
        super(ScikitClassificationsMerge,
              self).__init__(cfg, cfg_resources_file, resources_block_name)

        # step variables
        self.number_of_chunks = classification.classification.scikit_tile_split
        self.execution_mode = "cluster"
        self.working_directory = working_directory
        self.output_path = ServiceConfigFile.serviceConfigFile(
            self.cfg).getParam('chain', 'outputPath')
        self.runs = ServiceConfigFile.serviceConfigFile(self.cfg).getParam(
            'chain', 'runs')
        self.epsg_code = int(
            ServiceConfigFile.serviceConfigFile(self.cfg).getParam(
                'GlobChain', 'proj').split(":")[-1])
        self.use_scikitlearn = ServiceConfigFile.serviceConfigFile(
            self.cfg).getParam('scikit_models_parameters',
                               'model_type') is not None
        self.suffix_list = ["usually"]
        if ServiceConfigFile.serviceConfigFile(self.cfg).getParam(
                'argTrain', 'dempster_shafer_SAR_Opt_fusion') is True:
            self.suffix_list.append("SAR")
        for suffix in self.suffix_list:
            for model_name, model_meta in self.spatial_models_distribution.items(
            ):
                for seed in range(self.runs):
                    for tile in model_meta["tiles"]:
                        suff = ""
                        if suffix == "SAR":
                            suff = "_SAR"
                        task_parameters = self.get_param(
                            model_name, seed, suffix, tile)
                        task = self.i2_task(
                            task_name=
                            f"classif_confidence_{tile}_model_{model_name}_mosaic{suff}",
                            log_dir=self.log_step_dir,
                            execution_mode=self.execution_mode,
                            task_parameters=task_parameters,
                            task_resources=self.resources)

                        self.add_task_to_i2_processing_graph(
                            task,
                            task_group="tile_tasks_model",
                            task_sub_group=f"{tile}_{model_name}_{seed}",
                            task_dep_group="tile_tasks_model",
                            task_dep_sub_group=[
                                f"{tile}_{model_name}_{seed}_{chunk}"
                                for chunk in range(self.number_of_chunks)
                            ])

    def get_param(self, model_name: str, seed: int, suffix: str,
                  tile_name: str) -> Tuple[List[str], str]:
        """
        """
        param = None
        classification_files = []
        confidence_files = []
        sar_suff = ""
        if suffix == "SAR":
            sar_suff = "SAR_"
        for chunk in range(self.number_of_chunks):
            classification_files.append(
                os.path.join(
                    self.output_path, "classif",
                    f"Classif_{tile_name}_model_{model_name}_seed_{seed}_{sar_suff}SUBREGION_{chunk}.tif"
                ))
            confidence_files.append(
                os.path.join(
                    self.output_path, "classif",
                    f"{tile_name}_model_{model_name}_confidence_seed_{seed}_{sar_suff}SUBREGION_{chunk}.tif"
                ))
        classif_mosaic = os.path.join(
            self.output_path, "classif",
            f"Classif_{tile_name}_model_{model_name}_seed_{seed}.tif")
        confidence_mosaic = os.path.join(
            self.output_path, "classif",
            f"{tile_name}_model_{model_name}_confidence_seed_{seed}.tif")
        if suffix == "SAR":
            classif_mosaic = classif_mosaic.replace(".tif", "_SAR.tif")
            confidence_mosaic = confidence_mosaic.replace(".tif", "_SAR.tif")
        param = {
            "f": merge_sk_classifications,
            "rasters_to_merge": (classification_files, confidence_files),
            "mosaic_file": (classif_mosaic, confidence_mosaic),
            "epsg_code": self.epsg_code,
            "working_dir": self.working_directory
        }
        return param

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Merge tile's classification's part")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from iota2.Classification.skClassifier import sk_classifications_to_merge
        parameters = sk_classifications_to_merge(
            os.path.join(self.output_path, "classif"))
        # ~ in order to get only one task and iterate over raster to merge
        parameters = [parameters]
        return parameters

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from iota2.Classification.skClassifier import merge_sk_classifications
        step_function = lambda x: merge_sk_classifications(
            x, self.epsg_code, self.working_directory)
        return step_function

    def step_clean(self):
        """
        """
        from iota2.Classification.skClassifier import sk_classifications_to_merge
        rasters = sk_classifications_to_merge(
            os.path.join(self.output_path, "classif"))
        for rasters_already_merged in rasters:
            for raster in rasters_already_merged["rasters_list"]:
                os.remove(raster)

    def step_outputs(self):
        """
        """
        pass
