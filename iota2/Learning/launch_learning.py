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
import numpy as np
from osgeo import ogr
from typing import Tuple, List, Dict

from iota2.Common.Utils import run
from iota2.Common import FileUtils as fu
from iota2.Learning import TrainSkLearn
from iota2.Learning.trainAutoContext import train_autoContext


def getFeatures_labels(learning_vector):
    """
    """
    nb_no_features = 4
    fields = fu.get_all_fields_in_shape(learning_vector, driver='SQLite')
    return fields[nb_no_features::]


def learn_autocontext_model(model_name: str, seed: int,
                            list_learning_samples: List[str],
                            list_superPixel_samples: List[str],
                            list_slic: List[str], data_field: str, output_path,
                            superpix_data_field: str, iterations: int,
                            ram: int, working_directory: str):
    """
    """
    # TODO : if nb features > 999 convert to sqlite to geojson
    auto_context_dic = {
        "model_name": model_name,
        "seed": seed,
        "list_learning_samples": list_learning_samples,
        "list_superPixel_samples": list_superPixel_samples,
        "list_slic": list_slic
    }
    features_list_name = getFeatures_labels(list_learning_samples[0])

    for slic_field in ["superpix", "is_super_pix"]:
        if slic_field in features_list_name:
            features_list_name.remove(slic_field)

            train_autoContext(parameter_dict=auto_context_dic,
                              data_field=data_field,
                              output_path=output_path,
                              features_list_name=features_list_name,
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
                    classifier: str, classifier_options: str,
                    i2_running_dir: str, model_name: str, seed: int,
                    region_field: str, ground_truth: str) -> None:
    """
    """
    # TODO : if nb features > 999 convert to sqlite to geojson
    features = " ".join(getFeatures_labels(samples_file))

    cmd = f"otbcli_TrainVectorClassifier -classifier {classifier} {classifier_options} -io.vd {samples_file} -io.out {output_model} -cfield {data_field.lower()} -feat {features}"
    if classifier.lower() == "svm" or classifier.lower() == "libsvm":
        learning_stats_file = os.path.join(
            i2_running_dir, "stats",
            "Model_{}_seed_{}.xml".format(model_name, seed))
        if os.path.exists(learning_stats_file):
            os.remove(learning_stats_file)
        writeStatsFromSample(samples_file, learning_stats_file, ground_truth,
                             region_field)
        cmd = f"{cmd} -io.stats {learning_stats_file}"
    run(cmd)


def writeStatsFromSample(InSamples, outStats, ground_truth,
                         region_field) -> None:
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
