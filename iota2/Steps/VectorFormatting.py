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


class VectorFormatting(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "samplesFormatting"
        super(VectorFormatting, self).__init__(cfg, cfg_resources_file,
                                               resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.outputPath = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Prepare samples")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        tiles = SCF.serviceConfigFile(self.cfg).getParam('chain',
                                                         'listTile').split(" ")
        return tiles

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from iota2.Sampling import VectorFormatting as VF
        output_path = os.path.join(self.cfg.getParam('chain', 'outputPath'),
                                   "formattingVectors")
        ground_truth_vec = self.cfg.getParam('chain', 'groundTruth')
        data_field = (self.cfg.getParam('chain', 'dataField')).lower()

        cloud_threshold = self.cfg.getParam('chain', 'cloud_threshold')
        ratio = self.cfg.getParam('chain', 'ratio')
        random_seed = self.cfg.getParam('chain', 'random_seed')
        enable_cross_validation = self.cfg.getParam('chain',
                                                    'enableCrossValidation')
        enable_split_ground_truth = self.cfg.getParam('chain',
                                                      'splitGroundTruth')
        fusion_merge_all_validation = self.cfg.getParam(
            'chain', 'fusionOfClassificationAllSamplesValidation')
        runs = self.cfg.getParam('chain', 'runs')
        epsg = int((self.cfg.getParam('GlobChain', 'proj')).split(":")[-1])
        region_vec = self.cfg.getParam('chain', 'regionPath')
        region_field = (self.cfg.getParam('chain', 'regionField')).lower()
        if not region_vec:
            region_vec = os.path.join(self.cfg.getParam("chain", "outputPath"),
                                      "MyRegion.shp")

        merge_final_classifications = self.cfg.getParam(
            'chain', 'merge_final_classifications')
        merge_final_classifications_ratio = self.cfg.getParam(
            'chain', 'merge_final_classifications_ratio')
        step_function = lambda x: VF.vector_formatting(
            x, output_path, ground_truth_vec, data_field, cloud_threshold,
            ratio, random_seed, enable_cross_validation,
            enable_split_ground_truth, fusion_merge_all_validation, runs, epsg,
            region_field, merge_final_classifications,
            merge_final_classifications_ratio, region_vec, self.
            working_directory)
        return step_function

    def step_outputs(self):
        """
        """
        pass
