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
"""unittest s2 instance
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
    #before launching tests
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
            'Sentinel2_B11_20200111', 'Sentinel2_B12_20200111'
        ]

    #after launching tests
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
        #create directories
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

    #Tests definitions
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
            "s2_data": self.test_working_directory,
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
        (features_app,
         _), features_labels = s2_sensor.get_time_series_gapFilling()
        features_app.ExecuteAndWriteOutput()

        self.assertTrue(self.expected_s2_labels == features_labels,
                        msg="Sentinel-2 class broken, wrong features' labels")

        expected_output = features_app.GetParameterString("out")
        self.assertTrue(
            os.path.exists(expected_output),
            msg="Sentinel-2 class broken, not able to generate features")
