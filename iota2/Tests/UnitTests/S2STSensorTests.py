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

import os
import sys
import shutil
import unittest
import numpy as np

IOTA2DIR = os.environ.get('IOTA2DIR')
RM_IF_ALL_OK = True

iota2_script = os.path.join(IOTA2DIR, "iota2")
sys.path.append(iota2_script)


class iota_testS2STSensor(unittest.TestCase):
    #before launching tests
    @classmethod
    def setUpClass(self):

        # definition of local variables
        self.group_test_name = "iota_testS2STSensor"
        self.iota2_tests_directory = os.path.join(IOTA2DIR, "data",
                                                  self.group_test_name)
        self.all_tests_ok = []
        self.test_working_directory = None
        if os.path.exists(self.iota2_tests_directory):
            shutil.rmtree(self.iota2_tests_directory)
        os.mkdir(self.iota2_tests_directory)

        self.config_test = os.path.join(
            IOTA2DIR, "config", "Config_4Tuiles_Multi_FUS_Confidence.cfg")

        # generate fake input data
        self.MTD_files = [
            os.path.join(IOTA2DIR, "data", "MTD_MSIL2A_20190506.xml"),
            os.path.join(IOTA2DIR, "data", "MTD_MSIL2A_20190501.xml")
        ]

    #after launching tests
    @classmethod
    def tearDownClass(self):
        print("{} ended".format(self.group_test_name))
        if RM_IF_ALL_OK and all(self.all_tests_ok):
            shutil.rmtree(self.iota2_tests_directory)

    #before launching a test
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

        #Create test data

    def list2reason(self, exc_list):
        if exc_list and exc_list[-1][0] is self:
            return exc_list[-1][1]

    #after launching a test, remove test's data if test succeed
    def tearDown(self):
        if sys.version_info > (3, 4, 0):
            result = self.defaultTestResult()
            self._feedErrorsToResult(result, self._outcome.errors)
        else:
            result = getattr(self, '_outcomeForDoCleanups',
                             self._resultForDoCleanups)
        error = self.list2reason(result.errors)
        failure = self.list2reason(result.failures)
        ok = not error and not failure

        self.all_tests_ok.append(ok)
        if ok:
            shutil.rmtree(self.test_working_directory)

    #Tests definitions
    def test_Sensor(self):
        """
        """
        from config import Config
        from iota2.Common import IOTA2Directory
        from iota2.Common import ServiceConfigFile as SCF

        from iota2.Sensors.Sensors_container import sensors_container
        from iota2.Common.FileUtils import FileSearch_AND
        from iota2.Tests.UnitTests.TestsUtils import rasterToArray
        from iota2.Tests.UnitTests.TestsUtils import compute_brightness_from_vector
        import iota2.Tests.UnitTests.tests_utils.tests_utils_rasters as TUR
        # s2 sen2cor data
        TUR.generate_fake_s2_s2c_data(self.test_working_directory,
                                      "T31TCJ",
                                      self.MTD_files,
                                      res=10)

        # config file
        config_path_test = os.path.join(self.test_working_directory,
                                        "Config_TEST.cfg")
        shutil.copy(self.config_test, config_path_test)

        s2st_data = self.test_working_directory
        test_path = os.path.join(self.test_working_directory, "RUN")
        cfg_test = Config(open(config_path_test))
        cfg_test.chain.outputPath = test_path
        cfg_test.chain.listTile = "T31TCJ"
        cfg_test.chain.L8Path_old = "None"
        cfg_test.chain.L8Path = "None"
        cfg_test.chain.S2Path = "None"
        cfg_test.chain.S2_S2C_Path = s2st_data
        cfg_test.chain.userFeatPath = "None"
        cfg_test.chain.regionField = 'region'
        cfg_test.argTrain.cropMix = False
        cfg_test.argTrain.samplesClassifMix = False
        cfg_test.argTrain.annualClassesExtractionSource = None
        cfg_test.GlobChain.useAdditionalFeatures = False
        cfg_test.GlobChain.writeOutputs = False
        cfg_test.save(open(config_path_test, 'w'))

        IOTA2Directory.generate_directories(test_path, check_inputs=False)

        # Launch test
        tile_name = "T31TCJ"
        working_dir = None
        iota2_dico = SCF.iota2_parameters(
            config_path_test).get_sensors_parameters(tile_name)
        sensors = sensors_container(tile_name, working_dir,
                                    self.test_working_directory, **iota2_dico)
        sensors.sensors_preprocess()

        # produce the time series
        time_s = sensors.get_sensors_time_series()
        for sensor_name, ((time_s_app, app_dep), features_labels) in time_s:
            time_s_app.ExecuteAndWriteOutput()
        # produce the time series gapFilled
        time_s_g = sensors.get_sensors_time_series_gapfilling()
        for sensor_name, ((time_s_g_app, app_dep),
                          features_labels) in time_s_g:
            time_s_g_app.ExecuteAndWriteOutput()
        # produce features
        features = sensors.get_sensors_features()
        for sensor_name, ((features_app, app_dep),
                          features_labels) in features:
            features_app.ExecuteAndWriteOutput()

        feature_array = rasterToArray(
            FileSearch_AND(os.path.join(test_path), True, "_Features.tif")[0])
        data_value, brightness_value = feature_array[:, 0, 2][0:-1], int(
            feature_array[:, 0, 2][-1])
        theorical_brightness = int(compute_brightness_from_vector(data_value))
        self.assertEqual(theorical_brightness, brightness_value)
