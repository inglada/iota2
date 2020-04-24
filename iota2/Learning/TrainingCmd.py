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

import logging
import os
import numpy as np
from iota2.Common import FileUtils as fu
from iota2.Learning import TrainSkLearn
from iota2.Learning.trainAutoContext import train_autoContext
from iota2.Common.Utils import run
from osgeo import ogr
from typing import Tuple, List, Dict

LOGGER = logging.getLogger(__name__)


def learn_autoContext_model(model_name: str, seed: int,
                            list_learning_samples: List[str],
                            list_superPixel_samples: List[str],
                            list_tiles: List[str], list_slic: List[str],
                            data_field: str, output_path,
                            sensors_parameters: Dict, superpix_data_field: str,
                            iterations: int, ram: int, working_directory: str):
    """
    """
    auto_context_dic = {
        "model_name": model_name,
        "seed": seed,
        "list_learning_samples": list_learning_samples,
        "list_superPixel_samples": list_superPixel_samples,
        "list_tiles": list_tiles,
        "list_slic": list_slic
    }
    train_autoContext(parameter_dict=auto_context_dic,
                      data_field=data_field,
                      output_path=output_path,
                      sensors_parameters=sensors_parameters,
                      superpix_data_field=superpix_data_field,
                      iterations=iterations,
                      RAM=ram,
                      WORKING_DIR=working_directory)


def learn_scikitlearn_model(samples_file: str, output_model: str,
                            data_field: str, sk_model_name: str,
                            apply_standardization: bool,
                            cross_valid_params: Dict, cross_val_grouped: bool,
                            folds_number: int, available_ram: int,
                            sk_model_params: Dict):
    """
    """
    TrainSkLearn.sk_learn(dataset_path=samples_file,
                          features_labels=getFeatures_labels(samples_file),
                          model_path=output_model,
                          data_field=data_field,
                          sk_model_name=sk_model_name,
                          apply_standardization=apply_standardization,
                          cv_parameters=cross_valid_params,
                          cv_grouped=cross_val_grouped,
                          cv_folds=folds_number,
                          available_ram=available_ram,
                          **sk_model_params)


def learn_otb_model(samples_file: str, output_model: str, data_field: str,
                    classifier: str, classifier_options: str) -> None:
    """
    """
    # TODO get statistics if necessary
    # writeStatsFromSample(sample, out_stats, ground_truth, region_field)
    features = " ".join(getFeatures_labels(samples_file))

    cmd = f"otbcli_TrainVectorClassifier -classifier {classifier} {classifier_options} -io.vd {samples_file} -io.out {output_model} -cfield {data_field} -feat {features}"
    LOGGER.error(cmd)
    run(cmd)


def getStatsFromSamples(in_samples: str, ground_truth: str,
                        region_field: str) -> Tuple[List[float], List[float]]:
    """get statistics (mean + std) from a database file

    Parameters
    ----------
    in_samples : str
        path to a database file (SQLite format) generated by iota2
    ground_truth : str
        path to the user database
    region_field : str
        region field

    """
    driver = ogr.GetDriverByName("SQLite")
    if driver.Open(in_samples, 0):
        data_source = driver.Open(in_samples, 0)
    else:
        raise Exception("Can not open : " + in_samples)

    layer = data_source.GetLayer()
    features_fields = fu.getVectorFeatures(ground_truth, region_field,
                                           in_samples)

    all_stat = []
    for current_band in features_fields:
        band_values = []
        for feature in layer:
            val = feature.GetField(current_band)
            if isinstance(val, (float, int)):
                band_values.append(val)
        band_values = np.asarray(band_values)
        mean = np.mean(band_values)
        stddev = np.std(band_values)
        all_stat.append((mean, stddev))
    all_mean = [mean for mean, stddev in all_stat]
    all_std_dev = [stddev for mean, stddev in all_stat]
    return all_mean, all_std_dev


def writeStatsFromSample(InSamples, outStats, ground_truth, region_field):
    """ write statistics by reading samples database
    """
    all_mean, all_std_dev = getStatsFromSamples(InSamples, ground_truth,
                                                region_field)

    with open(outStats, "w") as stats_file:
        stats_file.write('<?xml version="1.0" ?>\n\
            <FeatureStatistics>\n\
            <Statistic name="mean">\n')
        for current_mean in all_mean:
            stats_file.write('        <StatisticVector value="' +
                             str(current_mean) + '" />\n')
        stats_file.write('    </Statistic>\n\
                            <Statistic name="stddev">\n')
        for current_std in all_std_dev:
            stats_file.write('        <StatisticVector value="' +
                             str(current_std) + '" />\n')
        stats_file.write('    </Statistic>\n\
                            </FeatureStatistics>')


def get_svm_normalization_stats(stats_dir, region_name, seed):
    """
    """
    return fu.FileSearch_AND(
        stats_dir, True,
        "samples_region_{}_seed_{}.xml".format(region_name, seed))[0]


def sqlite_to_geojson(input_db: str, output_db: str, logger=LOGGER) -> None:
    """sqlite database to geojson database
    """
    from iota2.Common.Utils import run
    logger.info(f"changin input data format {input_db} to {output_db}")
    run(f'ogr2ogr -f "GeoJSON" {output_db} {input_db}')


