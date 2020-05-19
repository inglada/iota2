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


class i2_classification(i2_builder):
    """
    class use to describe steps sequence and variable to use at
    each step (config)
    """
    def __init__(self,
                 cfg,
                 config_ressources,
                 hpc_working_directory: Optional[str] = "TMPDIR"):
        super().__init__(cfg, config_ressources, hpc_working_directory)

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

        from iota2.Steps import (
            IOTA2DirTree, CommonMasks, PixelValidity, Envelope,
            genRegionVector, VectorFormatting, splitSamples, samplesMerge,
            statsSamplesModel, samplingLearningPolygons, samplesByTiles,
            samplesExtraction, samplesByModels, copySamples,
            genSyntheticSamples, samplesDimReduction, learnModel, classiCmd,
            classification, confusionSAROpt, confusionSAROptMerge,
            SAROptFusion, classificationsFusion, fusionsIndecisions, mosaic,
            confusionCmd, confusionGeneration, confusionsMerge,
            reportGeneration, mergeSeedClassifications, additionalStatistics,
            additionalStatisticsMerge, sensorsPreprocess, Coregistration,
            Regularization, mergeRegularization, Clump, Grid, crownSearch,
            crownBuild, mosaicTilesVectorization, largeVectorization,
            mosaicTilesVectorization, largeSimplification, largeSmoothing,
            clipVectors, zonalStatistics, prodVectors, slicSegmentation,
            superPixPos, superPixSplit, skClassificationsMerge)
        # control variable
        Sentinel1 = SCF.serviceConfigFile(cfg).getParam('chain', 'S1Path')
        shapeRegion = SCF.serviceConfigFile(cfg).getParam(
            'chain', 'regionPath')
        classif_mode = SCF.serviceConfigFile(cfg).getParam(
            'argClassification', 'classifMode')
        sampleManagement = SCF.serviceConfigFile(cfg).getParam(
            'argTrain', 'sampleManagement')
        sample_augmentation = dict(
            SCF.serviceConfigFile(cfg).getParam('argTrain',
                                                'sampleAugmentation'))
        sample_augmentation_flag = sample_augmentation["activate"]
        dimred = SCF.serviceConfigFile(cfg).getParam('dimRed', 'dimRed')
        classifier = SCF.serviceConfigFile(cfg).getParam(
            'argTrain', 'classifier')
        ds_sar_opt = SCF.serviceConfigFile(cfg).getParam(
            'argTrain', 'dempster_shafer_SAR_Opt_fusion')
        keep_runs_results = SCF.serviceConfigFile(cfg).getParam(
            'chain', 'keep_runs_results')
        merge_final_classifications = SCF.serviceConfigFile(cfg).getParam(
            'chain', 'merge_final_classifications')
        ground_truth = SCF.serviceConfigFile(cfg).getParam(
            'chain', 'groundTruth')
        runs = SCF.serviceConfigFile(cfg).getParam('chain', 'runs')
        outStat = SCF.serviceConfigFile(cfg).getParam('chain',
                                                      'outputStatistics')
        VHR = SCF.serviceConfigFile(cfg).getParam('coregistration', 'VHRPath')
        gridsize = SCF.serviceConfigFile(cfg).getParam('Simplification',
                                                       'gridsize')
        umc1 = SCF.serviceConfigFile(cfg).getParam('Simplification', 'umc1')
        umc2 = SCF.serviceConfigFile(cfg).getParam('Simplification', 'umc2')
        rssize = SCF.serviceConfigFile(self.cfg).getParam(
            'Simplification', 'rssize')
        inland = SCF.serviceConfigFile(self.cfg).getParam(
            'Simplification', 'inland')
        iota2_outputs_dir = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        use_scikitlearn = SCF.serviceConfigFile(self.cfg).getParam(
            'scikit_models_parameters', 'model_type') is not None
        nomenclature = SCF.serviceConfigFile(self.cfg).getParam(
            'Simplification', 'nomenclature')
        enable_autoContext = SCF.serviceConfigFile(cfg).getParam(
            'chain', 'enable_autoContext')

        # will contains all IOTA² steps
        s_container = StepContainer()

        # class instance
        step_build_tree = IOTA2DirTree.IOTA2DirTree(cfg, config_ressources)
        step_PreProcess = sensorsPreprocess.sensorsPreprocess(
            cfg, config_ressources, self.workingDirectory)
        step_CommonMasks = CommonMasks.CommonMasks(cfg, config_ressources,
                                                   self.workingDirectory)
        step_coregistration = Coregistration.Coregistration(
            cfg, config_ressources, self.workingDirectory)
        step_pixVal = PixelValidity.PixelValidity(cfg, config_ressources,
                                                  self.workingDirectory)
        step_env = Envelope.Envelope(cfg, config_ressources,
                                     self.workingDirectory)
        step_reg_vector = genRegionVector.genRegionVector(
            cfg, config_ressources, self.workingDirectory)
        step_vector_form = VectorFormatting.VectorFormatting(
            cfg, config_ressources, self.workingDirectory)
        step_split_huge_vec = splitSamples.splitSamples(
            cfg, config_ressources, self.workingDirectory)
        step_merge_samples = samplesMerge.samplesMerge(cfg, config_ressources,
                                                       self.workingDirectory)
        step_models_samples_stats = statsSamplesModel.statsSamplesModel(
            cfg, config_ressources, self.workingDirectory)
        step_samples_selection = samplingLearningPolygons.samplingLearningPolygons(
            cfg, config_ressources, self.workingDirectory)
        step_prepare_selection = samplesByTiles.samplesByTiles(
            cfg, config_ressources, self.workingDirectory)
        step_generate_learning_samples = samplesExtraction.samplesExtraction(
            cfg, config_ressources, self.workingDirectory)
        step_merge_learning_samples = samplesByModels.samplesByModels(
            cfg, config_ressources)
        step_copy_sample_between_models = copySamples.copySamples(
            cfg, config_ressources, self.workingDirectory)
        step_generate_samples = genSyntheticSamples.genSyntheticSamples(
            cfg, config_ressources, self.workingDirectory)
        step_dimRed = samplesDimReduction.samplesDimReduction(
            cfg, config_ressources, self.workingDirectory)
        step_learning = learnModel.learnModel(cfg, config_ressources,
                                              self.workingDirectory)
        step_classiCmd = classiCmd.classiCmd(cfg, config_ressources,
                                             self.workingDirectory)
        step_classification = classification.classification(
            cfg, config_ressources, self.workingDirectory)
        step_sk_classifications_merge = skClassificationsMerge.ScikitClassificationsMerge(
            cfg, config_ressources, self.workingDirectory)
        step_confusion_sar_opt = confusionSAROpt.confusionSAROpt(
            cfg, config_ressources, self.workingDirectory)
        step_confusion_sar_opt_fusion = confusionSAROptMerge.confusionSAROptMerge(
            cfg, config_ressources, self.workingDirectory)
        step_sar_opt_fusion = SAROptFusion.SAROptFusion(
            cfg, config_ressources, self.workingDirectory)
        step_classif_fusion = classificationsFusion.classificationsFusion(
            cfg, config_ressources, self.workingDirectory)
        step_manage_fus_indecision = fusionsIndecisions.fusionsIndecisions(
            cfg, config_ressources, self.workingDirectory)
        step_mosaic = mosaic.mosaic(cfg, config_ressources,
                                    self.workingDirectory)

        step_confusions_cmd = confusionCmd.confusionCmd(
            cfg, config_ressources, self.workingDirectory)
        step_confusions = confusionGeneration.confusionGeneration(
            cfg, config_ressources, self.workingDirectory)
        step_confusions_merge = confusionsMerge.confusionsMerge(
            cfg, config_ressources, self.workingDirectory)
        step_report = reportGeneration.reportGeneration(
            cfg, config_ressources, self.workingDirectory)
        step_merge_iota_classif = mergeSeedClassifications.mergeSeedClassifications(
            cfg, config_ressources, self.workingDirectory)
        step_additional_statistics = additionalStatistics.additionalStatistics(
            cfg, config_ressources, self.workingDirectory)
        step_additional_statistics_merge = additionalStatisticsMerge.additionalStatisticsMerge(
            cfg, config_ressources, self.workingDirectory)

        step_clump = Clump.Clump(cfg, config_ressources, self.workingDirectory)
        step_grid = Grid.Grid(cfg, config_ressources, self.workingDirectory)
        step_crown_search = crownSearch.crownSearch(cfg, config_ressources,
                                                    self.workingDirectory)
        step_crown_build = crownBuild.crownBuild(cfg, config_ressources,
                                                 self.workingDirectory)
        step_mosaic_tiles = mosaicTilesVectorization.mosaicTilesVectorization(
            cfg, config_ressources, self.workingDirectory)
        step_large_vecto = largeVectorization.largeVectorization(
            cfg, config_ressources, self.workingDirectory)
        step_large_simp = largeSimplification.largeSimplification(
            cfg, config_ressources, self.workingDirectory)
        step_large_smoothing = largeSmoothing.largeSmoothing(
            cfg, config_ressources, self.workingDirectory)
        step_clip_vectors = clipVectors.clipVectors(cfg, config_ressources,
                                                    self.workingDirectory)

        step_zonal_stats = zonalStatistics.zonalStatistics(
            cfg, config_ressources, self.workingDirectory)
        step_SLIC_seg = slicSegmentation.slicSegmentation(
            cfg, config_ressources, self.workingDirectory)
        step_add_superPix_pos = superPixPos.superPixPos(
            cfg, config_ressources, self.workingDirectory)
        step_split_superPix_ref = superPixSplit.superPixSplit(
            cfg, config_ressources, self.workingDirectory)
        step_prod_vectors = prodVectors.prodVectors(cfg, config_ressources,
                                                    self.workingDirectory)
        # build chain
        # init steps
        s_container.append(step_build_tree, "init")
        s_container.append(step_PreProcess, "init")
        if not "none" in VHR.lower():
            s_container.append(step_coregistration, "init")
        s_container.append(step_CommonMasks, "init")
        s_container.append(step_pixVal, "init")
        if enable_autoContext:
            s_container.append(step_SLIC_seg, "init")

        # sampling steps
        s_container.append(step_env, "sampling")
        if not shapeRegion:
            s_container.append(step_reg_vector, "sampling")
        s_container.append(step_vector_form, "sampling")
        if shapeRegion and classif_mode == "fusion":
            s_container.append(step_split_huge_vec, "sampling")
        s_container.append(step_merge_samples, "sampling")
        s_container.append(step_models_samples_stats, "sampling")
        s_container.append(step_samples_selection, "sampling")

        if enable_autoContext is True:
            s_container.append(step_add_superPix_pos, "sampling")

        s_container.append(step_prepare_selection, "sampling")

        s_container.append(step_generate_learning_samples, "sampling")

        if enable_autoContext is False:
            s_container.append(step_merge_learning_samples, "sampling")
            if sampleManagement and sampleManagement.lower() != 'none':
                s_container.append(step_copy_sample_between_models, "sampling")
            if sample_augmentation_flag:
                s_container.append(step_generate_samples, "sampling")
            if dimred:
                s_container.append(step_dimRed, "sampling")

        if enable_autoContext is True:
            s_container.append(step_split_superPix_ref, "sampling")

        #~ # learning step
        s_container.append(step_learning, "learning")

        #~ # classifications steps
        if enable_autoContext is False:
            s_container.append(step_classiCmd, "classification")
        s_container.append(step_classification, "classification")
        if use_scikitlearn:
            s_container.append(step_sk_classifications_merge, "classification")
        if ds_sar_opt:
            s_container.append(step_confusion_sar_opt, "classification")
            s_container.append(step_confusion_sar_opt_fusion, "classification")
            s_container.append(step_sar_opt_fusion, "classification")
        if classif_mode == "fusion" and shapeRegion:
            s_container.append(step_classif_fusion, "classification")
            s_container.append(step_manage_fus_indecision, "classification")

        # mosaic step
        s_container.append(step_mosaic, "mosaic")

        # validation steps
        s_container.append(step_confusions_cmd, "validation")
        if keep_runs_results:
            s_container.append(step_confusions, "validation")
            s_container.append(step_confusions_merge, "validation")
            s_container.append(step_report, "validation")
        if merge_final_classifications and runs > 1:
            s_container.append(step_merge_iota_classif, "validation")
        if outStat:
            s_container.append(step_additional_statistics, "validation")
            s_container.append(step_additional_statistics_merge, "validation")

        # regularisation steps
        if umc1:
            # TODO : creer une variable adaptative / oso / regulier (avec "connection" en paramètre supplémentaire)
            outregul = os.path.join(iota2_outputs_dir, "final",
                                    "simplification", "classif_regul.tif")

            regulruns = 2 if umc2 is not None else 1
            if not os.path.exists(outregul):
                lognamereg = 'regul1'
                lognamemerge = "merge_regul1"
                if regulruns == 2:

                    outregul = os.path.join(iota2_outputs_dir, "final",
                                            "simplification", "tmp",
                                            "regul1.tif")
                    s_container.append(
                        Regularization.Regularization(
                            cfg,
                            config_ressources,
                            umc=umc1,
                            nomenclature=nomenclature,
                            stepname="regul1",
                            workingDirectory=self.workingDirectory),
                        "regularisation")

                    s_container.append(
                        mergeRegularization.mergeRegularization(
                            cfg,
                            config_ressources,
                            workingDirectory=self.workingDirectory,
                            resample=rssize,
                            umc=umc1,
                            stepname="merge_regul1",
                            output=outregul), "regularisation")
                    umc1 = umc2
                    rssize = None
                    outregul = os.path.join(iota2_outputs_dir, "final",
                                            "simplification",
                                            "classif_regul.tif")
                    logname = 'regul2'
                    lognamemerge = "merge_regul2"

                s_container.append(
                    Regularization.Regularization(
                        cfg,
                        config_ressources,
                        umc=umc1,
                        nomenclature=nomenclature,
                        stepname=logname,
                        workingDirectory=self.workingDirectory),
                    "regularisation")

                s_container.append(
                    mergeRegularization.mergeRegularization(
                        cfg,
                        config_ressources,
                        workingDirectory=self.workingDirectory,
                        resample=rssize,
                        water=inland,
                        umc=umc1,
                        stepname=lognamemerge,
                        output=outregul), "regularisation")

        s_container.append(step_clump, "regularisation")

        if gridsize is not None:
            # crown steps
            s_container.append(step_grid, "crown")
            s_container.append(step_crown_search, "crown")
            s_container.append(step_crown_build, "crown")
            # mosaic step
            s_container.append(step_mosaic_tiles, "mosaictiles")
            # vectorization step
            s_container.append(step_large_vecto, "vectorisation")
            s_container.append(step_large_simp, "simplification")
            s_container.append(step_large_smoothing, "smoothing")
            s_container.append(step_clip_vectors, "clipvectors")
        else:
            # vectorization step
            s_container.append(step_large_vecto, "vectorisation")
            s_container.append(step_large_simp, "simplification")
            s_container.append(step_large_smoothing, "smoothing")
            s_container.append(step_clip_vectors, "clipvectors")
        s_container.append(step_zonal_stats, "lcstatistics")
        s_container.append(step_prod_vectors, "lcstatistics")
        return s_container