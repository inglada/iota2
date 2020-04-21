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
        self.execution_mode = "cluster"
        self.step_tasks = []
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
                task = self.i2_task(
                    task_name=f"extraction_{tile}_{suffix}",
                    log_dir=self.log_step_dir,
                    execution_mode=self.execution_mode,
                    task_parameters={
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
                        SCF.serviceConfigFile(self.cfg).getParam(
                            'chain', 'runs'),
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
                    },
                    task_resources=self.resources)
                task_in_graph = self.add_task_to_i2_processing_graph(
                    task,
                    task_group="tile_tasks",
                    task_sub_group=f"{tile}_{suffix}",
                    task_dep_group="tile_tasks",
                    task_dep_sub_group=[tile])
                self.step_tasks.append(task_in_graph)

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Extract pixels values by tiles")
        return description