def buildTrainCmd_points(r, paths, classif, options, dataField, out, stat,
                         features_labels, model_name):
    """
    shape_ref [param] [string] path to a shape use to determine how many fields
                               are already present before adding features
    """
    nb_columns_limit = 999
    nb_features = len(features_labels.split(" "))
    if nb_features >= nb_columns_limit:
        output_geojson = paths.replace(".sqlite", ".geojson")
        try:
            sqlite_to_geojson(paths, output_geojson)
            os.remove(paths)
            paths = output_geojson
        except:
            raise Exception("changing input dataBase format failed")

    cmd = "otbcli_TrainVectorClassifier -io.vd "
    if paths.count("learn") != 0:
        cmd = cmd + " " + paths

    cmd = cmd + " -classifier " + classif + " " + options + " -cfield " + dataField.lower(
    ) + " -io.out " + out + "/" + model_name
    cmd = cmd + " -feat " + features_labels

    if "svm" in classif.lower():
        cmd = cmd + " -io.stats " + stat
        proba_option = "-classifier.libsvm.prob True"
        if not proba_option in options:
            cmd = "{} {}".format(cmd, proba_option)
    return cmd


def getFeatures_labels(learning_vector):
    """
    """
    nb_no_features = 4
    fields = fu.get_all_fields_in_shape(learning_vector, driver='SQLite')
    return fields[nb_no_features::]


def config_model(outputPath, region_field):
    """
    usage : determine which model will class which tile
    """
    #const
    output = None
    pos_tile = 0
    formatting_vec_dir = os.path.join(outputPath, "formattingVectors")
    samples = fu.FileSearch_AND(formatting_vec_dir, True, ".shp")

    #init
    all_regions = []
    for sample in samples:
        tile_name = os.path.splitext(
            os.path.basename(sample))[0].split("_")[pos_tile]
        regions = fu.getFieldElement(sample,
                                     driverName="ESRI Shapefile",
                                     field=region_field,
                                     mode="unique",
                                     elemType="str")
        for region in regions:
            all_regions.append((region, tile_name))

    #{'model_name':[TileName, TileName...],'...':...,...}
    model_tiles = dict(fu.sortByFirstElem(all_regions))

    #add tiles if they are missing by checking in /shapeRegion/ directory
    shape_region_dir = os.path.join(outputPath, "shapeRegion")
    shape_region_path = fu.FileSearch_AND(shape_region_dir, True, ".shp")

    #check if there is actually polygons
    shape_regions = [
        elem for elem in shape_region_path if len(
            fu.getFieldElement(elem,
                               driverName="ESRI Shapefile",
                               field=region_field,
                               mode="all",
                               elemType="str")) >= 1
    ]
    for shape_region in shape_regions:
        tile = os.path.splitext(
            os.path.basename(shape_region))[0].split("_")[-1]
        region = os.path.splitext(
            os.path.basename(shape_region))[0].split("_")[-2]
        for model_name, tiles_model in list(model_tiles.items()):
            if model_name.split("f")[0] == region and tile not in tiles_model:
                tiles_model.append(tile)

    #Construct output file string
    output = "AllModel:\n["
    for model_name, tiles_model in list(model_tiles.items()):
        output_tmp = "\n\tmodelName:'{}'\n\ttilesList:'{}'".format(
            model_name, "_".join(tiles_model))
        output = output + "\n\t{" + output_tmp + "\n\t}"
    output += "\n]"

    return output


def launch_training(classifier_name: str, classifier_options: str,
                    output_path: str, ground_truth: str, data_field: str,
                    region_field: str, path_to_cmd_train: str,
                    out: str) -> List[str]:
    """ generate training commands

    Parameters
    ----------
    classifier_name: str
        classifier name
    classifier_options: str
        classifier options
    output_path: str
        iota2 output path directory
    ground_truth: str
        path the the database
    data_field: str
        data field in database
    region_field: str
        region field in database
    path_to_cmd_train: str
        path to the directory which will contains training commands
    out: str
        path to iota2 models directory

    Return
    ------
    list
        list of commands as strings
    """
    #const
    pos_model = -3
    pos_seed = -2
    cmd_out = []

    path_to_model_config = output_path + "/config_model/configModel.cfg"
    learning_directory = os.path.join(output_path, "learningSamples")
    samples = fu.FileSearch_AND(learning_directory, True, "Samples_region",
                                "sqlite", "learn")

    config_model_rep = config_model(output_path, region_field)
    if not os.path.exists(path_to_model_config):
        with open(path_to_model_config, "w") as config_file:
            config_file.write(config_model_rep)

    cmd_out = []

    for sample in samples:
        features_labels = getFeatures_labels(sample)
        suffix = ""
        pos_model_sample = pos_model
        pos_seed_sample = pos_seed
        if "SAR.sqlite" in os.path.basename(sample):
            pos_model_sample = pos_model - 1
            pos_seed_sample = pos_seed - 1
            suffix = "_SAR"
        model = os.path.split(sample)[-1].split("_")[pos_model_sample]
        seed = os.path.split(sample)[-1].split("_")[pos_seed_sample].split(
            "seed")[-1]
        out_stats = None
        if classifier_name.lower() == "svm" or classifier_name.lower(
        ) == "libsvm":
            out_stats = os.path.join(
                output_path, "stats",
                "Model_{}_seed_{}.xml".format(model, seed))
            if os.path.exists(out_stats):
                os.remove(out_stats)
            writeStatsFromSample(sample, out_stats, ground_truth, region_field)

        model_name = "model_{}_seed_{}{}.txt".format(model, seed, suffix)
        cmd = buildTrainCmd_points(model, sample, classifier_name,
                                   classifier_options, data_field, out,
                                   out_stats, " ".join(features_labels),
                                   model_name)
        cmd_out.append(cmd)

    fu.writeCmds(path_to_cmd_train + "/train.txt", cmd_out)
    return cmd_out
