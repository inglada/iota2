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
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.ram_extraction = 1024.0 * get_RAM(self.resources["ram"])
        # read config file to init custom features and check validity
        self.custom_features = SCF.serviceConfigFile(
            self.cfg).checkCustomFeature()
        if self.custom_features:
            self.number_of_chunks = SCF.serviceConfigFile(self.cfg).getParam(
                'external_features', "number_of_chunks")
            self.chunk_size_mode = SCF.serviceConfigFile(self.cfg).getParam(
                'external_features', "chunk_size_mode")

        # implement tests for check if custom features are well provided
        # so the chain failed during step init
    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Extract pixels values by tiles")
        return description

    def step_inputs(self):
        # found all shapes
        list_shapefiles = vs.get_vectors_to_sample(
            os.path.join(self.output_path, "formattingVectors"),
            SCF.serviceConfigFile(self.cfg).getParam(
                'argTrain', 'dempster_shafer_SAR_Opt_fusion'))
        # check if prevFeatures is enabled
        annual_config_file = SCF.serviceConfigFile(self.cfg).getParam(
            'argTrain', 'prevFeatures')
        output_path_annual = None
        if (annual_config_file is not None
                and "none" not in annual_config_file.lower()):
            output_path_annual = SCF.serviceConfigFile(
                annual_config_file).getParam('chain', 'outputPath')
        # Initialize the sensors dictionnary with the first tile found
        # Sensors are the same for all tiles
        sensors_params = SCF.iota2_parameters(self.cfg).get_sensors_parameters(
            os.path.splitext(
                os.path.basename(list(list_shapefiles[0].items())[0][1]))[0])
        inv_dict = {
            "path_wd":
            self.workingDirectory,
            "data_field":
            SCF.serviceConfigFile(self.cfg).getParam('chain', 'dataField'),
            "output_path":
            SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath'),
            "annual_crop":
            SCF.serviceConfigFile(self.cfg).getParam('argTrain', 'annualCrop'),
            "crop_mix":
            SCF.serviceConfigFile(self.cfg).getParam('argTrain', 'cropMix'),
            "auto_context_enable":
            SCF.serviceConfigFile(self.cfg).getParam('chain',
                                                     'enable_autoContext'),
            "region_field":
            SCF.serviceConfigFile(self.cfg).getParam('chain', 'regionField'),
            "proj":
            SCF.serviceConfigFile(self.cfg).getParam('GlobChain', 'proj'),
            "enable_cross_validation":
            SCF.serviceConfigFile(self.cfg).getParam('chain',
                                                     'enableCrossValidation'),
            "runs":
            SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs'),
            "sensors_parameters":
            sensors_params,
            "sar_optical_post_fusion":
            SCF.serviceConfigFile(self.cfg).getParam(
                'argTrain', 'dempster_shafer_SAR_Opt_fusion'),
            "samples_classif_mix":
            SCF.serviceConfigFile(self.cfg).getParam('argTrain',
                                                     'samplesClassifMix'),
            "ram":
            self.ram_extraction,
            "w_mode":
            SCF.serviceConfigFile(self.cfg).getParam('GlobChain',
                                                     'writeOutputs'),
            "folder_annual_features":
            SCF.serviceConfigFile(self.cfg).getParam('argTrain',
                                                     'outputPrevFeatures'),
            "previous_classif_path":
            SCF.serviceConfigFile(self.cfg).getParam(
                'argTrain', 'annualClassesExtractionSource'),
            "validity_threshold":
            SCF.serviceConfigFile(self.cfg).getParam('argTrain',
                                                     'validityThreshold'),
            "target_resolution":
            SCF.serviceConfigFile(self.cfg).getParam('chain',
                                                     'spatialResolution'),
            "test_mode":
            None,
            "output_path_annual":
            output_path_annual,
            "custom_features":
            False
        }
        if self.custom_features:
            param_custom_features = {
                "custom_features":
                True,
                "module_path":
                SCF.serviceConfigFile(self.cfg).getParam(
                    'external_features', 'module'),
                "list_functions":
                SCF.serviceConfigFile(self.cfg).getParam(
                    'external_features', 'functions').split(" "),
                "force_standard_labels":
                SCF.serviceConfigFile(self.cfg).getParam(
                    'chain', 'force_standard_labels'),
                "number_of_chunks":
                self.number_of_chunks,
                "chunk_size_mode":
                self.chunk_size_mode,
                "custom_write_mode":
                SCF.serviceConfigFile(self.cfg).getParam(
                    'external_features', "custom_write_mode")
            }
        else:
            param_custom_features = {}
        # Merge and update inv_dict with custom features parameters
        input_dict = {**inv_dict, **param_custom_features}
        # Create the parameter list
        parameters = []
        for shape in list_shapefiles:
            if self.custom_features:
                # Create as job as number of chunks requiered
                for target_chunk in range(self.number_of_chunks):
                    # avoid overwriting parameters
                    param_d = input_dict.copy()
                    param_d["train_shape_dic"] = shape
                    param_d["targeted_chunk"] = target_chunk
                    parameters.append(param_d)
            else:
                param_d = input_dict.copy()
                param_d["train_shape_dic"] = shape
                parameters.append(param_d)
        return parameters

    def step_execute(self):
        """ 
        Return
        ------
        lambda
        """
        return lambda x: vs.generate_samples(**x)

    def step_outputs(self):
        """
        """
        pass
