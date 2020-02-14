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

# python -m unittest sensors_Tests
"""unittest sensors instances
"""
import os
import sys
import shutil
import unittest

IOTA2DIR = os.environ.get('IOTA2DIR')
RM_IF_ALL_OK = True


class iota2_test_sensors_test(unittest.TestCase):
    """Tests
    """
    # before launching tests
    @classmethod
    def setUpClass(cls):

        # definition of local variables
        cls.group_test_name = "iota2_test_sensors_test"
        cls.iota2_tests_directory = os.path.join(IOTA2DIR, "data",
                                                 cls.group_test_name)
        cls.all_tests_ok = []
        cls.test_working_directory = None
        if os.path.exists(cls.iota2_tests_directory):
            shutil.rmtree(cls.iota2_tests_directory)
        os.mkdir(cls.iota2_tests_directory)

        cls.config_test = os.path.join(
            IOTA2DIR, "config", "Config_4Tuiles_Multi_FUS_Confidence.cfg")

        # ref
        cls.expected_s2_labels = [
            'Sentinel2_B2_20200101', 'Sentinel2_B3_20200101',
            'Sentinel2_B4_20200101', 'Sentinel2_B5_20200101',
            'Sentinel2_B6_20200101', 'Sentinel2_B7_20200101',
            'Sentinel2_B8_20200101', 'Sentinel2_B8A_20200101',
            'Sentinel2_B11_20200101', 'Sentinel2_B12_20200101',
            'Sentinel2_B2_20200111', 'Sentinel2_B3_20200111',
            'Sentinel2_B4_20200111', 'Sentinel2_B5_20200111',
            'Sentinel2_B6_20200111', 'Sentinel2_B7_20200111',
            'Sentinel2_B8_20200111', 'Sentinel2_B8A_20200111',
            'Sentinel2_B11_20200111', 'Sentinel2_B12_20200111',
            'Sentinel2_NDVI_20200101', 'Sentinel2_NDVI_20200111',
            'Sentinel2_NDWI_20200101', 'Sentinel2_NDWI_20200111',
            'Sentinel2_Brightness_20200101', 'Sentinel2_Brightness_20200111'
        ]

        cls.expected_s2_s2c_labels = [
            'Sentinel2S2C_B02_20190501', 'Sentinel2S2C_B03_20190501',
            'Sentinel2S2C_B04_20190501', 'Sentinel2S2C_B05_20190501',
            'Sentinel2S2C_B06_20190501', 'Sentinel2S2C_B07_20190501',
            'Sentinel2S2C_B08_20190501', 'Sentinel2S2C_B8A_20190501',
            'Sentinel2S2C_B11_20190501', 'Sentinel2S2C_B12_20190501',
            'Sentinel2S2C_B02_20190504', 'Sentinel2S2C_B03_20190504',
            'Sentinel2S2C_B04_20190504', 'Sentinel2S2C_B05_20190504',
            'Sentinel2S2C_B06_20190504', 'Sentinel2S2C_B07_20190504',
            'Sentinel2S2C_B08_20190504', 'Sentinel2S2C_B8A_20190504',
            'Sentinel2S2C_B11_20190504', 'Sentinel2S2C_B12_20190504',
            'Sentinel2S2C_NDVI_20190501', 'Sentinel2S2C_NDVI_20190504',
            'Sentinel2S2C_NDWI_20190501', 'Sentinel2S2C_NDWI_20190504',
            'Sentinel2S2C_Brightness_20190501',
            'Sentinel2S2C_Brightness_20190504'
        ]

        cls.expected_l8_labels = [
            'Landsat8_B1_20200101', 'Landsat8_B2_20200101',
            'Landsat8_B3_20200101', 'Landsat8_B4_20200101',
            'Landsat8_B5_20200101', 'Landsat8_B6_20200101',
            'Landsat8_B7_20200101', 'Landsat8_B1_20200111',
            'Landsat8_B2_20200111', 'Landsat8_B3_20200111',
            'Landsat8_B4_20200111', 'Landsat8_B5_20200111',
            'Landsat8_B6_20200111', 'Landsat8_B7_20200111',
            'Landsat8_NDVI_20200101', 'Landsat8_NDVI_20200111',
            'Landsat8_NDWI_20200101', 'Landsat8_NDWI_20200111',
            'Landsat8_Brightness_20200101', 'Landsat8_Brightness_20200111'
        ]

        cls.expected_s2_l3a_labels = [
            'Sentinel2L3A_B2_20200101', 'Sentinel2L3A_B3_20200101',
            'Sentinel2L3A_B4_20200101', 'Sentinel2L3A_B5_20200101',
            'Sentinel2L3A_B6_20200101', 'Sentinel2L3A_B7_20200101',
            'Sentinel2L3A_B8_20200101', 'Sentinel2L3A_B8A_20200101',
            'Sentinel2L3A_B11_20200101', 'Sentinel2L3A_B12_20200101',
            'Sentinel2L3A_B2_20200120', 'Sentinel2L3A_B3_20200120',
            'Sentinel2L3A_B4_20200120', 'Sentinel2L3A_B5_20200120',
            'Sentinel2L3A_B6_20200120', 'Sentinel2L3A_B7_20200120',
            'Sentinel2L3A_B8_20200120', 'Sentinel2L3A_B8A_20200120',
            'Sentinel2L3A_B11_20200120', 'Sentinel2L3A_B12_20200120',
            'Sentinel2L3A_NDVI_20200101', 'Sentinel2L3A_NDVI_20200120',
            'Sentinel2L3A_NDWI_20200101', 'Sentinel2L3A_NDWI_20200120',
            'Sentinel2L3A_Brightness_20200101',
            'Sentinel2L3A_Brightness_20200120'
        ]
        cls.expected_user_features_labels = [
            'NUMBER_OF_THINGS_band_0', 'LAI_band_0'
        ]

        cls.expected_l8_old_labels = [
            'Landsat8Old_B1_20200101', 'Landsat8Old_B2_20200101',
            'Landsat8Old_B3_20200101', 'Landsat8Old_B4_20200101',
            'Landsat8Old_B5_20200101', 'Landsat8Old_B6_20200101',
            'Landsat8Old_B7_20200101', 'Landsat8Old_B1_20200111',
            'Landsat8Old_B2_20200111', 'Landsat8Old_B3_20200111',
            'Landsat8Old_B4_20200111', 'Landsat8Old_B5_20200111',
            'Landsat8Old_B6_20200111', 'Landsat8Old_B7_20200111',
            'Landsat8Old_NDVI_20200101', 'Landsat8Old_NDVI_20200111',
            'Landsat8Old_NDWI_20200101', 'Landsat8Old_NDWI_20200111',
            'Landsat8Old_Brightness_20200101',
            'Landsat8Old_Brightness_20200111'
        ]
        cls.expected_l5_old_labels = [
            'Landsat5Old_B1_20200101', 'Landsat5Old_B2_20200101',
            'Landsat5Old_B3_20200101', 'Landsat5Old_B4_20200101',
            'Landsat5Old_B5_20200101', 'Landsat5Old_B6_20200101',
            'Landsat5Old_B1_20200111', 'Landsat5Old_B2_20200111',
            'Landsat5Old_B3_20200111', 'Landsat5Old_B4_20200111',
            'Landsat5Old_B5_20200111', 'Landsat5Old_B6_20200111',
            'Landsat5Old_NDVI_20200101', 'Landsat5Old_NDVI_20200111',
            'Landsat5Old_NDWI_20200101', 'Landsat5Old_NDWI_20200111',
            'Landsat5Old_Brightness_20200101',
            'Landsat5Old_Brightness_20200111'
        ]

        cls.expected_sensors = [
            "Landsat5Old", "Landsat8", "Landsat8Old", "Sentinel2",
            "Sentinel2S2C", 'Sentinel2L3A'
        ]

    # after launching tests
    @classmethod
    def tearDownClass(cls):
        print("{} ended".format(cls.group_test_name))
        if RM_IF_ALL_OK and all(cls.all_tests_ok):
            shutil.rmtree(cls.iota2_tests_directory)

    # before launching a test
    def setUp(self):
        """
        create test environement (directories)
        """
        # create directories
        test_name = self.id().split(".")[-1]
        self.test_working_directory = os.path.join(self.iota2_tests_directory,
                                                   test_name)
        if os.path.exists(self.test_working_directory):
            shutil.rmtree(self.test_working_directory)
        os.mkdir(self.test_working_directory)

    def list2reason(self, exc_list):
        """ list2reason
        """
        out = None
        if exc_list and exc_list[-1][0] is self:
            out = exc_list[-1][1]
        return out

    def tearDown(self):
        """ after launching a test, remove test's data if test succeed
        """
        if sys.version_info > (3, 4, 0):
            result = self.defaultTestResult()
            self._feedErrorsToResult(result, self._outcome.errors)
        else:
            result = getattr(self, '_outcomeForDoCleanups',
                             self._resultForDoCleanups)
        error = self.list2reason(result.errors)
        failure = self.list2reason(result.failures)
        test_ok = not error and not failure

        self.all_tests_ok.append(test_ok)
        if test_ok:
            shutil.rmtree(self.test_working_directory)

    # Tests definitions
    def test_instance_s2(self):
        """Tests if the class sentinel_2 can be instanciate
        """
        from iota2.Sensors.Sentinel_2 import sentinel_2
        from TestsUtils import generate_fake_s2_data
        tile_name = "T31TCJ"
        generate_fake_s2_data(self.test_working_directory, tile_name,
                              ["20200101", "20200120"])
        args = {
            "tile_name": "T31TCJ",
            "target_proj": 2154,
            "all_tiles": "T31TCJ",
            "image_directory": self.test_working_directory,
            "write_dates_stack": False,
            "extract_bands_flag": False,
            "output_target_dir": None,
            "keep_bands": True,
            "i2_output_path": self.test_working_directory,
            "temporal_res": 10,
            "auto_date_flag": True,
            "date_interp_min_user": "",
            "date_interp_max_user": "",
            "write_outputs_flag": False,
            "features": ["NDVI", "NDWI", "Brightness"],
            "enable_gapfilling": True,
            "hand_features_flag": False,
            "hand_features": "",
            "copy_input": True,
            "rel_refl": False,
            "keep_dupl": True,
            "vhr_path": "none",
            "acorfeat": False
        }

        s2_sensor = sentinel_2(**args)
        (features_app, app_dep), features_labels = s2_sensor.get_features()
        print(features_labels)
        features_app.ExecuteAndWriteOutput()

        self.assertTrue(self.expected_s2_labels == features_labels,
                        msg="Sentinel-2 class broken, wrong features' labels")

        expected_output = features_app.GetParameterString("out")
        self.assertTrue(
            os.path.exists(expected_output),
            msg="Sentinel-2 class broken, not able to generate features")

    def test_instance_s2_s2c(self):
        """Tests if the class sentinel_2_s2c can be instanciate
        """
        from iota2.Sensors.Sentinel_2_S2C import sentinel_2_s2c
        from iota2.Tests.UnitTests.TestsUtils import generate_fake_s2_s2c_data
        tile_name = "T31TCJ"
        # generate fake input data
        mtd_files = [
            os.path.join(IOTA2DIR, "data", "MTD_MSIL2A_20190501.xml"),
            os.path.join(IOTA2DIR, "data", "MTD_MSIL2A_20190506.xml")
        ]

        generate_fake_s2_s2c_data(self.test_working_directory, mtd_files)
        args = {
            "tile_name": tile_name,
            "target_proj": 2154,
            "all_tiles": tile_name,
            "image_directory": self.test_working_directory,
            "write_dates_stack": False,
            "extract_bands_flag": False,
            "output_target_dir": "",
            "keep_bands": True,
            "i2_output_path": self.test_working_directory,
            "temporal_res": 3,
            "auto_date_flag": True,
            "date_interp_min_user": "",
            "date_interp_max_user": "",
            "write_outputs_flag": False,
            "features": ["NDVI", "NDWI", "Brightness"],
            "enable_gapfilling": True,
            "hand_features_flag": False,
            "hand_features": "",
            "copy_input": True,
            "rel_refl": False,
            "keep_dupl": True,
            "vhr_path": "none",
            "acorfeat": False
        }

        s2_sensor = sentinel_2_s2c(**args)
        (features_app, app_dep), features_labels = s2_sensor.get_features()
        features_app.ExecuteAndWriteOutput()

        self.assertTrue(
            self.expected_s2_s2c_labels == features_labels,
            msg="Sentinel_2_S2C class broken, wrong features' labels")

        expected_output = features_app.GetParameterString("out")
        self.assertTrue(
            os.path.exists(expected_output),
            msg="Sentinel_2_S2C class broken, not able to generate features")

    def test_instance_l8(self):
        """Tests if the class landsat_8 can be instanciate
        """
        from iota2.Sensors.Landsat_8 import landsat_8
        from TestsUtils import generate_fake_l8_data
        tile_name = "T31TCJ"
        generate_fake_l8_data(self.test_working_directory, tile_name,
                              ["20200101", "20200120"])
        args = {
            "tile_name": "T31TCJ",
            "target_proj": 2154,
            "all_tiles": "T31TCJ",
            "image_directory": self.test_working_directory,
            "write_dates_stack": False,
            "extract_bands_flag": False,
            "output_target_dir": None,
            "keep_bands": True,
            "i2_output_path": self.test_working_directory,
            "temporal_res": 10,
            "auto_date_flag": True,
            "date_interp_min_user": "",
            "date_interp_max_user": "",
            "write_outputs_flag": False,
            "features": ["NDVI", "NDWI", "Brightness"],
            "enable_gapfilling": True,
            "hand_features_flag": False,
            "hand_features": "",
            "copy_input": True,
            "rel_refl": False,
            "keep_dupl": True,
            "vhr_path": "none",
            "acorfeat": False
        }

        l8_sensor = landsat_8(**args)
        (features_app, _), features_labels = l8_sensor.get_features()
        features_app.ExecuteAndWriteOutput()

        self.assertTrue(self.expected_l8_labels == features_labels,
                        msg="Landsat_8 class broken, wrong features' labels")

        expected_output = features_app.GetParameterString("out")
        self.assertTrue(
            os.path.exists(expected_output),
            msg="Landsat_8 class broken, not able to generate features")

    def test_instance_user_features(self):
        """Tests if the class user_features can be instanciate
        """
        from iota2.Sensors.User_features import user_features
        from TestsUtils import generate_fake_user_features_data

        tile_name = "T31TCJ"
        patterns = ["NUMBER_OF_THINGS", "LAI"]
        generate_fake_user_features_data(self.test_working_directory,
                                         tile_name, patterns)
        args = {
            "tile_name": tile_name,
            "target_proj": 2154,
            "all_tiles": "T31TCJ",
            "image_directory": self.test_working_directory,
            "write_dates_stack": None,
            "extract_bands_flag": False,
            "output_target_dir": None,
            "keep_bands": True,
            "i2_output_path": self.test_working_directory,
            "temporal_res": None,
            "auto_date_flag": True,
            "date_interp_min_user": "",
            "date_interp_max_user": "",
            "write_outputs_flag": False,
            "features": [],
            "enable_gapfilling": True,
            "hand_features_flag": False,
            "hand_features": "",
            "copy_input": True,
            "rel_refl": False,
            "keep_dupl": True,
            "vhr_path": "none",
            "acorfeat": False,
            "patterns": patterns
        }
        user_feat_sensor = user_features(**args)
        (user_feat_stack, _), features_labels = user_feat_sensor.get_features()
        user_feat_stack.ExecuteAndWriteOutput()
        expected_output = user_feat_stack.GetParameterString("out")
        self.assertTrue(
            os.path.exists(expected_output),
            msg="user_features class broken, not able to generate features")
        self.assertTrue(
            self.expected_user_features_labels == features_labels,
            msg="user_features class broken, wrong features' labels")

    def test_instance_s2_l3a(self):
        """Tests if the class sentinel_2_l3a can be instanciate
        """
        from iota2.Sensors.Sentinel_2_L3A import sentinel_2_l3a
        from TestsUtils import generate_fake_s2_l3a_data
        tile_name = "T31TCJ"
        generate_fake_s2_l3a_data(self.test_working_directory, tile_name,
                                  ["20200101", "20200120"])
        args = {
            "tile_name": "T31TCJ",
            "target_proj": 2154,
            "all_tiles": "T31TCJ",
            "image_directory": self.test_working_directory,
            "write_dates_stack": False,
            "extract_bands_flag": False,
            "output_target_dir": None,
            "keep_bands": True,
            "i2_output_path": self.test_working_directory,
            "temporal_res": 10,
            "auto_date_flag": True,
            "date_interp_min_user": "",
            "date_interp_max_user": "",
            "write_outputs_flag": False,
            "features": ["NDVI", "NDWI", "Brightness"],
            "enable_gapfilling": True,
            "hand_features_flag": False,
            "hand_features": "",
            "copy_input": True,
            "rel_refl": False,
            "keep_dupl": True,
            "vhr_path": "none",
            "acorfeat": False
        }

        s2_l3a_sensor = sentinel_2_l3a(**args)
        (features_app, _), features_labels = s2_l3a_sensor.get_features()
        features_app.ExecuteAndWriteOutput()
        print(features_labels)
        self.assertTrue(
            self.expected_s2_l3a_labels == features_labels,
            msg="Sentinel 2 L3A class broken, wrong features' labels")

        expected_output = features_app.GetParameterString("out")
        self.assertTrue(
            os.path.exists(expected_output),
            msg="Sentinel 2 L3A class broken, not able to generate features")

    def test_sensors_container(self):
        """
        Test if the sensors_container class enable all required sensors
        """
        from iota2.Sensors.Sensors_container import sensors_container
        tile_name = "T31TCJ"
        args = {
            "Sentinel_2": {
                "tile_name": tile_name,
                "target_proj": 2154,
                "all_tiles": tile_name,
                "image_directory": self.test_working_directory,
                "write_dates_stack": False,
                "extract_bands_flag": False,
                "output_target_dir": "",
                "keep_bands": True,
                "i2_output_path": self.test_working_directory,
                "temporal_res": 10,
                "auto_date_flag": True,
                "date_interp_min_user": "",
                "date_interp_max_user": "",
                "write_outputs_flag": False,
                "features": ["NDVI", "NDWI", "Brightness"],
                "enable_gapfilling": True,
                "hand_features_flag": False,
                "hand_features": "",
                "copy_input": True,
                "rel_refl": False,
                "keep_dupl": True,
                "vhr_path": "none",
                "acorfeat": False
            },
            "Sentinel_2_S2C": {
                "tile_name": "T31TCJ",
                "target_proj": 2154,
                "all_tiles": "T31TCJ",
                "image_directory": self.test_working_directory,
                "write_dates_stack": False,
                "extract_bands_flag": False,
                "output_target_dir": None,
                "keep_bands": True,
                "i2_output_path": self.test_working_directory,
                "temporal_res": 10,
                "auto_date_flag": True,
                "date_interp_min_user": "",
                "date_interp_max_user": "",
                "write_outputs_flag": False,
                "features": ["NDVI", "NDWI", "Brightness"],
                "enable_gapfilling": True,
                "hand_features_flag": False,
                "hand_features": "",
                "copy_input": True,
                "rel_refl": False,
                "keep_dupl": True,
                "vhr_path": "none",
                "acorfeat": False
            },
            "Landsat8": {
                "tile_name": "T31TCJ",
                "target_proj": 2154,
                "all_tiles": "T31TCJ",
                "image_directory": self.test_working_directory,
                "write_dates_stack": False,
                "extract_bands_flag": False,
                "output_target_dir": None,
                "keep_bands": True,
                "i2_output_path": self.test_working_directory,
                "temporal_res": 10,
                "auto_date_flag": True,
                "date_interp_min_user": "",
                "date_interp_max_user": "",
                "write_outputs_flag": False,
                "features": ["NDVI", "NDWI", "Brightness"],
                "enable_gapfilling": True,
                "hand_features_flag": False,
                "hand_features": "",
                "copy_input": True,
                "rel_refl": False,
                "keep_dupl": True,
                "vhr_path": "none",
                "acorfeat": False
            },
            "Sentinel_2_L3A": {
                "tile_name": "T31TCJ",
                "target_proj": 2154,
                "all_tiles": "T31TCJ",
                "image_directory": self.test_working_directory,
                "write_dates_stack": False,
                "extract_bands_flag": False,
                "output_target_dir": None,
                "keep_bands": True,
                "i2_output_path": self.test_working_directory,
                "temporal_res": 10,
                "auto_date_flag": True,
                "date_interp_min_user": "",
                "date_interp_max_user": "",
                "write_outputs_flag": False,
                "features": ["NDVI", "NDWI", "Brightness"],
                "enable_gapfilling": True,
                "hand_features_flag": False,
                "hand_features": "",
                "copy_input": True,
                "rel_refl": False,
                "keep_dupl": True,
                "vhr_path": "none",
                "acorfeat": False
            }
        }
        sensors = sensors_container(tile_name, self.test_working_directory,
                                    self.test_working_directory, **args)
        enabled_sensors = sensors.get_enabled_sensors()
        sensors_name = [sensor.name for sensor in enabled_sensors]

        self.assertTrue(sensors_name == self.expected_sensors)

    def test_instance_l8_old(self):
        """Tests if the class landsat_8_old can be instanciate
        """
        from iota2.Sensors.Landsat_8_old import landsat_8_old
        from TestsUtils import generate_fake_l8_old_data
        tile_name = "France-MetropoleD0005H0002"
        generate_fake_l8_old_data(self.test_working_directory, tile_name,
                                  ["20200101", "20200120"])
        args = {
            "tile_name": tile_name,
            "target_proj": 2154,
            "all_tiles": tile_name,
            "image_directory": self.test_working_directory,
            "write_dates_stack": False,
            "extract_bands_flag": False,
            "output_target_dir": None,
            "keep_bands": True,
            "i2_output_path": self.test_working_directory,
            "temporal_res": 10,
            "auto_date_flag": True,
            "date_interp_min_user": "",
            "date_interp_max_user": "",
            "write_outputs_flag": False,
            "features": ["NDVI", "NDWI", "Brightness"],
            "enable_gapfilling": True,
            "hand_features_flag": False,
            "hand_features": "",
            "copy_input": True,
            "rel_refl": False,
            "keep_dupl": True,
            "vhr_path": "none",
            "acorfeat": False
        }

        l8_sensor = landsat_8_old(**args)
        (features_app, _), features_labels = l8_sensor.get_features()
        features_app.ExecuteAndWriteOutput()
        print(features_labels)
        self.assertTrue(
            self.expected_l8_old_labels == features_labels,
            msg="Landsat_ 8 old class broken, wrong features' labels")

        expected_output = features_app.GetParameterString("out")
        self.assertTrue(
            os.path.exists(expected_output),
            msg="Landsat_8_old class broken, not able to generate features")

    def test_instance_l5_old(self):
        """Tests if the class landsat_5_old can be instanciate
        """
        from iota2.Sensors.Landsat_5_old import landsat_5_old
        from TestsUtils import generate_fake_l5_old_data
        tile_name = "France-MetropoleD0005H0002"
        generate_fake_l5_old_data(self.test_working_directory, tile_name,
                                  ["20200101", "20200120"])
        args = {
            "tile_name": tile_name,
            "target_proj": 2154,
            "all_tiles": tile_name,
            "image_directory": self.test_working_directory,
            "write_dates_stack": False,
            "extract_bands_flag": False,
            "output_target_dir": None,
            "keep_bands": True,
            "i2_output_path": self.test_working_directory,
            "temporal_res": 10,
            "auto_date_flag": True,
            "date_interp_min_user": "",
            "date_interp_max_user": "",
            "write_outputs_flag": False,
            "features": ["NDVI", "NDWI", "Brightness"],
            "enable_gapfilling": True,
            "hand_features_flag": False,
            "hand_features": "",
            "copy_input": True,
            "rel_refl": False,
            "keep_dupl": True,
            "vhr_path": "none",
            "acorfeat": False
        }

        l5_sensor = landsat_5_old(**args)
        (features_app, _), features_labels = l5_sensor.get_features()
        features_app.ExecuteAndWriteOutput()
        self.assertTrue(
            self.expected_l5_old_labels == features_labels,
            msg="Landsat_ 5 old class broken, wrong features' labels")

        expected_output = features_app.GetParameterString("out")
        self.assertTrue(
            os.path.exists(expected_output),
            msg="Landsat_5_old class broken, not able to generate features")
