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
from inspect import getmembers, isfunction
from config import Config, Sequence, Mapping, Container
from iota2.Common.FileUtils import FileSearch_AND, getRasterNbands, get_iota2_project_dir
from iota2.Common import ServiceError as sErr
from iota2.configuration_files import default_config_parameters as dcp
from iota2.configuration_files import check_config_parameters as ccp
# this is a pointer to the module object instance itself.
this = sys.modules[__name__]

# declaration of path_conf and cfg variables
this.path_conf = None
this.cfg = None


def clearConfig():
    if this.path_conf is not None:
        # also in local function scope. no scope specifier
        # like global is needed
        this.path_conf = None
        this.cfg = None


class read_config_file:
    """
    The class serviceConfigFile defines all methods to access to the
    configuration file and to check the variables.
    """
    def __init__(self, path_conf):
        """
            Init class serviceConfigFile
            :param path_conf: string path of the config file
        """
        self.path_conf = path_conf
        self.cfg = Config(open(path_conf))
        # set default values
        builder = {
            "mode": "classification",
            "custom_file": None,
            "custom_builder_class": None
        }
        self.init_section("builder", builder)
        self.load_params()
        self.check_params()

    def load_params(self):

        function_list = [
            fun for fun in getmembers(dcp) if isfunction(fun[1])
            and fun[0].startswith("init") and fun[0].endswith("parameters")
        ]

        for fun in function_list:
            block_name, default_params = fun[1]()
            self.init_section(block_name, default_params)

    def check_params(self):
        function_list = [
            fun for fun in getmembers(ccp)
            if isfunction(fun[1]) and fun[0].startswith("check")
        ]
        for fun in function_list:
            fun[1](self.cfg, self.path_conf)

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
        return "Configuration file : " + self.path_conf

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

    def load_params2(self):
        """For debug"""
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
        ACropLabelReplacement = self.init_listSequence(["10", "annualCrop"])

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
            "features": self.init_listSequence(["NDVI", "NDWI", "Brightness"]),
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
            self.init_listSequence(["B1", "B2", "B3", "B4", "B5", "B6", "B7"])
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
            self.init_listSequence(["B1", "B2", "B3", "B4", "B5", "B6", "B7"])
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
                "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"
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
                "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"
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
                "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"
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
            "concat_mode": True,
            "output_name": None
        }
        self.init_section("external_features", custom_features)
        return 0


class iota2_parameters:
    """
    describe iota2 parameters as usual python dictionary
    """
    def __init__(self, configuration_file: str):
        """
        """
        self.__config = read_config_file(configuration_file)

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
        self.working_resolution = self.__config.getParam(
            'chain', 'spatialResolution')

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
        sensor_dict["working_resolution"] = self.working_resolution
        return sensor_dict


# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# # =========================================================================
# #   Program:   iota2
# #
# #   Copyright (c) CESBIO. All rights reserved.
# #
# #   See LICENSE for details.
# #
# #   This software is distributed WITHOUT ANY WARRANTY; without even
# #   the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# #   PURPOSE.  See the above copyright notices for more information.
# #
# # =========================================================================
# """
# Generic module to read any configuration file
# """
# import os
# import sys
# from inspect import getmembers, isfunction
# from typing import Dict, Union, List, Optional
# from config import Config, Sequence, Mapping
# from iota2.Common import ServiceError as sErr
# from iota2.configuration_files import default_config_parameters as dcp

# # this is a pointer to the module object instance itself.
# this = sys.modules[__name__]

# # declaration of pathConf and cfg variables
# this.pathConf = None
# this.cfg = None

# class read_config_file:
#     """
#     This class open a configuration file
#     and provide usefull manipulation functions
#     """
#     def __init__(self, config_file):
#         """
#             Init class serviceConfigFile
#             :param pathConf: string path of the config file
#         """
#         self.path_conf = config_file
#         self.cfg = Config(open(config_file))
#         name, block = dcp.init_chain_parameters()
#         self.init_section(name, block)
#         input(self.cfg)
#         # Load default builder parameters
#         # if these parameters are filled in config file
#         # they are not overwritted
#         builder = {
#             "mode": "classification",
#             "custom_file": None,
#             "custom_builder_class": None,
#             "init_default_config_param_file": None
#         }
#         self.init_section("builder", builder)
#         print(self.getParam("builder", "mode"))
#         # # user defaults settings have priority
#         # if self.cfg.builder.init_default_config_param_file is not None:
#         #     self.load_custom_parameters()
#         # then load all known parameters
#         # there is no overwrite on already initialized parameters
#         self.load_default_parameters()
#         print("init")
#         print(self.cfg)
#         print(self.getParam("builder", "mode"))

