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
                'Features', "number_of_chunks")
            self.chunk_size_mode = SCF.serviceConfigFile(self.cfg).getParam(
                'Features', "chunk_size_mode")

        # implement tests for check if custom features are well provided
        # so the chain failed during step init
    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Extract pixels values by tiles")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        list_shapefiles = vs.get_vectors_to_sample(
            os.path.join(self.output_path, "formattingVectors"),
            SCF.serviceConfigFile(self.cfg).getParam(
                'argTrain', 'dempster_shafer_SAR_Opt_fusion'))
        annual_config_file = SCF.serviceConfigFile(self.cfg).getParam(
            'argTrain', 'prevFeatures')
        output_path_annual = None
        if annual_config_file is not None and not "none" in annual_config_file.lower(
        ):
            output_path_annual = SCF.serviceConfigFile(
                annual_config_file).getParam('chain', 'outputPath')

        if self.custom_features:
            print(list_shapefiles[0])
            sensors_params = SCF.iota2_parameters(
                self.cfg).get_sensors_parameters(
                    os.path.splitext(
                        os.path.basename(
                            list(list_shapefiles[0].items())[0][1]))[0])
            parameters = []
            for shape in list_shapefiles:
                param = {
                    "train_shape_dic":
                    shape,
                    "path_wd":
                    self.workingDirectory,
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
                    sensors_params,
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
                        'chain', 'spatialResolution'),
                    "test_mode":
                    None,
                    "custom_features":
                    True,
                    "code_path":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'Features', 'codePath'),
                    "module_name":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'Features', 'namefile'),
                    "list_functions":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'Features', 'functions').split(" "),
                    "force_standard_labels":
                    SCF.serviceConfigFile(self.cfg).getParam(
                        'chain', 'force_standard_labels'),
                    "number_of_chunks":
                    self.number_of_chunks,
                    "chunk_size_mode":
                    self.chunk_size_mode
                }
                for target_chunk in range(self.number_of_chunks):
                    param_d = param.copy()
                    param_d["targeted_chunk"] = target_chunk
                    parameters.append(param_d)
            print("activate")
        else:
            parameters = list_shapefiles[:]
        return parameters

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        annual_config_file = SCF.serviceConfigFile(self.cfg).getParam(
            'argTrain', 'prevFeatures')
        output_path_annual = None
        if annual_config_file is not None and not "none" in annual_config_file.lower(
        ):
            output_path_annual = SCF.serviceConfigFile(
                annual_config_file).getParam('chain', 'outputPath')
        if self.custom_features:
            step_function = lambda x: vs.generate_samples(**x)
        else:
            step_function = lambda x: vs.generate_samples(
                x, self.workingDirectory,
                SCF.serviceConfigFile(self.cfg).getParam('chain', 'dataField'),
                SCF.serviceConfigFile(self.cfg).getParam(
                    'chain', 'outputPath'),
                SCF.serviceConfigFile(self.cfg).getParam(
                    'argTrain', 'annualCrop'),
                SCF.serviceConfigFile(self.cfg).getParam(
                    'argTrain', 'cropMix'),
                SCF.serviceConfigFile(self.cfg).getParam(
                    'chain', 'enable_autoContext'),
                SCF.serviceConfigFile(self.cfg).getParam(
                    'chain', 'regionField'),
                SCF.serviceConfigFile(self.cfg).getParam('GlobChain', 'proj'),
                SCF.serviceConfigFile(self.cfg).getParam(
                    'chain', 'enableCrossValidation'),
                SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs'),
                SCF.iota2_parameters(self.cfg).get_sensors_parameters(
                    os.path.splitext(os.path.basename(list(x.items())[0][1]))[
                        0]),
                SCF.serviceConfigFile(self.cfg).getParam(
                    'argTrain', 'dempster_shafer_SAR_Opt_fusion'),
                SCF.serviceConfigFile(self.cfg).getParam(
                    'argTrain', 'samplesClassifMix'), output_path_annual, self.
                ram_extraction,
                SCF.serviceConfigFile(self.cfg).getParam(
                    'GlobChain', 'writeOutputs'),
                SCF.serviceConfigFile(self.cfg).getParam(
                    'argTrain', 'outputPrevFeatures'),
                SCF.serviceConfigFile(self.cfg).getParam(
                    'argTrain', 'annualClassesExtractionSource'),
                SCF.serviceConfigFile(self.cfg).getParam(
                    'argTrain', 'validityThreshold'),
                SCF.serviceConfigFile(self.cfg).getParam(
                    'chain', 'spatialResolution'), None)
        return step_function

    def step_outputs(self):
        """
        """
        pass
