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
import shutil
import unittest
import numpy as np

# if all tests pass, remove 'iota2_tests_directory' which contains all
# sub-directory tests
RM_IF_ALL_OK = True
IOTA2DIR = os.environ.get('IOTA2DIR')


class Iota2TestsNumpyWorkflow(unittest.TestCase):

    # before launching tests
    @classmethod
    def setUpClass(cls):
        # definition of local variables
        cls.group_test_name = "iota_testNumpyFeatures"
        cls.iota2_tests_directory = os.path.join(IOTA2DIR, "data", cls.group_test_name)
        cls.features_dataBase = os.path.join(IOTA2DIR,
                                             "data",
                                             "reduced_output_samples.sqlite")
        cls.all_tests_ok = []

        # Tests directory
        cls.test_working_directory = None
        if os.path.exists(cls.iota2_tests_directory):
            shutil.rmtree(cls.iota2_tests_directory)
        os.mkdir(cls.iota2_tests_directory)

        cls.ref_cross_validation = ["Best Parameters:"]
        cls.ref_scale = np.array([2.26379081, 1.88323221, 0.7982067, 0.60191847, 0.39085819, 0.19637141,
                                  2.26379081, 1.88323221, 0.7982067, 0.60191847, 0.39085819, 0.19637141,
                                  2.2770817, 1.88356701, 0.82879011, 0.52570417, 0.37130111, 0.18286401,
                                  2.3113216, 1.82009071, 0.92872819, 0.41618358, 0.32543167, 0.25472347,
                                  2.42691728, 1.72997482, 0.84062143, 0.38731198, 0.25782248, 0.24453248,
                                  2.45312165, 1.75901026, 0.72865975, 0.3548426, 0.26213068, 0.17726742,
                                  2.47527844, 1.73895914, 0.65199415, 0.46599839, 0.2526496, 0.14894581,
                                  2.47947365, 1.72583852, 0.66522993, 0.46912169, 0.25860929, 0.15443434,
                                  2.46829782, 1.72538802, 0.68779437, 0.49106096, 0.26733444, 0.16386239,
                                  2.45930121, 1.72657813, 0.69013682, 0.50729237, 0.28364723, 0.17760912,
                                  2.48103485, 1.60658697, 0.8078123, 0.46817622, 0.42947051, 0.26274128,
                                  2.42499156, 1.72439242, 0.76069492, 0.49849193, 0.34698139, 0.24679596,
                                  2.38322473, 1.79774719, 0.71809114, 0.54897445, 0.29146343, 0.220741,
                                  2.35705107, 1.84537019, 0.68537724, 0.57784401, 0.26225397, 0.1968307,
                                  2.34456355, 1.85809104, 0.69565658, 0.5909745, 0.24434703, 0.18665792,
                                  2.27672512, 1.91074124, 0.76340315, 0.59972296, 0.24893347, 0.20510927,
                                  2.28776289, 1.91855255, 0.72640125, 0.57731692, 0.23880154, 0.21419432,
                                  2.28240157, 1.9095699, 0.74639484, 0.60961737, 0.23549034, 0.2126695,
                                  2.34223592, 1.84281525, 0.80507131, 0.45320055, 0.25136176, 0.24141408,
                                  2.33568571, 1.84493349, 0.85237784, 0.38862779, 0.28560659, 0.2084152,
                                  2.30312608, 1.85327544, 0.91991632, 0.37270513, 0.30898565, 0.2056479,
                                  2.24433067, 1.86446705, 1.01841375, 0.39264294, 0.32578043, 0.20842152,
                                  2.16757937, 1.89643401, 1.10610101, 0.41818918, 0.34620732, 0.19259937])
        cls.ref_var = np.array([5.12474884, 3.54656357, 0.63713394, 0.36230584, 0.15277012, 0.03856173,
                                5.12474884, 3.54656357, 0.63713394, 0.36230584, 0.15277012, 0.03856173,
                                5.18510106, 3.54782468, 0.68689304, 0.27636487, 0.13786452, 0.03343925,
                                5.34220754, 3.3127302, 0.86253605, 0.17320877, 0.10590577, 0.06488405,
                                5.88992751, 2.99281288, 0.70664438, 0.15001057, 0.06647243, 0.05979613,
                                6.01780582, 3.0941171, 0.53094504, 0.12591327, 0.06871249, 0.03142374,
                                6.12700335, 3.02397889, 0.42509638, 0.2171545, 0.06383182, 0.02218485,
                                6.14778957, 2.97851858, 0.44253086, 0.22007516, 0.06687876, 0.02384996,
                                6.09249414, 2.97696381, 0.47306109, 0.24114087, 0.0714677, 0.02685088,
                                6.04816243, 2.98107205, 0.47628883, 0.25734555, 0.08045575, 0.031545,
                                6.15553393, 2.58112168, 0.65256071, 0.21918897, 0.18444492, 0.06903298,
                                5.88058406, 2.97352921, 0.57865676, 0.24849421, 0.12039608, 0.06090825,
                                5.67976011, 3.23189496, 0.51565489, 0.30137295, 0.08495093, 0.04872659,
                                5.55568973, 3.40539114, 0.46974196, 0.3339037, 0.06877714, 0.03874233,
                                5.49697822, 3.4525023, 0.48393808, 0.34925086, 0.05970547, 0.03484118,
                                5.18347728, 3.65093209, 0.58278437, 0.35966763, 0.06196787, 0.04206981,
                                5.23385904, 3.6808439, 0.52765877, 0.33329483, 0.05702617, 0.04587921,
                                5.20935694, 3.64645719, 0.55710525, 0.37163334, 0.0554557, 0.04522832,
                                5.48606908, 3.39596805, 0.64813982, 0.20539074, 0.06318273, 0.05828076,
                                5.45542772, 3.40377958, 0.72654798, 0.15103156, 0.08157112, 0.0434369,
                                5.30438975, 3.43462987, 0.84624604, 0.13890911, 0.09547213, 0.04229106,
                                5.03702016, 3.47623737, 1.03716656, 0.15416848, 0.10613289, 0.04343953,
                                4.69840032, 3.59646196, 1.22345944, 0.17488219, 0.11985951, 0.03709452])
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
        from iota2.Common import rasterUtils as rasterU
        from iota2.Tests.UnitTests import TestsUtils
        from iota2.Common.OtbAppBank import CreateBandMathXApplication

        def custom_features(array):
            """
            """
            return array + array

        # First create some dummy data on disk
        dummy_raster_path = os.path.join(self.test_working_directory,
                                         "DUMMY.tif")
        array_to_rasterize = TestsUtils.fun_array("iota2_binary")
        TestsUtils.arrayToRaster(array_to_rasterize, dummy_raster_path)

        # Get it in a otbApplication (simulating full iota2 features pipeline)
        band_math = CreateBandMathXApplication({"il": [dummy_raster_path],
                                                "exp": "im1b1;im1b1"})
        # Then apply function
        function_partial = partial(custom_features)

        labels_features_name = ["NDVI_20200101"]

        new_features_path = os.path.join(self.test_working_directory, "DUMMY_test.tif")
        test_array, new_labels, _, _, _ = rasterU.apply_function(otb_pipeline=band_math,
                                                                 labels=labels_features_name,
                                                                 working_dir=self.test_working_directory,
                                                                 function=function_partial,
                                                                 output_path=new_features_path,
                                                                 chunck_size_x=5,
                                                                 chunck_size_y=5,
                                                                 ram=128)
        # asserts

        # check array' shape consistency
        # concerning np.array there is different convention between OTB(GDAL?)
        # and rasterio
        # OTB : [row, cols, bands]
        # rasterio : [bands, row, cols]
        band_math.Execute()
        pipeline_shape = band_math.GetVectorImageAsNumpyArray("out").shape
        pipeline_shape = (pipeline_shape[2],
                          pipeline_shape[0],
                          pipeline_shape[1])
        self.assertTrue(pipeline_shape == test_array.shape)

        # check if the input function is well applied
        pipeline_array = band_math.GetVectorImageAsNumpyArray("out")
        self.assertTrue(np.allclose(np.moveaxis(custom_features(pipeline_array), -1, 0),
                                    test_array))

        # purposely not implemented
        self.assertTrue(new_labels is None)

    def test_sk_cross_validation(self):
        """test cross validation
        """
        import shutil
        from iota2.Learning.TrainSkLearn import sk_learn
        from iota2.Common.FileUtils import FileSearch_AND

        _, db_file_name = os.path.split(self.features_dataBase)

        features_db_test = os.path.join(self.test_working_directory,
                                        db_file_name)
        shutil.copy(self.features_dataBase, features_db_test)

        test_model_path = os.path.join(self.test_working_directory,
                                       "test_model.rf")
        sk_learn(dataset_path=features_db_test,
                 features_labels=["reduced_{}".format(cpt) for cpt in range(138)],
                 model_path=test_model_path,
                 data_field="code",
                 sk_model_name="RandomForestClassifier",
                 cv_parameters={'n_estimators': [50, 100]},
                 min_samples_split=25)

        # asserts
        self.assertTrue(os.path.exists(test_model_path))
        test_cross_val_results = FileSearch_AND(self.test_working_directory,
                                                True,
                                                "cross_val_param.cv")[0]
        with open(test_cross_val_results, "r") as cross_val_f:
            test_cross_val = [line.rstrip() for line in cross_val_f]

        test_cv_val = all([val_to_find in test_cross_val for val_to_find in self.ref_cross_validation])
        self.assertTrue(test_cv_val, msg="cross validation failed")

    def test_sk_standardization(self):
        """test standardization
        """
        import shutil
        import pickle
        from iota2.Learning.TrainSkLearn import sk_learn

        _, db_file_name = os.path.split(self.features_dataBase)

        features_db_test = os.path.join(self.test_working_directory,
                                        db_file_name)
        shutil.copy(self.features_dataBase, features_db_test)

        test_model_path = os.path.join(self.test_working_directory,
                                       "test_model.rf")
        sk_learn(dataset_path=features_db_test,
                 features_labels=["reduced_{}".format(cpt) for cpt in range(138)],
                 model_path=test_model_path,
                 data_field="code",
                 sk_model_name="RandomForestClassifier",
                 apply_standardization=True)

        self.assertTrue(os.path.exists(test_model_path))

        with open(test_model_path, 'rb') as model_obj:
            model, scaler = pickle.load(model_obj)

        self.assertTrue(np.allclose(self.ref_scale, scaler.scale_))
        self.assertTrue(np.allclose(self.ref_var, scaler.var_))

    def test_machine_learning(self):
        """use sci-kit learn machine learning algorithm
        """
        from functools import partial
        from sklearn.ensemble import RandomForestClassifier
        from iota2.Common import rasterUtils as rasterU
        from iota2.Tests.UnitTests import TestsUtils
        from iota2.Common.OtbAppBank import CreateBandMathXApplication

        def do_predict(array, model, dtype="int32"):
            """
            """
            def wrapper(*args, **kwargs):
                return model.predict([args[0]])

            predicted_array = np.apply_along_axis(
                func1d=wrapper, axis=-1, arr=array
            )
            return predicted_array.astype(dtype)

        # build data to learn RF model
        from sklearn.datasets import make_classification

        X, y = make_classification(n_samples=1000,
                                   n_features=2,
                                   n_informative=2,
                                   n_redundant=0,
                                   random_state=0,
                                   shuffle=True)
        # learning
        clf = RandomForestClassifier(n_estimators=100,
                                     max_depth=2,
                                     random_state=0)
        clf.fit(X, y)

        # create some data on disk in order to predict them
        dummy_raster_path = os.path.join(self.test_working_directory,
                                         "DUMMY.tif")
        array_to_rasterize = TestsUtils.fun_array("iota2_binary")
        TestsUtils.arrayToRaster(array_to_rasterize, dummy_raster_path)

        # Get it in a otbApplication (simulating full iota2 features pipeline)
        band_math = CreateBandMathXApplication({"il": [dummy_raster_path],
                                                "exp": "im1b1;im1b1"})
        # prediction
        function_partial = partial(do_predict, model=clf)
        prediction_path = os.path.join(self.test_working_directory,
                                       "Classif_test.tif")
        test_array, new_labels, _, _, _ = rasterU.apply_function(otb_pipeline=band_math,
                                                                 labels=[""],
                                                                 working_dir=self.test_working_directory,
                                                                 function=function_partial,
                                                                 output_path=prediction_path,
                                                                 chunck_size_x=5,
                                                                 chunck_size_y=5,
                                                                 ram=128)
        self.assertTrue(os.path.exists(prediction_path))
        self.assertTrue(test_array.shape == (1, 16, 86))