#     def init_section(self, section_name, section_default):
#         """use to initialize a full configuration file section

#         Parameters
#         ----------
#         sectionName : string
#             section's name
#         sectionDefault : dict
#             default values are store in a python dictionnary
#         """

#         if not hasattr(self.cfg, section_name):
#             # section_default = dcp.dico_mapping_init(section_default)
#             self.cfg.addMapping(section_name, section_default, "")
#         else:
#             for key, value in list(section_default.items()):
#                 self.addParam(section_name, key, value)

#     def __repr__(self):
#         return "Configuration file : " + self.path_conf

#     def test_shape_name(self, input_vector):
#         """
#         """
#         import string

#         avail_characters = string.ascii_letters
#         first_character = os.path.basename(input_vector)[0]
#         if first_character not in avail_characters:
#             raise sErr.configError(
#                 f"the file '{input_vector}' is containing a non-ascii letter "
#                 f"at first position in it's name : {first_character}")

#     def test_var_config_file(self,
#                              section,
#                              variable,
#                              varType,
#                              valeurs="",
#                              valDefaut=""):
#         """
#             This function check if variable is in obj
#             and if it has varType type.
#             Optionnaly it can check if variable has values in valeurs
#             Exit the code if any error are detected
#         Inputs:
#             :param section: section name of the obj where to find
#             :param variable: string name of the variable
#             :param varType: type type of the variable for verification
#             :param valeurs: string list of the possible value of variable
#             :param valDefaut: value by default if variable is not in the configuration file
#         """

#         if not hasattr(self.cfg, section):
#             raise sErr.configFileError("Section '" + str(section) +
#                                        "' is not in the configuration file")

#         obj_section = getattr(self.cfg, section)

#         if not hasattr(obj_section, variable):
#             if valDefaut != "":
#                 setattr(obj_section, variable, valDefaut)
#             else:
#                 raise sErr.parameterError(
#                     section, "mandatory variable '" + str(variable) +
#                     "' is missing in the configuration file")
#         else:
#             tmpVar = getattr(obj_section, variable)

#             if not isinstance(tmpVar, varType):
#                 message = ("variable '" + str(variable) +
#                            "' has a wrong type\nActual: " + str(type(tmpVar)) +
#                            " expected: " + str(varType))
#                 raise sErr.parameterError(section, message)

#             if valeurs != "":
#                 ok = 0
#                 for index in range(len(valeurs)):
#                     if tmpVar == valeurs[index]:
#                         ok = 1
#                 if ok == 0:
#                     message = ("bad value for '" + variable +
#                                "' variable. Value accepted: " + str(valeurs) +
#                                " Value read: " + str(tmpVar))
#                     raise sErr.parameterError(section, message)

#     def testDirectory(self, directory):
#         if not os.path.exists(directory):
#             raise sErr.dirError(directory)

#     def checkConfigParameters(self):
#         """
#             check parameters coherence
#             :return: true if ok
#         """
#         # TODO
#         return True

#     def getAvailableSections(self):
#         """
#         Return all sections in the configuration file
#         :return: list of available section
#         """
#         return [section for section in list(self.cfg.keys())]

#     def getSection(self, section):
#         """
#         """
#         if not hasattr(self.cfg, section):
#             # not an osoError class because it should NEVER happened
#             raise Exception(
#                 "Section {} is not in the configuration file ".format(section))
#         return getattr(self.cfg, section)

#     def getParam(self, section, variable):
#         """
#             Return the value of variable in the section from config
#             file define in the init phase of the class.
#             :param section: string name of the section
#             :param variable: string name of the variable
#             :return: the value of variable
#         """

#         if not hasattr(self.cfg, section):
#             # not an osoError class because it should NEVER happened
#             raise Exception("Section is not in the configuration file: " +
#                             str(section))

#         obj_section = getattr(self.cfg, section)
#         if not hasattr(obj_section, variable):
#             # not an osoError class because it should NEVER happened
#             raise Exception("Variable is not in the configuration file: " +
#                             str(variable))

#         tmpVar = getattr(obj_section, variable)

#         return tmpVar

#     def setParam(self, section, variable, value):
#         """
#             Set the value of variable in the section from config
#             file define in the init phase of the class.
#             Mainly used in Unitary test in order to force a value
#             :param section: string name of the section
#             :param variable: string name of the variable
#             :param value: value to set
#         """

#         if not hasattr(self.cfg, section):
#             # not an osoError class because it should NEVER happened
#             raise Exception("Section is not in the configuration file: " +
#                             str(section))

#         obj_section = getattr(self.cfg, section)

