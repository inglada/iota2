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

from iota2.Common.FileUtils import ensure_dir

IOTA2DIR = os.environ.get('IOTA2DIR')
RM_IF_ALL_OK = True


class iota2_test_sentinel1_test(unittest.TestCase):
    """Test sentinel_1
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

        cls.ref_sar_config_test = os.path.join(
            IOTA2DIR, "data", "test_vector", "ConfigurationFile_SAR_Test.cfg")
        cls.large_scale_data = "/work/OT/theia/oso/dataTest/test_LargeScale"

        cls.ref_sar_config = os.path.join(IOTA2DIR, "config", "SARconfig.cfg")
        cls.sar_features_path = os.path.join(
            IOTA2DIR, "data", "test_vector",
            "checkOnlySarFeatures_features_SAR")
        ensure_dir(cls.sar_features_path)
        cls.sar_data = os.path.join(cls.large_scale_data, "SAR_directory",
                                    "raw_data")
        cls.srtm = os.path.join(cls.large_scale_data, "SAR_directory", "SRTM")
        cls.geoid = os.path.join(cls.large_scale_data, "SAR_directory",
                                 "egm96.grd")
        cls.s2_large_scale = os.path.join(cls.large_scale_data, "S2_50x50")
        cls.tiles_shape = os.path.join(cls.large_scale_data, "SAR_directory",
                                       "Features.shp")
        cls.srtm_shape = os.path.join(cls.large_scale_data, "SAR_directory",
                                      "srtm.shp")
        cls.expected_labels = [
            'sentinel1_des_vv_20151231', 'sentinel1_des_vh_20151231'
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
    def test_instance_s1(self):
        """Tests if the class sentinel_1 can be instanciate
        """
        from iota2.Sensors.Sentinel_1 import sentinel_1

        def prepare_sar_config():
            """prepare sentinel_1 configuration file
            """
            from configparser import SafeConfigParser
            parser = SafeConfigParser()
            parser.read(self.ref_sar_config)
            parser.set('Paths', 'Output', self.sar_features_path)
            parser.set('Paths', 'S1Images', self.sar_data)
            parser.set('Paths', 'SRTM', self.srtm)
            parser.set('Paths', 'GeoidFile', self.geoid)
            parser.set('Processing', 'ReferencesFolder', self.s2_large_scale)
            parser.set('Processing', 'RasterPattern', "STACK.tif")
            parser.set('Processing', 'OutputSpatialResolution', '10')
            parser.set('Processing', 'TilesShapefile', self.tiles_shape)
            parser.set('Processing', 'SRTMShapefile', self.srtm_shape)

            with open(self.ref_sar_config_test, "w+") as config_file:
                parser.write(config_file)

        args = {
            "tile_name": "T31TCJ",
            "target_proj": 2154,
            "all_tiles": "T31TCJ",
            "image_directory": self.ref_sar_config_test,
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
        prepare_sar_config()
        ensure_dir(
            os.path.join(self.test_working_directory, "features", "T31TCJ",
                         "tmp"))
        s1_sensor = sentinel_1(**args)
        (sar_features, _), features_labels = s1_sensor.get_features()
        sar_features.ExecuteAndWriteOutput()
        expected_output = sar_features.GetParameterString("out")
        self.assertTrue(os.path.exists(expected_output))
        self.assertTrue(features_labels == self.expected_labels)
