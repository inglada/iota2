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


class samplingLearningPolygons(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "samplesSelection"
        super(samplingLearningPolygons, self).__init__(cfg, cfg_resources_file,
                                                       resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.enable_cross_validation = SCF.serviceConfigFile(
            self.cfg).getParam('chain', 'enableCrossValidation')

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Select pixels in learning polygons by models")
        return description

    def sort_by_seed(self, item):
        """
        """
        return os.path.splitext(os.path.basename(item))[0].split("_")[4]

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from iota2.Common import FileUtils as fut
        selected_polygons = fut.FileSearch_AND(
            os.path.join(self.output_path, "samplesSelection"), True, ".shp")
        if self.enable_cross_validation:
            selected_polygons = sorted(selected_polygons,
                                       key=self.sort_by_seed)[:-1]
        return selected_polygons

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from iota2.Sampling import SamplesSelection

        output_path = SCF.serviceConfigFile(self.cfg).getParam(
            "chain", "outputPath")
        runs = SCF.serviceConfigFile(self.cfg).getParam('chain', 'runs')
        epsg = SCF.serviceConfigFile(self.cfg).getParam('GlobChain', 'proj')
        random_seed = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'random_seed')
        data_field = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'dataField').lower()
        parameters = dict(
            SCF.serviceConfigFile(self.cfg).getParam('argTrain',
                                                     'sampleSelection'))
        masks_name = "MaskCommunSL.tif"
        step_function = lambda x: SamplesSelection.samples_selection(
            x, self.workingDirectory, output_path, runs, epsg, masks_name,
            parameters, data_field, random_seed)
        return step_function

    def step_outputs(self):
        """
        """
        pass
