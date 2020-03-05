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


class Iota2TestsGetModel(unittest.TestCase):

    # before launching tests
    @classmethod
    def setUpClass(cls):
        # definition of local variables
        cls.group_test_name = "iota_Iota2TestGetModel"
        cls.iota2_tests_directory = os.path.join(IOTA2DIR, "data",
                                                 cls.group_test_name)
        cls.reference_directory = os.path.join(IOTA2DIR, "data", "references",
                                               "getModel", "Input")
        cls.all_tests_ok = []

        cls.tile_for_region_number = [[0, ['tile0']], [
            1, ['tile0', 'tile4']
        ], [2, ['tile0', 'tile1', 'tile2', 'tile3', 'tile4']],
                                      [3, ['tile0', 'tile1', 'tile6']]]
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
        # os.mkdir(self.test_working_directory)

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

    def test_get_model(self):
        '''
        We check we have the expected files in the output
        '''
        from iota2.Learning import GetModel

        shutil.copytree(self.reference_directory, self.test_working_directory)
        # We execute the function getModel()
        outputstr = GetModel.getModel(self.test_working_directory)

        # the function produces a list of regions and its tiles
        # We check if we have all the expected element in the list
        for element in outputstr:
            # We get the region number and all the tiles for the region number
            region = int(element[0])
            tiles = element[1]

            # We check if we have this region number in the list
            # tileForRegionNumber
            irn = -1
            for i, val in enumerate(self.tile_for_region_number):
                if region == val[0]:
                    irn = i
            self.assertEqual(irn, region)

            # for each tile for this region, we check if we have
            # this value in the list of the expected values
            for tile in tiles:
                itfrn = self.tile_for_region_number[irn][1].index(tile)
                self.assertEqual(tile,
                                 self.tile_for_region_number[irn][1][itfrn])
