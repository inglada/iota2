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
This class manage sensor's data by tile, providing services needed in whole IOTA²
library
"""
import os

from Sensors.Sentinel_1 import Sentinel_1
from Sensors.Sentinel_2 import Sentinel_2
from Sensors.Sentinel_2_S2C import Sentinel_2_S2C
from Sensors.Sentinel_2_L3A import Sentinel_2_L3A
from Sensors.Landsat_5_old import Landsat_5_old
from Sensors.Landsat_8 import Landsat_8
from Sensors.Landsat_8_old import Landsat_8_old
from Sensors.User_features import User_features


class Sensors_container(object):
    def __init__(self, config_path, tile_name, working_dir):
        """
        Parameters
        ----------
        config_path : string
            absolute path to a IOTA2 configuration file
        tile_name : string
            tile to consider : "T31TCJ"
        working_dir : string
            absolute path to a working directory dedicated to compute temporary
            data

        TODO : make the class independant from a configuration file
        """
        from Common import ServiceConfigFile as SCF

        self.cfg = SCF.serviceConfigFile(config_path)
        self.tile_name = tile_name
        self.working_dir = working_dir

        self.enabled_sensors = self.get_enabled_sensors()
        self.common_mask_name = "MaskCommunSL.tif"
        self.features_dir = os.path.join(self.cfg.getParam("chain", "outputPath"),
                                         "features", tile_name)
        self.common_mask_dir = os.path.join(self.features_dir, "tmp")

    def __str__(self):
        """return enabled sensors and the current tile
        """
        return "tile's name : {}, available sensors : {}".format(self.tile_name,
                                                                 ", ".join(self.print_enabled_sensors_name()))

    def __repr__(self):
        """return enabled sensors and the current tile
        """
        return self.__str__()

    def get_iota2_sensors_names(self):
        """sensor manageable by IOTA2

        Return
        ------
        list
            list of manageable sensors' name
        """
        available_sensors_name = [Landsat5.name,
                                  Landsat8.name,
                                  Landsat_8_old.name,
                                  Sentinel_1.name,
                                  Sentinel_2.name,
                                  Sentinel_2_S2C.name,
                                  Sentinel_2_L3A.name,
                                  User_features.name]
        return available_sensors_name

    def print_enabled_sensors_name(self):
        """define which sensors will be used

        Return
        ------
        list
            list of enabled sensors's name
        """
        l5_old = self.cfg.getParam("chain", "L5Path_old")
        l8 = self.cfg.getParam("chain", "L8Path")
        l8_old = self.cfg.getParam("chain", "L8Path_old")
        s1 = self.cfg.getParam("chain", "S1Path")
        s2 = self.cfg.getParam("chain", "S2Path")
        s2_s2c = self.cfg.getParam("chain", "S2_S2C_Path")
        s2_l3a = self.cfg.getParam("chain", "S2_L3A_Path")
        user_feat = self.cfg.getParam("chain", "userFeatPath")

        enabled_sensors = []
        if not "none" in l5_old.lower():
            enabled_sensors.append(Landsat_5_old.name)
        if not "none" in l8.lower():
            enabled_sensors.append(Landsat_8.name)
        if not "none" in l8_old.lower():
            enabled_sensors.append(Landsat_8_old.name)
        if not "none" in s1.lower():
            enabled_sensors.append(Sentinel_1.name)
        if not "none" in s2.lower():
            enabled_sensors.append(Sentinel_2.name)
        if not "none" in s2_s2c.lower():
            enabled_sensors.append(Sentinel_2_S2C.name)
        if not "none" in s2_l3a.lower():
            enabled_sensors.append(Sentinel_2_L3A.name)
        if not "none" in user_feat.lower():
            enabled_sensors.append(User_features.name)
        return enabled_sensors

    def get_sensor(self, sensor_name):
        """get a sensor by name

        Parameters
        ----------
        sensor_name : string
            sensor's name

        Return
        ------
        sensor
            return the sensor with the name "sensor_name". If no sensors are found
            return None
        """
        sensor_found = []
        for sensor in self.enabled_sensors:
            if sensor_name == sensor.__class__.name:
                sensor_found.append(sensor)
        if len(sensor_found) > 1:
            raise Exception(
                "Too many sensors found with the name {}".format(sensor_name))
        return sensor_found[0] if sensor_found else None

    def remove_sensor(self, sensor_name):
        """remove a sensor in the available sensor list

        Parameters
        ----------
        sensor_name : string
            sensor's name
        """
        for index, sensor in enumerate(self.enabled_sensors):
            if sensor_name == sensor.__class__.name:
                self.enabled_sensors.pop(index)

    def get_enabled_sensors(self):
        """build enabled sensor list

        This function define sensors to use in IOTA2 run. It is where sensor's
        order is define : Landsat-5, Landsat-8 until user-features

        Return
        ------
        list
            list of enabled sensors
        """
        l5_old = self.cfg.getParam("chain", "L5Path_old")
        l8 = self.cfg.getParam("chain", "L8Path")
        l8_old = self.cfg.getParam("chain", "L8Path_old")
        s1 = self.cfg.getParam("chain", "S1Path")
        s2 = self.cfg.getParam("chain", "S2Path")
        s2_s2c = self.cfg.getParam("chain", "S2_S2C_Path")
        s2_l3a = self.cfg.getParam("chain", "S2_L3A_Path")
        user_feat = self.cfg.getParam("chain", "userFeatPath")

        enabled_sensors = []
        if not "none" in l5_old.lower():
            enabled_sensors.append(
                Landsat_5_old(
                    self.cfg.pathConf,
                    tile_name=self.tile_name))
        if not "none" in l8.lower():
            enabled_sensors.append(
                Landsat_8(
                    self.cfg.pathConf,
                    tile_name=self.tile_name))
        if not "none" in l8_old.lower():
            enabled_sensors.append(
                Landsat_8_old(
                    self.cfg.pathConf,
                    tile_name=self.tile_name))
        if not "none" in s1.lower():
            enabled_sensors.append(
                Sentinel_1(
                    self.cfg.pathConf,
                    tile_name=self.tile_name))
        if not "none" in s2.lower():
            enabled_sensors.append(
                Sentinel_2(
                    self.cfg.pathConf,
                    tile_name=self.tile_name))
        if not "none" in s2_s2c.lower():
            enabled_sensors.append(
                Sentinel_2_S2C(
                    self.cfg.pathConf,
                    tile_name=self.tile_name))
        if not "none" in s2_l3a.lower():
            enabled_sensors.append(
                Sentinel_2_L3A(
                    self.cfg.pathConf,
                    tile_name=self.tile_name))
        if not "none" in user_feat.lower():
            enabled_sensors.append(
                User_features(
                    self.cfg.pathConf,
                    tile_name=self.tile_name))
        return enabled_sensors

    def sensors_preprocess(self, available_ram=128):
        """preprocessing every enabled sensors

        Parameters
        ----------
        available_ram : int
            RAM, usefull to many OTB's applications.
        """
        for sensor in self.enabled_sensors:
            self.sensor_preprocess(sensor, self.working_dir, available_ram)

    def sensor_preprocess(self, sensor, working_dir, available_ram):
        """sensor preprocessing

        Parameters
        ----------
        sensor : sensor
        working_dir : string
            absolute path to a working directory dedicated to compute temporary
            data
        available_ram : int
            RAM, usefull to many OTB's applications.

        Return
        ------
        object
            return the object returned from sensor.preprocess. Nowadays, nothing
            is done with it, no object's type are imposed but it could change.
        """
        sensor_prepro_app = None
        if "preprocess" in dir(sensor):
            sensor_prepro_app = sensor.preprocess(
                working_dir=working_dir, ram=available_ram)
        return sensor_prepro_app

    def sensors_dates(self):
        """by sensors, get available dates

        if exists get_available_dates's sensor method is called. The method must
        return a list of sorted available dates.

        Return
        ------
        list
            list of tuple containing (sensor's name, [list of available dates])
        """
        sensors_dates = []
        for sensor in self.enabled_sensors:
            dates_list = []
            if "get_available_dates" in dir(sensor):
                dates_list = sensor.get_available_dates()
            sensors_dates.append((sensor.__class__.name, dates_list))
        return sensors_dates

    def get_sensors_footprint(self, available_ram=128):
        """get sensor's footprint

        It provide the list of otb's application dedicated to generate sensor's
        footprint. Each otb's application must be dedicated to the generation of
        a binary raster, 0 meaning 'NODATA'

        Parameters
        ----------
        available_ram : int
            RAM, usefull to many OTB's applications.

        Return
        ------
        list
            list of tuple containing (sensor's name, otbApplication)
        """
        sensors_footprint = []
        for sensor in self.enabled_sensors:
            sensors_footprint.append(
                (sensor.__class__.name, sensor.footprint(available_ram)))
        return sensors_footprint

    def get_common_sensors_footprint(self, available_ram=128):
        """get common sensor's footprint

        provide an otbApplication ready to be 'ExecuteAndWriteOutput' generating
        a binary raster which is the intersection of all sensor's footprint

        Parameters
        ----------
        available_ram : int
            RAM, usefull to many OTB's applications.

        Return
        ------
        tuple
            (otbApplication, dependencies)
        """
        from Common.OtbAppBank import CreateBandMathApplication
        sensors_footprint = []
        all_dep = []
        for sensor in self.enabled_sensors:
            footprint, _ = sensor.footprint(available_ram)
            footprint.Execute()
            sensors_footprint.append(footprint)
            all_dep.append(_)
            all_dep.append(footprint)

        expr = "+".join("im{}b1".format(i + 1)
                        for i in range(len(sensors_footprint)))
        expr = "{}=={}?1:0".format(expr, len(sensors_footprint))
        common_mask_out = os.path.join(
            self.common_mask_dir, self.common_mask_name)
        common_mask = CreateBandMathApplication({"il": sensors_footprint,
                                                 "exp": expr,
                                                 "out": common_mask_out,
                                                 "pixType": "uint8",
                                                 "ram": str(available_ram)})
        return common_mask, all_dep

    def get_sensors_time_series(self, available_ram=128):
        """get time series to each enabled sensors

        Parameters
        ----------
        available_ram : int
            RAM, usefull to many OTB's applications.

        Return
        ------
        list
            list of tuple : (sensor's name, (otbApplication, dependencies), labels)
            where labels are sorted feature's name
        """
        sensors_time_series = []
        for sensor in self.enabled_sensors:
            if "get_time_series" in dir(sensor):
                sensors_time_series.append(
                    (sensor.__class__.name, sensor.get_time_series(available_ram)))
        return sensors_time_series

    def get_sensors_time_series_masks(self, available_ram=128):
        """get time series masks to each enabled sensors

        Parameters
        ----------
        available_ram : int
            RAM, usefull to many OTB's applications.

        Return
        ------
        list
            list of tuple : (sensor's name, (otbApplication, dependencies, number of masks))
        """
        sensors_time_series_masks = []
        for sensor in self.enabled_sensors:
            if "get_time_series_masks" in dir(sensor):
                sensors_time_series_masks.append(
                    (sensor.__class__.name, sensor.get_time_series_masks(available_ram)))
        return sensors_time_series_masks

    def get_sensors_time_series_gapfilling(self, available_ram=128):
        """get time series gapfilled to each enabled sensors

        Parameters
        ----------
        available_ram : int
            RAM, usefull to many OTB's applications.

        Return
        ------
        list
            list of tuple : (sensor's name, ((otbApplication, dependencies), labels))
            where labels are sorted feature's name
        """
        sensors_time_series = []
        for sensor in self.enabled_sensors:
            if "get_time_series_gapFilling" in dir(sensor):
                sensors_time_series.append(
                    (sensor.__class__.name, sensor.get_time_series_gapFilling(available_ram)))
        return sensors_time_series

    def get_sensors_features(self, available_ram=128):
        """get features to each enabled sensors

        Parameters
        ----------
        available_ram : int
            RAM, usefull to many OTB's applications.

        Return
        ------
        list
            list of tuple : (sensor's name, ((otbApplication, dependencies), labels))
            where labels are sorted feature's name
        """
        sensors_features = []
        for sensor in self.enabled_sensors:
            sensors_features.append(
                (sensor.__class__.name, sensor.get_features(available_ram)))
        return sensors_features