#         if not hasattr(obj_section, variable):
#             # not an osoError class because it should NEVER happened
#             raise Exception("Variable is not in the configuration file: " +
#                             str(variable))

#         setattr(obj_section, variable, value)

#     def addParam(self, section, variable, value):
#         """
#             ADD and set a parameter in an existing section in the config
#             file define in the init phase of the class.
#             Do nothing if the parameter exist.
#             :param section: string name of the section
#             :param variable: string name of the variable
#             :param value: value to set
#         """
#         if not hasattr(self.cfg, section):
#             raise Exception(
#                 f"Section is not in the configuration file: {section}")

#         obj_section = getattr(self.cfg, section)
#         print(self.cfg)
#         if not hasattr(obj_section, variable):
#             # input("here add params")
#             print(obj_section, variable, value)
#             # input("wait")
#             setattr(obj_section, variable, value)

#     def forceParam(self, section, variable, value):
#         """
#             ADD a parameter in an existing section in the config
#             file define in the init phase of the class if the parameter
#             doesn't exist.
#             FORCE the value if the parameter exist.
#             Mainly used in Unitary test in order to force a value
#             :param section: string name of the section
#             :param variable: string name of the variable
#             :param value: value to set
#         """

#         if not hasattr(self.cfg, section):
#             # not an osoError class because it should NEVER happened
#             raise Exception(
#                 f"Section is not in the configuration file: {section}")

#         obj_section = getattr(self.cfg, section)

#         if not hasattr(obj_section, variable):
#             # It's normal because the parameter should not already exist
#             # creation of attribute
#             setattr(obj_section, variable, value)

#         else:
#             # It already exist !!
#             # setParam instead !!
#             self.setParam(section, variable, value)

#     def load_default_parameters(self):
#         # get all init function in default config parameters
#         function_list = [
#             fun for fun in getmembers(dcp) if isfunction(fun[1])
#             and fun[0].startswith("init") and fun[0].endswith("parameters")
#         ]
#         # input(function_list)
#         for fun in function_list:
#             block_name, default_params = fun[1]()
#             # input(block_name)
#             # input(default_params)
#             print("load def fun : ", fun)
#             self.init_section(block_name, default_params)

#     def load_custom_parameters(self):
#         # TODO
#         # dynamic load of custom file cf custom features
#         # for each function found, call init_section
#         pass

# class iota2_parameters:
#     """
#     describe iota2 parameters as usual python dictionary
#     """
#     def __init__(self, configuration_file: str):
#         """
#         """
#         self.__config = read_config_file(configuration_file)

#         self.projection = int(
#             self.__config.getParam('GlobChain', 'proj').split(":")[-1])
#         self.all_tiles = self.__config.getParam('chain', 'listTile')
#         self.i2_output_path = self.__config.getParam('chain', 'outputPath')
#         self.extract_bands_flag = self.__config.getParam(
#             'iota2FeatureExtraction', 'extractBands')
#         self.auto_date = self.__config.getParam('GlobChain', 'autoDate')
#         self.write_outputs_flag = self.__config.getParam(
#             'GlobChain', 'writeOutputs')
#         self.features_list = self.__config.getParam('GlobChain', 'features')
#         self.enable_gapfilling = self.__config.getParam(
#             'GlobChain', 'useGapFilling')
#         self.hand_features_flag = self.__config.getParam(
#             'GlobChain', 'useAdditionalFeatures')
#         self.copy_input = self.__config.getParam('iota2FeatureExtraction',
#                                                  'copyinput')
#         self.rel_refl = self.__config.getParam('iota2FeatureExtraction',
#                                                'relrefl')
#         self.keep_dupl = self.__config.getParam('iota2FeatureExtraction',
#                                                 'keepduplicates')
#         self.vhr_path = self.__config.getParam('coregistration', 'VHRPath')
#         self.acorfeat = self.__config.getParam('iota2FeatureExtraction',
#                                                'acorfeat')
#         self.user_patterns = self.__config.getParam('userFeat',
#                                                     'patterns').split(",")
#         self.available_sensors_section = [
#             "Sentinel_2", "Sentinel_2_S2C", "Sentinel_2_L3A", "Sentinel_1",
#             "Landsat8", "Landsat8_old", "Landsat5_old", "userFeat"
#         ]

#     def get_sensors_parameters(
#             self, tile_name: str
#     ) -> Dict[str, Dict[str, Union[str, List[str], int, Optional[str]]]]:
#         """get enabled sensors parameters
#         """
#         sensors_parameters = {}
#         for sensor_section_name in self.available_sensors_section:
#             sensor_parameter = self.build_sensor_dict(tile_name,
#                                                       sensor_section_name)
#             if sensor_parameter:
#                 sensors_parameters[sensor_section_name] = sensor_parameter
#         return sensors_parameters

