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
# import dill

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
                       'learningSamples', 'model', 'shapeRegion']

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
        import outStats as OutS
        import mergeOutStats as MOutS
        import tileEnvelope as env
        import tileArea as area
        import LaunchTraining as LT
        import createRegionsByTiles as RT
        import ExtractDataByRegion as ExtDR
        import RandomInSituByTile as RIST
        import launchClassification as LC
        import ClassificationShaping as CS
        import genConfusionMatrix as GCM
        from Sampling.DataAugmentation import augmentation_samples_user
        import ModelStat as MS
        import genResults as GR
        import os
        import fusion as FUS
        import noData as ND
        import confusionFusion as confFus
        import reArrangeModel as RAM
        import genCmdSplitShape as genCmdSplitS
        import vectorSampler as vs
        import vectorSamplesMerge as VSM
        import oso_directory as IOTA2_dir
        import fileUtils as fu
        import DimensionalityReduction as DR
        import NbView
        import S1Processor as SAR
        import bPy_ImageClassifier as imageClassifier
        import vector_formatting as VF
        import splitSamples as splitS
        import mergeSamples as samplesMerge
        import statSamples as samplesStats
        import selectionSamples as samplesSelection
        import mergeFinalClassifications as mergeCl

        fu.updatePyPath()
        # get variable from configuration file
        PathTEST = cfg.getParam('chain', 'outputPath')
        TmpTiles = cfg.getParam('chain', 'listTile')
        tiles = TmpTiles.split(" ")
        Sentinel1 = cfg.getParam('chain', 'S1Path')
        pathTilesFeat = cfg.getParam('chain', 'featuresPath')
        shapeRegion = cfg.getParam('chain', 'regionPath')
        field_Region = cfg.getParam('chain', 'regionField')
        model = cfg.getParam('chain', 'model')
        shapeData = cfg.getParam('chain', 'groundTruth')
        dataField = cfg.getParam('chain', 'dataField')
        N = cfg.getParam('chain', 'runs')
        MODE = cfg.getParam('chain', 'mode')
        CLASSIFMODE = cfg.getParam('argClassification', 'classifMode')
        NOMENCLATURE = cfg.getParam('chain', 'nomenclaturePath')
        COLORTABLE = cfg.getParam('chain', 'colorTable')
        RATIO = cfg.getParam('chain', 'ratio')
        outStat = cfg.getParam('chain', 'outputStatistics')
        classifier = cfg.getParam('argTrain', 'classifier')
        cloud_threshold = cfg.getParam('chain', 'cloud_threshold')
        sampleManagement = cfg.getParam('argTrain', 'sampleManagement')
        pixType = cfg.getParam('argClassification', 'pixType')

        merge_final_classifications = cfg.getParam('chain', 'merge_final_classifications')
        merge_final_classifications_method = cfg.getParam('chain',
                                                          'merge_final_classifications_method')
        undecidedlabel = cfg.getParam("chain", "merge_final_classifications_undecidedlabel")
        dempstershafer_mof = cfg.getParam("chain", "dempstershafer_mof")
        keep_runs_results = cfg.getParam('chain', 'keep_runs_results')

        dimred = cfg.getParam('dimRed', 'dimRed')
        targetDimension = cfg.getParam('dimRed', 'targetDimension')
        reductionMode = cfg.getParam('dimRed', 'reductionMode')

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

        import launch_tasks as tLauncher
        import ressourcesByStep as iota2Ressources
        if config_ressources:
            ressourcesByStep = iota2Ressources.iota2_ressources(config_ressources)
        else:
            ressourcesByStep = iota2Ressources.iota2_ressources()
        
        t_container = []
        t_counter = 0
        
        pathConf = cfg.pathConf
        workingDirectory = os.getenv(self.HPC_working_directory)
        
        bashLauncherFunction = tLauncher.launchBashCmd
        launchPythonCmd = tLauncher.launchPythonCmd

        #STEP : directories.
        t_counter += 1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: IOTA2_dir.GenerateDirectories(x), [pathConf]),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["iota2_dir"]))
        self.steps_group["init"][t_counter] = "create directories"

        #STEP : preprocess SAR data
        if not "None" in Sentinel1:
            t_counter += 1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: SAR.S1Processor(Sentinel1, x, workingDirectory), tiles),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["SAR_pre_process"]))
            self.steps_group["init"][t_counter] = "Sentinel-1 pre-processing"

        #STEP : Common masks generation
        t_counter += 1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: fu.getCommonMasks(x, pathConf, workingDirectory), tiles),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["get_common_mask"]))
        self.steps_group["init"][t_counter] = "generate common masks"
        
        #STEP : pix Validity by tiles generation
        t_counter += 1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: NbView.genNbView(x, "CloudThreshold_" + str(cloud_threshold) + ".shp", cloud_threshold, pathConf, workingDirectory), [os.path.join(pathTilesFeat, tile) for tile in tiles]),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["get_pixValidity"]))
        self.steps_group["init"][t_counter] = "compute validity mask by tile" 

        #STEP : Envelope generation
        t_counter += 1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: env.GenerateShapeTile(tiles, pathTilesFeat,
                                                                                  x, workingDirectory,
                                                                                  pathConf), [pathEnvelope]),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["envelope"]))
        self.steps_group["sampling"][t_counter] = "generate envelopes" 

        if MODE != "outside":
            #STEP : Region shape generation
            t_counter += 1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: area.generateRegionShape(MODE, pathEnvelope,
                                                                                         model, x,
                                                                                         field_Region, pathConf,
                                                                                         workingDirectory), [shapeRegion]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["regionShape"]))
            self.steps_group["sampling"][t_counter] = "generate region shapes" 

        #STEP : Samples formatting
        t_counter += 1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: VF.vector_formatting(pathConf, x, workingDirectory),
                                                  tiles),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["samplesFormatting"]))
        self.steps_group["sampling"][t_counter] = "Prepare samples"

        if MODE == "outside" and CLASSIFMODE == "fusion":
            #STEP : Split learning polygons and Validation polygons in sub-sample if necessary
            #(too many samples to learn a model)
            t_counter += 1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: splitS.splitSamples(x, workingDirectory),
                                                      [pathConf]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["split_samples"]))
            self.steps_group["sampling"][t_counter] = "split learning polygons and Validation polygons in sub-sample if necessary"

        #STEP : Samples models merge
        t_counter += 1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: samplesMerge.samples_merge(x, pathConf, workingDirectory),
                                                  lambda: samplesMerge.get_models(os.path.join(PathTEST, "formattingVectors"), field_Region, N)),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["samplesMerge"]))
        self.steps_group["sampling"][t_counter] = "merge samples by models"

        #STEP : Samples statistics
        t_counter += 1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: samplesStats.samples_stats(x, pathConf, workingDirectory),
                                                  lambda: samplesStats.region_tile(os.path.join(PathTEST, "samplesSelection"))),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["samplesStatistics"]))
        self.steps_group["sampling"][t_counter] = "generate samples statistics"

        #STEP : Samples Selection
        t_counter += 1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: samplesSelection.samples_selection(x, pathConf, workingDirectory),
                                                  lambda: fu.FileSearch_AND(os.path.join(PathTEST, "samplesSelection"), True, ".shp")),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["samplesSelection"]))
        self.steps_group["sampling"][t_counter] = "select samples"

        #STEP : Samples Extraction
        t_counter += 1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: vs.generateSamples(x, workingDirectory, pathConf),
                                                  lambda: fu.FileSearch_AND(PathTEST + "/formattingVectors", True, ".shp")),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["vectorSampler"]))
        self.steps_group["sampling"][t_counter] = "generate samples"

        #STEP : MergeSamples
        t_counter += 1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: VSM.vectorSamplesMerge(pathConf, x),
                                                  lambda: fu.split_vectors_by_regions((fu.FileSearch_AND(PathTEST + "/learningSamples", True, "Samples_learn.sqlite")))),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["mergeSample"]))
        self.steps_group["sampling"][t_counter] = "merge samples"
        
        if sampleManagement and sampleManagement.lower() != 'none':
            #STEP : sampleManagement
            t_counter+=1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: augmentation_samples_user.samples_management_csv(dataField.lower(),
                                                                                                                 sampleManagement,
                                                                                                                 x, workingDirectory),
                                                      lambda: augmentation_samples_user.GetSamplesSet(PathTEST + "/learningSamples")),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["samplesManagement"]))
            self.steps_group["sampling"][t_counter] = "balance samples according to user request"


        #STEP : Dimensionality Reduction
        if dimred:
            t_counter+=1
            t_container.append(
                tLauncher.Tasks(tasks=(lambda x: 
                                       DR.SampleDimensionalityReduction(x, PathTEST,
                                                                        targetDimension,
                                                                        reductionMode),
                                       lambda: DR.BuildIOSampleFileLists(PathTEST)),
                                iota2_config=cfg,
                                ressources=ressourcesByStep["dimensionalityReduction"]))
            self.steps_group["dimred"][t_counter] = "dimensionality reduction"

        if classifier == "svm":
            #STEP : Compute statistics by models
            t_counter += 1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x),
                                                      lambda: MS.generateStatModel(pathAppVal,
                                                                                   pathTilesFeat,
                                                                                   pathStats,
                                                                                   cmdPath + "/stats",
                                                                                   None, cfg)),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["stats_by_models"]))
            self.steps_group["learning"][t_counter] = "compute statistics for each model"        

        #STEP : Learning
        t_counter += 1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x),
                                                  lambda: LT.launchTraining(pathAppVal,
                                                                            cfg, pathTilesFeat,
                                                                            dataField,
                                                                            pathStats,
                                                                            N, cmdPath + "/train",
                                                                            pathModels, workingDirectory, None)),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["training"]))
        self.steps_group["learning"][t_counter] = "learning"

        #STEP : generate Classifications commands and masks
       
        t_counter += 1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: LC.launchClassification(pathModels, pathConf, pathStats,
                                                                                    pathTileRegion, pathTilesFeat,
                                                                                    shapeRegion, x,
                                                                                    N, cmdPath + "/cla", pathClassif, workingDirectory), [field_Region]),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["cmdClassifications"]))
        self.steps_group["classification"][t_counter] = "generate classification commands"

        #STEP : generate Classifications
        
        t_counter += 1
        t_container.append(tLauncher.Tasks(tasks=(lambda x: launchPythonCmd(imageClassifier.launchClassification, *x),
                                                  lambda: fu.parseClassifCmd(cmdPath + "/cla/class.txt")),
                                           iota2_config=cfg,
                                           ressources=ressourcesByStep["classifications"]))
        self.steps_group["classification"][t_counter] = "generate classifications"

        if CLASSIFMODE == "separate":
            #STEP : Classification's shaping
            t_counter += 1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: CS.ClassificationShaping(x,
                                                                                         pathEnvelope,
                                                                                         pathTilesFeat,
                                                                                         fieldEnv, N,
                                                                                         classifFinal, workingDirectory,
                                                                                         pathConf, COLORTABLE), [pathClassif]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["classifShaping"]))
            self.steps_group["mosaic"][t_counter] = "classfication shaping"

            #STEP : confusion matrix commands generation
            t_counter += 1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: GCM.genConfMatrix(x, pathAppVal,
                                                                                  N, dataField,
                                                                                  cmdPath + "/confusion",
                                                                                  pathConf, workingDirectory), [classifFinal]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["gen_confusionMatrix"]))
            self.steps_group["validation"][t_counter] = "confusion matrix command generation" 

            if keep_runs_results:
                #STEP : confusion matrix generation
                t_counter += 1
                t_container.append(tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x),
                                                          lambda: fu.getCmd(cmdPath + "/confusion/confusion.txt")),
                                                   iota2_config=cfg,
                                                   ressources=ressourcesByStep["confusionMatrix"]))
                self.steps_group["validation"][t_counter] = "generate confusion matrix" 

                #STEP : confusion matrix fusion
                t_counter += 1
                t_container.append(tLauncher.Tasks(tasks=(lambda x: confFus.confFusion(x, dataField,
                                                                                       classifFinal + "/TMP",
                                                                                       classifFinal + "/TMP",
                                                                                       classifFinal + "/TMP",
                                                                                       pathConf), [shapeData]),
                                                   iota2_config=cfg,
                                                   ressources=ressourcesByStep["confusionMatrixFusion"]))
                self.steps_group["validation"][t_counter] = "confusion matrix fusion" 

                #STEP : results report generation
                t_counter += 1
                t_container.append(tLauncher.Tasks(tasks=(lambda x: GR.genResults(x,
                                                                                  NOMENCLATURE), [classifFinal]),
                                                   iota2_config=cfg,
                                                   ressources=ressourcesByStep["reportGen"]))
                self.steps_group["validation"][t_counter] = "report generation"

        elif CLASSIFMODE == "fusion" and MODE != "one_region":
            #STEP : Classifications fusion
            t_counter += 1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x),
                                                      lambda: FUS.fusion(pathClassif, cfg, None)),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["fusion"]))
            self.steps_group["classification"][t_counter] = "fusion of classification"

            #STEP : Managing fusion's indecisions
            t_counter += 1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: ND.noData(PathTEST, x, field_Region,
                                                                          pathTilesFeat, shapeRegion,
                                                                          N, pathConf, workingDirectory),
                                                      lambda: fu.FileSearch_AND(pathClassif, True, "_FUSION_")),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["noData"]))
            self.steps_group["classification"][t_counter] = "process fusion tile" 

            #STEP : Classification's shaping
            t_counter += 1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: CS.ClassificationShaping(x,
                                                                                         pathEnvelope,
                                                                                         pathTilesFeat,
                                                                                         fieldEnv, N,
                                                                                         classifFinal, workingDirectory,
                                                                                         pathConf, COLORTABLE), [pathClassif]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["classifShaping"]))
            self.steps_group["mosaic"][t_counter] = "classification shaping" 

            #STEP : confusion matrix commands generation
            t_counter += 1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: GCM.genConfMatrix(x, pathAppVal,
                                                                                  N, dataField,
                                                                                  cmdPath + "/confusion",
                                                                                  pathConf, workingDirectory), [classifFinal]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["gen_confusionMatrix"]))
            self.steps_group["validation"][t_counter] = "confusion matrix command generation"

            if keep_runs_results:
                #STEP : confusion matrix generation
                t_counter += 1
                t_container.append(tLauncher.Tasks(tasks=(lambda x: bashLauncherFunction(x),
                                                          lambda: fu.getCmd(cmdPath + "/confusion/confusion.txt")),
                                                   iota2_config=cfg,
                                                   ressources=ressourcesByStep["confusionMatrix"]))
                self.steps_group["validation"][t_counter] = "confusion matrix generation" 

                #STEP : confusion matrix fusion
                t_counter += 1
                t_container.append(tLauncher.Tasks(tasks=(lambda x: confFus.confFusion(x, dataField,
                                                                                       classifFinal + "/TMP",
                                                                                       classifFinal + "/TMP",
                                                                                       classifFinal + "/TMP",
                                                                                       pathConf), [shapeData]),
                                                   iota2_config=cfg,
                                                   ressources=ressourcesByStep["confusionMatrixFusion"]))
                self.steps_group["validation"][t_counter] = "confusion matrix fusion"

                #STEP : results report generation
                t_counter += 1
                t_container.append(tLauncher.Tasks(tasks=(lambda x: GR.genResults(x,
                                                                                  NOMENCLATURE), [classifFinal]),
                                                   iota2_config=cfg,
                                                   ressources=ressourcesByStep["reportGen"]))
                self.steps_group["validation"][t_counter] = "result report generation" 

        if merge_final_classifications and N > 1:
            t_counter += 1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: mergeCl.mergeFinalClassifications(x,
                                                                                                  dataField.lower(),
                                                                                                  NOMENCLATURE,
                                                                                                  COLORTABLE,
                                                                                                  N,
                                                                                                  pixType,
                                                                                                  merge_final_classifications_method,
                                                                                                  undecidedlabel,
                                                                                                  dempstershafer_mof,
                                                                                                  keep_runs_results,
                                                                                                  workingDirectory), [PathTEST]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["merge_final_classifications"]))
            self.steps_group["validation"][t_counter] = "use final classifications to compute a majority voting map"

        if outStat:
            #STEP : compute output statistics tiles
            t_counter += 1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: OutS.outStats(pathConf, x,
                                                                              N, workingDirectory), tiles),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["statsReport"]))
            self.steps_group["validation"][t_counter] = "compute output statistics"

            #STEP : merge statistics
            t_counter += 1
            t_container.append(tLauncher.Tasks(tasks=(lambda x: MOutS.mergeOutStats(x), [pathConf]),
                                               iota2_config=cfg,
                                               ressources=ressourcesByStep["mergeOutStats"]))
            self.steps_group["validation"][t_counter] = "merge statistics"

        return t_container
