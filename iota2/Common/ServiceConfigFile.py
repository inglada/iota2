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
""" Module for parse config file"""
import os
import sys
from typing import Dict, Union, List
from osgeo import ogr
from config import Config, Sequence, Mapping, Container
from iota2.Common.FileUtils import FileSearch_AND, getRasterNbands, get_iota2_project_dir
from iota2.Common import ServiceError as sErr

# this is a pointer to the module object instance itself.
this = sys.modules[__name__]

# declaration of pathConf and cfg variables
this.pathConf = None
this.cfg = None


def clearConfig():
    if this.pathConf is not None:
        # also in local function scope. no scope specifier
        # like global is needed
        this.pathConf = None
        this.cfg = None


class serviceConfigFile:
    """
    The class serviceConfigFile defines all methods to access to the
    configuration file and to check the variables.
    """
    def __init__(self, pathConf, iota_config=True):
        """
            Init class serviceConfigFile
            :param pathConf: string path of the config file
        """
        self.pathConf = pathConf
        self.cfg = Config(open(pathConf))
        # set default values
        if iota_config:
            #init chain section
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
            self.init_section("chain", chain_default)
            #init coregistration section
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
            self.init_section("coregistration", coregistration_default)

            sklearn_default = {
                "model_type": None,
                "cross_validation_folds": 5,
                "cross_validation_grouped": False,
                "standardization": False,
                "cross_validation_parameters": self.init_dicoMapping({})
            }
            self.init_section("scikit_models_parameters", sklearn_default)

            #init argTrain section
            sampleSel_default = self.init_dicoMapping({
                "sampler": "random",
                "strategy": "all"
            })
            sampleAugmentationg_default = self.init_dicoMapping(
                {"activate": False})
            annualCrop = self.init_listSequence(["11", "12"])
            ACropLabelReplacement = self.init_listSequence(
                ["10", "annualCrop"])

            argTrain_default = {
                "sampleSelection": sampleSel_default,
                "sampleAugmentation": sampleAugmentationg_default,
                "sampleManagement": None,
                "dempster_shafer_SAR_Opt_fusion": False,
                "cropMix": False,
                "prevFeatures": "None",
                "outputPrevFeatures": "None",
                "annualCrop": annualCrop,
                "ACropLabelReplacement": ACropLabelReplacement,
                "samplesClassifMix": False,
                "classifier": "rf",
                "options": " -classifier.rf.min 5 -classifier.rf.max 25 ",
                "annualClassesExtractionSource": "None",
                "validityThreshold": 1
            }
            if self.cfg.scikit_models_parameters.model_type is None:
                del argTrain_default["classifier"]
                del argTrain_default["options"]

            self.init_section("argTrain", argTrain_default)
            #init argClassification section
            argClassification_default = {
                "noLabelManagement": "maxConfidence",
                "enable_probability_map": False,
                "fusionOptions": "-nodatalabel 0 -method majorityvoting"
            }
            self.init_section("argClassification", argClassification_default)
            #init GlobChain section
            GlobChain_default = {
                "features":
                self.init_listSequence(["NDVI", "NDWI", "Brightness"]),
                "autoDate": True,
                "writeOutputs": False,
                "useAdditionalFeatures": False,
                "useGapFilling": True
            }
            self.init_section("GlobChain", GlobChain_default)
            #init iota2FeatureExtraction reduction
            iota2FeatureExtraction_default = {
                "copyinput": True,
                "relrefl": False,
                "keepduplicates": True,
                "extractBands": False,
                "acorfeat": False
            }
            self.init_section("iota2FeatureExtraction",
                              iota2FeatureExtraction_default)
            #init dimensionality reduction
            dimRed_default = {
                "dimRed": False,
                "targetDimension": 4,
                "reductionMode": "global"
            }
            self.init_section("dimRed", dimRed_default)
            #init sensors parameters
            Landsat8_default = {
                "additionalFeatures":
                "",
                "temporalResolution":
                16,
                "write_reproject_resampled_input_dates_stack":
                True,
                "startDate":
                "",
                "endDate":
                "",
                "keepBands":
                self.init_listSequence(
                    ["B1", "B2", "B3", "B4", "B5", "B6", "B7"])
            }
            Landsat8_old_default = {
                "additionalFeatures":
                "",
                "temporalResolution":
                16,
                "startDate":
                "",
                "endDate":
                "",
                "keepBands":
                self.init_listSequence(
                    ["B1", "B2", "B3", "B4", "B5", "B6", "B7"])
            }
            Landsat5_old_default = {
                "additionalFeatures":
                "",
                "temporalResolution":
                16,
                "startDate":
                "",
                "endDate":
                "",
                "keepBands":
                self.init_listSequence(["B1", "B2", "B3", "B4", "B5", "B6"])
            }
            Sentinel_2_default = {
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
                self.init_listSequence([
                    "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11",
                    "B12"
                ])
            }
            Sentinel_2_S2C_default = {
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
                self.init_listSequence([
                    "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11",
                    "B12"
                ])
            }
            Sentinel_2_L3A_default = {
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
                self.init_listSequence([
                    "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11",
                    "B12"
                ])
            }

            userFeat = {"arbo": "/*", "patterns": "ALT,ASP,SLP"}

            self.init_section("Landsat5_old", Landsat5_old_default)
            self.init_section("Landsat8", Landsat8_default)
            self.init_section("Landsat8_old", Landsat8_old_default)
            self.init_section("Sentinel_2", Sentinel_2_default)
            self.init_section("Sentinel_2_S2C", Sentinel_2_S2C_default)
            self.init_section("Sentinel_2_L3A", Sentinel_2_L3A_default)
            self.init_section("userFeat", userFeat)

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

            self.init_section("Simplification", simp_default)
            custom_features = {
                "module": None,
                "functions": None,
                "number_of_chunks": 50,
                "chunk_size_x": 50,
                "chunk_size_y": 50,
                "chunk_size_mode": "split_number",
                "custom_write_mode": False
            }
            self.init_section("external_features", custom_features)

    def init_section(self, sectionName, sectionDefault):
        """use to initialize a full configuration file section

        Parameters
        ----------
        sectionName : string
            section's name
        sectionDefault : dict
            default values are store in a python dictionnary
        """
        if not hasattr(self.cfg, sectionName):
            section_default = self.init_dicoMapping(sectionDefault)
            self.cfg.addMapping(sectionName, section_default, "")
        for key, value in list(sectionDefault.items()):
            self.addParam(sectionName, key, value)

    def init_dicoMapping(self, myDict):
        """use to init a mapping object from a dict
        """
        new_map = Mapping()
        for key, value in list(myDict.items()):
            new_map.addMapping(key, value, "")
        return new_map

    def init_listSequence(self, myList):
        """use to init a Sequence object from a list
        """
        new_seq = Sequence()
        for elem in myList:
            new_seq.append(elem, "#comment")
        return new_seq

    def __repr__(self):
        return "Configuration file : " + self.pathConf

    def testShapeName(self, input_vector):
        """
        """
        import string

        avail_characters = string.ascii_letters
        first_character = os.path.basename(input_vector)[0]
        if first_character not in avail_characters:
            raise sErr.configError(
                "the file '{}' is containing a non-ascii letter at first position in it's name : {}"
                .format(input_vector, first_character))

    def testVarConfigFile(self,
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

        if not hasattr(self.cfg, section):
            raise sErr.configFileError("Section '" + str(section) +
                                       "' is not in the configuration file")

        objSection = getattr(self.cfg, section)

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

    def testDirectory(self, directory):
        if not os.path.exists(directory):
            raise sErr.dirError(directory)

    def checkConfigParameters(self):
        """
            check parameters coherence
            :return: true if ok
        """
        def check_sampleAugmentation():
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
                    if samples_strategy not in [
                            "minNumber", "balance", "byClass"
                    ]:
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

            sampleAug = dict(self.cfg.argTrain.sampleAugmentation)
            check_parameters(sampleAug)

        def check_sampleSelection():
            """
            """
            def check_parameters(sampleSel):

                not_allowed_p = [
                    "outrates", "in", "mask", "vec", "out", "instats", "field",
                    "layer", "rand", "inxml"
                ]
                strats = [
                    "byclass", "constant", "percent", "total", "smallest",
                    "all"
                ]
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
                            ' or '.join(
                                ["'{}'".format(elem) for elem in strats])))
                if "strategy.byclass.in" in sampleSel:
                    byclass = sampleSel["strategy.byclass.in"]
                    if not isinstance(byclass, str):
                        raise sErr.configError(
                            "strategy.byclass.in must a string")
                if "strategy.constant.nb" in sampleSel:
                    constant = sampleSel["strategy.constant.nb"]
                    if not isinstance(constant, int):
                        raise sErr.configError(
                            "strategy.constant.nb must an integer")
                if "strategy.percent.p" in sampleSel:
                    percent = sampleSel["strategy.percent.p"]
                    if not isinstance(percent, float):
                        raise sErr.configError(
                            "strategy.percent.p must a float")
                if "strategy.total.v" in sampleSel:
                    total = sampleSel["strategy.total.v"]
                    if not isinstance(total, int):
                        raise sErr.configError(
                            "strategy.total.v must an integer")
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

            sampleSel = dict(self.cfg.argTrain.sampleSelection)
            check_parameters(sampleSel)
            if "per_model" in sampleSel:
                for model in sampleSel["per_model"]:
                    check_parameters(dict(model))

        def check_region_vector(cfg):
            """
            """
            region_path = cfg.chain.regionPath
            self.testShapeName(region_path)
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
            fieldType = layerDefinition.GetFieldDefn(
                field_index).GetFieldTypeName(fieldTypeCode)
            if fieldType != "String":
                raise sErr.configError("the region field must be a string")

        def all_sameBands(items):
            return all(bands == items[0][1] for path, bands in items)

        try:
            # test of variable
            self.testVarConfigFile("chain", "outputPath", str)
            self.testVarConfigFile("chain", "nomenclaturePath", str)
            self.testVarConfigFile("chain", "remove_outputPath", bool)
            self.testVarConfigFile("chain", "listTile", str)
            self.testVarConfigFile("chain", "L5Path_old", str)
            self.testVarConfigFile("chain", "L8Path", str)
            self.testVarConfigFile("chain", "S2Path", str)
            self.testVarConfigFile("chain", "S1Path", str)

            self.testVarConfigFile(
                "chain",
                "firstStep",
                str,
                [
                    "init",
                    "sampling",
                    "dimred",
                    "learning",
                    "classification",
                    "mosaic",
                    "validation",
                    "regularisation",
                    "crown",
                    "mosaictiles",
                    "vectorisation",
                    "simplification",
                    "smoothing",
                    "clipvectors",
                    "lcstatistics",
                ],
            )
            self.testVarConfigFile(
                "chain",
                "lastStep",
                str,
                [
                    "init",
                    "sampling",
                    "dimred",
                    "learning",
                    "classification",
                    "mosaic",
                    "validation",
                    "regularisation",
                    "crown",
                    "mosaictiles",
                    "vectorisation",
                    "simplification",
                    "smoothing",
                    "clipvectors",
                    "lcstatistics",
                ],
            )

            if self.getParam("chain", "regionPath"):
                check_region_vector(self.cfg)
            self.testVarConfigFile('chain', 'regionField', str)
            self.testVarConfigFile('chain', 'check_inputs', bool)
            self.testVarConfigFile('chain', 'model', str)
            self.testVarConfigFile('chain', 'enableCrossValidation', bool)
            self.testVarConfigFile('chain', 'groundTruth', str)
            self.testVarConfigFile('chain', 'dataField', str)
            self.testVarConfigFile('chain', 'runs', int)
            self.testVarConfigFile('chain', 'ratio', float)
            self.testVarConfigFile('chain', 'splitGroundTruth', bool)
            self.testVarConfigFile('chain', 'outputStatistics', bool)
            self.testVarConfigFile('chain', 'cloud_threshold', int)
            # self.testVarConfigFile('chain', 'spatialResolution', int)
            self.testVarConfigFile('chain', 'colorTable', str)
            self.testVarConfigFile('chain', 'mode_outside_RegionSplit', float)
            self.testVarConfigFile('chain', 'merge_final_classifications',
                                   bool)
            self.testVarConfigFile('chain', 'enable_autoContext', bool)
            self.testVarConfigFile('chain', 'autoContext_iterations', int)
            if self.getParam("chain", "merge_final_classifications"):
                self.testVarConfigFile(
                    'chain', 'merge_final_classifications_undecidedlabel', int)
                self.testVarConfigFile('chain',
                                       'merge_final_classifications_ratio',
                                       float)
                self.testVarConfigFile('chain',
                                       'merge_final_classifications_method',
                                       str,
                                       ["majorityvoting", "dempstershafer"])
                self.testVarConfigFile(
                    'chain', 'dempstershafer_mob', str,
                    ["precision", "recall", "accuracy", "kappa"])
                self.testVarConfigFile('chain', 'keep_runs_results', bool)
                self.testVarConfigFile(
                    'chain', 'fusionOfClassificationAllSamplesValidation',
                    bool)

            self.testVarConfigFile('argTrain', 'classifier', str)
            self.testVarConfigFile('argTrain', 'options', str)
            self.testVarConfigFile('argTrain', 'cropMix', bool)
            self.testVarConfigFile('argTrain', 'prevFeatures', str)
            self.testVarConfigFile('argTrain', 'outputPrevFeatures', str)
            self.testVarConfigFile('argTrain', 'annualCrop', Sequence)
            self.testVarConfigFile('argTrain', 'ACropLabelReplacement',
                                   Sequence)

            self.testVarConfigFile('argTrain', 'sampleSelection', Mapping)
            self.testVarConfigFile('argTrain', 'samplesClassifMix', bool)
            self.testVarConfigFile('argTrain', 'validityThreshold', int)

            check_sampleSelection()
            check_sampleAugmentation()

            self.testVarConfigFile('argClassification', 'classifMode', str,
                                   ["separate", "fusion"])
            self.testVarConfigFile('argClassification',
                                   'enable_probability_map', bool)
            self.testVarConfigFile('argClassification', 'noLabelManagement',
                                   str, ["maxConfidence", "learningPriority"])

            self.testVarConfigFile('GlobChain', 'proj', str)
            self.testVarConfigFile('GlobChain', 'features', Sequence)
            self.testVarConfigFile('GlobChain', 'autoDate', bool)
            self.testVarConfigFile('GlobChain', 'writeOutputs', bool)
            self.testVarConfigFile('GlobChain', 'useAdditionalFeatures', bool)
            self.testVarConfigFile('GlobChain', 'useGapFilling', bool)

            self.testVarConfigFile('iota2FeatureExtraction', 'copyinput', bool)
            self.testVarConfigFile('iota2FeatureExtraction', 'relrefl', bool)
            self.testVarConfigFile('iota2FeatureExtraction', 'keepduplicates',
                                   bool)
            self.testVarConfigFile('iota2FeatureExtraction', 'extractBands',
                                   bool)
            self.testVarConfigFile('iota2FeatureExtraction', 'acorfeat', bool)

            self.testVarConfigFile('dimRed', 'dimRed', bool)
            self.testVarConfigFile('dimRed', 'targetDimension', int)
            self.testVarConfigFile('dimRed', 'reductionMode', str)

            self.testVarConfigFile('chain', 'remove_tmp_files', bool)

            self.testVarConfigFile('chain', 'remove_tmp_files', bool)

            self.testVarConfigFile('chain', 'remove_tmp_files', bool)

            if self.cfg.scikit_models_parameters.model_type is not None:
                self.testVarConfigFile('scikit_models_parameters',
                                       'model_type', str)
                self.testVarConfigFile('scikit_models_parameters',
                                       'cross_validation_folds', int)
                self.testVarConfigFile('scikit_models_parameters',
                                       'cross_validation_grouped', bool)
                self.testVarConfigFile('scikit_models_parameters',
                                       'standardization', bool)
                self.testVarConfigFile('scikit_models_parameters',
                                       'cross_validation_parameters', Mapping)

            if self.cfg.chain.L5Path_old != "None":
                #L5 variable check
                self.testVarConfigFile('Landsat5_old', 'temporalResolution',
                                       int)
                self.testVarConfigFile('Landsat5_old', 'keepBands', Sequence)
            if self.cfg.chain.L8Path != "None":
                # L8 variable check
                self.testVarConfigFile("Landsat8", "temporalResolution", int)
                self.testVarConfigFile("Landsat8", "keepBands", Sequence)
            if self.cfg.chain.L8Path_old != "None":
                #L8 variable check
                self.testVarConfigFile('Landsat8_old', 'temporalResolution',
                                       int)
                self.testVarConfigFile('Landsat8_old', 'keepBands', Sequence)

            if self.cfg.chain.S2Path != "None":
                # S2 variable check
                self.testVarConfigFile("Sentinel_2", "temporalResolution", int)
                self.testVarConfigFile("Sentinel_2", "keepBands", Sequence)

            if self.cfg.chain.random_seed != None:
                self.testVarConfigFile('chain', 'random_seed', int)

            nbTile = len(self.cfg.chain.listTile.split(" "))

            # directory tests
            if self.getParam("chain", "jobsPath"):
                self.testDirectory(self.getParam("chain", "jobsPath"))

            try:
                epsg = int(self.getParam("GlobChain", "proj").split(":")[-1])
            except ValueError:
                raise ValueError(
                    "parameter GlobChain.proj not in the right format (proj:\"EPSG:2154\")"
                )

            self.testDirectory(os.path.join(get_iota2_project_dir(), "iota2"))
            self.testDirectory(self.cfg.chain.nomenclaturePath)
            self.testDirectory(self.cfg.chain.groundTruth)
            self.testDirectory(self.cfg.chain.colorTable)
            if self.cfg.chain.S2_output_path:
                self.testDirectory(self.cfg.chain.S2_output_path)
            if self.cfg.chain.S2_S2C_output_path:
                self.testDirectory(self.cfg.chain.S2_S2C_output_path)
            # test of groundTruth file
            Field_FType = []

            dataSource = ogr.Open(self.cfg.chain.groundTruth)
            self.testShapeName(self.cfg.chain.groundTruth)
            daLayer = dataSource.GetLayer(0)
            layerDefinition = daLayer.GetLayerDefn()
            for i in range(layerDefinition.GetFieldCount()):
                fieldName = layerDefinition.GetFieldDefn(i).GetName()
                fieldTypeCode = layerDefinition.GetFieldDefn(i).GetType()
                fieldType = layerDefinition.GetFieldDefn(i).GetFieldTypeName(
                    fieldTypeCode)
                Field_FType.append((fieldName, fieldType))
            flag = 0
            for currentField, fieldType in Field_FType:
                if currentField == self.cfg.chain.dataField:
                    flag = 1
                    if "Integer" not in fieldType:
                        raise sErr.fileError("the data's field " +
                                             currentField +
                                             " must be an integer in " +
                                             self.cfg.chain.groundTruth)
            if flag == 0:
                raise sErr.fileError("field name '" +
                                     self.cfg.chain.dataField +
                                     "' doesn't exist in " +
                                     self.cfg.chain.groundTruth)

            # parameters compatibilities check
            classier_probamap_avail = ["sharkrf"]
            if (self.getParam("argClassification", "enable_probability_map") is
                    True and self.getParam(
                        "argTrain",
                        "classifier").lower() not in classier_probamap_avail):
                raise sErr.configError(
                    "'enable_probability_map:True' only available with the 'sharkrf' classifier"
                )
            if self.getParam("chain", "enableCrossValidation") is True:
                raise sErr.configError(
                    "enableCrossValidation not available, please set it to False\n"
                )
            if self.getParam(
                    "chain", "regionPath"
            ) is None and self.cfg.argClassification.classifMode == "fusion":
                raise sErr.configError(
                    "you can't chose 'one_region' mode and ask a fusion of classifications\n"
                )
            if self.cfg.chain.merge_final_classifications and self.cfg.chain.runs == 1:
                raise sErr.configError(
                    "these parameters are incompatible runs:1 and merge_final_classifications:True"
                )
            if self.cfg.chain.enableCrossValidation and self.cfg.chain.runs == 1:
                raise sErr.configError(
                    "these parameters are incompatible runs:1 and enableCrossValidation:True"
                )
            if self.cfg.chain.enableCrossValidation and self.cfg.chain.splitGroundTruth is False:
                raise sErr.configError(
                    "these parameters are incompatible splitGroundTruth:False and enableCrossValidation:True"
                )
            if self.cfg.chain.splitGroundTruth is False and self.cfg.chain.runs != 1:
                raise sErr.configError(
                    "these parameters are incompatible splitGroundTruth:False and runs different from 1"
                )
            if self.cfg.chain.merge_final_classifications and self.cfg.chain.splitGroundTruth is False:
                raise sErr.configError(
                    "these parameters are incompatible merge_final_classifications:True and splitGroundTruth:False"
                )
            if self.cfg.argTrain.dempster_shafer_SAR_Opt_fusion and 'None' in self.cfg.chain.S1Path:
                raise sErr.configError(
                    "these parameters are incompatible dempster_shafer_SAR_Opt_fusion : True and S1Path : 'None'"
                )
            if self.cfg.argTrain.dempster_shafer_SAR_Opt_fusion and 'None' in self.cfg.chain.userFeatPath and 'None' in self.cfg.chain.L5Path_old and 'None' in self.cfg.chain.L8Path and 'None' in self.cfg.chain.L8Path_old and 'None' in self.cfg.chain.S2Path and 'None' in self.cfg.chain.S2_S2C_Path:
                raise sErr.configError(
                    "to perform post-classification fusion, optical data must be used"
                )
            if self.cfg.scikit_models_parameters.model_type is not None and self.cfg.chain.enable_autoContext is True:
                raise sErr.configError(
                    "these parameters are incompatible enable_autoContext : True and model_type"
                )
            if self.cfg.scikit_models_parameters.model_type is not None and self.checkCustomFeature(
            ):
                raise sErr.configError(
                    "these parameters are incompatible external_features and scikit_models_parameters"
                )
            if self.checkCustomFeature and self.cfg.chain.enable_autoContext:
                raise sErr.configError(
                    "these parameters are incompatible external_features and enable_autoContext"
                )
        # Error managed
        except sErr.configFileError:
            print("Error in the configuration file " + self.pathConf)
            raise
        # Warning error not managed !
        except Exception:
            print("Something wrong happened in serviceConfigFile !")
            raise

        return True

    def getAvailableSections(self):
        """
        Return all sections in the configuration file
        :return: list of available section
        """
        return [section for section in list(self.cfg.keys())]

    def getSection(self, section):
        """
        """
        if not hasattr(self.cfg, section):
            # not an osoError class because it should NEVER happened
            raise Exception(
                "Section {} is not in the configuration file ".format(section))
        return getattr(self.cfg, section)

    def getParam(self, section, variable):
        """
            Return the value of variable in the section from config
            file define in the init phase of the class.
            :param section: string name of the section
            :param variable: string name of the variable
            :return: the value of variable
        """

        if not hasattr(self.cfg, section):
            # not an osoError class because it should NEVER happened
            raise Exception("Section is not in the configuration file: " +
                            str(section))

        objSection = getattr(self.cfg, section)
        if not hasattr(objSection, variable):
            # not an osoError class because it should NEVER happened
            raise Exception("Variable is not in the configuration file: " +
                            str(variable))

        tmpVar = getattr(objSection, variable)

        return tmpVar

    def setParam(self, section, variable, value):
        """
            Set the value of variable in the section from config
            file define in the init phase of the class.
            Mainly used in Unitary test in order to force a value
            :param section: string name of the section
            :param variable: string name of the variable
            :param value: value to set
        """

        if not hasattr(self.cfg, section):
            # not an osoError class because it should NEVER happened
            raise Exception("Section is not in the configuration file: " +
                            str(section))

        objSection = getattr(self.cfg, section)

        if not hasattr(objSection, variable):
            # not an osoError class because it should NEVER happened
            raise Exception("Variable is not in the configuration file: " +
                            str(variable))

        setattr(objSection, variable, value)

    def addParam(self, section, variable, value):
        """
            ADD and set a parameter in an existing section in the config
            file define in the init phase of the class.
            Do nothing if the parameter exist.
            :param section: string name of the section
            :param variable: string name of the variable
            :param value: value to set
        """
        if not hasattr(self.cfg, section):
            raise Exception(
                f"Section is not in the configuration file: {section}")

        objSection = getattr(self.cfg, section)
        if not hasattr(objSection, variable):
            setattr(objSection, variable, value)

    def forceParam(self, section, variable, value):
        """
            ADD a parameter in an existing section in the config
            file define in the init phase of the class if the parameter
            doesn't exist.
            FORCE the value if the parameter exist.
            Mainly used in Unitary test in order to force a value
            :param section: string name of the section
            :param variable: string name of the variable
            :param value: value to set
        """

        if not hasattr(self.cfg, section):
            # not an osoError class because it should NEVER happened
            raise Exception(
                f"Section is not in the configuration file: {section}")

        objSection = getattr(self.cfg, section)

        if not hasattr(objSection, variable):
            # It's normal because the parameter should not already exist
            # creation of attribute
            setattr(objSection, variable, value)

        else:
            # It already exist !!
            # setParam instead !!
            self.setParam(section, variable, value)

    def checkCustomFeature(self):
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

        module_path = self.getParam("external_features", "module")
        module_path_valid = check_code_path(module_path)
        if module_path_valid:
            module = check_import(module_path)
            check_function_in_module(
                module,
                self.getParam("external_features", "functions").split(" "))

            flag = True
        return flag


