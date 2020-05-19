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
Module for initialize default parameter of any config file.
These functions return dictionnary ready to be set using the
init_section function.

If a parameter is given in a configuration file the default values is not used.
"""
from config import Sequence, Mapping


def dico_mapping_init(my_dict):
    """
    use to init a mapping object from a dict
    """
    new_map = Mapping()
    for key, value in list(my_dict.items()):
        new_map.addMapping(key, value, "")
    return new_map


def list_sequence_init(my_list):
    """
    use to init a Sequence object from a list
    """
    new_seq = Sequence()
    for elem in my_list:
        new_seq.append(elem, "#comment")
    return new_seq


def init_chain_parameters():
    """
    Set all chain block parameters to default values
    """
    chain_default = {
        "outputStatistics": False,
        "L5Path_old": "None",
        "L5_old_output_path": None,
        "L8Path": "None",
        "L8_output_path": None,
        "L8Path_old": "None",
        "L8_old_output_path": None,
        "S2Path": "None",
        "S2_output_path": None,
        "S2_S2C_Path": "None",
        "S2_S2C_output_path": None,
        "S2_L3A_Path": "None",
        "S2_L3A_output_path": None,
        "S1Path": "None",
        "userFeatPath": "None",
        "jobsPath": None,
        "runs": 1,
        "enableCrossValidation": False,
        "model": "None",
        "cloud_threshold": 0,
        "splitGroundTruth": True,
        "ratio": 0.5,
        "random_seed": None,
        "firstStep": "init",
        "lastStep": "validation",
        "logFileLevel": "INFO",
        "mode_outside_RegionSplit": 0.1,
        "logFile": "iota2LogFile.log",
        "logConsoleLevel": "INFO",
        "regionPath": None,
        "regionField": "region",
        "logConsole": True,
        "enableConsole": False,
        "merge_final_classifications": False,
        "merge_final_classifications_method": "majorityvoting",
        "merge_final_classifications_undecidedlabel": 255,
        "fusionOfClassificationAllSamplesValidation": False,
        "dempstershafer_mob": "precision",
        "merge_final_classifications_ratio": 0.1,
        "keep_runs_results": True,
        "check_inputs": True,
        "enable_autoContext": False,
        "autoContext_iterations": 3,
        "remove_tmp_files": False,
        "force_standard_labels": False
    }
    return chain_default


def init_corregistration_parameters():
    """
    Set all corregistration block parameters to default values
    """
    coregistration_default = {
        "VHRPath": "None",
        "dateVHR": "None",
        "dateSrc": "None",
        "bandRef": 1,
        "bandSrc": 3,
        "resample": True,
        "step": 256,
        "minstep": 16,
        "minsiftpoints": 40,
        "iterate": True,
        "prec": 3,
        "mode": 2,
        "pattern": "None"
    }

    return coregistration_default


def init_sklearn_parameters():
    """
    Set all sklearn block parameters to default values
    """
    sklearn_default = {
        "model_type": None,
        "cross_validation_folds": 5,
        "cross_validation_grouped": False,
        "standardization": False,
        "cross_validation_parameters": dico_mapping_init({})
    }
    return sklearn_default


def init_arg_train_parameters():
    """
    Set all argTrain block parameters to default values
    """
    sample_sel_default = dico_mapping_init({
        "sampler": "random",
        "strategy": "all"
    })
    sample_augmentationg_default = dico_mapping_init({"activate": False})
    annual_crop = list_sequence_init(["11", "12"])
    a_crop_label_replacement = list_sequence_init(["10", "annualCrop"])

    arg_train_default = {
        "sampleSelection": sample_sel_default,
        "sampleAugmentation": sample_augmentationg_default,
        "sampleManagement": None,
        "dempster_shafer_SAR_Opt_fusion": False,
        "cropMix": False,
        "prevFeatures": "None",
        "outputPrevFeatures": "None",
        "annualCrop": annual_crop,
        "ACropLabelReplacement": a_crop_label_replacement,
        "samplesClassifMix": False,
        "classifier": "rf",
        "options": " -classifier.rf.min 5 -classifier.rf.max 25 ",
        "annualClassesExtractionSource": "None",
        "validityThreshold": 1
    }

    return arg_train_default


def init_classification_parameters():
    """
    Set all classification block parameters to default values
    """

    arg_classification_default = {
        "noLabelManagement": "maxConfidence",
        "enable_probability_map": False,
        "fusionOptions": "-nodatalabel 0 -method majorityvoting"
    }
    return arg_classification_default


def init_glob_chain_parameters():
    """
    Set all globChain block parameters to default values
    """
    glob_chain_default = {
        "features": list_sequence_init(["NDVI", "NDWI", "Brightness"]),
        "autoDate": True,
        "writeOutputs": False,
        "useAdditionalFeatures": False,
        "useGapFilling": True
    }
    return glob_chain_default


def init_i2_features_extraction_parameters():
    """
    Set all iota2FeatureExtraction block parameters to default values
    """
    iota2_feature_extraction_default = {
        "copyinput": True,
        "relrefl": False,
        "keepduplicates": True,
        "extractBands": False,
        "acorfeat": False
    }
    return iota2_feature_extraction_default


def init_dim_reduction_parameters():
    """
    Set all dimRed block parameters to default values
    """
    dim_red_default = {
        "dimRed": False,
        "targetDimension": 4,
        "reductionMode": "global"
    }
    return dim_red_default


def init_landsat8_parameters():
    """
    Set all Landsat8 block parameters to default values
    """
    landsat8_default = {
        "additionalFeatures": "",
        "temporalResolution": 16,
        "write_reproject_resampled_input_dates_stack": True,
        "startDate": "",
        "endDate": "",
        "keepBands":
        list_sequence_init(["B1", "B2", "B3", "B4", "B5", "B6", "B7"])
    }
    return landsat8_default


def init_landsat8_old_parameters():
    """
    Set all Landsat8_old block parameters to default values
    """
    landsat8_old_default = {
        "additionalFeatures": "",
        "temporalResolution": 16,
        "startDate": "",
        "endDate": "",
        "keepBands":
        list_sequence_init(["B1", "B2", "B3", "B4", "B5", "B6", "B7"])
    }
    return landsat8_old_default


def init_landsat5_old_parameters():
    """
    Set all Landsat5_old block parameters to default values
    """
    landsat5_old_default = {
        "additionalFeatures": "",
        "temporalResolution": 16,
        "startDate": "",
        "endDate": "",
        "keepBands": list_sequence_init(["B1", "B2", "B3", "B4", "B5", "B6"])
    }
    return landsat5_old_default


def init_sentinel2_parameters():
    """
    Set all Sentinel_2 block parameters to default values
    """
    sentinel_2_default = {
        "additionalFeatures":
        "",
        "temporalResolution":
        10,
        "write_reproject_resampled_input_dates_stack":
        True,
        "startDate":
        "",
        "endDate":
        "",
        "keepBands":
        list_sequence_init(
            ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"])
    }
    return sentinel_2_default


def init_sentinel2_s2c_parameters():
    """
    Set all Sentinel_2_S2C block parameters to default values
    """
    sentinel_2_s2c_default = {
        "additionalFeatures":
        "",
        "temporalResolution":
        10,
        "write_reproject_resampled_input_dates_stack":
        True,
        "startDate":
        "",
        "endDate":
        "",
        "keepBands":
        list_sequence_init(
            ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"])
    }
    return sentinel_2_s2c_default


def init_sentinel2_l3a_parameters():
    """
    Set all Sentinel_2_L3A block parameters to default values
    """
    sentinel_2_l3a_default = {
        "additionalFeatures":
        "",
        "temporalResolution":
        10,
        "write_reproject_resampled_input_dates_stack":
        True,
        "startDate":
        "",
        "endDate":
        "",
        "keepBands":
        list_sequence_init(
            ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"])
    }
    return sentinel_2_l3a_default


def init_userfeat_parameters():
    """
    Set all userFeat block parameters to default values
    """
    user_feat = {"arbo": "/*", "patterns": "ALT,ASP,SLP"}
    return user_feat


def init_simp_parameters():
    """
    Set all Simplification block parameters to default values
    """
    simp_default = {
        "classification": None,
        "confidence": None,
        "validity": None,
        "seed": None,
        "umc1": None,
        "umc2": None,
        "inland": None,
        "rssize": 20,
        "lib64bit": None,
        "gridsize": None,
        "grasslib":
        "/work/OT/theia/oso/OTB/GRASS/grass7.2.1svn-x86_64-pc-linux-gnu-13_03_2017",
        "douglas": 10,
        "hermite": 10,
        "mmu": 1000,
        "angle": True,
        "clipfile": None,
        "clipfield": None,
        "clipvalue": None,
        "outprefix": "dept",
        "lcfield": "Class",
        "blocksize": 2000,
        "dozip": True,
        "bingdal": None,
        "chunk": 10,
        "systemcall": False,
        "chunk": 1,
        "nomenclature": None,
        "statslist": {
            1: "rate",
            2: "statsmaj",
            3: "statsmaj"
        }
    }
    return simp_default


def init_external_features_parameters():
    """
    Set all external_features block parameters to default values
    """
    external_features = {
        "module": None,
        "functions": None,
        "number_of_chunks": 50,
        "chunk_size_x": 50,
        "chunk_size_y": 50,
        "chunk_size_mode": "split_number",
        "concat_mode": True,
        "output_name": None
    }
    return external_features
