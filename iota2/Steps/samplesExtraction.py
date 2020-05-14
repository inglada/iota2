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
from functools import partial

from iota2.Steps import IOTA2Step
from iota2.Common import ServiceConfigFile as SCF
from iota2.Cluster import get_RAM
from iota2.Sampling import VectorSampler as vs


class samplesExtraction(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "vectorSampler"
        super(samplesExtraction, self).__init__(cfg, cfg_resources_file,
                                                resources_block_name)
        # step variables
        self.working_directory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.ram_extraction = 1024.0 * get_RAM(self.resources["ram"])
        self.custom_features = SCF.serviceConfigFile(
            self.cfg).checkCustomFeature()
        if self.custom_features:
            self.number_of_chunks = SCF.serviceConfigFile(self.cfg).getParam(
                'external_features', "number_of_chunks")
            self.chunk_size_mode = SCF.serviceConfigFile(self.cfg).getParam(
                'external_features', "chunk_size_mode")
        # implement tests for check if custom features are well provided
        # so the chain failed during step init

        self.execution_mode = "cluster"
        output_path_annual = None
        annual_config_file = SCF.serviceConfigFile(self.cfg).getParam(
            'argTrain', 'prevFeatures')
        if annual_config_file is not None and not "none" in annual_config_file.lower(
        ):
            output_path_annual = SCF.serviceConfigFile(
                annual_config_file).getParam('chain', 'outputPath')

        suffix_list = ["usually"]
        if SCF.serviceConfigFile(self.cfg).getParam(
                'argTrain', 'dempster_shafer_SAR_Opt_fusion') is True:
            suffix_list.append("SAR")
        for suffix in suffix_list:
            for tile in self.tiles:
                task_name = f"extraction_{tile}"
                if suffix == "SAR":
                    task_name += f"_{suffix}"

                parameters_dic = {
                    "f":
                    vs.generate_samples,
                    "train_shape_dic": {
                        f"{suffix}":
                        os.path.join(self.output_path, "formattingVectors",
                                     f"{tile}.shp")
                    },
                    "path_wd":
                    self.working_directory,
                    "data_field":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'chain', 'dataField'),
                    "output_path":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'chain', 'outputPath'),
                    "annual_crop":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'argTrain', 'annualCrop'),
                    "crop_mix":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'argTrain', 'cropMix'),
                    "auto_context_enable":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'chain', 'enable_autoContext'),
                    "region_field":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'chain', 'regionField'),
                    "proj":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'GlobChain', 'proj'),
                    "enable_cross_validation":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'chain', 'enableCrossValidation'),
                    "runs":
                    SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs'),
                    "sensors_parameters":
                    SCF.iota2_parameters(
                        self.cfg).get_sensors_parameters(tile),
                    "sar_optical_post_fusion":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'argTrain', 'dempster_shafer_SAR_Opt_fusion'),
                    "samples_classif_mix":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'argTrain', 'samplesClassifMix'),
                    "output_path_annual":
                    output_path_annual,
                    "ram":
                    self.ram_extraction,
                    "w_mode":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'GlobChain', 'writeOutputs'),
                    "folder_annual_features":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'argTrain', 'outputPrevFeatures'),
                    "previous_classif_path":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'argTrain', 'annualClassesExtractionSource'),
                    "validity_threshold":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'argTrain', 'validityThreshold'),
                    "target_resolution":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'chain', 'spatialResolution')
                }
                if self.custom_features:
                    parameters_dic["custom_features"] = True
                    parameters_dic["module_path"] = SCF.serviceConfigFile(
                        self.cfg).getParam('external_features', 'module')
                    parameters_dic["list_functions"] = SCF.serviceConfigFile(
                        self.cfg).getParam('external_features',
                                           'functions').split(" ")
                    parameters_dic[
                        "force_standard_labels"] = SCF.serviceConfigFile(
                            self.cfg).getParam('chain',
                                               'force_standard_labels')
                    parameters_dic["number_of_chunks"] = self.number_of_chunks
                    parameters_dic["chunk_size_mode"] = self.chunk_size_mode
                    parameters_dic[
                        "custom_write_mode"] = SCF.serviceConfigFile(
                            self.cfg).getParam('external_features',
                                               "custom_write_mode")
                    for target_chunk in range(self.number_of_chunks):

                        parameters_dic_chunk = parameters_dic.copy()
                        parameters_dic_chunk["targeted_chunk"] = target_chunk
                        task_name_chunk = f"{task_name}_chunk_{target_chunk}"
                        task = self.i2_task(
                            task_name=task_name_chunk,
                            log_dir=self.log_step_dir,
                            execution_mode=self.execution_mode,
                            task_parameters=parameters_dic_chunk,
                            task_resources=self.resources)
                        self.add_task_to_i2_processing_graph(
                            task,
                            task_group="tile_tasks",
                            task_sub_group=
                            f"{tile}_chunk_{target_chunk}_{suffix}",
                            task_dep_group="tile_tasks",
                            task_dep_sub_group=[tile])
                else:
                    task = self.i2_task(task_name=task_name,
                                        log_dir=self.log_step_dir,
                                        execution_mode=self.execution_mode,
                                        task_parameters=parameters_dic,
                                        task_resources=self.resources)
                    self.add_task_to_i2_processing_graph(
                        task,
                        task_group="tile_tasks",
                        task_sub_group=f"{tile}_{suffix}",
                        task_dep_group="tile_tasks",
                        task_dep_sub_group=[tile])

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Extract pixels values by tiles")
        return description
