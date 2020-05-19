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
"""
from iota2.Common import ServiceError as sErr


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
    fieldType = layerDefinition.GetFieldDefn(field_index).GetFieldTypeName(
        fieldTypeCode)
    if fieldType != "String":
        raise sErr.configError("the region field must be a string")


def all_sameBands(items):
    return all(bands == items[0][1] for path, bands in items)


def check_chain_parameters(self):
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

        # self.testVarConfigFile(
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
        # self.testVarConfigFile(
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
        self.testVarConfigFile('chain', 'spatialResolution', int)
        self.testVarConfigFile('chain', 'colorTable', str)
        self.testVarConfigFile('chain', 'mode_outside_RegionSplit', float)
        self.testVarConfigFile('chain', 'merge_final_classifications', bool)
        self.testVarConfigFile('chain', 'enable_autoContext', bool)
        self.testVarConfigFile('chain', 'autoContext_iterations', int)
        if self.getParam("chain", "merge_final_classifications"):
            self.testVarConfigFile(
                'chain', 'merge_final_classifications_undecidedlabel', int)
            self.testVarConfigFile('chain',
                                   'merge_final_classifications_ratio', float)
            self.testVarConfigFile('chain',
                                   'merge_final_classifications_method', str,
                                   ["majorityvoting", "dempstershafer"])
            self.testVarConfigFile(
                'chain', 'dempstershafer_mob', str,
                ["precision", "recall", "accuracy", "kappa"])
            self.testVarConfigFile('chain', 'keep_runs_results', bool)
            self.testVarConfigFile(
                'chain', 'fusionOfClassificationAllSamplesValidation', bool)
        self.testVarConfigFile('chain', 'remove_tmp_files', bool)

        self.testVarConfigFile('chain', 'remove_tmp_files', bool)

        self.testVarConfigFile('chain', 'remove_tmp_files', bool)

    # Error managed
    except sErr.configFileError:
        print("Error in the configuration file " + self.pathConf)
        raise
    # Warning error not managed !
    except Exception:
        print("Something wrong happened in serviceConfigFile !")
        raise


def check_arg_train_parameters():
    try:
        self.testVarConfigFile('argTrain', 'classifier', str)
        self.testVarConfigFile('argTrain', 'options', str)
        self.testVarConfigFile('argTrain', 'cropMix', bool)
        self.testVarConfigFile('argTrain', 'prevFeatures', str)
        self.testVarConfigFile('argTrain', 'outputPrevFeatures', str)
        self.testVarConfigFile('argTrain', 'annualCrop', Sequence)
        self.testVarConfigFile('argTrain', 'ACropLabelReplacement', Sequence)

        self.testVarConfigFile('argTrain', 'sampleSelection', Mapping)
        self.testVarConfigFile('argTrain', 'samplesClassifMix', bool)
        self.testVarConfigFile('argTrain', 'validityThreshold', int)
    # Error managed
    except sErr.configFileError:
        print("Error in the configuration file " + self.pathConf)
        raise
    # Warning error not managed !
    except Exception:
        print("Something wrong happened in serviceConfigFile !")
        raise


def check_arg_classification_parameters():
    try:
        check_sampleSelection()
        check_sampleAugmentation()

        self.testVarConfigFile('argClassification', 'classifMode', str,
                               ["separate", "fusion"])
        self.testVarConfigFile('argClassification', 'enable_probability_map',
                               bool)
        self.testVarConfigFile('argClassification', 'noLabelManagement', str,
                               ["maxConfidence", "learningPriority"])
    # Error managed
    except sErr.configFileError:
        print("Error in the configuration file " + self.pathConf)
        raise
    # Warning error not managed !
    except Exception:
        print("Something wrong happened in serviceConfigFile !")
        raise


def check_glob_chain_parameters():
    try:
        self.testVarConfigFile('GlobChain', 'proj', str)
        self.testVarConfigFile('GlobChain', 'features', Sequence)
        self.testVarConfigFile('GlobChain', 'autoDate', bool)
        self.testVarConfigFile('GlobChain', 'writeOutputs', bool)
        self.testVarConfigFile('GlobChain', 'useAdditionalFeatures', bool)
        self.testVarConfigFile('GlobChain', 'useGapFilling', bool)
    # Error managed
    except sErr.configFileError:
        print("Error in the configuration file " + self.pathConf)
        raise
    # Warning error not managed !
    except Exception:
        print("Something wrong happened in serviceConfigFile !")
        raise


def check_i2_feature_extraction_parameters():
    try:
        self.testVarConfigFile('iota2FeatureExtraction', 'copyinput', bool)
        self.testVarConfigFile('iota2FeatureExtraction', 'relrefl', bool)
        self.testVarConfigFile('iota2FeatureExtraction', 'keepduplicates',
                               bool)
        self.testVarConfigFile('iota2FeatureExtraction', 'extractBands', bool)
        self.testVarConfigFile('iota2FeatureExtraction', 'acorfeat', bool)
    # Error managed
    except sErr.configFileError:
        print("Error in the configuration file " + self.pathConf)
        raise
    # Warning error not managed !
    except Exception:
        print("Something wrong happened in serviceConfigFile !")
        raise


def check_dim_red_parameters():
    try:
        self.testVarConfigFile('dimRed', 'dimRed', bool)
        self.testVarConfigFile('dimRed', 'targetDimension', int)
        self.testVarConfigFile('dimRed', 'reductionMode', str)

        if self.cfg.scikit_models_parameters.model_type is not None:
            self.testVarConfigFile('scikit_models_parameters', 'model_type',
                                   str)
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
            self.testVarConfigFile('Landsat5_old', 'temporalResolution', int)
            self.testVarConfigFile('Landsat5_old', 'keepBands', Sequence)
        if self.cfg.chain.L8Path != "None":
            # L8 variable check
            self.testVarConfigFile("Landsat8", "temporalResolution", int)
            self.testVarConfigFile("Landsat8", "keepBands", Sequence)
        if self.cfg.chain.L8Path_old != "None":
            #L8 variable check
            self.testVarConfigFile('Landsat8_old', 'temporalResolution', int)
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
                    raise sErr.fileError("the data's field " + currentField +
                                         " must be an integer in " +
                                         self.cfg.chain.groundTruth)
        if flag == 0:
            raise sErr.fileError("field name '" + self.cfg.chain.dataField +
                                 "' doesn't exist in " +
                                 self.cfg.chain.groundTruth)
    # Error managed
    except sErr.configFileError:
        print("Error in the configuration file " + self.pathConf)
        raise
    # Warning error not managed !
    except Exception:
        print("Something wrong happened in serviceConfigFile !")
        raise


def check_compat_param():

    # parameters compatibilities check
    classier_probamap_avail = ["sharkrf"]
    if (self.getParam("argClassification", "enable_probability_map") is True
            and self.getParam(
                "argTrain",
                "classifier").lower() not in classier_probamap_avail):
        raise sErr.configError(
            "'enable_probability_map:True' only available with the 'sharkrf' classifier"
        )
    if self.getParam("chain", "enableCrossValidation") is True:
        raise sErr.configError(
            "enableCrossValidation not available, please set it to False\n")
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
            "to perform post-classification fusion, optical data must be used")
    if self.cfg.scikit_models_parameters.model_type is not None and self.cfg.chain.enable_autoContext is True:
        raise sErr.configError(
            "these parameters are incompatible enable_autoContext : True and model_type"
        )

    return True
