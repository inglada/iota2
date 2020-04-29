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
import math
from functools import partial
from typing import Optional
from collections import OrderedDict
from iota2.Common import ServiceConfigFile as SCF
from typing import List, Dict, Optional


def get_region_area(ground_truth: str,
                    region_file: str,
                    region_field: str,
                    sensor_path: str,
                    epsg_code: int,
                    tiles: List[str],
                    ground_truth_driver: Optional[str] = "ESRI ShapeFile",
                    region_driver: Optional[str] = "ESRI ShapeFile"):
    """
    """
    import time
    from iota2.Common.verifyInputs import get_tile_raster_footprint
    from iota2.Common.FileUtils import sortByFirstElem
    import ogr

    start = time.time()
    areas_container = set()

    multipolygon = ogr.Geometry(ogr.wkbMultiPolygon)
    for cpt, tile in enumerate(tiles):
        # print(f"tile : {cpt+1}/{len(tiles)}")
        geom_raster_envelope = get_tile_raster_footprint(
            tile, sensor_path, epsg_code)
        multipolygon.AddGeometry(geom_raster_envelope)

    driver_reg = ogr.GetDriverByName(region_driver)
    reg_src = driver_reg.Open(region_file, 0)
    reg_layer = reg_src.GetLayer()
    reg_layer.SetSpatialFilter(multipolygon)
    for cpt_reg, region_feat in enumerate(reg_layer):
        # print(f"region {cpt_reg +1}/{len(reg_layer)}")
        region_val = region_feat.GetField(region_field)
        driver_gt = ogr.GetDriverByName(ground_truth_driver)
        gt_src = driver_gt.Open(ground_truth, 0)
        gt_layer = gt_src.GetLayer()
        region_geom = region_feat.GetGeometryRef()
        gt_layer.SetSpatialFilter(region_geom)
        for learning_polygon_gt in gt_layer:
            geom = learning_polygon_gt.GetGeometryRef()
            areas_container.add((region_val, geom.GetArea()))
    end = time.time()
    # print(f"recuperation terminé en {end-start} secondes")
    areas_sorted = sortByFirstElem(areas_container)
    time_sort = time.time()
    # print(f"trie en {time_sort-end} secondes")
    dico = {}

    for area_name, areas in areas_sorted:
        dico[area_name] = sum(areas)
    time_sum = time.time()
    # print(f"calcul des sommes en {time_sum-time_sort} secondes")
    # print(dico)

    return dico


def get_region_tile_distribution(
        sensor_path: str,
        tiles: List[str],
        region_vector_file: str,
        region_vector_datafield: str,
        epsg_code: int,
        region_vector_driver: Optional[str] = "ESRI ShapeFile"
) -> Dict[str, List[str]]:
    """get spatial model repartition across tiles

    Parameters
    ----------
    sensor_path: str
        path to a directory containing sensor's data by tile
    tiles: list
        list of tile's name
    region_vector_file: str
        region shapeFile
    region_vector_datafield: str
        datafield in the region shapeFile discriminating regions
    epsg_code: int
        targeted epsg code
    region_vector_driver: str
        ogr driver's name

    Return
    ------
    dict
        dictionary containing by regions every tiles intersected
    """
    # TODO : manage the Sentinel-1 sensor path is a configuration file
    output_distribution = {}
    import ogr

    from iota2.Common.FileUtils import sortByFirstElem
    from iota2.Common.ServiceError import invalidProjection
    from iota2.VectorTools.vector_functions import get_vector_proj
    from iota2.Common.verifyInputs import get_tile_raster_footprint

    if region_vector_file:
        if int(get_vector_proj(region_vector_file)) != int(epsg_code):
            raise invalidProjection(
                f"wrong projection of {region_vector_file}, must be {epsg_code}"
            )
        region_list = []
        for tile in tiles:
            geom_raster_envelope = get_tile_raster_footprint(
                tile, sensor_path, epsg_code)
            driver_reg = ogr.GetDriverByName(region_vector_driver)
            reg_src = driver_reg.Open(region_vector_file, 0)
            reg_layer = reg_src.GetLayer()
            reg_layer.SetSpatialFilter(geom_raster_envelope)
            for feature in reg_layer:
                region_list.append(
                    (feature.GetField(region_vector_datafield), tile))
        output_distribution_tmp = [
            (model_name, sorted(list(set(tile_list))))
            for model_name, tile_list in sortByFirstElem(region_list)
        ]
        output_distribution = dict(output_distribution_tmp)

    else:
        output_distribution = {"1": tiles}
    return output_distribution


