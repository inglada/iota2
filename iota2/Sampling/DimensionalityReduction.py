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
The dimensionality reduction module
"""
import os
import shutil
# import string
import glob
import logging
import argparse
from logging import Logger
from typing import Optional, Dict, List, Tuple, TypeVar, Union, Set
import otbApplication as otb
from iota2.Common import FileUtils as fu
from iota2.Common import OtbAppBank
from iota2.VectorTools import join_sqlites as jsq

# root logger
LOGGER = logging.getLogger(__name__)
otb_app_type = TypeVar('otbApplication')
otb_dep_type = List[Union[otb_app_type, List[otb_app_type]]]


def get_available_features(input_sample_file_name: str,
                           first_level: Optional[str] = 'sensor',
                           second_level: Optional[str] = 'band'
                           ) -> Tuple[Dict[str, Set[str]], List[str]]:
    """
    Parameters
    ----------
    input_sample_file_name: string
    first_level: string
    second_level: string
    Return
    ------
    Tuple(dict[str,dict[str, set(str)]], list(str) )
    Notes
    -----
    Assumes that the features are named following a pattern like
    sensor_date_band : S2_b1_20170324. Returns a dictionary containing
    the available features in a 3 level data structure (dict of dicts
    of lists). For example, if first level is sensor and second level
    is band:

    {'S2' : { 'b1' : {'20170324', '20170328'},
              'ndvi' : {'20170324', '20170328'}, },
     'L8' : ...}

    The number of meta data fields is needed to eliminate the first
    fields in the file.

    """
    # getAllFieldsInShape
    feature_list = fu.get_all_fields_in_shape(input_sample_file_name, 'SQLite')
    features = dict()

    meta_data_fields = []
    for feat in feature_list:
        try:
            (sensor, band, date) = feat.split('_')
            fi_lv = sensor
            se_lv = band
            th_lv = date
            if first_level == 'global':
                pass
            if first_level == 'sensor':
                fi_lv = sensor
                if second_level == 'band':
                    se_lv = band
                    th_lv = date
                else:
                    se_lv = date
                    th_lv = band
            elif first_level == 'band':
                fi_lv = band
                if second_level == 'date':
                    se_lv = date
                    th_lv = sensor
                else:
                    se_lv = sensor
                    th_lv = date
            elif first_level == 'date':
                fi_lv = date
                if second_level == 'band':
                    se_lv = band
                    th_lv = sensor
                else:
                    se_lv = sensor
                    th_lv = band
            if fi_lv not in list(features.keys()):
                features[fi_lv] = dict()
            if se_lv not in list(features[fi_lv].keys()):
                features[fi_lv][se_lv] = list()
            features[fi_lv][se_lv].append(th_lv)
        except:
            if feat not in meta_data_fields:
                meta_data_fields.append(feat)
    if first_level == 'global':
        return (feature_list[len(meta_data_fields):], meta_data_fields)
    return (features, meta_data_fields)


# def BuildFeaturesLists(inputSampleFileName, reductionMode='global'):
def build_features_lists(input_sample_file_name: str,
                         reduction_mode: Optional[str] = 'global'
                         ) -> Tuple[List[str], List[str]]:
    """
    Parameters
    ----------
    input_sample_file_name: string
    reduction_mode: string
    Return
    ------
    tuple(list(string), list(string))
    Notes
    -----
    Build a list of lists of the features containing the features to be
    used for each reduction.

    'global' reduction mode selects all the features

    'sensor_band' reduction mode selects all the dates for each
    feature of each sensor (we don't mix L8 and S2 ndvi)

    'sensor_date' reduction mode selects all the features for each
    date for each sensor (we don't mix sensors if the have common
    dates)

    'date' reduction mode selects all the features for each date (we
    mix sensors if the have common dates)

    'sensor' reduction mode selects all the features for a particular
    sensor

    'band' all the dates for each band (we mix L8 and S2 ndvi)

    """
    (all_features,
     meta_data_fields) = get_available_features(input_sample_file_name,
                                                'global')

    feat_list = list()
    if reduction_mode == 'global':
        feat_list.append(all_features)
    elif reduction_mode == 'sensor_date':
        (feat_dict, dummy) = get_available_features(input_sample_file_name,
                                                    'date', 'sensor')
        for date in sorted(feat_dict.keys()):
            tmpfeat_list = list()
            for sensor in sorted(feat_dict[date].keys()):
                tmpfeat_list += [
                    "%s_%s_%s" % (sensor, band, date)
                    for band in feat_dict[date][sensor]
                ]
            feat_list.append(tmpfeat_list)
    elif reduction_mode == 'date':
        (feat_dict, dummy) = get_available_features(input_sample_file_name,
                                                    'date', 'sensor')
        for date in sorted(feat_dict.keys()):
            tmpfeat_list = list()
            for sensor in sorted(feat_dict[date].keys()):
                tmpfeat_list += [
                    "%s_%s_%s" % (sensor, band, date)
                    for band in feat_dict[date][sensor]
                ]
            feat_list.append(tmpfeat_list)
    elif reduction_mode == 'sensor_band':
        (feat_dict, dummy) = get_available_features(input_sample_file_name,
                                                    'sensor', 'band')
        for sensor in sorted(feat_dict.keys()):
            for band in sorted(feat_dict[sensor].keys()):
                feat_list.append([
                    "%s_%s_%s" % (sensor, band, date)
                    for date in feat_dict[sensor][band]
                ])
    elif reduction_mode == 'band':
        (feat_dict, dummy) = get_available_features(input_sample_file_name,
                                                    'band', 'sensor')
        for band in sorted(feat_dict.keys()):
            tmpfeat_list = list()
            for sensor in sorted(feat_dict[band].keys()):
                tmpfeat_list += [
                    "%s_%s_%s" % (sensor, band, date)
                    for date in feat_dict[band][sensor]
                ]
            feat_list.append(tmpfeat_list)
    elif reduction_mode == 'sensor_date':
        (feat_dict, dummy) = get_available_features(input_sample_file_name,
                                                    'sensor', 'date')
        for sensor in sorted(feat_dict.keys()):
            for date in sorted(feat_dict[sensor].keys()):
                feat_list.append([
                    "%s_%s_%s" % (sensor, band, date)
                    for band in feat_dict[sensor][date]
                ])
    else:
        raise RuntimeError("Unknown reduction mode")
    if len(feat_list) == 0:
        raise Exception("Did not find any valid features in " +
                        input_sample_file_name)
    return (feat_list, meta_data_fields)


def compute_feature_statistics(input_sample_file_name: str,
                               output_stats_file: str,
                               feature_list: List[str]) -> None:
    """
    Parameters
    ----------
    input_sample_file_name: string
    output_stats_file : string
    feature_list: list(string)
    Return
    ------
    None
    Notes
    -----
    Computes the mean and the standard deviation of a set of features
    of a file of samples. It will be used for the dimensionality
    reduction training and reduction applications.
    """
    cstats = otb.Registry.CreateApplication(
        "ComputeOGRLayersFeaturesStatistics")
    cstats.SetParameterString("inshp", input_sample_file_name)
    cstats.SetParameterString("outstats", output_stats_file)
    cstats.UpdateParameters()
    cstats.SetParameterStringList("feat", feature_list)
    cstats.ExecuteAndWriteOutput()


def train_dimensionality_reduction(input_sample_file_name: str,
                                   output_model_file_name: str,
                                   feature_list: List[str],
                                   target_dimension: int,
                                   stats_file: Optional[str] = None) -> None:
    """
    Parameters
    ----------
    input_sample_file_name: string
    output_model_file_name: string
    feature_list: list(str)
    target_dimension: integer
    stats_file: string
    Return
    ------
    None
    """
    drtrain = otb.Registry.CreateApplication("TrainDimensionalityReduction")
    drtrain.SetParameterString("io.vd", input_sample_file_name)
    drtrain.SetParameterStringList("feat", feature_list)
    if stats_file is not None:
        drtrain.SetParameterString("io.stats", stats_file)
    drtrain.SetParameterString("io.out", output_model_file_name)
    drtrain.SetParameterString("algorithm", "pca")
    drtrain.SetParameterInt("algorithm.pca.dim", target_dimension)
    drtrain.ExecuteAndWriteOutput()


def extract_meta_data_fields(input_sample_file_name: str,
                             reduced_output_file_name: str) -> None:
    """
    Parameters
    ----------
    input_sample_file_name: string
    reduced_output_file_name: string
    Return
    ------
    None
    Notes
    -----
    Extract MetaDataFields from input vector file in order to append reduced
    fields
    """
    from iota2.Common.Utils import run

    reduced_output_file_name_table = "output"

    (_, meta_data_fields) = get_available_features(input_sample_file_name,
                                                   'global')

    fields = ",".join(meta_data_fields)
    cmd = (f"ogr2ogr -dialect 'SQLITE' -nln {reduced_output_file_name_table} "
           f"-f 'SQLite' -select '{fields}' "
           f"{reduced_output_file_name} {input_sample_file_name}")
    run(cmd)


def apply_dimensionality_reduction(input_sample_file_name,
                                   reduced_output_file_name,
                                   model_file_name,
                                   input_features,
                                   output_features,
                                   stats_file: Optional[str] = None,
                                   pca_dimension: Optional[str] = None,
                                   writing_mode: Optional[str] = 'update'
                                   ) -> None:
    """
    Parameters
    ----------
    input_sample_file_name: string
    reduced_output_file_name: string
    model_file_name: string
    input_features: string
    output_features: string
    input_dimensions: string
    stats_file: string
    pca_dimension: string
    writing_mode: string
    Return
    ------
    None
    """
    extract_meta_data_fields(input_sample_file_name, reduced_output_file_name)

    drapply = otb.Registry.CreateApplication("VectorDimensionalityReduction")
    drapply.SetParameterString("in", input_sample_file_name)
    drapply.SetParameterString("out", reduced_output_file_name)
    drapply.SetParameterString("model", model_file_name)
    drapply.UpdateParameters()
    drapply.SetParameterStringList("feat", input_features)
    drapply.SetParameterString("featout", "list")
    drapply.SetParameterStringList("featout.list.names", output_features)

    if stats_file is not None:
        drapply.SetParameterString("instat", stats_file)
    if pca_dimension is not None:
        drapply.SetParameterInt("pcadim", pca_dimension)
    drapply.SetParameterString("mode", writing_mode)
    drapply.ExecuteAndWriteOutput()


def join_reduced_sample_files(input_file_list: str,
                              output_sample_file_name: str,
                              component_list: Optional[str] = None,
                              renaming: Optional[str] = None) -> None:
    """
    Parameters
    ----------
    input_file_list: string
    output_sample_file_name: string
    component_list: string
    renaming: string
    Return
    ------
    None
    Notes
    -----
    Join the columns of several sample files assuming that they all
    correspond to the same samples and that they all have the same
    names for the fields to copy (component_list). They are joined
    using the ogc_fid field which is supposed to uniquely identify the
    samples.

    """

    # Copy the first file to merge as de destination
    shutil.copyfile(input_file_list[0], output_sample_file_name)

    jsq.join_sqlites(output_sample_file_name,
                     input_file_list[1:],
                     'ogc_fid',
                     component_list,
                     renaming=renaming)


def sample_file_pca_reduction(input_sample_file_name: str,
                              output_sample_file_name: str,
                              reduction_mode: str,
                              target_dimension: str,
                              tmp_dir: Optional[str] = '/tmp',
                              remove_tmp_files: Optional[str] = 'False'
                              ) -> None:
    """usage : Apply a PCA reduction

    IN:
    input_sample_file_name [string] : path to a vector file containing training samples
    reduction_mode [string] : 'date', 'band', 'global' modes of PCA application

    The names of the fields containing the features are supposed to follow the pattern

    sensor_band_date

    OUT:
    outputSampleFileName [string] : name of the resulting reduced sample file

    """

    (feature_list,
     meta_data_fields) = build_features_lists(input_sample_file_name,
                                              reduction_mode)
    reduced_features = [
        'reduced_' + str(pc_number) for pc_number in range(target_dimension)
    ]

    files_to_remove = list()
    reduced_file_list = list()
    fl_counter = 0

    basename = os.path.basename(input_sample_file_name)[:-(len('sqlite') + 1)]
    for feat in feature_list:
        stats_file = tmp_dir + '/' + basename + '_stats_' + str(
            fl_counter) + '.xml'
        model_file = tmp_dir + '/' + basename + '_model_' + str(fl_counter)
        reduced_sample_file = tmp_dir + '/' + basename + '_reduced_' + str(
            fl_counter) + '.sqlite'
        files_to_remove.append(stats_file)
        files_to_remove.append(model_file)
        files_to_remove.append(reduced_sample_file)
        reduced_file_list.append(reduced_sample_file)
        fl_counter += 1
        compute_feature_statistics(input_sample_file_name, stats_file, feat)
        train_dimensionality_reduction(input_sample_file_name, model_file,
                                       feat, target_dimension, stats_file)
        apply_dimensionality_reduction(input_sample_file_name,
                                       reduced_sample_file, model_file, feat,
                                       reduced_features, stats_file)

    join_reduced_sample_files(reduced_file_list,
                              output_sample_file_name,
                              reduced_features,
                              renaming=('reduced', target_dimension))

    if remove_tmp_files:
        for ifile in files_to_remove:
            os.remove(ifile)


def rename_sample_files(in_sample_file: str, out_sample_file: str,
                        output_dir: str) -> None:
    """
    Parameters
    ----------
    in_sample_file: string
    out_sample_file: string
    output_dir: string
    Return
    ------
    None
    """
    backup_dir = output_dir + "/dimRed/before_reduction"
    backup_file = backup_dir + '/' + os.path.basename(in_sample_file)
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    shutil.copyfile(in_sample_file, backup_file)
    shutil.copyfile(out_sample_file, in_sample_file)


def retrieve_original_sample_file(in_sample_file: str,
                                  output_dir: str) -> None:
    """
    Parameters
    ----------
    in_sample_file: string
    output_dir: string
    Return
    ------
    None
    Notes
    -----
    If the chain runs after the dimensionality reduction has already
    been done during a previous run, the input sample file available in
    learningSamples is not the original one, but the result of a
    reduction. We have to retrieve the original one which was saved into
    dimRed/before_reduction and copy it to learningSamples."""
    backup_dir = output_dir + "/dimRed/before_reduction"
    backup_file = backup_dir + '/' + os.path.basename(in_sample_file)
    if os.path.isfile(backup_file):
        shutil.copyfile(backup_file, in_sample_file)


def sample_file_dimensionality_reduction(in_sample_file: str,
                                         out_sample_file: str, output_dir: str,
                                         target_dimension: int,
                                         reduction_mode: str) -> None:
    """
    Parameters
    ----------
    in_sample_file: string
    out_sample_file: string
    output_dir: string
    target_dimension: string
    reduction_mode: string
    Return
    ------
    None
    Notes
    -----
    Applies the dimensionality reduction on a file of samples and gets
    the parameters from the configuration file"""
    reduced_samples_dir = output_dir + "/dimRed/reduced"
    if not os.path.exists(reduced_samples_dir):
        os.makedirs(reduced_samples_dir)
    sample_file_pca_reduction(in_sample_file,
                              out_sample_file,
                              reduction_mode,
                              target_dimension,
                              reduced_samples_dir,
                              remove_tmp_files=False)
    rename_sample_files(in_sample_file, out_sample_file, output_dir)


def sample_dimensionality_reduction(io_file_pair: str, iota2_output: str,
                                    target_dimension: int,
                                    reduction_mode: str) -> None:
    """
    Parameters
    ----------
    io_file_pair: string
    iota2_output: string
    target_dimension: string
    reduction_mode: string
    Return
    ------
    None
    Notes
    -----
    Applies the dimensionality reduction to all sample files and gets
    the parameters from the configuration file"""
    (in_sample_file, out_sample_file) = io_file_pair
    retrieve_original_sample_file(in_sample_file, iota2_output)
    sample_file_dimensionality_reduction(in_sample_file, out_sample_file,
                                         iota2_output, target_dimension,
                                         reduction_mode)


def build_io_sample_file_lists(output_dir: str) -> List[str]:
    """
    Parameters
    ----------
    output_dir: string
    Return
    ------
    list(str)
    """
    sample_file_dir = os.path.join(output_dir, "learningSamples")
    reduced_samples_dir = os.path.join(output_dir, "dimRed", "reduced")
    result = list()
    for input_sample_file in glob.glob(sample_file_dir + '/*sqlite'):
        basename = os.path.basename(input_sample_file)[:-(len('sqlite') + 1)]
        output_sample_file = os.path.join(reduced_samples_dir,
                                          basename + '_reduced.sqlite')
        result.append((input_sample_file, output_sample_file))
    return result


def get_dim_red_models_from_classification_model(
        classification_model: str,
        logger: Optional[Logger] = LOGGER) -> List[str]:
    """
    Parameters
    ----------
    classification_model: string
    Return
    ------
    list(str)
    Notes
    -----
    Builds the name and path of the dimensionality model from the
    classification model matching the region and the seed
    output/model/model_1_seed_0.txt gives
    dimRed/reduced/Samples_region_1_seed0_learn_model_*
    """

    fname = classification_model.split('/')[-1]
    logger.debug(f"fname : {fname}")
    output_dir = classification_model.split('/')[:-2] + os.sep
    fname = fname.split('.')[0]
    [_, region, _, seed] = fname.split('_')
    logger.debug(f"fname : {fname} | outputDir : {output_dir} | region :"
                 f" {region} | seed {seed}")
    models = glob.glob(output_dir + '/dimRed/reduced/Samples_region_' +
                       str(region) + '_seed' + str(seed) + '_learn_model_*txt')
    logger.debug(f"{models}")
    models = [m[:-4] for m in models]
    logger.debug(f"{sorted(models)}")
    return sorted(models)


def build_channel_groups(reduction_mode: str,
                         output_path: str,
                         logger: Optional[Logger] = LOGGER):
    """
    Parameters
    ----------
    reduction_mode: string
    output_path: string
    Return
    ------
    list(list(str))
    Notes
    -----
    Build the lists of channels which have to be extracted from the
    time series stack in order to apply the dimensionality reduction.
    The operation consists in translating the features selected for
    each date/band group into the channel indices for the ExtractROI
    application.

    We use the original sample files (before reduction) to deduce the
    position of the features.

    """
    backup_dir = os.path.join(output_path, "dimRed", "before_reduction")
    # Any original sample file will do, because we only need the names
    input_sample_file_name = glob.glob(backup_dir + '/*sqlite')[0]
    (feature_groups,
     meta_data_fields) = build_features_lists(input_sample_file_name,
                                              reduction_mode)
    number_of_meta_data_fields = len(meta_data_fields)
    feature_list = fu.get_all_fields_in_shape(
        input_sample_file_name, 'SQLite')[number_of_meta_data_fields:]
    channel_groups = list()
    for feat_g in feature_groups:
        # Channels start at 1 for ExtractROI
        logger.debug(f"Feature group {feat_g}")
        chan_l = [f'Channel{feature_list.index(x) + 1}' for x in feat_g]
        logger.debug(f"Channels {chan_l}".format(chan_l))
        channel_groups.append(chan_l)
    return channel_groups


def apply_dimensionality_reduction_to_feature_stack(
        reduction_mode: str,
        output_path: str,
        image_stack: str,
        dim_red_model_list: str,
        logger: Optional[Logger] = LOGGER
) -> Tuple[otb_app_type, otb_dep_type]:
    """Apply dimensionality reduction to the full stack of features. A
    list of dimensionality reduction models is provided since the
    reduction can be done per date, band, etc. The rationale is
    extracting the features for each model, applying each model, then
    concatenating the resulting reduced images tu build the final
    reduced stack.

    """
    # Build the feature list
    extract_rois = list()
    dim_reds = list()
    channel_groups = build_channel_groups(reduction_mode, output_path)

    if isinstance(image_stack, otb.Application):
        image_stack.Execute()
    for (chan_list, model) in zip(channel_groups, dim_red_model_list):
        stats_file = model + '.xml'
        stats_file = stats_file.replace('model', 'stats')
        # Extract the features
        logger.debug(f"Model : {model}")
        logger.debug(f"Stats file : {stats_file}")
        logger.debug(f"Channel list : {chan_list}")

        extract_roi_app = otb.Registry.CreateApplication("ExtractROI")
        if isinstance(image_stack, str):
            extract_roi_app.SetParameterString("in", image_stack)
        elif isinstance(image_stack, otb.Application):
            extract_roi_app.SetParameterInputImage(
                "in", image_stack.GetParameterOutputImage("out"))

        extract_roi_app.UpdateParameters()
        extract_roi_app.SetParameterStringList("cl", chan_list)
        extract_roi_app.Execute()
        extract_rois.append(extract_roi_app)
        # Apply the reduction
        dim_red_app = otb.Registry.CreateApplication(
            "ImageDimensionalityReduction")
        dim_red_app.SetParameterInputImage(
            "in", extract_roi_app.GetParameterOutputImage("out"))
        dim_red_app.SetParameterString("model", model)
        dim_red_app.SetParameterString("imstat", stats_file)
        dim_red_app.Execute()
        dim_reds.append(dim_red_app)
    # Concatenate reduced features
    logger.debug(f"Channel groups : {channel_groups}")
    logger.debug(f"Dimred models : {dim_red_model_list}")
    logger.debug(f"DimRed list : {dim_reds}")

    concatenate_app = OtbAppBank.CreateConcatenateImagesApplication({
        "il": dim_reds,
        "out": ""
    })
    return concatenate_app, [extract_rois, dim_reds, image_stack]


if __name__ == "__main__":

    PARSER = argparse.ArgumentParser(
        description="Apply dimensionality reduction to a sample file")
    PARSER.add_argument("-in",
                        dest="inSampleFile",
                        help="path to the input sample file",
                        default=None,
                        required=True)
    PARSER.add_argument("-out",
                        dest="outSampleFile",
                        help="path to the output sample file",
                        default=None,
                        required=True)
    PARSER.add_argument("-target_dim",
                        help="target dimension (mandatory)",
                        dest="target_dim",
                        required=True)
    PARSER.add_argument("-redu_mode",
                        help="reduction mode (mandatory)",
                        dest="reduc_mode",
                        required=True)
    PARSER.add_argument("-output_dir",
                        help="the output path (mandatory)",
                        dest="output_dir",
                        required=True)
    ARGS = PARSER.parse_args()

    if ARGS.conf:
        sample_file_dimensionality_reduction(ARGS.inSampleFile,
                                             ARGS.outSampleFile,
                                             ARGS.output_dir, ARGS.target_dim,
                                             ARGS.redu_mode)
    else:
        sample_file_pca_reduction(ARGS.inSampleFile, ARGS.outSampleFile,
                                  'date', 6, 5)
