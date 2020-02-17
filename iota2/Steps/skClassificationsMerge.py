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

from Steps import IOTA2Step
from Common import ServiceConfigFile


class ScikitClassificationsMerge(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, working_directory=None):
        # heritage init
        resources_block_name = "mergeClassifications"
        super(ScikitClassificationsMerge, self).__init__(cfg, cfg_resources_file, resources_block_name)

        # step variables
        self.working_directory = working_directory
        self.output_path = ServiceConfigFile.serviceConfigFile(self.cfg).getParam('chain', 'outputPath')
        self.epsg_code = int(ServiceConfigFile.serviceConfigFile(self.cfg).getParam('GlobChain', 'proj').split(":")[-1])
        self.use_scikitlearn = ServiceConfigFile.serviceConfigFile(self.cfg).getParam('scikit_models_parameters', 'model_type') is not None

    def step_description(self):
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
        parameters = sk_classifications_to_merge(os.path.join(self.output_path, "classif"))
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
        
        from iota2.Common.rasterUtils import merge_rasters
        step_function = lambda x: merge_sk_classifications(x,
                                                           self.epsg_code,
                                                           self.working_directory)
        return step_function

    def step_clean(self):
        """
        """
        from iota2.Classification.skClassifier import sk_classifications_to_merge
        rasters = sk_classifications_to_merge(os.path.join(self.output_path, "classif"))
        for rasters_already_merged in rasters:
            for raster in rasters_already_merged["rasters_list"]:
                os.remove(raster)

    def step_outputs(self):
        """
        """
        pass