class iota2_parameters:
    """
    describe iota2 parameters as usual python dictionary
    """
    def __init__(self, configuration_file: str):
        """
        """
        self.__config = serviceConfigFile(configuration_file)

        self.projection = int(
            self.__config.getParam('GlobChain', 'proj').split(":")[-1])
        self.all_tiles = self.__config.getParam('chain', 'listTile')
        self.i2_output_path = self.__config.getParam('chain', 'outputPath')
        self.extract_bands_flag = self.__config.getParam(
            'iota2FeatureExtraction', 'extractBands')
        self.auto_date = self.__config.getParam('GlobChain', 'autoDate')
        self.write_outputs_flag = self.__config.getParam(
            'GlobChain', 'writeOutputs')
        self.features_list = self.__config.getParam('GlobChain', 'features')
        self.enable_gapfilling = self.__config.getParam(
            'GlobChain', 'useGapFilling')
        self.hand_features_flag = self.__config.getParam(
            'GlobChain', 'useAdditionalFeatures')
        self.copy_input = self.__config.getParam('iota2FeatureExtraction',
                                                 'copyinput')
        self.rel_refl = self.__config.getParam('iota2FeatureExtraction',
                                               'relrefl')
        self.keep_dupl = self.__config.getParam('iota2FeatureExtraction',
                                                'keepduplicates')
        self.vhr_path = self.__config.getParam('coregistration', 'VHRPath')
        self.acorfeat = self.__config.getParam('iota2FeatureExtraction',
                                               'acorfeat')
        self.user_patterns = self.__config.getParam('userFeat',
                                                    'patterns').split(",")
        self.available_sensors_section = [
            "Sentinel_2", "Sentinel_2_S2C", "Sentinel_2_L3A", "Sentinel_1",
            "Landsat8", "Landsat8_old", "Landsat5_old", "userFeat"
        ]

    def get_sensors_parameters(
            self, tile_name: str
    ) -> Dict[str, Dict[str, Union[str, List[str], int]]]:
        """get enabled sensors parameters
        """
        sensors_parameters = {}
        for sensor_section_name in self.available_sensors_section:
            sensor_parameter = self.build_sensor_dict(tile_name,
                                                      sensor_section_name)
            if sensor_parameter:
                sensors_parameters[sensor_section_name] = sensor_parameter
        return sensors_parameters

    def build_sensor_dict(self, tile_name: str, sensor_section_name: str
                          ) -> Dict[str, Union[str, List[str], int]]:
        """get sensor parameters
        """
        sensor_dict = {}
        sensor_output_target_dir = None
        sensor_data_param_name = ""
        if sensor_section_name == "Sentinel_2":
            sensor_data_param_name = "S2Path"
            sensor_output_target_dir = self.__config.getParam(
                "chain", "S2_output_path")
        elif sensor_section_name == "Sentinel_1":
            sensor_data_param_name = "S1Path"
        elif sensor_section_name == "Landsat8":
            sensor_data_param_name = "L8Path"
        elif sensor_section_name == "Landsat8_old":
            sensor_data_param_name = "L8Path_old"
        elif sensor_section_name == "Landsat5_old":
            sensor_data_param_name = "L5Path_old"
        elif sensor_section_name == "Sentinel_2_S2C":
            sensor_data_param_name = "S2_S2C_Path"
            sensor_output_target_dir = self.__config.getParam(
                "chain", "S2_S2C_output_path")
        elif sensor_section_name == "Sentinel_2_L3A":
            sensor_data_param_name = "S2_L3A_Path"
            sensor_output_target_dir = self.__config.getParam(
                "chain", "S2_L3A_output_path")
        elif sensor_section_name == "userFeat":
            sensor_data_param_name = "userFeatPath"
        else:
            raise ValueError(f"unknown section : {sensor_section_name}")

        sensor_data_path = self.__config.getParam("chain",
                                                  sensor_data_param_name)
        if "none" in sensor_data_path.lower():
            return sensor_dict
        if sensor_section_name == "Sentinel_1":
            sensor_section = {}
        else:
            sensor_section = self.__config.getSection(sensor_section_name)
        sensor_dict["tile_name"] = tile_name
        sensor_dict["target_proj"] = self.projection
        sensor_dict["all_tiles"] = self.all_tiles
        sensor_dict["image_directory"] = sensor_data_path
        sensor_dict["write_dates_stack"] = sensor_section.get(
            "write_reproject_resampled_input_dates_stack", None)
        sensor_dict["extract_bands_flag"] = self.extract_bands_flag
        sensor_dict["output_target_dir"] = sensor_output_target_dir
        sensor_dict["keep_bands"] = sensor_section.get("keepBands", None)
        sensor_dict["i2_output_path"] = self.i2_output_path
        sensor_dict["temporal_res"] = sensor_section.get(
            "temporalResolution", None)
        sensor_dict["auto_date_flag"] = self.auto_date
        sensor_dict["date_interp_min_user"] = sensor_section.get(
            "startDate", None)
        sensor_dict["date_interp_max_user"] = sensor_section.get(
            "endDate", None)
        sensor_dict["write_outputs_flag"] = self.write_outputs_flag
        sensor_dict["features"] = self.features_list
        sensor_dict["enable_gapfilling"] = self.enable_gapfilling
        sensor_dict["hand_features_flag"] = self.hand_features_flag
        sensor_dict["hand_features"] = sensor_section.get(
            "additionalFeatures", None)
        sensor_dict["copy_input"] = self.copy_input
        sensor_dict["rel_refl"] = self.rel_refl
        sensor_dict["keep_dupl"] = self.keep_dupl
        sensor_dict["vhr_path"] = self.vhr_path
        sensor_dict["acorfeat"] = self.acorfeat
        sensor_dict["patterns"] = self.user_patterns

        return sensor_dict
