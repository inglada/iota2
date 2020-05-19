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
Generic module to read any configuration file
"""
import os
import sys
from inspect import getmembers, isfunction
from typing import Dict, Union, List
from config import Config, Sequence, Mapping
from iota2.Common import ServiceError as sErr
from iota2.configuration_files import default_config_parameters as dcp


class read_config_file:
    """
    This class open a configuration file
    and provide usefull manipulation functions
    """
    def __init__(self, config_file):
        """
            Init class serviceConfigFile
            :param pathConf: string path of the config file
        """
        self.path_conf = config_file
        self.cfg = Config(open(config_file))
        # Load default builder parameters
        # if these parameters are filled in config file
        # they are not overwritted
        builder = {
            "mode": "classification",
            "custom_file": None,
            "custom_builder_class": None,
            "init_default_config_param_file": None
        }
        self.init_section("builder", builder)
        # user defaults settings have priority
        if self.cfg.builder.init_default_config_param_file is not None:
            self.load_custom_parameters()
        # then load all known parameters
        # there is no overwrite on already initialized parameters
        self.load_default_parameters()

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
            section_default = dcp.dico_mapping_init(sectionDefault)
            self.cfg.addMapping(sectionName, section_default, "")
        for key, value in list(sectionDefault.items()):
            self.addParam(sectionName, key, value)

    def __repr__(self):
        return "Configuration file : " + self.path_conf

    def testShapeName(self, input_vector):
        """
        """
        import string

        avail_characters = string.ascii_letters
        first_character = os.path.basename(input_vector)[0]
        if first_character not in avail_characters:
            raise sErr.configError(
                f"the file '{input_vector}' is containing a non-ascii letter "
                f"at first position in it's name : {first_character}")

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
        # TODO
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

    def load_default_parameters(self):
        # get all init function in default config parameters
        function_list = [
            fun for fun in getmembers(dcp) if isfunction(fun[1])
            and fun[0].startswith("init") and fun[0].endswith("parameters")
        ]

        for fun in function_list:
            block_name, default_params = fun[1]()
            self.init_section(block_name, default_params)

    def load_custom_parameters(self):
        # TODO
        # dynamic load of custom file cf custom features
        # for each function found, call init_section
        pass


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


# from iota2.configuration_files.base_read_config_file import base_config_file

# class load_config_file(base_config_file):
#     """
#     This class read a config file and init the different section
#     according to the detected builder
#     """
#     def __init__(self, path_conf):
#         super(load_config_file).__init__(path_conf)
#         builder_mode = self.cfg.getParam("builder", "mode")
#         if builder_mode == "classification":
#             from iota2.sequence_builders.i2_classification import i2_classification as builder
#         elif builder_mode == "features_map":
#             from iota2.sequence_builders.i2_features_map import i2_features_map as builder
#         else:
#             raise NotImplementedError

#         builder.load_default_parameters(self.cfg)

#     def init_config(self, params):

#         print(self, params)