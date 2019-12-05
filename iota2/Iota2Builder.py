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
from collections import OrderedDict
from Common import ServiceConfigFile as SCF


class iota2():
    """
    class use to describe steps sequence and variable to use at each step (config)
    """

    def __init__(self, cfg, config_ressources):

        # config object
        # ~ self.cfg = cfg
        self.cfg = cfg

        # working directory, HPC
        HPC_working_directory = "TMPDIR"
        self.workingDirectory = os.getenv(HPC_working_directory)

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
        self.steps_group["vectorisation"] = OrderedDict()
        self.steps_group["lcstatistics"] = OrderedDict()

        # build steps
        self.steps = self.build_steps(self.cfg, config_ressources)
        self.sort_step()

        # pickle's path
        self.iota2_pickle = os.path.join(SCF.serviceConfigFile(self.cfg).getParam("chain", "outputPath"),
                                         "logs", "iota2.txt")

    def save_chain(self):
        """
        use dill to save chain instance
        """
        import dill
        if os.path.exists(self.iota2_pickle):
            os.remove(self.iota2_pickle)
        with open(self.iota2_pickle, 'wb') as fp:
            dill.dump(self, fp)

    def load_chain(self):
        import dill
        if os.path.exists(self.iota2_pickle):
            with open(self.iota2_pickle, 'rb') as fp:
                iota2_chain = dill.load(fp)
        else:
            iota2_chain = self
        return iota2_chain

    def sort_step(self):
        """
        use to establish which step is going to which step group
        """

        for step_place, step in enumerate(self.steps):
            self.steps_group[step.step_group][step_place +
                                              1] = step.step_description()

    def print_step_summarize(self, start, end, show_resources=False, checked="x"):
        """
        print iota2 steps that will be run
        """
        summarize = "Full processing include the following steps (checked steps will be run):\n"
        step_position = 0
        for group in list(self.steps_group.keys()):
            if len(self.steps_group[group]) > 0:
                summarize += "Group {}:\n".format(group)
            for key in self.steps_group[group]:
                highlight = "[ ]"
                if key >= start and key <= end:
                    highlight = "[{}]".format(checked)
                summarize += "\t {} Step {}: {}".format(highlight, key,
                                                        self.steps_group[group][key])
                if show_resources:
                    cpu = self.steps[step_position].resources["cpu"]
                    ram = self.steps[step_position].resources["ram"]
                    walltime = self.steps[step_position].resources["walltime"]
                    resource_block_name = self.steps[step_position].resources["resource_block_name"]
                    resource_block_found = self.steps[step_position].resources["resource_block_found"]
                    resource_miss = "" if resource_block_found else " -> MISSING"
                    summarize += "\n\t\t\tresources block name : {}{}\n\t\t\tcpu : {}\n\t\t\tram : {}\n\t\t\twalltime : {}".format(
                        resource_block_name, resource_miss, cpu, ram, walltime)
                summarize += "\n"
                step_position += 1
        summarize += "\n"
        return summarize

    def get_dir(self):
        """
        usage : return iota2_directories
        """
        import os
        directories = ['classif', 'config_model', 'dataRegion', 'envelope',
                       'formattingVectors', 'metaData', 'samplesSelection',
                       'stats', 'cmd', 'dataAppVal', 'dimRed', 'final',
                       'learningSamples', 'model', 'shapeRegion', "features"]

        iota2_outputs_dir = SCF.serviceConfigFile(
            self.cfg).getParam('chain', 'outputPath')

        return [os.path.join(iota2_outputs_dir, d) for d in directories]

    def get_steps_number(self):
        start = SCF.serviceConfigFile(self.cfg).getParam('chain', 'firstStep')
        end = SCF.serviceConfigFile(self.cfg).getParam('chain', 'lastStep')
        start_ind = list(self.steps_group.keys()).index(start)
        end_ind = list(self.steps_group.keys()).index(end)

        steps = []
        for key in list(self.steps_group.keys())[start_ind:end_ind+1]:
            steps.append(self.steps_group[key])
        step_to_compute = [step for step_group in steps for step in step_group]
        return step_to_compute

    def build_steps(self, cfg, config_ressources=None):
        """
        build steps
        """

        import os
        from MPI import ressourcesByStep as iota2Ressources
        from Common import ServiceConfigFile as SCF
        from Steps.IOTA2Step import StepContainer

        from Steps import (IOTA2DirTree,
                           CommonMasks, PixelValidity,
                           Envelope, genRegionVector,
                           VectorFormatting, splitSamples,
                           samplesMerge, statsSamplesModel,
                           samplingLearningPolygons, samplesByTiles,
                           samplesExtraction, samplesByModels,
                           copySamples, genSyntheticSamples,
                           samplesDimReduction, samplesNormalization,
                           learnModel, classiCmd,
                           classification, confusionSAROpt,
                           confusionSAROptMerge, SAROptFusion,
                           classificationsFusion, fusionsIndecisions,
                           mosaic, confusionCmd,
                           confusionGeneration, confusionsMerge,
                           reportGeneration, mergeSeedClassifications,
                           additionalStatistics, additionalStatisticsMerge,
                           sensorsPreprocess, Coregistration, Regularization,
                           Clump, Grid, crownSearch, crownBuild,
                           largeVectorization, VectSimplification,
                           zonalStatistics, joinStatistics)

        # will contains all IOTA² steps
        s_container = StepContainer()

        # class instance
        step_build_tree = IOTA2DirTree.IOTA2DirTree(cfg, config_ressources)
        step_PreProcess = sensorsPreprocess.sensorsPreprocess(cfg,
                                                              config_ressources,
                                                              self.workingDirectory)
        step_CommonMasks = CommonMasks.CommonMasks(cfg,
                                                   config_ressources,
                                                   self.workingDirectory)
        step_coregistration = Coregistration.Coregistration(cfg,
                                                            config_ressources,
                                                            self.workingDirectory)
        step_pixVal = PixelValidity.PixelValidity(cfg,
                                                  config_ressources,
                                                  self.workingDirectory)
        step_env = Envelope.Envelope(cfg,
                                     config_ressources,
                                     self.workingDirectory)
        step_reg_vector = genRegionVector.genRegionVector(cfg,
                                                          config_ressources,
                                                          self.workingDirectory)
        step_vector_form = VectorFormatting.VectorFormatting(cfg,
                                                             config_ressources,
                                                             self.workingDirectory)
        step_split_huge_vec = splitSamples.splitSamples(cfg,
                                                        config_ressources,
                                                        self.workingDirectory)
        step_merge_samples = samplesMerge.samplesMerge(cfg,
                                                       config_ressources,
                                                       self.workingDirectory)
        step_models_samples_stats = statsSamplesModel.statsSamplesModel(cfg,
                                                                        config_ressources,
                                                                        self.workingDirectory)
        step_samples_selection = samplingLearningPolygons.samplingLearningPolygons(cfg,
                                                                                   config_ressources,
                                                                                   self.workingDirectory)
        step_prepare_selection = samplesByTiles.samplesByTiles(cfg,
                                                               config_ressources,
                                                               self.workingDirectory)
        step_generate_learning_samples = samplesExtraction.samplesExtraction(cfg,
                                                                             config_ressources,
                                                                             self.workingDirectory)
        step_merge_learning_samples = samplesByModels.samplesByModels(cfg,
                                                                      config_ressources)
        step_copy_sample_between_models = copySamples.copySamples(cfg,
                                                                  config_ressources,
                                                                  self.workingDirectory)
        step_generate_samples = genSyntheticSamples.genSyntheticSamples(cfg,
                                                                        config_ressources,
                                                                        self.workingDirectory)
        step_dimRed = samplesDimReduction.samplesDimReduction(cfg,
                                                              config_ressources,
                                                              self.workingDirectory)
        step_normalize_samples = samplesNormalization.samplesNormalization(cfg,
                                                                           config_ressources)
        step_learning = learnModel.learnModel(cfg,
                                              config_ressources,
                                              self.workingDirectory)
        step_classiCmd = classiCmd.classiCmd(cfg,
                                             config_ressources,
                                             self.workingDirectory)
        step_classification = classification.classification(cfg,
                                                            config_ressources,
                                                            self.workingDirectory)
        step_confusion_sar_opt = confusionSAROpt.confusionSAROpt(cfg,
                                                                 config_ressources,
                                                                 self.workingDirectory)
        step_confusion_sar_opt_fusion = confusionSAROptMerge.confusionSAROptMerge(cfg,
                                                                                  config_ressources,
                                                                                  self.workingDirectory)
        step_sar_opt_fusion = SAROptFusion.SAROptFusion(cfg,
                                                        config_ressources,
                                                        self.workingDirectory)
        step_classif_fusion = classificationsFusion.classificationsFusion(cfg,
                                                                          config_ressources,
                                                                          self.workingDirectory)
        step_manage_fus_indecision = fusionsIndecisions.fusionsIndecisions(cfg,
                                                                           config_ressources,
                                                                           self.workingDirectory)
        step_mosaic = mosaic.mosaic(cfg,
                                    config_ressources,
                                    self.workingDirectory)
        step_confusions_cmd = confusionCmd.confusionCmd(cfg,
                                                        config_ressources,
                                                        self.workingDirectory)
        step_confusions = confusionGeneration.confusionGeneration(cfg,
                                                                  config_ressources,
                                                                  self.workingDirectory)
        step_confusions_merge = confusionsMerge.confusionsMerge(cfg,
                                                                config_ressources,
                                                                self.workingDirectory)
        step_report = reportGeneration.reportGeneration(cfg,
                                                        config_ressources,
                                                        self.workingDirectory)
        step_merge_iota_classif = mergeSeedClassifications.mergeSeedClassifications(cfg,
                                                                                    config_ressources,
                                                                                    self.workingDirectory)
        step_additional_statistics = additionalStatistics.additionalStatistics(cfg,
                                                                               config_ressources,
                                                                               self.workingDirectory)
        step_additional_statistics_merge = additionalStatisticsMerge.additionalStatisticsMerge(cfg,
                                                                                               config_ressources,
                                                                                               self.workingDirectory)
        step_regularization = Regularization.Regularization(cfg,
                                                            config_ressources,
                                                            self.workingDirectory)
        step_clump = Clump.Clump(cfg,
                                 config_ressources,
                                 self.workingDirectory)
        step_grid = Grid.Grid(cfg,
                              config_ressources,
                              self.workingDirectory)
        step_crown_search = crownSearch.crownSearch(cfg,
                                                    config_ressources,
                                                    self.workingDirectory)
        step_crown_build = crownBuild.crownBuild(cfg,
                                                 config_ressources,
                                                 self.workingDirectory)
        step_large_vecto = largeVectorization.largeVectorization(cfg,
                                                                 config_ressources,
                                                                 self.workingDirectory)
        step_simplification = VectSimplification.simplification(cfg,
                                                                config_ressources,
                                                                self.workingDirectory)
        step_zonal_stats = zonalStatistics.zonalStatistics(cfg,
                                                           config_ressources,
                                                           self.workingDirectory)
        step_join_stats = joinStatistics.joinStatistics(cfg,
                                                        config_ressources,
                                                        self.workingDirectory)

        # control variable
        Sentinel1 = SCF.serviceConfigFile(cfg).getParam('chain', 'S1Path')
        shapeRegion = SCF.serviceConfigFile(
            cfg).getParam('chain', 'regionPath')
        classif_mode = SCF.serviceConfigFile(cfg).getParam(
            'argClassification', 'classifMode')
        sampleManagement = SCF.serviceConfigFile(
            cfg).getParam('argTrain', 'sampleManagement')
        sample_augmentation = dict(SCF.serviceConfigFile(
            cfg).getParam('argTrain', 'sampleAugmentation'))
        sample_augmentation_flag = sample_augmentation["activate"]
        dimred = SCF.serviceConfigFile(cfg).getParam('dimRed', 'dimRed')
        classifier = SCF.serviceConfigFile(
            cfg).getParam('argTrain', 'classifier')
        ds_sar_opt = SCF.serviceConfigFile(cfg).getParam(
            'argTrain', 'dempster_shafer_SAR_Opt_fusion')
        keep_runs_results = SCF.serviceConfigFile(
            cfg).getParam('chain', 'keep_runs_results')
        merge_final_classifications = SCF.serviceConfigFile(
            cfg).getParam('chain', 'merge_final_classifications')
        ground_truth = SCF.serviceConfigFile(
            cfg).getParam('chain', 'groundTruth')
        runs = SCF.serviceConfigFile(cfg).getParam('chain', 'runs')
        outStat = SCF.serviceConfigFile(
            cfg).getParam('chain', 'outputStatistics')
        VHR = SCF.serviceConfigFile(cfg).getParam('coregistration', 'VHRPath')
        gridsize = SCF.serviceConfigFile(
            cfg).getParam('Simplification', 'gridsize')

        # build chain
        # init steps
        s_container.append(step_build_tree, "init")
        s_container.append(step_PreProcess, "init")
        if not "none" in VHR.lower():
            s_container.append(step_coregistration, "init")

        s_container.append(step_CommonMasks, "init")
        s_container.append(step_pixVal, "init")

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
        s_container.append(step_prepare_selection, "sampling")
        s_container.append(step_generate_learning_samples, "sampling")
        s_container.append(step_merge_learning_samples, "sampling")
        if sampleManagement and sampleManagement.lower() != 'none':
            s_container.append(step_copy_sample_between_models, "sampling")
        if sample_augmentation_flag:
            s_container.append(step_generate_samples, "sampling")
        if dimred:
            s_container.append(step_dimRed, "sampling")

        # learning step
        s_container.append(step_learning, "learning")

        # classifications steps
        s_container.append(step_classiCmd, "classification")
        s_container.append(step_classification, "classification")
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
        s_container.append(step_regularization, "regularisation")
        if gridsize is not None:
            s_container.append(step_clump, "regularisation")
            # crown steps
            s_container.append(step_grid, "crown")
            s_container.append(step_crown_search, "crown")
            s_container.append(step_crown_build, "crown")
            # vectorization step
            s_container.append(step_large_vecto, "vectorisation")
        else:
            # vectorization step
            s_container.append(step_simplification, "vectorisation")
        s_container.append(step_zonal_stats, "lcstatistics")
        s_container.append(step_join_stats, "lcstatistics")
        return s_container
