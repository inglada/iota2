# !/usr/bin/python
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

# python -m unittest ClassificationsTests

import os
import sys
import shutil
import unittest
import numpy as np
import iota2.Tests.UnitTests.tests_utils.tests_utils_rasters as TUR
from TestsUtils import rasterToArray

IOTA2DIR = os.environ.get('IOTA2DIR')

if not IOTA2DIR:
    raise Exception("IOTA2DIR environment variable must be set")

# if all tests pass, remove 'iota2_tests_directory' which contains all
# sub-directory tests
RM_IF_ALL_OK = True


class iota_testClassifications(unittest.TestCase):
    # before launching tests
    @classmethod
    def setUpClass(cls):
        # definition of local variables
        cls.group_test_name = "iota_testClassifications"
        cls.iota2_tests_directory = os.path.join(IOTA2DIR, "data",
                                                 cls.group_test_name)
        cls.all_tests_ok = []

        # input data
        cls.config_test = os.path.join(
            IOTA2DIR, "config", "Config_4Tuiles_Multi_FUS_Confidence.cfg")

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
            result = getattr(self, '_outcomeForDoCleanups',
                             self._resultForDoCleanups)
        error = self.list2reason(result.errors)
        failure = self.list2reason(result.failures)
        ok = not (error or failure)

        self.all_tests_ok.append(ok)
        if ok:
            shutil.rmtree(self.test_working_directory)

    # Tests definitions
    def test_reorder_proba_map(self):
        """
        TEST : ImageClassifier.iota2Classification.reorder_proba_map()
        """
        from iota2.Common import ServiceConfigFile as SCF
        from iota2.Classification.ImageClassifier import iota2Classification

        # prepare inputs
        probamap_arr = [
            np.array([[268, 528, 131], [514, 299, 252], [725, 427, 731]]),
            np.array([[119, 241, 543], [974, 629, 626], [3, 37, 819]]),
            np.array([[409, 534, 710], [916, 43, 993], [207, 68, 282]]),
            np.array([[820, 169, 423], [710, 626, 525], [377, 777, 461]]),
            np.array([[475, 116, 395], [838, 297, 262], [650, 828, 595]]),
            np.array([[0, 0, 0], [0, 0, 0], [0, 0, 0]])
        ]
        probamap_path = os.path.join(self.test_working_directory,
                                     "PROBAMAP_T31TCJ_model_1_seed_0.tif")
        TUR.array_to_raster(probamap_arr, probamap_path)

        cfg = SCF.serviceConfigFile(self.config_test)
        fake_model = "model_1_seed_0.txt"
        fake_tile = "T31TCJ"
        fake_output_directory = "fake_output_directory"
        classifier = iota2Classification(
            features_stack=None,
            classifier_type=None,
            model=fake_model,
            tile=fake_tile,
            output_directory=fake_output_directory,
            models_class=None)
        class_model = [1, 2, 3, 4, 6]
        all_class = [1, 2, 3, 4, 5, 6]
        proba_map_path_out = os.path.join(
            self.test_working_directory,
            "PROBAMAP_T31TCJ_model_1_seed_0_ORDERED.tif")
        classifier.reorder_proba_map(probamap_path, proba_map_path_out,
                                     class_model, all_class)

        # assert
        probamap_arr_ref = [
            np.array([[268, 528, 131], [514, 299, 252], [725, 427, 731]]),
            np.array([[119, 241, 543], [974, 629, 626], [3, 37, 819]]),
            np.array([[409, 534, 710], [916, 43, 993], [207, 68, 282]]),
            np.array([[820, 169, 423], [710, 626, 525], [377, 777, 461]]),
            np.array([[0, 0, 0], [0, 0, 0], [0, 0, 0]]),
            np.array([[475, 116, 395], [838, 297, 262], [650, 828, 595]])
        ]
        reordered_test_arr = rasterToArray(proba_map_path_out)
        self.assertEqual(len(all_class), len(reordered_test_arr))
        is_bands_ok = []
        for band in range(len(reordered_test_arr)):
            band_ref = probamap_arr_ref[band]
            band_test = reordered_test_arr[band]
            for ref_val, test_val in zip(band_ref.flat, band_test.flat):
                is_bands_ok.append(int(ref_val) == int(test_val))
        self.assertTrue(all(is_bands_ok),
                        msg="reordering probability maps failed")
