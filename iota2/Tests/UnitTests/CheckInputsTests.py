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

# python -m unittest CheckInputsTests
"""check inputs tests"""
import os
import sys
import shutil
import unittest

# if all tests pass, remove 'iota2_tests_directory' which contains all
# sub-directory tests
RM_IF_ALL_OK = True
IOTA2DIR = os.environ.get('IOTA2DIR')


class Iota2CheckInputs(unittest.TestCase):

    # before launching tests
    @classmethod
    def setUpClass(cls):
        # definition of local variables
        cls.group_test_name = "iota_Iota2CheckInputs"
        cls.iota2_tests_directory = os.path.join(IOTA2DIR, "data",
                                                 cls.group_test_name)
        cls.all_tests_ok = []
        references_directory = os.path.join(IOTA2DIR, "data", "references")
        cls.config_test = os.path.join(
            IOTA2DIR, "config", "Config_4Tuiles_Multi_FUS_Confidence.cfg")
        cls.ground_truth = os.path.join(references_directory,
                                        "ZONAGE_BV_ALL.shp")
        cls.region_target_miss = os.path.join(references_directory,
                                              "region_target_miss.shp")
        cls.region_target = os.path.join(references_directory,
                                         "region_target.shp")
        cls.gt_target_miss = os.path.join(references_directory,
                                          "gt_target_miss.shp")
        cls.gt_target = os.path.join(references_directory, "gt_target.shp")
        cls.gt_target_miss_region = os.path.join(references_directory,
                                                 "gt_target_miss_region.shp")
        cls.gt_target_miss_one_region = os.path.join(
            references_directory, "gt_target_miss_one_region.shp")

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
    def test_check_database(self):
        """
        TEST : check the database
        """
        from iota2.Common import ServiceError
        from iota2.Common.Tools import checkDataBase
        from iota2.Common.FileUtils import cpShapeFile
        from TestsUtils import random_ground_truth_generator

        _, ground_truth_name = os.path.split(self.ground_truth)
        test_ground_truth = os.path.join(self.test_working_directory,
                                         ground_truth_name)
        cpShapeFile(self.ground_truth.replace(".shp", ""),
                    test_ground_truth.replace(".shp", ""),
                    [".prj", ".shp", ".dbf", ".shx"])
        data_field = "code"
        epsg = 2154
        gt_errors = checkDataBase.check_ground_truth(test_ground_truth,
                                                     "",
                                                     data_field,
                                                     epsg,
                                                     do_corrections=False,
                                                     display=False)
        # multipolygons detected
        self.assertTrue(len(gt_errors) == 1)
        self.assertTrue(isinstance(type(
            gt_errors[0]), ServiceError.containsMultipolygon.__class__),
                        msg="multipolygons undetected")
        # wrong projection
        epsg = 2155
        gt_errors = checkDataBase.check_ground_truth(test_ground_truth,
                                                     "",
                                                     data_field,
                                                     epsg,
                                                     do_corrections=False,
                                                     display=False)
        self.assertTrue(len(gt_errors) == 2)
        self.assertTrue(isinstance(type(gt_errors[0]),
                                   ServiceError.invalidProjection.__class__),
                        msg="invalid projection miss detected")
        self.assertTrue(isinstance(type(
            gt_errors[1]), ServiceError.containsMultipolygon.__class__),
                        msg="multipolygons undetected")
        # no field detected
        data_field = "error"
        epsg = 2154
        gt_errors = checkDataBase.check_ground_truth(test_ground_truth,
                                                     "",
                                                     data_field,
                                                     epsg,
                                                     do_corrections=False,
                                                     display=False)
        self.assertTrue(len(gt_errors) == 2)
        self.assertTrue(isinstance(type(gt_errors[0]),
                                   ServiceError.missingField.__class__),
                        msg="missing field undetected")
        self.assertTrue(isinstance(type(
            gt_errors[1]), ServiceError.containsMultipolygon.__class__),
                        msg="multipolygons undetected")
        # field type
        data_field = "region"
        epsg = 2154
        gt_errors = checkDataBase.check_ground_truth(test_ground_truth,
                                                     "",
                                                     data_field,
                                                     epsg,
                                                     do_corrections=False,
                                                     display=False)
        self.assertTrue(len(gt_errors) == 2)
        self.assertTrue(isinstance(type(gt_errors[0]),
                                   ServiceError.fieldType.__class__),
                        msg="integer field Type undetected")
        self.assertTrue(isinstance(type(
            gt_errors[1]), ServiceError.containsMultipolygon.__class__),
                        msg="multipolygons undetected")
        # invalid geometry
        no_geom_shape = os.path.join(self.test_working_directory,
                                     "no_geom_shape.shp")
        random_ground_truth_generator(no_geom_shape,
                                      data_field,
                                      3,
                                      set_geom=False)
        gt_errors = checkDataBase.check_ground_truth(no_geom_shape,
                                                     "",
                                                     data_field,
                                                     epsg,
                                                     do_corrections=False,
                                                     display=False)
        self.assertTrue(len(gt_errors) == 1)
        self.assertTrue(isinstance(type(gt_errors[0]),
                                   ServiceError.invalidGeometry.__class__),
                        msg="invalid geometries undetected")

        # empty geometry
        # ~ TODO

        # duplicated features
        dupli_feat_path = os.path.join(self.test_working_directory,
                                       "duplicate_features.shp")
        random_ground_truth_generator(dupli_feat_path, data_field, 3)
        gt_errors = checkDataBase.check_ground_truth(dupli_feat_path,
                                                     "",
                                                     data_field,
                                                     epsg,
                                                     do_corrections=False,
                                                     display=False)
        self.assertTrue(len(gt_errors) == 1)
        self.assertTrue(isinstance(type(gt_errors[0]),
                                   ServiceError.duplicatedFeatures.__class__),
                        msg="duplicated features undetected")

    def test_check_region_shape(self):
        """
        TEST : check the region shape database
        """
        from iota2.Common import ServiceError
        from iota2.Common.Tools import checkDataBase
        from iota2.Common.FileUtils import cpShapeFile

        _, ground_truth_name = os.path.split(self.ground_truth)
        test_ground_truth = os.path.join(self.test_working_directory,
                                         ground_truth_name)
        cpShapeFile(self.ground_truth.replace(".shp", ""),
                    test_ground_truth.replace(".shp", ""),
                    [".prj", ".shp", ".dbf", ".shx"])

        data_field = "region"
        epsg = 2154
        region_errors = checkDataBase.check_region_shape(test_ground_truth,
                                                         "",
                                                         data_field,
                                                         epsg,
                                                         do_corrections=False,
                                                         display=False)
        self.assertTrue(len(region_errors) == 1)
        self.assertTrue(isinstance(type(region_errors[0]),
                                   ServiceError.tooSmallRegion.__class__),
                        msg="too small regions undetected")

    def test_check_intersections(self):
        """
        TEST : check if no intersection between geo-reference data is detected
        """
        from iota2.Common import verifyInputs
        from iota2.Common import ServiceError
        from TestsUtils import generate_fake_s2_data

        s2_data = os.path.join(self.test_working_directory, "S2_data")
        generate_fake_s2_data(s2_data, "T31TCJ",
                              ["20190909", "20190919", "20190929"])

        # usually use case
        intersections_errors = verifyInputs.check_data_intersection(
            self.gt_target, None, "region", 2154, s2_data, ["T31TCJ"])
        self.assertTrue(
            len(intersections_errors) == 0,
            msg="no intersections detected, but there is intersections")

        # no intersections between input rasters and the ground truth
        intersections_errors = verifyInputs.check_data_intersection(
            self.gt_target_miss, None, "region", 2154, s2_data, ["T31TCJ"])

        self.assertTrue(len(intersections_errors) == 1)
        self.assertTrue(isinstance(type(intersections_errors[0]),
                                   ServiceError.intersectionError.__class__),
                        msg="no intersections undetected")

        # no intersections between the ground truth and the region shape
        intersections_errors = verifyInputs.check_data_intersection(
            self.gt_target_miss_region, self.region_target, "region", 2154,
            s2_data, ["T31TCJ"])

        self.assertTrue(len(intersections_errors) == 1)
        self.assertTrue(isinstance(type(intersections_errors[0]),
                                   ServiceError.intersectionError.__class__),
                        msg="no intersections undetected")

        # intersections between the ground truth and the region shape
        intersections_errors = verifyInputs.check_data_intersection(
            self.gt_target, self.region_target, "region", 2154, s2_data,
            ["T31TCJ"])

        self.assertTrue(
            len(intersections_errors) == 0,
            msg="no intersections detected, but there is intersections")

        # no intersections between the ground truth and ONE region
        intersections_errors = verifyInputs.check_data_intersection(
            self.gt_target_miss_one_region, self.region_target, "region", 2154,
            s2_data, ["T31TCJ"])

        self.assertTrue(len(intersections_errors) == 1)
        self.assertTrue(isinstance(type(intersections_errors[0]),
                                   ServiceError.intersectionError.__class__),
                        msg="no intersections undetected")
