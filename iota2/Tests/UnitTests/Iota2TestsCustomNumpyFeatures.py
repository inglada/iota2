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

IOTA2DIR = os.environ.get("IOTA2DIR")

if not IOTA2DIR:
    raise Exception("IOTA2DIR environment variable must be set")
# if all tests pass, remove 'iota2_tests_directory' which contains all
# sub-directory tests
RM_IF_ALL_OK = True


class Iota2TestsCustomNumpyFeatures(unittest.TestCase):

    # before launching tests
    @classmethod
    def setUpClass(cls):
        # definition of local variables
        cls.group_test_name = "Iota2TestsCustomNumpyFeatures"
        cls.iota2_tests_directory = os.path.join(IOTA2DIR, "data",
                                                 cls.group_test_name)
        cls.all_tests_ok = []
        cls.config_test = os.path.join(IOTA2DIR, "data", "numpy_features",
                                       "config_plugins.cfg")
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
        self.test_working_directory = os.path.join(self.iota2_tests_directory,
                                                   test_name)
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
            result = getattr(self, "_outcomeForDoCleanups",
                             self._resultForDoCleanups)
        error = self.list2reason(result.errors)
        failure = self.list2reason(result.failures)
        ok = not error and not failure

        self.all_tests_ok.append(ok)
        if ok:
            shutil.rmtree(self.test_working_directory)

    # Tests definitions
    def test_check_custom_features_valid_inputs(self):
        """Test the behaviour of check custom features"""
        from config import Config
        from iota2.Common import ServiceConfigFile as SCF
        s2st_data = self.test_working_directory
        test_path = os.path.join(self.test_working_directory, "RUN")

        # Valid test
        config_path_test = os.path.join(self.test_working_directory,
                                        "Config_TEST_valid.cfg")

        shutil.copy(self.config_test, config_path_test)
        cfg_test = Config(open(config_path_test))
        cfg_test.chain.outputPath = test_path
        cfg_test.chain.listTile = "T31TCJ"
        cfg_test.chain.L8Path_old = "None"
        cfg_test.chain.L8Path = "None"
        cfg_test.chain.check_inputs = False
        cfg_test.chain.S2Path = s2st_data
        cfg_test.chain.userFeatPath = "None"
        cfg_test.chain.regionField = "region"
        cfg_test.argTrain.cropMix = False
        cfg_test.argTrain.samplesClassifMix = False
        cfg_test.argTrain.annualClassesExtractionSource = None
        cfg_test.GlobChain.useAdditionalFeatures = False
        cfg_test.GlobChain.writeOutputs = False
        cfg_test.Features.module = os.path.join(IOTA2DIR, "data",
                                                "numpy_features",
                                                "user_custom_function.py")

        # cfg_test.Features.module = self.module
        # cfg_test.Features.namefile = "user_custom_function"  # whithout .py ?
        cfg_test.Features.functions = "get_identity get_ndvi"
        cfg_test.save(open(config_path_test, "w"))
        cfg = SCF.serviceConfigFile(config_path_test)

        self.assertTrue(cfg.checkCustomFeature())

    def test_check_invalid_module_name(self):
        """Test the behaviour of check custom features"""
        from config import Config
        from iota2.Common import ServiceConfigFile as SCF
        s2st_data = self.test_working_directory
        test_path = os.path.join(self.test_working_directory, "RUN")

        # Invalid module name
        config_path_test = os.path.join(self.test_working_directory,
                                        "Config_TEST_invalidmodule.cfg")

        shutil.copy(self.config_test, config_path_test)
        cfg_test = Config(open(config_path_test))
        cfg_test.chain.outputPath = test_path
        cfg_test.chain.listTile = "T31TCJ"
        cfg_test.chain.L8Path_old = "None"
        cfg_test.chain.L8Path = "None"
        cfg_test.chain.check_inputs = False
        cfg_test.chain.S2Path = s2st_data
        cfg_test.chain.userFeatPath = "None"
        cfg_test.chain.regionField = "region"
        cfg_test.argTrain.cropMix = False
        cfg_test.argTrain.samplesClassifMix = False
        cfg_test.argTrain.annualClassesExtractionSource = None
        cfg_test.GlobChain.useAdditionalFeatures = False
        cfg_test.GlobChain.writeOutputs = False
        cfg_test.Features.module = os.path.join(IOTA2DIR, "data",
                                                "numpy_features", "dummy.py")

        cfg_test.Features.functions = "get_identity get_ndvi"
        cfg_test.save(open(config_path_test, "w"))
        cfg = SCF.serviceConfigFile(config_path_test)
        self.assertRaises(ValueError, cfg.checkCustomFeature)

    def test_check_invalid_function_name(self):
        """Test the behaviour of check custom features"""
        from config import Config
        from iota2.Common import ServiceConfigFile as SCF
        s2st_data = self.test_working_directory
        test_path = os.path.join(self.test_working_directory, "RUN")

        # Invalid function name
        config_path_test = os.path.join(self.test_working_directory,
                                        "Config_TEST_invalid_functions.cfg")

        shutil.copy(self.config_test, config_path_test)
        cfg_test = Config(open(config_path_test))
        cfg_test.chain.outputPath = test_path
        cfg_test.chain.listTile = "T31TCJ"
        cfg_test.chain.L8Path_old = "None"
        cfg_test.chain.L8Path = "None"
        cfg_test.chain.check_inputs = False
        cfg_test.chain.S2Path = s2st_data
        cfg_test.chain.userFeatPath = "None"
        cfg_test.chain.regionField = "region"
        cfg_test.argTrain.cropMix = False
        cfg_test.argTrain.samplesClassifMix = False
        cfg_test.argTrain.annualClassesExtractionSource = None
        cfg_test.GlobChain.useAdditionalFeatures = False
        cfg_test.GlobChain.writeOutputs = False
        cfg_test.Features.module = os.path.join(IOTA2DIR, "data",
                                                "numpy_features",
                                                "user_custom_function.py")

        cfg_test.Features.functions = "dummy_function"  # " get_ndvi"
        cfg_test.save(open(config_path_test, "w"))
        cfg = SCF.serviceConfigFile(config_path_test)
        self.assertRaises(AttributeError, cfg.checkCustomFeature)

    def test_apply_function_with_custom_features(self):
        """
        TEST : check the whole workflow
        """
        from functools import partial
        from iota2.Tests.UnitTests import TestsUtils
        import iota2.Tests.UnitTests.tests_utils.tests_utils_rasters as TUR
        from iota2.Common import rasterUtils as rasterU
        from iota2.Common.customNumpyFeatures import custom_numpy_features
        from iota2.Common import ServiceConfigFile as SCF
        from iota2.Common import IOTA2Directory
        from config import Config
        from iota2.Sensors.Sensors_container import sensors_container
        from iota2.Common.GenerateFeatures import generate_features
        TUR.generate_fake_s2_data(
            self.test_working_directory,
            "T31TCJ",
            ["20200101", "20200512", "20200702", "20201002"],
        )
        config_path_test = os.path.join(self.test_working_directory,
                                        "Config_TEST.cfg")

        shutil.copy(self.config_test, config_path_test)
        S2ST_data = self.test_working_directory
        testPath = os.path.join(self.test_working_directory, "RUN")
        cfg_test = Config(open(config_path_test))
        cfg_test.chain.outputPath = testPath
        cfg_test.chain.listTile = "T31TCJ"
        cfg_test.chain.L8Path_old = "None"
        cfg_test.chain.L8Path = "None"
        cfg_test.chain.check_inputs = False
        cfg_test.chain.S2Path = S2ST_data
        cfg_test.chain.userFeatPath = "None"
        cfg_test.chain.regionField = "region"
        cfg_test.argTrain.cropMix = False
        cfg_test.argTrain.samplesClassifMix = False
        cfg_test.argTrain.annualClassesExtractionSource = None
        cfg_test.GlobChain.useAdditionalFeatures = False
        cfg_test.GlobChain.writeOutputs = False
        cfg_test.Features.module = os.path.join(IOTA2DIR, "data",
                                                "numpy_features",
                                                "user_custom_function.py")
        # cfg_test.Features.codePath = self.code_path
        # cfg_test.Features.namefile = "user_custom_function"  # whithout .py ?
        cfg_test.Features.functions = "get_identity"  # " get_ndvi"
        cfg_test.save(open(config_path_test, "w"))
        cfg = SCF.serviceConfigFile(config_path_test)

        IOTA2Directory.generate_directories(self.test_working_directory,
                                            check_inputs=False)
        tile_name = "T31TCJ"
        working_dir = None
        sensors_param = SCF.iota2_parameters(
            config_path_test).get_sensors_parameters(tile_name)
        sensors = sensors_container(tile_name, working_dir,
                                    self.test_working_directory,
                                    **sensors_param)
        sensors.sensors_preprocess()
        list_sensors = sensors.get_enabled_sensors()
        sensor = list_sensors[0]
        ((time_s_app, app_dep), features_labels) = sensor.get_time_series()

        time_s_app.ExecuteAndWriteOutput()
        time_s = sensor.get_time_series_masks()
        time_s_app, app_dep, nbdates = time_s
        time_s_app.ExecuteAndWriteOutput()

        ((time_s_app, app_dep),
         features_labels) = sensor.get_time_series_gapfilling()
        # only one sensor for test
        # sensor_name, ((time_s_app, app_dep), features_labels) = time_s[0]
        # ( (time_s_app, app_dep), features_labels) = time_s
        ori_features, ori_feat_labels, ori_dep = generate_features(
            working_dir, "T31TCJ", False, self.test_working_directory,
            sensors_param)
        # Then apply function
        module_path = os.path.join(IOTA2DIR, "data", "numpy_features",
                                   "dhi.py")
        # list_functions = ["get_identity", "get_ndvi", "duplicate_ndvi"]
        list_functions = [
            "get_cumulative_productivity", "get_seasonal_variation"
        ]
        cust = custom_numpy_features(tile_name, self.test_working_directory,
                                     sensors_param, module_path,
                                     list_functions)
        function_partial = partial(cust.process)

        labels_features_name = ["NDVI_20200101", "NDVI_20200102"]
        new_features_path = os.path.join(self.test_working_directory,
                                         "DUMMY_test.tif")
        (test_array, new_labels, _, _, _,
         _) = rasterU.insert_external_function_to_pipeline(
             otb_pipeline=ori_features,
             labels=labels_features_name,
             working_dir=self.test_working_directory,
             function=function_partial,
             output_path=new_features_path,
             chunk_size_x=5,
             chunk_size_y=5,
             ram=128,
         )

        self.assertTrue(os.path.exists(new_features_path))
        self.assertTrue(new_labels is not None)
        # self.assertTrue(False)

    def test_compute_custom_features(self):
        """
        TEST : check the whole workflow
        """
        from functools import partial
        import numpy as np
        from iota2.Tests.UnitTests import TestsUtils
        import iota2.Tests.UnitTests.tests_utils.tests_utils_rasters as TUR
        from iota2.Common import rasterUtils as rasterU
        from iota2.Common.customNumpyFeatures import custom_numpy_features
        from iota2.Common.customNumpyFeatures import compute_custom_features
        from iota2.Common import ServiceConfigFile as SCF
        from iota2.Common import IOTA2Directory
        from config import Config
        from iota2.Sensors.Sensors_container import sensors_container
        from iota2.Common.GenerateFeatures import generate_features
        TUR.generate_fake_s2_data(
            self.test_working_directory,
            "T31TCJ",
            ["20200101", "20200512", "20200702", "20201002"],
        )
        config_path_test = os.path.join(self.test_working_directory,
                                        "Config_TEST.cfg")

        shutil.copy(self.config_test, config_path_test)
        S2ST_data = self.test_working_directory
        testPath = os.path.join(self.test_working_directory, "RUN")
        cfg_test = Config(open(config_path_test))
        cfg_test.chain.outputPath = testPath
        cfg_test.chain.listTile = "T31TCJ"
        cfg_test.chain.L8Path_old = "None"
        cfg_test.chain.L8Path = "None"
        cfg_test.chain.check_inputs = False
        cfg_test.chain.S2Path = S2ST_data
        cfg_test.chain.userFeatPath = "None"
        cfg_test.chain.regionField = "region"
        cfg_test.argTrain.cropMix = False
        cfg_test.argTrain.samplesClassifMix = False
        cfg_test.argTrain.annualClassesExtractionSource = None
        cfg_test.GlobChain.useAdditionalFeatures = False
        cfg_test.GlobChain.writeOutputs = False
        cfg_test.Features.module = os.path.join(IOTA2DIR, "data",
                                                "numpy_features",
                                                "user_custom_function.py")
        # cfg_test.Features.codePath = self.code_path
        # cfg_test.Features.namefile = "user_custom_function"  # whithout .py ?
        cfg_test.Features.functions = "get_identity"  # " get_ndvi"
        cfg_test.save(open(config_path_test, "w"))
        cfg = SCF.serviceConfigFile(config_path_test)

        IOTA2Directory.generate_directories(self.test_working_directory,
                                            check_inputs=False)
        tile_name = "T31TCJ"
        working_dir = None
        sensors_param = SCF.iota2_parameters(
            config_path_test).get_sensors_parameters(tile_name)
        sensors = sensors_container(tile_name, working_dir,
                                    self.test_working_directory,
                                    **sensors_param)
        sensors.sensors_preprocess()
        list_sensors = sensors.get_enabled_sensors()
        sensor = list_sensors[0]
        ((time_s_app, app_dep), features_labels) = sensor.get_time_series()

        time_s_app.ExecuteAndWriteOutput()
        time_s = sensor.get_time_series_masks()
        time_s_app, app_dep, nbdates = time_s
        time_s_app.ExecuteAndWriteOutput()

        ((time_s_app, app_dep),
         features_labels) = sensor.get_time_series_gapfilling()
        # only one sensor for test
        # sensor_name, ((time_s_app, app_dep), features_labels) = time_s[0]
        # ( (time_s_app, app_dep), features_labels) = time_s
        ori_features, ori_feat_labels, ori_dep = generate_features(
            working_dir, "T31TCJ", False, self.test_working_directory,
            sensors_param)
        # Then apply function
        module_path = os.path.join(IOTA2DIR, "data", "numpy_features",
                                   "dhi.py")
        # list_functions = ["get_identity", "get_ndvi", "duplicate_ndvi"]
        list_functions = [
            "get_cumulative_productivity", "get_seasonal_variation"
        ]
        cust = custom_numpy_features(tile_name, self.test_working_directory,
                                     sensors_param, module_path,
                                     list_functions)
        function_partial = partial(cust.process)

        labels_features_name = ["NDVI_20200101", "NDVI_20200102"]
        new_features_path = os.path.join(self.test_working_directory,
                                         "DUMMY_test.tif")

        crop_image, new_labels = compute_custom_features(
            "T31TCJ",
            self.test_working_directory,
            sensors_param,
            module_path,
            list_functions,
            ori_features,
            ori_feat_labels,
            self.test_working_directory,
            "user_fixed",
            0,
            1,
            chunk_size_x=5,
            chunk_size_y=5)
        # (test_array, new_labels, _, _, _,
        #  _) = rasterU.insert_external_function_to_pipeline(
        #      otb_pipeline=ori_features,
        #      labels=labels_features_name,
        #      working_dir=self.test_working_directory,
        #      function=function_partial,
        #      output_path=new_features_path,
        #      chunk_size_x=5,
        #      chunk_size_y=5,
        #      ram=128,
        #  )

        # self.assertTrue(np.isfinite(crop_image).all())
        self.assertTrue(new_labels is not None)
