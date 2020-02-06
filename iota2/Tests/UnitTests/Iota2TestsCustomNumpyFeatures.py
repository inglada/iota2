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

# python -m unittest Iota2TestsCustomNumpyFeatures

import os
import sys
import shutil
import unittest
import numpy as np

IOTA2DIR = os.environ.get("IOTA2DIR")

if not IOTA2DIR:
    raise Exception("IOTA2DIR environment variable must be set")
# if all tests pass, remove 'iota2_tests_directory' which contains all
# sub-directory tests
RM_IF_ALL_OK = True
IOTA2_SCRIPTS = IOTA2DIR + "/iota2"
sys.path.append(IOTA2_SCRIPTS)


class Iota2TestsCustomNumpyFeatures(unittest.TestCase):

    # before launching tests
    @classmethod
    def setUpClass(cls):
        # definition of local variables
        cls.group_test_name = "Iota2TestsCustomNumpyFeatures"
        cls.iota2_tests_directory = os.path.join(
            os.path.split(__file__)[0], cls.group_test_name
        )
        cls.all_tests_ok = []
        cls.config_test = os.path.join(
            IOTA2DIR, "data", "numpy_features", "config_plugins.cfg"
        )
        cls.code_path = os.path.join(IOTA2DIR, "data", "numpy_features")
        # Tests directory
        cls.test_working_directory = None
        if os.path.exists(cls.iota2_tests_directory):
            shutil.rmtree(cls.iota2_tests_directory)
        os.mkdir(cls.iota2_tests_directory)

    # after launching all tests
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
        # self.test_working_directory is the diretory dedicated to each tests
        # it changes for each tests

        test_name = self.id().split(".")[-1]
        self.test_working_directory = os.path.join(
            self.iota2_tests_directory, test_name
        )
        if os.path.exists(self.test_working_directory):
            shutil.rmtree(self.test_working_directory)
        os.mkdir(self.test_working_directory)

    def list2reason(self, exc_list):
        if exc_list and exc_list[-1][0] is self:
            return exc_list[-1][1]

    # after launching a test, remove test's data if test succeed
    def tearDown(self):
        if sys.version_info > (3, 4, 0):
            result = self.defaultTestResult()
            self._feedErrorsToResult(result, self._outcome.errors)
        else:
            result = getattr(self, "_outcomeForDoCleanups", self._resultForDoCleanups)
        error = self.list2reason(result.errors)
        failure = self.list2reason(result.failures)
        ok = not error and not failure

        self.all_tests_ok.append(ok)
        if ok:
            shutil.rmtree(self.test_working_directory)

    # Tests definitions
    def test_apply_function(self):
        """
        TEST : check the whole workflow
        """
        from functools import partial
        from iota2.Tests.UnitTests import TestsUtils
        from iota2.Common import rasterUtils as rasterU
        from iota2.Common.customNumpyFeatures import customNumpyFeatures
        from iota2.Common import ServiceConfigFile as SCF
        from iota2.Common import IOTA2Directory
        from config import Config
        from iota2.Sensors.Sensors_container import Sensors_container

        TestsUtils.generate_fake_s2_data(
            self.test_working_directory,
            "T31TCJ",
            ["20200101", "20200512", "20200702", "20201002"],
        )
        # TestsUtils.fun_array("iota2_binary")
        # TestsUtils.arrayToRaster(array_to_rasterize, dummy_raster_path)
        # self.config_test = ("./config_plugins.cfg")
        config_path_test = os.path.join(self.test_working_directory, "Config_TEST.cfg")

        shutil.copy(self.config_test, config_path_test)
        S2ST_data = self.test_working_directory
        testPath = os.path.join(self.test_working_directory, "RUN")
        cfg_test = Config(open(config_path_test))
        cfg_test.chain.outputPath = testPath
        cfg_test.chain.listTile = "T31TCJ"
        cfg_test.chain.L8Path_old = "None"
        cfg_test.chain.L8Path = "None"
        cfg_test.chain.S2Path = S2ST_data
        # cfg_test.chain.S2_S2C_Path = S2ST_data
        cfg_test.chain.userFeatPath = "None"
        cfg_test.chain.regionField = "region"
        cfg_test.argTrain.cropMix = False
        cfg_test.argTrain.samplesClassifMix = False
        cfg_test.argTrain.annualClassesExtractionSource = None
        cfg_test.GlobChain.useAdditionalFeatures = False
        cfg_test.GlobChain.writeOutputs = False
        cfg_test.Features.codePath = self.code_path
        cfg_test.Features.namefile = "user_custom_function"  # whithout .py ?
        cfg_test.Features.functions = "get_identity get_ndvi"
        cfg_test.save(open(config_path_test, "w"))
        cfg = SCF.serviceConfigFile(config_path_test)
        IOTA2Directory.GenerateDirectories(config_path_test)
        tile_name = "T31TCJ"
        working_dir = None
        sensors = Sensors_container(config_path_test, tile_name, working_dir)
        sensors.sensors_preprocess()
        list_sensors = sensors.get_enabled_sensors()
        sensor = list_sensors[0]
        ((time_s_app, app_dep), features_labels) = sensor.get_time_series()

        time_s_app.ExecuteAndWriteOutput()
        time_s = sensor.get_time_series_masks()
        time_s_app, app_dep, nbdates = time_s
        time_s_app.ExecuteAndWriteOutput()

        ((time_s_app, app_dep), features_labels) = sensor.get_time_series_gapFilling()
        # only one sensor for test
        # sensor_name, ((time_s_app, app_dep), features_labels) = time_s[0]
        # ( (time_s_app, app_dep), features_labels) = time_s

        # Then apply function
        cust = customNumpyFeatures(config_path_test)
        function_partial = partial(cust.process)

        labels_features_name = ["NDVI_20200101", "NDVI_20200102"]
        new_features_path = os.path.join(self.test_working_directory, "DUMMY_test.tif")
        test_array, new_labels, _, _, _ = rasterU.apply_function(
            otb_pipeline=time_s_app,
            labels=labels_features_name,
            working_dir=self.test_working_directory,
            function=function_partial,
            output_path=new_features_path,
            chunck_size_x=5,
            chunck_size_y=5,
            ram=128,
        )
        time_s_app.ExecuteAndWriteOutput()
        # time_s_app.Execute()
        pipeline_shape = time_s_app.GetVectorImageAsNumpyArray("out").shape
        pipeline_shape = (pipeline_shape[2], pipeline_shape[0], pipeline_shape[1])
        # self.assertTrue(pipeline_shape == test_array.shape)

        # check if the input function is well apply
        pipeline_array = time_s_app.GetVectorImageAsNumpyArray("out")
        # self.assertTrue(
        #     np.allclose(np.moveaxis(cust.process(pipeline_array), -1, 0), test_array)
        # )

        # purposely not implemented
        self.assertTrue(new_labels is None)
        # self.assertTrue(False)
