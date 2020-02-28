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
import os
import sys
import unittest
import shutil
from iota2.Common import FileUtils as fu
RM_IF_ALL_OK = True
IOTA2DIR = os.environ.get('IOTA2DIR')
IOTA2_DATATEST = os.path.join(os.environ.get('IOTA2DIR'), "data")


class iota_testGenerateShapeTile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Test variables
        cls.group_test_name = "iota_Iota2Envelope"
        cls.all_tests_ok = []
        cls.iota2_tests_directory = os.path.join(IOTA2_DATATEST,
                                                 cls.group_test_name)
        cls.tiles = ['D0005H0002']  # , 'D0005H0003']
        cls.path_tiles_feat = IOTA2_DATATEST + "/references/features/"
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

    def test_generate_shape_tile(self):
        from iota2.Sampling import TileEnvelope as env

        # Test de création des enveloppes
        features_path = os.path.join(self.iota2_tests_directory, "features")

        masks_references = '../../../data/references/features'
        if os.path.exists(features_path):
            shutil.rmtree(features_path)

        shutil.copytree(masks_references, features_path)

        # Test de création des enveloppes
        # Launch function
        env.generate_shape_tile(self.tiles, None, self.iota2_tests_directory,
                                2154)

        # For each tile test if the shapefile is ok
        for i in self.tiles:
            # generate filename
            reference_shape_file = (IOTA2_DATATEST +
                                    "/references/GenerateShapeTile/" + i +
                                    ".shp")
            shape_file = self.iota2_tests_directory + "/envelope/" + i + ".shp"
            service_compare_vector_file = fu.serviceCompareVectorFile()
            # Launch shapefile comparison
            self.assertTrue(
                service_compare_vector_file.testSameShapefiles(
                    reference_shape_file, shape_file))
        shutil.rmtree(features_path)