class iota2():
    """
    class use to describe steps sequence and variable to use at each step (config)
    """
    def __init__(self,
                 cfg,
                 config_ressources,
                 hpc_working_directory: Optional[str] = "TMPDIR"):

        self.cfg = cfg
        self.workingDirectory = os.getenv(hpc_working_directory)

        # self.model_spatial_distrib, self.tiles = self.get_run_spatial_informations(
        # )

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

    def get_run_spatial_informations(self):
        """
        Return
        ------
        tuple(dict, list)
            dict[str, dict[str,list[str]; str, int]]:
                dictionary which gives for each model the intersecting tiles
                and the number if sub models to generate if needed
            list : list of all tiles in the run intersecting groundtruth

        >>> get_run_spatial_informations()
        >>> {"1": {"tiles": [T31TCJ, T31TDJ], "nb_sub_models": 2}, ...}
        """
        from iota2.Common.ServiceConfigFile import iota2_parameters
        from iota2.Sensors.Sensors_container import sensors_container
        tiles = SCF.serviceConfigFile(self.cfg).getParam('chain',
                                                         'listTile').split(" ")
        i2_epsg_code = int(
            SCF.serviceConfigFile(self.cfg).getParam(
                'GlobChain', 'proj').replace(" ", "").split(":")[-1])
        output_path = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        region_vector_file = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'regionPath')
        region_vector_datafield = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'regionField')
        region_area_threshold = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'mode_outside_RegionSplit')
        ground_truth = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'groundTruth')
        classif_mode = SCF.serviceConfigFile(self.cfg).getParam(
            'argClassification', 'classifMode')

        running_parameters = iota2_parameters(
            SCF.serviceConfigFile(self.cfg).pathConf)
        sensors_parameters = running_parameters.get_sensors_parameters(
            tiles[0])
        sensor_tile_container = sensors_container(tiles[0], None, output_path,
                                                  **sensors_parameters)
        sensor_path = sensor_tile_container.get_enabled_sensors_path()[0]
        region_distrib = get_region_tile_distribution(sensor_path, tiles,
                                                      region_vector_file,
                                                      region_vector_datafield,
                                                      i2_epsg_code)
        if region_vector_file:
            models_area = get_region_area(ground_truth, region_vector_file,
                                          region_vector_datafield, sensor_path,
                                          i2_epsg_code, tiles)
        spatial_region_info = {}
        spatial_region_info_tmp = {}
        for models_name, tiles in region_distrib.items():
            spatial_region_info_tmp[models_name] = {}
            spatial_region_info_tmp[models_name]["tiles"] = tiles
            spatial_region_info_tmp[models_name]["nb_sub_models"] = None
            if region_vector_file and classif_mode == "fusion":
                spatial_region_info_tmp[models_name][
                    "nb_sub_models"] = math.ceil(
                        models_area[models_name] /
                        (region_area_threshold * 10e5))
        for model_name, model_meta in spatial_region_info_tmp.items():
            nb_sub_models = model_meta["nb_sub_models"]
            if nb_sub_models is not None and nb_sub_models != 1:
                for nb_sub_model in range(nb_sub_models):
                    spatial_region_info[f"{model_name}f{nb_sub_model + 1}"] = {
                        "tiles": model_meta["tiles"]
                    }
            else:
                spatial_region_info[model_name] = {
                    "tiles": model_meta["tiles"]
                }
        run_tiles = []
        for _, tiles in region_distrib.items():
            run_tiles += tiles
        run_tiles = sorted(list(set(run_tiles)))
        return spatial_region_info, run_tiles

    def sort_step(self):
        """
        use to establish which step is going to which step group
        """

        for step_place, step in enumerate(self.steps):
            self.steps_group[step.step_group][
                step_place + 1] = step.func.step_description()

    def print_step_summarize(self,
                             start,
                             end,
                             show_resources=False,
                             checked="x",
                             log=False,
                             running_step=False,
                             running_sym='r'):
        """
        print iota2 steps that will be run
        """
        if log:
            summarize = "Full processing include the following steps (x : done; r : running; f : failed):\n"
        else:
            summarize = "Full processing include the following steps (checked steps will be run):\n"
        step_position = 0
        for group in list(self.steps_group.keys()):
            if len(self.steps_group[group]) > 0:
                summarize += "Group {}:\n".format(group)

            for key in self.steps_group[group]:
                highlight = "[ ]"
                if key >= start and key <= end:
                    highlight = "[{}]".format(checked)
                if key == end and running_step:
                    highlight = "[{}]".format(running_sym)
                summarize += "\t {} Step {}: {}".format(
                    highlight, key, self.steps_group[group][key])
                if show_resources:
                    cpu = self.steps[step_position].resources["cpu"]
                    ram = self.steps[step_position].resources["ram"]
                    walltime = self.steps[step_position].resources["walltime"]
                    resource_block_name = self.steps[step_position].resources[
                        "resource_block_name"]
                    resource_block_found = self.steps[step_position].resources[
                        "resource_block_found"]
                    log_identifier = self.steps[step_position].step_name
                    resource_miss = "" if resource_block_found else " -> MISSING"
                    summarize += "\n\t\t\tresources block name : {}{}\n\t\t\tcpu : {}\n\t\t\tram : {}\n\t\t\twalltime : {}\n\t\t\tlog identifier : {}".format(
                        resource_block_name, resource_miss, cpu, ram, walltime,
                        log_identifier)
                summarize += "\n"
                step_position += 1
        summarize += "\n"
        return summarize

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

    def get_steps_number(self):
        start = SCF.serviceConfigFile(self.cfg).getParam('chain', 'firstStep')
        end = SCF.serviceConfigFile(self.cfg).getParam('chain', 'lastStep')
        start_ind = list(self.steps_group.keys()).index(start)
        end_ind = list(self.steps_group.keys()).index(end)

        steps = []
        for key in list(self.steps_group.keys())[start_ind:end_ind + 1]:
            steps.append(self.steps_group[key])
        step_to_compute = [step for step_group in steps for step in step_group]
        return step_to_compute

    def get_final_i2_exec_graph(self,
                                first_step_index: int,
                                last_step_index: int,
                                output_figure: Optional[str] = None):
        """
        """
        from iota2.Steps.IOTA2Step import Step
        # instanciate steps which must me launched
        steps_to_exe = [
            step() for step in self.steps[first_step_index:last_step_index + 1]
        ]
        if output_figure:
            figure_graph = Step.get_figure_graph()
            figure_graph.visualize(filename=output_figure,
                                   optimize_graph=True,
                                   collapse_outputs=True)
        return Step.get_exec_graph()

    def build_steps(self, cfg, config_ressources=None):
        """
        build steps
        """

        import os
        from iota2.Steps.IOTA2Step import StepContainer
        from iota2.Steps.IOTA2Step import Step

        from Steps import (
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

        # self.model_spatial_distrib = {
        #     '6': {
        #         'tiles': [
        #             'T30TXP', 'T30TXR', 'T30TYP', 'T31TCH', 'T31TCJ', 'T31TDH',
        #             'T31TDJ', 'T31TEH', 'T31TEJ', 'T31TEK', 'T31TFJ', 'T31TFK',
        #             'T31TFL', 'T31TGH', 'T31TGJ', 'T31TGK', 'T32TLP', 'T32TLQ'
        #         ],
        #         'nb_sub_models':
        #         None
        #     },
        #     '4': {
        #         'tiles': [
        #             'T30TXN', 'T30TXP', 'T30TXQ', 'T30TXR', 'T30TYN', 'T30TYP',
        #             'T30TYQ', 'T31TCH', 'T31TCJ', 'T31TCK', 'T31TDH', 'T31TDJ',
        #             'T31TDK', 'T31TEK', 'T31TFK', 'T31TFL', 'T31TGK', 'T31TGL',
        #             'T32TLQ', 'T32TLR'
        #         ],
        #         'nb_sub_models':
        #         None
        #     },
        #     '5': {
        #         'tiles': [
        #             'T30TXN', 'T30TXP', 'T30TXQ', 'T30TXR', 'T30TYQ', 'T31TGK',
        #             'T32TLQ'
        #         ],
        #         'nb_sub_models':
        #         None
        #     },
        #     '2': {
        #         'tiles': [
        #             'T30TXN', 'T30TXP', 'T30TYN', 'T30TYP', 'T31TCH', 'T31TDH',
        #             'T31TDJ', 'T31TDK', 'T31TEJ', 'T31TEK', 'T31TFK', 'T31TFL',
        #             'T31TGJ', 'T31TGK', 'T31TGL', 'T32TLP', 'T32TLQ', 'T32TLR'
        #         ],
        #         'nb_sub_models':
        #         None
        #     },
        #     '1': {
        #         'tiles': [
        #             'T30TXN', 'T30TYN', 'T31TCH', 'T31TDH', 'T31TDJ', 'T31TDK',
        #             'T31TEJ', 'T31TEK', 'T31TFK', 'T31TFL', 'T31TGJ', 'T31TGK',
        #             'T31TGL', 'T32TLP', 'T32TLQ', 'T32TLR'
        #         ],
        #         'nb_sub_models':
        #         None
        #     },
        #     '7': {
        #         'tiles': [
        #             'T30TYP', 'T30TYQ', 'T31TCH', 'T31TCJ', 'T31TCK', 'T31TDH',
        #             'T31TDJ', 'T31TDK', 'T31TFK', 'T31TFL'
        #         ],
        #         'nb_sub_models':
        #         None
        #     },
        #     '8': {
        #         'tiles': [
        #             'T31TDH', 'T31TDJ', 'T31TEH', 'T31TEJ', 'T31TEK', 'T31TFH',
        #             'T31TFJ', 'T31TFK', 'T31TGH', 'T31TGJ', 'T32TLP'
        #         ],
        #         'nb_sub_models':
        #         None
        #     },
        #     '3': {
        #         'tiles': ['T31TFL'],
        #         'nb_sub_models': None
        #     }
        # }

        self.tiles = ["T31TCJ"]
        # self.model_spatial_distrib = {
        #     '1f1': {
        #         'tiles': ["T31TCJ"]
        #     },
        #     '1f2': {
        #         'tiles': ["T31TCJ"]
        #     },
        #     '1f3': {
        #         'tiles': ["T31TCJ"]
        #     },
        #     '2f1': {
        #         'tiles': ['T31TCJ']
        #     },
        #     '2f2': {
        #         'tiles': ['T31TCJ']
        #     },
        #     '2f3': {
        #         'tiles': ['T31TCJ']
        #     }
        # }
        self.model_spatial_distrib = {'1': {'tiles': ["T31TCJ"]}}

        Step.set_models_spatial_information(self.tiles,
                                            self.model_spatial_distrib)
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

        # build chain
        # init steps
        s_container.append(
            partial(IOTA2DirTree.IOTA2DirTree, cfg, config_ressources), "init")
        s_container.append(
            partial(sensorsPreprocess.sensorsPreprocess, cfg,
                    config_ressources, self.workingDirectory), "init")
        if not "none" in VHR.lower():
            s_container.append(
                partial(Coregistration.Coregistration, cfg, config_ressources,
                        self.workingDirectory), "init")
        s_container.append(
            partial(CommonMasks.CommonMasks, cfg, config_ressources,
                    self.workingDirectory), "init")
        s_container.append(
            partial(PixelValidity.PixelValidity, cfg, config_ressources,
                    self.workingDirectory), "init")
        if enable_autoContext:
            s_container.append(
                partial(slicSegmentation.slicSegmentation, cfg,
                        config_ressources, self.workingDirectory), "init")
        # sampling steps
        s_container.append(
            partial(Envelope.Envelope, cfg, config_ressources,
                    self.workingDirectory), "sampling")
        if not shapeRegion:
            s_container.append(
                partial(genRegionVector.genRegionVector, cfg,
                        config_ressources, self.workingDirectory), "sampling")
        s_container.append(
            partial(VectorFormatting.VectorFormatting, cfg, config_ressources,
                    self.workingDirectory), "sampling")
        huge_models = False
        if shapeRegion and classif_mode == "fusion":
            huge_models = True
            s_container.append(
                partial(splitSamples.splitSamples, cfg, config_ressources,
                        self.workingDirectory), "sampling")
        s_container.append(
            partial(samplesMerge.samplesMerge, cfg, config_ressources,
                    self.workingDirectory, huge_models), "sampling")
        s_container.append(
            partial(statsSamplesModel.statsSamplesModel, cfg,
                    config_ressources, self.workingDirectory), "sampling")
        s_container.append(
            partial(samplingLearningPolygons.samplingLearningPolygons, cfg,
                    config_ressources, self.workingDirectory), "sampling")
        if enable_autoContext is True:
            s_container.append(
                partial(superPixPos.superPixPos, cfg, config_ressources,
                        self.workingDirectory), "sampling")
        s_container.append(
            partial(samplesByTiles.samplesByTiles, cfg, config_ressources,
                    enable_autoContext, self.workingDirectory), "sampling")
        s_container.append(
            partial(samplesExtraction.samplesExtraction, cfg,
                    config_ressources, self.workingDirectory), "sampling")
        if enable_autoContext is False:
            s_container.append(
                partial(samplesByModels.samplesByModels, cfg,
                        config_ressources), "sampling")
            transfert_samples = False
            if sampleManagement and sampleManagement.lower() != 'none':
                transfert_samples = True
                s_container.append(
                    partial(copySamples.copySamples, cfg, config_ressources,
                            self.workingDirectory), "sampling")
            if sample_augmentation_flag:
                s_container.append(
                    partial(genSyntheticSamples.genSyntheticSamples, cfg,
                            config_ressources, transfert_samples,
                            self.workingDirectory), "sampling")
            if dimred:
                s_container.append(
                    partial(samplesDimReduction.samplesDimReduction, cfg,
                            config_ressources, transfert_samples
                            and not sample_augmentation_flag,
                            self.workingDirectory), "sampling")
        else:
            s_container.append(
                partial(superPixSplit.superPixSplit, cfg, config_ressources,
                        self.workingDirectory), "sampling")
        # learning
        s_container.append(
            partial(learnModel.learnModel, cfg, config_ressources,
                    self.workingDirectory), "learning")

        s_container.append(
            partial(classification.classification, cfg, config_ressources,
                    self.workingDirectory), "classification")
        if use_scikitlearn:
            s_container.append(
                partial(skClassificationsMerge.ScikitClassificationsMerge, cfg,
                        config_ressources, self.workingDirectory),
                "classification")

        return s_container
