# !/usr/bin/env python3
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
"""Test vector split"""
# python -m unittest Iota2TestsVectorSplits
import os
import sys
import shutil
import unittest

# if all tests pass, remove 'iota2_tests_directory' which contains all
# sub-directory tests
RM_IF_ALL_OK = True
IOTA2DIR = os.environ.get('IOTA2DIR')


class iota_test_vector_splits(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # We create the test folder
        cls.group_test_name = "iota2_Iota2TestsVectorSplits"
        cls.iota2_tests_directory = os.path.join(IOTA2DIR, "data",
                                                 cls.group_test_name)
        cls.all_tests_ok = []
        references_directory = os.path.join(IOTA2DIR, "data", "references")

        # attributes
        cls.data_field = "CODE"
        cls.region_field = "region"
        cls.ratio = 0.5
        cls.seeds = 2
        cls.epsg = 2154
        cls.new_regions_shapes = [
            os.path.join(cls.iota2_tests_directory, "formattingVectors",
                         "T31TCJ.shp")
        ]
        cls.data_app_val_dir = os.path.join(cls.iota2_tests_directory,
                                            "dataAppVal")
        # References
        output_ref_path = os.path.join(IOTA2DIR, "data", "references",
                                       "vector_splits", "Output",
                                       "splitInSubSets")
        cls.ref_split_dbf = os.path.join(output_ref_path, "T31TCJ.dbf")
        cls.ref_split_shp = os.path.join(output_ref_path, "T31TCJ.shp")
        cls.ref_split_shx = os.path.join(output_ref_path, "T31TCJ.shx")
        cls.ref_split_prj = os.path.join(output_ref_path, "T31TCJ.prj")

        # Ouput files
        cls.emvs = os.path.join(cls.iota2_tests_directory, "T31TCJ.shp")
        cls.out_split_dbf = os.path.join(cls.iota2_tests_directory,
                                         "formattingVectors", "T31TCJ.dbf")
        cls.out_split_shp = os.path.join(cls.iota2_tests_directory,
                                         "formattingVectors", "T31TCJ.shp")
        cls.out_split_shx = os.path.join(cls.iota2_tests_directory,
                                         "formattingVectors", "T31TCJ.shx")
        cls.out_split_prj = os.path.join(cls.iota2_tests_directory,
                                         "formattingVectors", "T31TCJ.prj")
        # Tests directory
        cls.test_working_directory = None
        if os.path.exists(cls.iota2_tests_directory):
            shutil.rmtree(cls.iota2_tests_directory)
        # os.mkdir(cls.iota2_tests_directory)
        # copy necessary directory from reference
        shutil.copytree(
            os.path.join(references_directory, "vector_splits", "Input"),
            cls.iota2_tests_directory)

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
        ok = not (error or failure)

        self.all_tests_ok.append(ok)
        if ok:
            shutil.rmtree(self.test_working_directory)

    def test_vector_splits(self):
        from iota2.Sampling import SplitInSubSets as VS
        from iota2.Common import FileUtils as fu
        from iota2.Tests.UnitTests import TestsUtils
        # We execute the function splitInSubSets()
        for new_region_shape in self.new_regions_shapes:
            tile_name = os.path.splitext(os.path.basename(new_region_shape))[0]
            vectors_to_rm = fu.FileSearch_AND(self.data_app_val_dir, True,
                                              tile_name)
            for vect in vectors_to_rm:
                os.remove(vect)
            VS.splitInSubSets(new_region_shape,
                              self.data_field,
                              self.region_field,
                              self.ratio,
                              self.seeds,
                              "ESRI Shapefile",
                              random_seed=0)
            print(new_region_shape)
        # We check the output
        self.assertTrue(
            TestsUtils.compareVectorFile(self.ref_split_shp,
                                         self.out_split_shp, 'coordinates',
                                         'polygon', "ESRI Shapefile"),
            "Split vector output are different")

    def test_vector_splits_cross_validation(self):
        from iota2.Sampling import SplitInSubSets as VS
        from iota2.Common import FileUtils as fut
        # We execute the function splitInSubSets()
        new_region_shape = self.new_regions_shapes[0]
        VS.splitInSubSets(new_region_shape,
                          self.data_field,
                          self.region_field,
                          self.ratio,
                          self.seeds,
                          "ESRI Shapefile",
                          crossValidation=True,
                          random_seed=0)

        seed0 = fut.getFieldElement(new_region_shape,
                                    driverName="ESRI Shapefile",
                                    field="seed_0",
                                    mode="all",
                                    elemType="str")
        seed1 = fut.getFieldElement(new_region_shape,
                                    driverName="ESRI Shapefile",
                                    field="seed_1",
                                    mode="all",
                                    elemType="str")

        for elem in seed0:
            self.assertTrue(elem in ["unused", "learn"],
                            msg="flag not in ['unused', 'learn']")
        for elem in seed1:
            self.assertTrue(elem in ["unused", "validation"],
                            msg="flag not in ['unused', 'validation']")

    def test_vectorSplitsNoSplits(self):
        from iota2.Sampling import SplitInSubSets as VS
        from iota2.Common import FileUtils as fut

        new_region_shape = self.new_regions_shapes[0]
        tile_name = os.path.splitext(os.path.basename(new_region_shape))[0]
        VS.splitInSubSets(new_region_shape,
                          self.data_field,
                          self.region_field,
                          self.ratio,
                          1,
                          "ESRI Shapefile",
                          crossValidation=False,
                          splitGroundTruth=False,
                          random_seed=0)
        seed0 = fut.getFieldElement(new_region_shape,
                                    driverName="ESRI Shapefile",
                                    field="seed_0",
                                    mode="all",
                                    elemType="str")

        for elem in seed0:
            self.assertTrue(elem in ["learn"], msg="flag not in ['learn']")
