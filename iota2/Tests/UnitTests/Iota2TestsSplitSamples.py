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
"""Test Split Samples"""
# python -m unittest Iota2TestsSplitSamples
import os
import sys
import shutil
import unittest
from iota2.Common import FileUtils as fu
# if all tests pass, remove 'iota2_tests_directory' which contains all
# sub-directory tests
RM_IF_ALL_OK = True
IOTA2DIR = os.environ.get('IOTA2DIR')


class iota2_tests_split_samples(unittest.TestCase):
    """Test split samples module functions"""
    # before launching tests
    @classmethod
    def setUpClass(cls):
        # definition of local variables
        cls.group_test_name = "iota_Iota2TestsSplitSamples"
        cls.iota2_tests_directory = os.path.join(IOTA2DIR, "data",
                                                 cls.group_test_name)
        cls.all_tests_ok = []
        cls.data_field = "CODE"
        cls.region_field = "region"
        cls.region_threshold = 0.0098
        cls.proj = 2154
        cls.runs = 2
        cls.ratio = 0.5
        # We define several output
        cls.formatting_vector_dir = os.path.join(cls.iota2_tests_directory,
                                                 'formattingVectors')
        cls.shape_region_dir = os.path.join(cls.iota2_tests_directory,
                                            'shapeRegion')
        cls.vectors = os.path.join(cls.iota2_tests_directory,
                                   "formattingVectors", "T31TCJ.shp")
        cls.shapes_region = os.path.join(
            cls.iota2_tests_directory,
            "shapeRegion/Myregion_region_1_T31TCJ.shp")
        cls.regions = "1"
        cls.areas = 12399.173485632864
        cls.region_tiles = os.path.join(cls.iota2_tests_directory,
                                        "formattingVectors", "T31TCJ.sqlite")
        cls.data_to_rm = os.path.join(cls.iota2_tests_directory,
                                      "formattingVectors", "T31TCJ.sqlite")
        cls.regions_split = 2
        cls.updated_vector = os.path.join(cls.iota2_tests_directory,
                                          "formattingVectors", "T31TCJ.sqlite")
        cls.new_region_shape = os.path.join(cls.iota2_tests_directory,
                                            "formattingVectors", "T31TCJ.shp")
        cls.data_app_val_dir = os.path.join(cls.iota2_tests_directory,
                                            "dataAppVal")
        cls.enable_cross_validation = False
        # Tests directory
        cls.test_working_directory = None
        if os.path.exists(cls.iota2_tests_directory):
            shutil.rmtree(cls.iota2_tests_directory)
        # cls.iota2_tests_directory is created by copy tree
        # os.mkdir(cls.iota2_tests_directory)
        # We copy every file from the input folder
        shutil.copytree(
            os.path.join(IOTA2DIR, "data", 'references', 'splitSamples',
                         'Input'), cls.iota2_tests_directory)

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
        ok_test = not error and not failure

        self.all_tests_ok.append(ok_test)
        if ok_test:
            shutil.rmtree(self.test_working_directory)

    def test_split_samples(self):
        from iota2.Sampling import SplitSamples

        # We execute several functions of this file
        regions_pos = -2

        formatting_vectors_dir = os.path.join(self.iota2_tests_directory,
                                              "formattingVectors")
        # We check we have the correct file
        self.assertEqual(self.formatting_vector_dir,
                         os.path.abspath(formatting_vectors_dir))

        shape_region_dir = os.path.join(self.iota2_tests_directory,
                                        "shapeRegion")
        # We check we have the correct file
        self.assertEqual(self.shape_region_dir,
                         os.path.abspath(shape_region_dir))

        vectors = fu.FileSearch_AND(formatting_vectors_dir, True, ".shp")

        # We check we have the correct file
        self.assertEqual(self.vectors, os.path.abspath(vectors[0]))

        shapes_region = fu.FileSearch_AND(shape_region_dir, True, ".shp")
        # We check we have the correct file
        self.assertEqual(self.shapes_region, os.path.abspath(shapes_region[0]))

        regions = list(
            set([
                os.path.split(shape)[-1].split("_")[regions_pos]
                for shape in shapes_region
            ]))
        # We check we have the correct value
        self.assertEqual(self.regions, regions[0])

        areas, regions_tiles, data_to_rm = SplitSamples.get_regions_area(
            vectors, regions, formatting_vectors_dir, None, self.region_field)
        # We check we have the correct values
        self.assertAlmostEqual(self.areas, areas['1'], 9e-3)
        self.assertEqual(self.region_tiles,
                         os.path.abspath(regions_tiles['1'][0]))
        self.assertEqual(self.data_to_rm, os.path.abspath(data_to_rm[0]))

        regions_split = SplitSamples.get_splits_regions(
            areas, self.region_threshold)
        # We check we have the correct value
        self.assertEqual(self.regions_split, regions_split['1'])

        updated_vectors = SplitSamples.split(regions_split, regions_tiles,
                                             self.data_field,
                                             self.region_field)

        # We check we have the correct file
        self.assertEqual(self.updated_vector,
                         os.path.abspath(updated_vectors[0]))

        new_regions_shapes = SplitSamples.transform_to_shape(
            updated_vectors, formatting_vectors_dir)
        # We check we have the correct file
        self.assertEqual(self.new_region_shape,
                         os.path.abspath(new_regions_shapes[0]))

        for data in data_to_rm:
            os.remove(data)

        data_app_val_dir = os.path.join(self.iota2_tests_directory,
                                        "dataAppVal")
        self.assertEqual(self.data_app_val_dir,
                         os.path.abspath(data_app_val_dir))

        SplitSamples.update_learning_validation_sets(
            new_regions_shapes,
            data_app_val_dir,
            self.data_field,
            self.region_field,
            self.ratio,
            self.runs,
            self.proj,
            self.enable_cross_validation,
            random_seed=None)
