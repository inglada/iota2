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
from iota2.scheduling.i2_scheduler import i2_scheduler


class i2_features_map(i2_scheduler):
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
        #~ self.cfg = cfg
        self.cfg = cfg

        # working directory, HPC

        self.workingDirectory = os.getenv(hpc_working_directory)

        # steps definitions
        self.steps_group = OrderedDict()

        self.steps_group["init"] = OrderedDict()
        self.steps_group["sampling"] = OrderedDict()
        self.steps_group["dimred"] = OrderedDict()
        self.steps_group["learning"] = OrderedDict()
        self.steps_group["classification"] = OrderedDict()
        self.steps_group["mosaic"] = OrderedDict()
        self.steps_group["validation"] = OrderedDict()
        self.steps_group["regularisation"] = OrderedDict()
        self.steps_group["crown"] = OrderedDict()
        self.steps_group["mosaictiles"] = OrderedDict()
        self.steps_group["vectorisation"] = OrderedDict()
        self.steps_group["simplification"] = OrderedDict()
        self.steps_group["smoothing"] = OrderedDict()
        self.steps_group["clipvectors"] = OrderedDict()
        self.steps_group["lcstatistics"] = OrderedDict()

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
        import os
        directories = [
            'classif', 'config_model', 'dataRegion', 'envelope',
            'formattingVectors', 'metaData', 'samplesSelection', 'stats',
            'cmd', 'dataAppVal', 'dimRed', 'final', 'learningSamples', 'model',
            'shapeRegion', "features"
        ]

        iota2_outputs_dir = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')

        return [os.path.join(iota2_outputs_dir, d) for d in directories]

    def build_steps(self, cfg, config_ressources=None):
        """
        build steps
        """

        import os
        from iota2.MPI import ressourcesByStep as iota2Ressources
        from iota2.Common import ServiceConfigFile as SCF
        from iota2.Steps.IOTA2Step import StepContainer

        from iota2.Steps import (IOTA2DirTree, CommonMasks, PixelValidity,
                                 Envelope, genRegionVector, VectorFormatting,
                                 splitSamples, samplesMerge, statsSamplesModel,
                                 samplingLearningPolygons, samplesByTiles,
                                 samplesExtraction, sensorsPreprocess,
                                 write_features_map, merge_features_maps)
        # control variable
        Sentinel1 = SCF.serviceConfigFile(cfg).getParam('chain', 'S1Path')
        shapeRegion = SCF.serviceConfigFile(cfg).getParam(
            'chain', 'regionPath')
        classif_mode = SCF.serviceConfigFile(cfg).getParam(
            'argClassification', 'classifMode')

        # will contains all IOTA² steps
        s_container = StepContainer()

        # class instance
        step_build_tree = IOTA2DirTree.IOTA2DirTree(cfg, config_ressources)
        step_PreProcess = sensorsPreprocess.sensorsPreprocess(
            cfg, config_ressources, self.workingDirectory)
        step_CommonMasks = CommonMasks.CommonMasks(cfg, config_ressources,
                                                   self.workingDirectory)
        step_pixVal = PixelValidity.PixelValidity(cfg, config_ressources,
                                                  self.workingDirectory)
        step_compute_features = write_features_map.write_features_map(
            cfg, config_ressources, self.workingDirectory)
        step_merge_features = merge_features_maps.merge_features_maps(
            cfg, config_ressources, self.workingDirectory)
        # build chain
        # init steps
        s_container.append(step_build_tree, "init")
        s_container.append(step_PreProcess, "init")
        s_container.append(step_CommonMasks, "init")
        s_container.append(step_pixVal, "init")

        s_container.append(step_compute_features, "sampling")
        return s_container
