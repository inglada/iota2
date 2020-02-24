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
"""
Step for compute statistics for SVM learning
"""
import os

from iota2.Steps import IOTA2Step
from iota2.Common import ServiceConfigFile as SCF


class samplesNormalization(IOTA2Step.Step):
    """
    The samples Normalization class
    """
    def __init__(self, cfg, cfg_resources_file):
        # heritage init
        resources_block_name = "stats_by_models"
        super(samplesNormalization, self).__init__(cfg, cfg_resources_file,
                                                   resources_block_name)

        # step variables
        self.output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Normalize samples")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from iota2.Learning import ModelStat as MS
        cfg = SCF.serviceConfigFile(self.cfg)
        user_feat_pattern = cfg.getParam("userFeat", "patterns")
        if "none" in user_feat_pattern.lower():
            user_feat_pattern = None
        return MS.generate_stat_model(
            os.path.join(self.output_path, "dataAppVal"),
            os.path.join(self.output_path, "features"),
            os.path.join(self.output_path, "stats"),
            os.path.join(self.output_path, "cmd", "stats"),
            cfg.getParam("chain", "outputPath"),
            cfg.getParam('argTrain', 'classifier'),
            cfg.getParam("GlobChain", "features"),
            cfg.getParam("chain", "userFeatPath"), user_feat_pattern)

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from iota2.MPI import launch_tasks as tLauncher
        bash_launcher_function = tLauncher.launchBashCmd
        step_function = lambda x: bash_launcher_function(x)
        return step_function

    def step_outputs(self):
        """
        """
        pass
