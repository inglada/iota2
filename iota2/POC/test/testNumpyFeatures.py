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

# python -m unittest testNumpyFeatures

import os
import sys
import pickle
import shutil
import unittest
import numpy as np

# if all tests pass, remove 'iota2_tests_directory' which contains all
# sub-directory tests
RM_IF_ALL_OK = True


class Iota2TestNumpyFeatures(unittest.TestCase):

    # before launching tests
    @classmethod
    def setUpClass(cls):
        # definition of local variables
        cls.group_test_name = "iota_testNumpyFeatures"
        cls.iota2_tests_directory = os.path.join(
            os.path.split(__file__)[0], cls.group_test_name
        )
        cls.all_tests_ok = []

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
            result = getattr(
                self, "_outcomeForDoCleanups", self._resultForDoCleanups
            )
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
        from iota2.POC import rasterUtils as rasterU
        from iota2.Tests.UnitTests import TestsUtils
        from iota2.Common.OtbAppBank import CreateBandMathXApplication

        def custom_features(array):
            """
            """
            return array + array

        # First create some dummy data on disk
        dummy_raster_path = os.path.join(
            self.test_working_directory, "DUMMY.tif"
        )
        array_to_rasterize = TestsUtils.fun_array("iota2_binary")
        TestsUtils.arrayToRaster(array_to_rasterize, dummy_raster_path)

        # Get it in a otbApplication (simulating full iota2 features pipeline)
        band_math = CreateBandMathXApplication(
            {"il": [dummy_raster_path], "exp": "im1b1;im1b1"}
        )
        # Then apply function
        function_partial = partial(custom_features)

        labels_features_name = ["NDVI_20200101"]
        new_features_path = os.path.join(
            self.test_working_directory, "DUMMY_test.tif"
        )
        test_array, new_labels, _, _ = rasterU.apply_function(
            otb_pipeline=band_math,
            labels=labels_features_name,
            working_dir=self.test_working_directory,
            function=function_partial,
            output_path=new_features_path,
            chunck_size_x=5,
            chunck_size_y=5,
            ram=128,
        )
        # asserts

        # check array' shape consistency
        # concerning np.array there is different convention between OTB(GDAL?)
        # and rasterio
        # OTB : [row, cols, bands]
        # rasterio : [bands, row, cols]
        band_math.Execute()
        pipeline_shape = band_math.GetVectorImageAsNumpyArray("out").shape
        pipeline_shape = (
            pipeline_shape[2],
            pipeline_shape[0],
            pipeline_shape[1],
        )
        self.assertTrue(pipeline_shape == test_array.shape)

        # check if the input function is well applied
        pipeline_array = band_math.GetVectorImageAsNumpyArray("out")
        self.assertTrue(
            np.allclose(
                np.moveaxis(custom_features(pipeline_array), -1, 0), test_array
            )
        )

        # purposely not implemented
        self.assertTrue(new_labels is None)

    def test_machine_learning(self):
        """use sci-kit learn machine learning algorithm
        """
        from functools import partial
        from sklearn.ensemble import RandomForestClassifier
        from iota2.POC import rasterUtils as rasterU
        from iota2.Tests.UnitTests import TestsUtils
        from iota2.Common.OtbAppBank import CreateBandMathXApplication

        def do_predict(array, model, dtype="int32"):
            """
            """
            # ~ TODO : is there a more effective way to invoke model.predict ?
            def wrapper(*args, **kwargs):
                return model.predict([args[0]])

            predicted_array = np.apply_along_axis(
                func1d=wrapper, axis=-1, arr=array
            )
            return predicted_array.astype(dtype)

        # build data to learn RF model
        from sklearn.datasets import make_classification

        X, y = make_classification(
            n_samples=1000,
            n_features=2,
            n_informative=2,
            n_redundant=0,
            random_state=0,
            shuffle=True,
        )
        # learning
        clf = RandomForestClassifier(
            n_estimators=100, max_depth=2, random_state=0
        )
        clf.fit(X, y)

        # create some data on disk in order to predict them
        dummy_raster_path = os.path.join(
            self.test_working_directory, "DUMMY.tif"
        )
        array_to_rasterize = TestsUtils.fun_array("iota2_binary")
        TestsUtils.arrayToRaster(array_to_rasterize, dummy_raster_path)

        # Get it in a otbApplication (simulating full iota2 features pipeline)
        band_math = CreateBandMathXApplication(
            {"il": [dummy_raster_path], "exp": "im1b1;im1b1"}
        )
        # prediction
        function_partial = partial(do_predict, model=clf)
        prediction_path = os.path.join(
            self.test_working_directory, "Classif_test.tif"
        )
        test_array, new_labels, _, _ = rasterU.apply_function(
            otb_pipeline=band_math,
            labels=[""],
            working_dir=self.test_working_directory,
            function=function_partial,
            output_path=prediction_path,
            chunck_size_x=5,
            chunck_size_y=5,
            ram=128,
        )
        self.assertTrue(os.path.exists(prediction_path))
        self.assertTrue(test_array.shape == (1, 16, 86))
