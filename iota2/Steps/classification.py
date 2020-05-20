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
from typing import Optional
from iota2.Steps import IOTA2Step
from iota2.Cluster import get_RAM
from iota2.Common import ServiceConfigFile as SCF
from iota2.Common import FileUtils as fut
from iota2.Classification import skClassifier
from iota2.Classification import ImageClassifier as imageClassifier
from iota2.Classification.ImageClassifier import autoContext_launch_classif


class classification(IOTA2Step.Step):
    # ~ TODO : find a smarted way to determine the attribute self.scikit_tile_split
    scikit_tile_split = 5

    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "classifications"

        super(classification, self).__init__(cfg, cfg_resources_file,
                                             resources_block_name)

        # step variables
        self.custom_features = SCF.serviceConfigFile(
            self.cfg).checkCustomFeature()
        if self.custom_features:
            self.number_of_chunks = SCF.serviceConfigFile(self.cfg).getParam(
                'external_features', "number_of_chunks")
        self.working_directory = workingDirectory
        self.autoContext_iterations = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'autoContext_iterations')
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.nomenclature_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'nomenclaturePath')
        self.data_field = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'dataField')
        self.enable_autoContext = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'enable_autoContext')
        self.RAM = 1024.0 * get_RAM(self.resources["ram"])
        self.use_scikitlearn = SCF.serviceConfigFile(self.cfg).getParam(
            'scikit_models_parameters', 'model_type') is not None
        self.runs = SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs')
        self.classifier = SCF.serviceConfigFile(self.cfg).getParam(
            'argTrain', 'classifier')
        self.available_ram = 1024.0 * get_RAM(self.resources["ram"])

        self.pixel_type = fut.getOutputPixType(self.nomenclature_path)

        self.execution_mode = "cluster"
        self.suffix_list = ["usually"]
        if SCF.serviceConfigFile(self.cfg).getParam(
                'argTrain', 'dempster_shafer_SAR_Opt_fusion') is True:
            self.suffix_list.append("SAR")

        for suffix in self.suffix_list:
            for model_name, model_meta in self.spatial_models_distribution.items(
            ):
                for seed in range(self.runs):
                    for tile in model_meta["tiles"]:
                        task_name = f"classification_{tile}_model_{model_name}_seed_{seed}"
                        if suffix == "SAR":
                            task_name += "_SAR"
                        target_model = f"model_{model_name}_seed_{seed}_{suffix}"
                        task_params = self.get_classification_params(
                            model_name, tile, seed, suffix)
                        if self.enable_autoContext is False and (
                                self.use_scikitlearn is True
                                or self.custom_features):
                            # TODO: mutualize between scikit and custom features
                            chunk_number = self.scikit_tile_split if not self.custom_features else self.number_of_chunks
                            for chunk in range(chunk_number):
                                task_params = self.get_classification_params(
                                    model_name, tile, seed, suffix, chunk)
                                task = self.i2_task(
                                    task_name=f"{task_name}_{chunk}",
                                    log_dir=self.log_step_dir,
                                    execution_mode=self.execution_mode,
                                    task_parameters=task_params,
                                    task_resources=self.resources)
                                self.add_task_to_i2_processing_graph(
                                    task,
                                    task_group="tile_tasks_model_mode",
                                    task_sub_group=
                                    f"{tile}_{model_name}_{seed}_{suffix}_{chunk}",
                                    task_dep_dico={
                                        "region_tasks": [target_model]
                                    })
                        else:
                            task = self.i2_task(
                                task_name=task_name,
                                log_dir=self.log_step_dir,
                                execution_mode=self.execution_mode,
                                task_parameters=task_params,
                                task_resources=self.resources)
                            self.add_task_to_i2_processing_graph(
                                task,
                                task_group="tile_tasks_model_mode",
                                task_sub_group=
                                f"{tile}_{model_name}_{seed}_{suffix}",
                                task_dep_dico={"region_tasks": [target_model]})

    def get_classification_params(self,
                                  region_name: str,
                                  tile_name: str,
                                  seed: int,
                                  suffix: str,
                                  target_chunk: Optional[int] = None):

        param = None
        region_mask_name = region_name.split("f")[0]
        target_model_name = f"model_{region_name}_seed_{seed}.txt"
        classif_file = os.path.join(
            self.output_path, "classif",
            f"Classif_{tile_name}_model_{region_name}_seed_{seed}.tif")
        confidence_file = os.path.join(
            self.output_path, "classif",
            f"{tile_name}_model_{region_name}_confidence_seed_{seed}.tif")
        if suffix == "SAR":
            target_model_name = target_model_name.replace(".txt", "_SAR.txt")
            classif_file = classif_file.replace(".tif", "_SAR.tif")
            confidence_file = confidence_file.replace(".tif", "_SAR.tif")
        classif_mask_file = os.path.join(
            self.output_path, "classif", "MASK",
            f"MASK_region_{region_mask_name}_{tile_name}.tif")
        model_file = os.path.join(self.output_path, "model", target_model_name)
        stats_file = None

        if "svm" in self.classifier:
            stats_file = os.path.join(self.output_path, "stats",
                                      f"Model_{region_name}_seed_{seed}.xml")

        if self.enable_autoContext is False and self.use_scikitlearn is False:
            param = {
                "f":
                imageClassifier.launchClassification,
                "Classifmask":
                classif_mask_file,
                "model":
                model_file,
                "stats":
                stats_file,
                "outputClassif":
                classif_file,
                "pathWd":
                self.working_directory,
                "classifier_type":
                self.classifier,
                "tile":
                tile_name,
                "proba_map_expected":
                SCF.serviceConfigFile(self.cfg).getParam(
                    'argClassification', 'enable_probability_map'),
                "dimred":
                SCF.serviceConfigFile(self.cfg).getParam('dimRed', 'dimRed'),
                "sar_optical_post_fusion":
                SCF.serviceConfigFile(self.cfg).getParam(
                    'argTrain', 'dempster_shafer_SAR_Opt_fusion'),
                "output_path":
                self.output_path,
                "data_field":
                self.data_field,
                "write_features":
                SCF.serviceConfigFile(self.cfg).getParam(
                    'GlobChain', 'writeOutputs'),
                "reduction_mode":
                SCF.serviceConfigFile(self.cfg).getParam(
                    'dimRed', 'reductionMode'),
                "sensors_parameters":
                SCF.iota2_parameters(
                    self.cfg).get_sensors_parameters(tile_name),
                "pixType":
                self.pixel_type,
                "RAM":
                self.available_ram,
                "auto_context":
                False
            }
            if self.custom_features:
                param["custom_features"] = True
                param["module_path"] = SCF.serviceConfigFile(
                    self.cfg).getParam('external_features', 'module')
                param["number_of_chunks"] = self.number_of_chunks
                param["chunk_size_mode"] = SCF.serviceConfigFile(
                    self.cfg).getParam('external_features', 'chunk_size_mode')
                param["chunk_size_x"] = SCF.serviceConfigFile(
                    self.cfg).getParam('external_features', 'chunk_size_x')
                param["chunk_size_y"] = SCF.serviceConfigFile(
                    self.cfg).getParam('external_features', 'chunk_size_y')
                param["targeted_chunk"] = target_chunk
                param["list_functions"] = SCF.serviceConfigFile(
                    self.cfg).getParam("external_features",
                                       "functions").split(" ")
                param["force_standard_labels"] = SCF.serviceConfigFile(
                    self.cfg).getParam('external_features', 'module')

        elif self.enable_autoContext is True and self.use_scikitlearn is False:
            param = {
                "f":
                autoContext_launch_classif,
                "parameters_dict": {
                    "model_name":
                    region_name,
                    "seed_num":
                    seed,
                    "tile":
                    tile_name,
                    "tile_segmentation":
                    os.path.join(self.output_path, "features", tile_name,
                                 "tmp", f"SLIC_{tile_name}.tif"),
                    "tile_mask":
                    classif_mask_file,
                    "model_list": [
                        os.path.join(self.output_path, "model",
                                     f"model_{region_name}_seed_{seed}",
                                     f"model_it_{auto_it}.rf")
                        for auto_it in range(self.autoContext_iterations)
                    ]
                },
                "classifier_type":
                self.classifier,
                "tile":
                tile_name,
                "proba_map_expected":
                SCF.serviceConfigFile(self.cfg).getParam(
                    'argClassification', 'enable_probability_map'),
                "dimred":
                SCF.serviceConfigFile(self.cfg).getParam('dimRed', 'dimRed'),
                "data_field":
                self.data_field,
                "write_features":
                SCF.serviceConfigFile(self.cfg).getParam(
                    'GlobChain', 'writeOutputs'),
                "reduction_mode":
                SCF.serviceConfigFile(self.cfg).getParam(
                    'dimRed', 'reductionMode'),
                "iota2_run_dir":
                self.output_path,
                "sar_optical_post_fusion":
                SCF.serviceConfigFile(self.cfg).getParam(
                    'argTrain', 'dempster_shafer_SAR_Opt_fusion'),
                "nomenclature_path":
                self.nomenclature_path,
                "sensors_parameters":
                SCF.iota2_parameters(
                    self.cfg).get_sensors_parameters(tile_name),
                "RAM":
                self.available_ram,
                "WORKING_DIR":
                self.working_directory
            }

        elif self.enable_autoContext is False and self.use_scikitlearn is True:
            param = {
                "f":
                skClassifier.predict,
                "mask":
                classif_mask_file,
                "model":
                model_file,
                "stat":
                stats_file,
                "out_classif":
                classif_file,
                "out_confidence":
                confidence_file,
                "out_proba":
                None,
                "working_dir":
                self.working_directory,
                "tile_name":
                tile_name,
                "sar_optical_post_fusion":
                SCF.serviceConfigFile(self.cfg).getParam(
                    'argTrain', 'dempster_shafer_SAR_Opt_fusion'),
                "output_path":
                SCF.serviceConfigFile(self.cfg).getParam(
                    'chain', 'outputPath'),
                "sensors_parameters":
                SCF.iota2_parameters(
                    self.cfg).get_sensors_parameters(tile_name),
                "pixel_type":
                self.pixel_type,
                "number_of_chunks":
                self.scikit_tile_split,
                "targeted_chunk":
                target_chunk,
                "ram":
                self.available_ram
            }

        return param

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Generate classifications")
        return description
