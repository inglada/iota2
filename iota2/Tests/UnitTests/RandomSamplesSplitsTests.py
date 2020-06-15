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
import shutil
import unittest
from iota2.Common import FileUtils as fut

IOTA2DIR = os.environ.get('IOTA2DIR')
RM_IF_ALL_OK = True


class iota_testSamplesSplits(unittest.TestCase):
    # before launching tests
    @classmethod
    def setUpClass(self):

        # definition of local variables
        self.group_test_name = "iota_testSamplesSplits"
        self.iota2_tests_directory = os.path.join(IOTA2DIR, "data",
                                                  self.group_test_name)
        self.all_tests_ok = []
        self.test_working_directory = None
        if os.path.exists(self.iota2_tests_directory):
            shutil.rmtree(self.iota2_tests_directory)
        os.mkdir(self.iota2_tests_directory)

        self.random_splits = 10

        # generate fake input data

        self.data_field = "code"
        self.region_field = "region"

    # after launching tests
    @classmethod
    def tearDownClass(self):
        print("{} ended".format(self.group_test_name))
        if RM_IF_ALL_OK and all(self.all_tests_ok):
            shutil.rmtree(self.iota2_tests_directory)

    # before launching a test
    def setUp(self):
        """
        create test environement (directories)
        """
        # create directories
        test_name = self.id().split(".")[-1]
        self.test_working_directory = os.path.join(self.iota2_tests_directory,
                                                   test_name)
        if os.path.exists(self.test_working_directory):
            shutil.rmtree(self.test_working_directory)
        os.mkdir(self.test_working_directory)

        # Create test data

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
    def test_NoSeed(self):
        """considering 2 iota's run with no random seed provided, check if the
        two runs generate 2 times 10 independant sample-set.
        """
        from iota2.Sampling.SplitInSubSets import splitInSubSets
        from iota2.Tests.UnitTests.TestsUtils import random_ground_truth_generator
        from iota2.Common.FileUtils import cpShapeFile
        from iota2.Common.FileUtils import getFieldElement

        vector_file_to_split = os.path.join(self.test_working_directory,
                                            "test_NoSeed.shp")
        numbler_of_class = 23
        random_ground_truth_generator(vector_file_to_split, self.data_field,
                                      numbler_of_class, self.region_field)

        random_seed = None

        # first run
        vector_file_first = os.path.join(self.test_working_directory,
                                         "test_NoSeed_first.shp")
        cpShapeFile(vector_file_to_split.replace(".shp", ""),
                    vector_file_first.replace(".shp", ""),
                    [".prj", ".shp", ".dbf", ".shx"])
        splitInSubSets(vector_file_first,
                       self.data_field,
                       self.region_field,
                       driver_name="ESRI shapefile",
                       seeds=self.random_splits,
                       random_seed=random_seed)
        # second run
        vector_file_second = os.path.join(self.test_working_directory,
                                          "test_NoSeed_second.shp")
        cpShapeFile(vector_file_to_split.replace(".shp", ""),
                    vector_file_second.replace(".shp", ""),
                    [".prj", ".shp", ".dbf", ".shx"])
        splitInSubSets(vector_file_second,
                       self.data_field,
                       self.region_field,
                       driver_name="ESRI shapefile",
                       seeds=self.random_splits,
                       random_seed=random_seed)

        # asserts
        seeds_runs = []
        seeds_first = []
        seeds_second = []
        for seed in range(self.random_splits):
            seeds_first.append(
                tuple(
                    getFieldElement(vector_file_first,
                                    driverName="ESRI Shapefile",
                                    field="seed_{}".format(seed),
                                    mode="all",
                                    elemType="str")))
            seeds_second.append(
                tuple(
                    getFieldElement(vector_file_second,
                                    driverName="ESRI Shapefile",
                                    field="seed_{}".format(seed),
                                    mode="all",
                                    elemType="str")))

            seeds_runs.append(seeds_first[seed] != seeds_second[seed])

        # seeds between runs must be different
        self.assertTrue(
            all(seeds_runs),
            msg=
            "two runs of iota², will produce same random split despite chain.random_seed is None"
        )

        # of course each seed in the same run must be different one an other
        from collections import Counter
        all_different = []
        first_seeds_counter = Counter(seeds_first)
        second_seeds_counter = Counter(seeds_second)
        for k1, v1 in first_seeds_counter.items():
            all_different.append(v1 == 1)
        for k2, v2 in second_seeds_counter.items():
            all_different.append(v2 == 1)
        self.assertTrue(
            all(all_different),
            msg=
            "two seeds have the same learning / validation split > random does not work"
        )

    def test_Seed(self):
        """considering 2 iota's run with no random seed provided, check if the
        two runs generate 2 times the same 10 independant sample-set.
        """
        from iota2.Sampling.SplitInSubSets import splitInSubSets
        from iota2.Tests.UnitTests.TestsUtils import random_ground_truth_generator
        from iota2.Common.FileUtils import cpShapeFile
        from iota2.Common.FileUtils import getFieldElement

        vector_file_to_split = os.path.join(self.test_working_directory,
                                            "test_Seed.shp")
        numbler_of_class = 23
        random_ground_truth_generator(vector_file_to_split, self.data_field,
                                      numbler_of_class, self.region_field)

        random_seed = 1

        # first run
        vector_file_first = os.path.join(self.test_working_directory,
                                         "test_NoSeed_first.shp")
        cpShapeFile(vector_file_to_split.replace(".shp", ""),
                    vector_file_first.replace(".shp", ""),
                    [".prj", ".shp", ".dbf", ".shx"])
        splitInSubSets(vector_file_first,
                       self.data_field,
                       self.region_field,
                       driver_name="ESRI shapefile",
                       seeds=self.random_splits,
                       random_seed=random_seed)
        # second run
        vector_file_second = os.path.join(self.test_working_directory,
                                          "test_NoSeed_second.shp")
        cpShapeFile(vector_file_to_split.replace(".shp", ""),
                    vector_file_second.replace(".shp", ""),
                    [".prj", ".shp", ".dbf", ".shx"])
        splitInSubSets(vector_file_second,
                       self.data_field,
                       self.region_field,
                       driver_name="ESRI shapefile",
                       seeds=self.random_splits,
                       random_seed=random_seed)

        # asserts
        seeds_runs = []
        seeds_first = []
        seeds_second = []
        for seed in range(self.random_splits):
            seeds_first.append(
                tuple(
                    getFieldElement(vector_file_first,
                                    driverName="ESRI Shapefile",
                                    field="seed_{}".format(seed),
                                    mode="all",
                                    elemType="str")))
            seeds_second.append(
                tuple(
                    getFieldElement(vector_file_second,
                                    driverName="ESRI Shapefile",
                                    field="seed_{}".format(seed),
                                    mode="all",
                                    elemType="str")))

            seeds_runs.append(seeds_first[seed] == seeds_second[seed])

        # seeds between runs must be the same
        self.assertTrue(
            all(seeds_runs),
            msg=
            "two runs of iota², does not produce same random split despite chain.random_seed is set to an integer"
        )

        # of course each seed in the same run must be different one an other
        from collections import Counter
        all_different = []
        first_seeds_counter = Counter(seeds_first)
        second_seeds_counter = Counter(seeds_second)
        for k1, v1 in first_seeds_counter.items():
            all_different.append(v1 == 1)
        for k2, v2 in second_seeds_counter.items():
            all_different.append(v2 == 1)
        self.assertTrue(
            all(all_different),
            msg=
            "two seeds have the same learning / validation split > random does not work"
        )