#     def build_sensor_dict(
#             self, tile_name: str, sensor_section_name: str
#     ) -> Dict[str, Union[str, List[str], int, Optional[str]]]:
#         """get sensor parameters
#         """
#         sensor_dict: Dict[str, Union[str, List[str], int, Optional[str]]] = {}
#         sensor_output_target_dir: Optional[str] = None
#         sensor_data_param_name = ""
#         if sensor_section_name == "Sentinel_2":
#             sensor_data_param_name = "S2Path"
#             sensor_output_target_dir = self.__config.getParam(
#                 "chain", "S2_output_path")
#         elif sensor_section_name == "Sentinel_1":
#             sensor_data_param_name = "S1Path"
#         elif sensor_section_name == "Landsat8":
#             sensor_data_param_name = "L8Path"
#         elif sensor_section_name == "Landsat8_old":
#             sensor_data_param_name = "L8Path_old"
#         elif sensor_section_name == "Landsat5_old":
#             sensor_data_param_name = "L5Path_old"
#         elif sensor_section_name == "Sentinel_2_S2C":
#             sensor_data_param_name = "S2_S2C_Path"
#             sensor_output_target_dir = self.__config.getParam(
#                 "chain", "S2_S2C_output_path")
#         elif sensor_section_name == "Sentinel_2_L3A":
#             sensor_data_param_name = "S2_L3A_Path"
#             sensor_output_target_dir = self.__config.getParam(
#                 "chain", "S2_L3A_output_path")
#         elif sensor_section_name == "userFeat":
#             sensor_data_param_name = "userFeatPath"
#         else:
#             raise ValueError(f"unknown section : {sensor_section_name}")

#         sensor_data_path = self.__config.getParam("chain",
#                                                   sensor_data_param_name)
#         if "none" in sensor_data_path.lower():
#             return sensor_dict
#         if sensor_section_name == "Sentinel_1":
#             sensor_section = {}
#         else:
#             sensor_section = self.__config.getSection(sensor_section_name)
#         sensor_dict["tile_name"] = tile_name
#         sensor_dict["target_proj"] = self.projection
#         sensor_dict["all_tiles"] = self.all_tiles
#         sensor_dict["image_directory"] = sensor_data_path
#         sensor_dict["write_dates_stack"] = sensor_section.get(
#             "write_reproject_resampled_input_dates_stack", None)
#         sensor_dict["extract_bands_flag"] = self.extract_bands_flag
#         sensor_dict["output_target_dir"] = sensor_output_target_dir
#         sensor_dict["keep_bands"] = sensor_section.get("keepBands", None)
#         sensor_dict["i2_output_path"] = self.i2_output_path
#         sensor_dict["temporal_res"] = sensor_section.get(
#             "temporalResolution", None)
#         sensor_dict["auto_date_flag"] = self.auto_date
#         sensor_dict["date_interp_min_user"] = sensor_section.get(
#             "startDate", None)
#         sensor_dict["date_interp_max_user"] = sensor_section.get(
#             "endDate", None)
#         sensor_dict["write_outputs_flag"] = self.write_outputs_flag
#         sensor_dict["features"] = self.features_list
#         sensor_dict["enable_gapfilling"] = self.enable_gapfilling
#         sensor_dict["hand_features_flag"] = self.hand_features_flag
#         sensor_dict["hand_features"] = sensor_section.get(
#             "additionalFeatures", None)
#         sensor_dict["copy_input"] = self.copy_input
#         sensor_dict["rel_refl"] = self.rel_refl
#         sensor_dict["keep_dupl"] = self.keep_dupl
#         sensor_dict["vhr_path"] = self.vhr_path
#         sensor_dict["acorfeat"] = self.acorfeat
#         sensor_dict["patterns"] = self.user_patterns

#         return sensor_dict

# # from iota2.configuration_files.base_read_config_file import base_config_file

# # class load_config_file(base_config_file):
# #     """
# #     This class read a config file and init the different section
# #     according to the detected builder
# #     """
# #     def __init__(self, path_conf):
# #         super(load_config_file).__init__(path_conf)
# #         builder_mode = self.cfg.getParam("builder", "mode")
# #         if builder_mode == "classification":
# #             from iota2.sequence_builders.i2_classification import i2_classification as builder
# #         elif builder_mode == "features_map":
# #             from iota2.sequence_builders.i2_features_map import i2_features_map as builder
# #         else:
# #             raise NotImplementedError

# #         builder.load_default_parameters(self.cfg)

# #     def init_config(self, params):

# #         print(self, params)
