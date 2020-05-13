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
from collections import OrderedDict
from iota2.Common import ServiceConfigFile as SCF
from iota2.sequence_builders.i2_sequence_builder import i2_builder


class i2_features_map(i2_builder):
    """
    class use to describe steps sequence and variable to use at
    each step (config)
    """
    def __init__(self,
                 cfg,
                 config_ressources,
                 hpc_working_directory: Optional[str] = "TMPDIR"):
        super().__init__(cfg, config_ressources, hpc_working_directory)
        # config object
        self.cfg = cfg

        # working directory, HPC
        self.workingDirectory = os.getenv(hpc_working_directory)

        # steps definitions
        self.steps_group = OrderedDict()
        self.steps_group["init"] = OrderedDict()
        self.steps_group["sampling"] = OrderedDict()

        #build steps
        self.steps = self.build_steps(self.cfg, config_ressources)
        self.sort_step()

        # pickle's path
        self.iota2_pickle = os.path.join(
            SCF.serviceConfigFile(self.cfg).getParam("chain", "outputPath"),
            "logs", "iota2.txt")

    def get_dir(self):
        """
        usage : return iota2_directories
        """
        directories = ['final', "features", "customF"]

        iota2_outputs_dir = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')

        return [os.path.join(iota2_outputs_dir, d) for d in directories]

    def build_steps(self, cfg, config_ressources=None):
        """
        build steps
        """

        from iota2.Steps.IOTA2Step import StepContainer

        from iota2.Steps import features_maps_dir_tree
        from iota2.Steps import CommonMasks
        from iota2.Steps import PixelValidity
        from iota2.Steps import sensorsPreprocess
        from iota2.Steps import write_features_map
        from iota2.Steps import merge_features_maps

        # will contains all IOTA² steps
        s_container = StepContainer()

        # class instance
        step_build_tree = features_maps_dir_tree.features_maps_dir_tree(
            cfg, config_ressources)
        step_preprocess = sensorsPreprocess.sensorsPreprocess(
            cfg, config_ressources, self.workingDirectory)
        step_commonmasks = CommonMasks.CommonMasks(cfg, config_ressources,
                                                   self.workingDirectory)
        step_pixval = PixelValidity.PixelValidity(cfg, config_ressources,
                                                  self.workingDirectory)
        step_compute_features = write_features_map.write_features_map(
            cfg, config_ressources, self.workingDirectory)
        step_merge_features = merge_features_maps.merge_features_maps(
            cfg, config_ressources, self.workingDirectory)
        # build chain
        # init steps
        s_container.append(step_build_tree, "init")
        s_container.append(step_preprocess, "init")
        s_container.append(step_commonmasks, "init")
        s_container.append(step_pixval, "init")

        s_container.append(step_compute_features, "sampling")
        s_container.append(step_merge_features, "sampling")
        return s_container
