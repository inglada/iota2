#!/usr/bin/python
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

from collections import OrderedDict


class iota2():
    """
    class use to describe steps sequence and variable to use at each step (config)
    """
    def __init__(self, cfg, config_ressources):
        #Config object
        self.cfg = cfg
        
        #working directory, HPC
        self.HPC_working_directory = "TMPDIR"
        
        #steps definitions
        self.steps_group = OrderedDict()

        self.steps_group["init"] = OrderedDict()
        self.steps_group["sampling"] = OrderedDict()
        self.steps_group["dimred"] = OrderedDict()
        self.steps_group["learning"] = OrderedDict()
        self.steps_group["classification"] = OrderedDict()
        self.steps_group["mosaic"] = OrderedDict()
        self.steps_group["validation"] = OrderedDict()
        #build steps
        self.steps = self.build_steps(self.cfg, config_ressources)

    def get_dir(self):
        """
        usage : return iota2_directories
        """
        import os
        directories = ['classif', 'config_model', 'dataRegion', 'envelope',
                       'formattingVectors', 'metaData', 'samplesSelection',
                       'stats', 'cmd', 'dataAppVal', 'dimRed', 'final',
                       'learningSamples', 'model', 'shapeRegion', "features"]

        iota2_outputs_dir = self.cfg.getParam('chain', 'outputPath')
        
        return [os.path.join(iota2_outputs_dir, d) for d in directories]

    def get_steps_number(self):
        
        start = self.cfg.getParam('chain', 'firstStep')
        end = self.cfg.getParam('chain', 'lastStep')
        start_ind = self.steps_group.keys().index(start)
        end_ind = self.steps_group.keys().index(end)
        
        steps = []
        for key in self.steps_group.keys()[start_ind:end_ind+1]:
            steps.append(self.steps_group[key])

        step_to_compute = [step for step_group in steps for step in step_group]
        
        return step_to_compute


    def build_steps(self, cfg, config_ressources=None):
        """
        build steps
        """
        from Cluster import get_RAM
        from Validation import OutStats as OutS
        from Validation import MergeOutStats as MOutS
        from Sampling import TileEnvelope as env
        from Sampling import TileArea as area
        from Learning import TrainingCmd as TC
        from Classification import ClassificationCmd as CC
        from Validation import ClassificationShaping as CS
        from Validation import GenConfusionMatrix as GCM
        from Sampling import DataAugmentation
        from Learning import ModelStat as MS
        from Validation import GenResults as GR
        import os
        from Classification import Fusion as FUS
        from Classification import NoData as ND
        from Validation import ConfusionFusion as confFus
        from Sampling import VectorSampler as vs
        from Sampling import VectorSamplesMerge as VSM
        from Common import IOTA2Directory as IOTA2_dir
        from Common import FileUtils as fu
        from Sampling import DimensionalityReduction as DR
        from Sensors import NbView
        from Sensors.SAR import S1Processor as SAR
        from Classification import ImageClassifier as imageClassifier
        from Sampling import VectorFormatting as VF
        from Sampling import SplitSamples as splitS
        from Sampling import SamplesMerge as samplesMerge
        from Sampling import SamplesStat
        from Sampling import SamplesSelection
        from Classification import MergeFinalClassifications as mergeCl

        # get variable from configuration file
        PathTEST = cfg.getParam('chain', 'outputPath')
        TmpTiles = cfg.getParam('chain', 'listTile')
        tiles = TmpTiles.split(" ")
        Sentinel1 = cfg.getParam('chain', 'S1Path')
        pathTilesFeat = os.path.join(PathTEST, "features")
        shapeRegion = cfg.getParam('chain', 'regionPath')
        field_Region = cfg.getParam('chain', 'regionField')
        model = cfg.getParam('chain', 'model')
        shapeData = cfg.getParam('chain', 'groundTruth')
        dataField = cfg.getParam('chain', 'dataField')
        N = cfg.getParam('chain', 'runs')
        CLASSIFMODE = cfg.getParam('argClassification', 'classifMode')
        NOMENCLATURE = cfg.getParam('chain', 'nomenclaturePath')
        COLORTABLE = cfg.getParam('chain', 'colorTable')
        RATIO = cfg.getParam('chain', 'ratio')
        outStat = cfg.getParam('chain', 'outputStatistics')
        classifier = cfg.getParam('argTrain', 'classifier')
        ds_sar_opt = cfg.getParam('argTrain', 'dempster_shafer_SAR_Opt_fusion')
        cloud_threshold = cfg.getParam('chain', 'cloud_threshold')
        enableCrossValidation = cfg.getParam('chain', 'enableCrossValidation')
        fusionClaAllSamplesVal = cfg.getParam('chain', 'fusionOfClassificationAllSamplesValidation')
        sampleManagement = cfg.getParam('argTrain', 'sampleManagement')
        pixType = fu.getOutputPixType(NOMENCLATURE)

        merge_final_classifications = cfg.getParam('chain', 'merge_final_classifications')
        merge_final_classifications_method = cfg.getParam('chain',
                                                          'merge_final_classifications_method')
        undecidedlabel = cfg.getParam("chain", "merge_final_classifications_undecidedlabel")
        dempstershafer_mob = cfg.getParam("chain", "dempstershafer_mob")
        keep_runs_results = cfg.getParam('chain', 'keep_runs_results')

        dimred = cfg.getParam('dimRed', 'dimRed')
        targetDimension = cfg.getParam('dimRed', 'targetDimension')
        reductionMode = cfg.getParam('dimRed', 'reductionMode')
        sample_augmentation = dict(cfg.getParam('argTrain', 'sampleAugmentation'))
        sample_augmentation_flag = sample_augmentation["activate"]

        #do not change
        fieldEnv = "FID"

        pathModels = PathTEST + "/model"
        pathEnvelope = PathTEST + "/envelope"
        pathClassif = PathTEST + "/classif"
        pathTileRegion = PathTEST + "/shapeRegion"
        classifFinal = PathTEST + "/final"
        dataRegion = PathTEST + "/dataRegion"
        pathAppVal = PathTEST + "/dataAppVal"
        pathSamples = PathTEST + "/learningSamples"
        pathStats = PathTEST + "/stats"
        cmdPath = PathTEST + "/cmd"

        from Steps import IOTA2Step
        from Steps import FirstStep

        monEtape = FirstStep.FirstStep()
        pause = raw_input("W8")

        return step_container
