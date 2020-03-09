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
        return vs.get_vectors_to_sample(
            os.path.join(self.output_path, "formattingVectors"),
            SCF.serviceConfigFile(self.cfg).getParam(
                'argTrain', 'dempster_shafer_SAR_Opt_fusion'))

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
        step_function = lambda x: vs.generate_samples(
            x, self.workingDirectory,
            SCF.serviceConfigFile(self.cfg).getParam('chain', 'dataField'),
            SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath'),
            SCF.serviceConfigFile(self.cfg).getParam('argTrain', 'annualCrop'),
            SCF.serviceConfigFile(self.cfg).getParam('argTrain', 'cropMix'),
            SCF.serviceConfigFile(self.cfg).getParam('chain',
                                                     'enable_autoContext'),
            SCF.serviceConfigFile(self.cfg).getParam('chain', 'regionField'),
            SCF.serviceConfigFile(self.cfg).getParam('GlobChain', 'proj'),
            SCF.serviceConfigFile(self.cfg).getParam('chain',
                                                     'enableCrossValidation'),
            SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs'),
            SCF.iota2_parameters(self.cfg).get_sensors_parameters(
                os.path.splitext(os.path.basename(list(x.items())[0][1]))[0]),
            SCF.serviceConfigFile(self.cfg).getParam(
                'argTrain', 'dempster_shafer_SAR_Opt_fusion'),
            SCF.serviceConfigFile(self.cfg).getParam(
                'argTrain', 'samplesClassifMix'), output_path_annual, self.
            ram_extraction,
            SCF.serviceConfigFile(self.cfg).getParam('GlobChain',
                                                     'writeOutputs'),
            SCF.serviceConfigFile(self.cfg).getParam('argTrain',
                                                     'outputPrevFeatures'),
            SCF.serviceConfigFile(self.cfg).getParam(
                'argTrain', 'annualClassesExtractionSource'),
            SCF.serviceConfigFile(self.cfg).getParam('argTrain',
                                                     'validityThreshold'),
            SCF.serviceConfigFile(self.cfg).getParam(
                'chain', 'spatialResolution'), None)
        return step_function

    def step_outputs(self):
        """
        """
        pass
