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
This module contains all functions for testing known configuration parameters

These test must concern only typing

They can be overloaded by providing custom check.
"""
import os
from config import Config, Sequence, Mapping
from iota2.Common import ServiceError as sErr
from iota2.Common.FileUtils import get_iota2_project_dir
# #########################################################################
# Tools
# #########################################################################


def test_var_config_file(cfg,
                         section,
                         variable,
                         varType,
                         valeurs="",
                         valDefaut=""):
    """
        This function check if variable is in obj
        and if it has varType type.
        Optionnaly it can check if variable has values in valeurs
        Exit the code if any error are detected
        :param section: section name of the obj where to find
        :param variable: string name of the variable
        :param varType: type type of the variable for verification
        :param valeurs: string list of the possible value of variable
        :param valDefaut: value by default if variable is not in the configuration file
    """

    if not hasattr(cfg, section):
        raise sErr.configFileError("Section '" + str(section) +
                                   "' is not in the configuration file")

    objSection = getattr(cfg, section)

    if not hasattr(objSection, variable):
        if valDefaut != "":
            setattr(objSection, variable, valDefaut)
        else:
            raise sErr.parameterError(
                section, "mandatory variable '" + str(variable) +
                "' is missing in the configuration file")
    else:
        tmpVar = getattr(objSection, variable)

        if not isinstance(tmpVar, varType):
            message = ("variable '" + str(variable) +
                       "' has a wrong type\nActual: " + str(type(tmpVar)) +
                       " expected: " + str(varType))
            raise sErr.parameterError(section, message)

        if valeurs != "":
            ok = 0
            for index in range(len(valeurs)):
                if tmpVar == valeurs[index]:
                    ok = 1
            if ok == 0:
                message = ("bad value for '" + variable +
                           "' variable. Value accepted: " + str(valeurs) +
                           " Value read: " + str(tmpVar))
                raise sErr.parameterError(section, message)


def get_param(cfg, section, variable):
    """
        Return the value of variable in the section from config
        file define in the init phase of the class.
        :param section: string name of the section
        :param variable: string name of the variable
        :return: the value of variable
    """

    if not hasattr(cfg, section):
        # not an osoError class because it should NEVER happened
        raise Exception("Section is not in the configuration file: " +
                        str(section))

    objSection = getattr(cfg, section)
    if not hasattr(objSection, variable):
        # not an osoError class because it should NEVER happened
        raise Exception("Variable is not in the configuration file: " +
                        str(variable))

    tmpVar = getattr(objSection, variable)

    return tmpVar


def test_ifexists(path):
    if not os.path.exists(path):
        raise sErr.dirError(path)


def test_shape_name(input_vector):
    """
    """
    import string

    avail_characters = string.ascii_letters
    first_character = os.path.basename(input_vector)[0]
    if first_character not in avail_characters:
        raise sErr.configError(
            "the file '{}' is containing a non-ascii letter at first "
            "position in it's name : {}".format(input_vector, first_character))

    ext = input_vector.split(".")[-1]
    # If required test if gdal can open this file
    allowed_format = ["shp", "sqlite"]
    if not ext in allowed_format:
        raise sErr.configError(f"{input_vector} is not in right format."
                               f"\nAllowed format are {allowed_format}")


# #############################################################################
# Check functions
# #############################################################################


def check_sampleAugmentation(cfg, path_conf):
    """
    """
    def check_parameters(sampleAug):

        not_allowed_p = [
            "in", "out", "field", "layer", "label", "seed", "inxml",
            "progress", "help"
        ]
        for p in not_allowed_p:
            if p in sampleAug:
                raise sErr.configError(
                    "'{}' parameter must not be set in argTrain.sampleAugmentation"
                    .format(p))

            if "strategy" in sampleAug:
                strategy = sampleAug["strategy"]
                if strategy not in ["replicate", "jitter", "smote"]:
                    raise sErr.configError(
                        "augmentation strategy must be 'replicate', 'jitter' or 'smote'"
                    )
            if "strategy.jitter.stdFactor" in sampleAug:
                jitter = sampleAug["strategy.jitter.stdFactor"]
                if not isinstance(jitter, int):
                    raise sErr.configError(
                        "strategy.jitter.stdFactor must an integer")
            if "strategy.smote.neighbors" in sampleAug:
                byclass = sampleAug["strategy.smote.neighbors"]
                if not isinstance(byclass, int):
                    raise sErr.configError(
                        "strategy.smote.neighbors must be an integer")
            if "samples.strategy" in sampleAug:
                samples_strategy = sampleAug["samples.strategy"]
                if samples_strategy not in ["minNumber", "balance", "byClass"]:
                    raise sErr.configError(
                        "augmentation strategy must be 'minNumber', 'balance' or 'byClass'"
                    )
            if "samples.strategy.minNumber" in sampleAug:
                minNumber = sampleAug["samples.strategy.minNumber"]
                if not isinstance(minNumber, int):
                    raise sErr.configError(
                        "samples.strategy.minNumber must an integer")
            if "samples.strategy.byClass" in sampleAug:
                byClass = sampleAug["samples.strategy.byClass"]
                if not isinstance(byClass, str):
                    raise sErr.configError(
                        "samples.strategy.byClass must be a string")
            if "activate" in sampleAug:
                activate = sampleAug["activate"]
                if not isinstance(activate, bool):
                    raise sErr.configError("activate must be a bool")
            if "target_models" in sampleAug:
                TargetModels = sampleAug["target_models"]
                if not isinstance(TargetModels, Sequence):
                    raise sErr.configError("target_models must a list")
                if not isinstance(TargetModels[0], str):
                    raise sErr.configError(
                        "target_models must constains strings")

    try:
        sampleAug = dict(cfg.argTrain.sampleAugmentation)
        check_parameters(sampleAug)
    # Error managed
    except sErr.configFileError:
        print("Error in the configuration file " + path_conf)
        raise
    # Warning error not managed !
    except Exception:
        print("Something wrong happened in serviceConfigFile !")
        raise


def check_sample_selection(cfg, path_conf):
    """
    """
    def check_parameters(sampleSel):

        not_allowed_p = [
            "outrates", "in", "mask", "vec", "out", "instats", "field",
            "layer", "rand", "inxml"
        ]
        strats = ["byclass", "constant", "percent", "total", "smallest", "all"]
        for p in not_allowed_p:
            if p in sampleSel:
                raise sErr.configError(
                    "'{}' parameter must not be set in argTrain.sampleSelection"
                    .format(p))

        if "sampler" in sampleSel:
            sampler = sampleSel["sampler"]
            if sampler not in ["periodic", "random"]:
                raise sErr.configError(
                    "sampler must be 'periodic' or 'random'")
        if "sampler.periodic.jitter" in sampleSel:
            jitter = sampleSel["sampler.periodic.jitter"]
            if not isinstance(jitter, int):
                raise sErr.configError("jitter must an integer")
        if "strategy" in sampleSel:
            strategy = sampleSel["strategy"]
            if strategy not in strats:
                raise sErr.configError("strategy must be {}".format(
                    ' or '.join(["'{}'".format(elem) for elem in strats])))
        if "strategy.byclass.in" in sampleSel:
            byclass = sampleSel["strategy.byclass.in"]
            if not isinstance(byclass, str):
                raise sErr.configError("strategy.byclass.in must a string")
        if "strategy.constant.nb" in sampleSel:
            constant = sampleSel["strategy.constant.nb"]
            if not isinstance(constant, int):
                raise sErr.configError("strategy.constant.nb must an integer")
        if "strategy.percent.p" in sampleSel:
            percent = sampleSel["strategy.percent.p"]
            if not isinstance(percent, float):
                raise sErr.configError("strategy.percent.p must a float")
        if "strategy.total.v" in sampleSel:
            total = sampleSel["strategy.total.v"]
            if not isinstance(total, int):
                raise sErr.configError("strategy.total.v must an integer")
        if "elev.dem" in sampleSel:
            dem = sampleSel["elev.dem"]
            if not isinstance(dem, str):
                raise sErr.configError("elev.dem must a string")
        if "elev.geoid" in sampleSel:
            geoid = sampleSel["elev.geoid"]
            if not isinstance(geoid, str):
                raise sErr.configError("elev.geoid must a string")
        if "elev.default" in sampleSel:
            default = sampleSel["elev.default"]
            if not isinstance(default, float):
                raise sErr.configError("elev.default must a float")
        if "ram" in sampleSel:
            ram = sampleSel["ram"]
            if not isinstance(ram, int):
                raise sErr.configError("ram must a int")
        if "target_model" in sampleSel:
            target_model = sampleSel["target_model"]
            if not isinstance(target_model, int):
                raise sErr.configError("target_model must an integer")

    try:
        sampleSel = dict(cfg.argTrain.sampleSelection)
        check_parameters(sampleSel)
        if "per_model" in sampleSel:
            for model in sampleSel["per_model"]:
                check_parameters(dict(model))
    # Error managed
    except sErr.configFileError:
        print("Error in the configuration file " + path_conf)
        raise
    # Warning error not managed !
    except Exception:
        print("Something wrong happened in serviceConfigFile !")
        raise


def check_arg_classification_parameters(cfg, path_conf):
    try:
        test_var_config_file(cfg, 'argClassification', 'classifMode', str,
                             ["separate", "fusion"])
        test_var_config_file(cfg, 'argClassification',
                             'enable_probability_map', bool)
        test_var_config_file(cfg, 'argClassification', 'noLabelManagement',
                             str, ["maxConfidence", "learningPriority"])
    # Error managed
    except sErr.configFileError:
        print("Error in the configuration file " + path_conf)
        raise
    # Warning error not managed !
    except Exception:
        print("Something wrong happened in serviceConfigFile !")
        raise


def all_sameBands(items):
    return all(bands == items[0][1] for path, bands in items)


def check_chain_parameters(cfg, path_conf):
    try:
        # test of variable
        test_var_config_file(cfg, "chain", "outputPath", str)
        test_var_config_file(cfg, "chain", "nomenclaturePath", str)
        test_var_config_file(cfg, "chain", "remove_outputPath", bool)
        test_var_config_file(cfg, "chain", "listTile", str)
        test_var_config_file(cfg, "chain", "L5Path_old", str)
        test_var_config_file(cfg, "chain", "L8Path", str)
        test_var_config_file(cfg, "chain", "S2Path", str)
        test_var_config_file(cfg, "chain", "S1Path", str)

        # test_var_config_file(cfg,
        #     "chain",
        #     "firstStep",
        #     str,
        #     [
        #         "init",
        #         "sampling",
        #         "dimred",
        #         "learning",
        #         "classification",
        #         "mosaic",
        #         "validation",
        #         "regularisation",
        #         "crown",
        #         "mosaictiles",
        #         "vectorisation",
        #         "simplification",
        #         "smoothing",
        #         "clipvectors",
        #         "lcstatistics",
        #     ],
        # )
        # test_var_config_file(cfg,
        #     "chain",
        #     "lastStep",
        #     str,
        #     [
        #         "init",
        #         "sampling",
        #         "dimred",
        #         "learning",
        #         "classification",
        #         "mosaic",
        #         "validation",
        #         "regularisation",
        #         "crown",
        #         "mosaictiles",
        #         "vectorisation",
        #         "simplification",
        #         "smoothing",
        #         "clipvectors",
        #         "lcstatistics",
        #     ],
        # )
        if get_param(cfg, "chain", "regionPath"):
            check_region_vector(cfg)
        test_var_config_file(cfg, 'chain', 'regionField', str)
        test_var_config_file(cfg, 'chain', 'check_inputs', bool)
        test_var_config_file(cfg, 'chain', 'model', str)
        test_var_config_file(cfg, 'chain', 'enableCrossValidation', bool)
        test_var_config_file(cfg, 'chain', 'groundTruth', str)
        test_var_config_file(cfg, 'chain', 'dataField', str)
        test_var_config_file(cfg, 'chain', 'runs', int)
        test_var_config_file(cfg, 'chain', 'ratio', float)
        test_var_config_file(cfg, 'chain', 'splitGroundTruth', bool)
        test_var_config_file(cfg, 'chain', 'outputStatistics', bool)
        test_var_config_file(cfg, 'chain', 'cloud_threshold', int)
        test_var_config_file(cfg, 'chain', 'spatialResolution', int)
        test_var_config_file(cfg, 'chain', 'colorTable', str)
        test_var_config_file(cfg, 'chain', 'mode_outside_RegionSplit', float)
        test_var_config_file(cfg, 'chain', 'merge_final_classifications', bool)
        test_var_config_file(cfg, 'chain', 'enable_autoContext', bool)
        test_var_config_file(cfg, 'chain', 'autoContext_iterations', int)
        if get_param(cfg, "chain", "merge_final_classifications"):
            test_var_config_file(cfg, 'chain',
                                 'merge_final_classifications_undecidedlabel',
                                 int)
            test_var_config_file(cfg, 'chain',
                                 'merge_final_classifications_ratio', float)
            test_var_config_file(cfg, 'chain',
                                 'merge_final_classifications_method', str,
                                 ["majorityvoting", "dempstershafer"])
            test_var_config_file(cfg, 'chain', 'dempstershafer_mob', str,
                                 ["precision", "recall", "accuracy", "kappa"])
            test_var_config_file(cfg, 'chain', 'keep_runs_results', bool)
            test_var_config_file(cfg, 'chain',
                                 'fusionOfClassificationAllSamplesValidation',
                                 bool)
        test_var_config_file(cfg, 'chain', 'remove_tmp_files', bool)

        test_var_config_file(cfg, 'chain', 'remove_tmp_files', bool)

        test_var_config_file(cfg, 'chain', 'remove_tmp_files', bool)
        if cfg.chain.random_seed is not None:
            test_var_config_file(cfg, 'chain', 'random_seed', int)

        nbTile = len(cfg.chain.listTile.split(" "))

        # directory tests
        if get_param(cfg, "chain", "jobsPath"):
            test_ifexists(get_param(cfg, "chain", "jobsPath"))
        test_ifexists(os.path.join(get_iota2_project_dir(), "iota2"))
        test_ifexists(cfg.chain.nomenclaturePath)
        test_ifexists(cfg.chain.groundTruth)
        test_ifexists(cfg.chain.colorTable)
        if cfg.chain.S2_output_path:
            test_ifexists(cfg.chain.S2_output_path)
        if cfg.chain.S2_S2C_output_path:
            test_ifexists(cfg.chain.S2_S2C_output_path)

    # Error managed
    except sErr.configFileError:
        print("Error in the configuration file " + path_conf)
        raise
    # Warning error not managed !
    except Exception:
        print("Something wrong happened in serviceConfigFile !")
        raise


def check_arg_train_parameters(cfg, path_conf):
    try:
        test_var_config_file(cfg, 'argTrain', 'classifier', str)
        test_var_config_file(cfg, 'argTrain', 'options', str)
        test_var_config_file(cfg, 'argTrain', 'cropMix', bool)
        test_var_config_file(cfg, 'argTrain', 'prevFeatures', str)
        test_var_config_file(cfg, 'argTrain', 'outputPrevFeatures', str)
        test_var_config_file(cfg, 'argTrain', 'annualCrop', Sequence)
        test_var_config_file(cfg, 'argTrain', 'ACropLabelReplacement',
                             Sequence)

        test_var_config_file(cfg, 'argTrain', 'sampleSelection', Mapping)
        test_var_config_file(cfg, 'argTrain', 'samplesClassifMix', bool)
        test_var_config_file(cfg, 'argTrain', 'validityThreshold', int)
    # Error managed
    except sErr.configFileError:
        print("Error in the configuration file " + path_conf)
        raise
    # Warning error not managed !
    except Exception:
        print("Something wrong happened in serviceConfigFile !")
        raise


def check_glob_chain_parameters(cfg, path_conf):
    try:
        test_var_config_file(cfg, 'GlobChain', 'proj', str)
        test_var_config_file(cfg, 'GlobChain', 'features', Sequence)
        test_var_config_file(cfg, 'GlobChain', 'autoDate', bool)
        test_var_config_file(cfg, 'GlobChain', 'writeOutputs', bool)
        test_var_config_file(cfg, 'GlobChain', 'useAdditionalFeatures', bool)
        test_var_config_file(cfg, 'GlobChain', 'useGapFilling', bool)

    # Error managed
    except sErr.configFileError:
        print("Error in the configuration file " + path_conf)
        raise
    # Warning error not managed !
    except Exception:
        print("Something wrong happened in serviceConfigFile !")
        raise
    try:
        epsg = int(get_param(cfg, "GlobChain", "proj").split(":")[-1])
    except ValueError:
        raise ValueError(
            "parameter GlobChain.proj not in the right format (proj:\"EPSG:2154\")"
        )


def check_i2_feature_extraction_parameters(cfg, path_conf):
    try:
        test_var_config_file(cfg, 'iota2FeatureExtraction', 'copyinput', bool)
        test_var_config_file(cfg, 'iota2FeatureExtraction', 'relrefl', bool)
        test_var_config_file(cfg, 'iota2FeatureExtraction', 'keepduplicates',
                             bool)
        test_var_config_file(cfg, 'iota2FeatureExtraction', 'extractBands',
                             bool)
        test_var_config_file(cfg, 'iota2FeatureExtraction', 'acorfeat', bool)
    # Error managed
    except sErr.configFileError:
        print("Error in the configuration file " + path_conf)
        raise
    # Warning error not managed !
    except Exception:
        print("Something wrong happened in serviceConfigFile !")
        raise


def check_dim_red_parameters(cfg, path_conf):
    try:
        test_var_config_file(cfg, 'dimRed', 'dimRed', bool)
        test_var_config_file(cfg, 'dimRed', 'targetDimension', int)
        test_var_config_file(cfg, 'dimRed', 'reductionMode', str)
    # Error managed
    except sErr.configFileError:
        print("Error in the configuration file " + path_conf)
        raise
    # Warning error not managed !
    except Exception:
        print("Something wrong happened in serviceConfigFile !")
        raise


def check_scikit_models_parameters(cfg, path_conf):
    try:

        if cfg.scikit_models_parameters.model_type is not None:
            test_var_config_file(cfg, 'scikit_models_parameters', 'model_type',
                                 str)
            test_var_config_file(cfg, 'scikit_models_parameters',
                                 'cross_validation_folds', int)
            test_var_config_file(cfg, 'scikit_models_parameters',
                                 'cross_validation_grouped', bool)
            test_var_config_file(cfg, 'scikit_models_parameters',
                                 'standardization', bool)
            test_var_config_file(cfg, 'scikit_models_parameters',
                                 'cross_validation_parameters', Mapping)
    # Error managed
    except sErr.configFileError:
        print("Error in the configuration file " + path_conf)
        raise
    # Warning error not managed !
    except Exception:
        print("Something wrong happened in serviceConfigFile !")
        raise


def check_sensors(cfg, path_conf):
    try:

        if cfg.chain.L5Path_old != "None":
            #L5 variable check
            test_var_config_file(cfg, 'Landsat5_old', 'temporalResolution',
                                 int)
            test_var_config_file(cfg, 'Landsat5_old', 'keepBands', Sequence)
        if cfg.chain.L8Path != "None":
            # L8 variable check
            test_var_config_file(cfg, "Landsat8", "temporalResolution", int)
            test_var_config_file(cfg, "Landsat8", "keepBands", Sequence)
        if cfg.chain.L8Path_old != "None":
            #L8 variable check
            test_var_config_file(cfg, 'Landsat8_old', 'temporalResolution',
                                 int)
            test_var_config_file(cfg, 'Landsat8_old', 'keepBands', Sequence)

        if cfg.chain.S2Path != "None":
            # S2 variable check
            test_var_config_file(cfg, "Sentinel_2", "temporalResolution", int)
            test_var_config_file(cfg, "Sentinel_2", "keepBands", Sequence)
    # Error managed
    except sErr.configFileError:
        print("Error in the configuration file " + path_conf)
        raise
    # Warning error not managed !
    except Exception:
        print("Something wrong happened in serviceConfigFile !")
        raise


def check_custom_feature(cfg, path_conf):
    """
    This function return True if the custom features field
    is activate and all imports success
    """
    flag = False

    def check_code_path(code_path):

        if code_path is None:
            return False
        if code_path.lower() == "none":
            return False
        if len(code_path) < 1:
            return False
        if not os.path.isfile(code_path):
            raise ValueError(f"Error: {code_path} is not a correct path")
        return True

    def check_import(module_path):
        import importlib

        spec = importlib.util.spec_from_file_location(
            module_path.split(os.sep)[-1].split('.')[0], module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def check_function_in_module(module, list_functions):
        for fun in list_functions:
            try:
                getattr(module, fun)
            except AttributeError:
                raise AttributeError(
                    f"{module.__name__} has no function {fun}")

    module_path = get_param(cfg, "external_features", "module")
    module_path_valid = check_code_path(module_path)
    if module_path_valid:
        module = check_import(module_path)
        check_function_in_module(
            module,
            get_param(cfg, "external_features", "functions").split(" "))

        flag = True
    return flag


def v_check_compat_param(cfg):

    # parameters compatibilities check
    classier_probamap_avail = ["sharkrf"]
    if (get_param(cfg, "argClassification", "enable_probability_map") is True
            and get_param(
                cfg, "argTrain",
                "classifier").lower() not in classier_probamap_avail):
        raise sErr.configError(
            "'enable_probability_map:True' only available with the 'sharkrf' classifier"
        )
    if get_param(cfg, "chain", "enableCrossValidation") is True:
        raise sErr.configError(
            "enableCrossValidation not available, please set it to False\n")
    if get_param(cfg, "chain", "regionPath"
                 ) is None and cfg.argClassification.classifMode == "fusion":
        raise sErr.configError(
            "you can't chose 'one_region' mode and ask a fusion of classifications\n"
        )
    if cfg.chain.merge_final_classifications and cfg.chain.runs == 1:
        raise sErr.configError(
            "these parameters are incompatible runs:1 and merge_final_classifications:True"
        )
    if cfg.chain.enableCrossValidation and cfg.chain.runs == 1:
        raise sErr.configError(
            "these parameters are incompatible runs:1 and enableCrossValidation:True"
        )
    if cfg.chain.enableCrossValidation and cfg.chain.splitGroundTruth is False:
        raise sErr.configError(
            "these parameters are incompatible splitGroundTruth:False and enableCrossValidation:True"
        )
    if cfg.chain.splitGroundTruth is False and cfg.chain.runs != 1:
        raise sErr.configError(
            "these parameters are incompatible splitGroundTruth:False and runs different from 1"
        )
    if cfg.chain.merge_final_classifications and cfg.chain.splitGroundTruth is False:
        raise sErr.configError(
            "these parameters are incompatible merge_final_classifications:True and splitGroundTruth:False"
        )
    if cfg.argTrain.dempster_shafer_SAR_Opt_fusion and 'None' in cfg.chain.S1Path:
        raise sErr.configError(
            "these parameters are incompatible dempster_shafer_SAR_Opt_fusion : True and S1Path : 'None'"
        )
    if cfg.argTrain.dempster_shafer_SAR_Opt_fusion and 'None' in cfg.chain.userFeatPath and 'None' in cfg.chain.L5Path_old and 'None' in cfg.chain.L8Path and 'None' in cfg.chain.L8Path_old and 'None' in cfg.chain.S2Path and 'None' in cfg.chain.S2_S2C_Path:
        raise sErr.configError(
            "to perform post-classification fusion, optical data must be used")
    if cfg.scikit_models_parameters.model_type is not None and cfg.chain.enable_autoContext is True:
        raise sErr.configError(
            "these parameters are incompatible enable_autoContext : True and model_type"
        )

    return True


# #############################################################################
# Functions usable by builders for input checking
# #############################################################################


def region_vector_field_as_string(cfg):
    """
    This function raise an error if region field is not a string
    """
    import ogr
    region_path = cfg.chain.regionPath
    if region_path is None:
        return True
    test_shape_name(region_path)
    if not region_path:
        raise sErr.configError("chain.regionPath must be set")

    region_field = cfg.chain.regionField
    if not region_path:
        raise sErr.configError("chain.regionField must be set")

    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = driver.Open(region_path, 0)
    if dataSource is None:
        raise Exception("Could not open " + region_path)
    layer = dataSource.GetLayer()
    field_index = layer.FindFieldIndex(region_field, False)
    layerDefinition = layer.GetLayerDefn()
    fieldTypeCode = layerDefinition.GetFieldDefn(field_index).GetType()
    fieldType = layerDefinition.GetFieldDefn(field_index).GetFieldTypeName(
        fieldTypeCode)
    if fieldType != "String":
        raise sErr.configError("the region field must be a string")


def is_field_in_vector_data(vector_file, data_field, expected_type="Integer"):
    """
    This function open a shapefile and search the data_field.
    If data_field is found the function check that is well in the expected type
    """
    import ogr
    # test of groundTruth file
    field_ftype = []

    data_source = ogr.Open(vector_file)
    test_shape_name(vector_file)
    da_layer = data_source.GetLayer(0)
    layer_definition = da_layer.GetLayerDefn()
    for i in range(layer_definition.GetFieldCount()):
        field_name = layer_definition.GetFieldDefn(i).GetName()
        field_type_code = layer_definition.GetFieldDefn(i).GetType()
        field_type = layer_definition.GetFieldDefn(i).GetFieldTypeName(
            field_type_code)
        field_ftype.append((field_name, field_type))
    flag = 0
    for current_field, field_type in field_ftype:
        if current_field == data_field:
            flag = 1
            if expected_type not in field_type:
                raise sErr.fileError(f"the data's field {current_field}"
                                     f" must be an integer in {vector_file}")
    if flag == 0:
        raise sErr.fileError(f"field name '{data_field}'"
                             f"' doesn't exist in {vector_file}")
