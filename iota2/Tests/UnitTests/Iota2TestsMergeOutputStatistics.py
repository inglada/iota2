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


class iota2_tests_merge_output_statistics(unittest.TestCase):
    """ Test merge output statistics"""
    # before launching tests
    @classmethod
    def setUpClass(cls):
        # definition of local variables
        cls.group_test_name = "iota_Iota2MergeOutputStatistics"
        cls.iota2_tests_directory = os.path.join(IOTA2DIR, "data",
                                                 cls.group_test_name)
        cls.all_tests_ok = []
        cls.references_directory = os.path.join(IOTA2DIR, "data", "references",
                                                "mergeOutStats")

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
        shutil.copytree(
            os.path.join(self.references_directory, "Input", "final", "TMP"),
            os.path.join(self.test_working_directory, "final", "TMP"))

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
        ok_test = not (error or failure)

        self.all_tests_ok.append(ok_test)
        if ok_test:
            shutil.rmtree(self.test_working_directory)

    def test_merge_output_statistics(self):
        import filecmp
        from iota2.Validation import MergeOutStats

        MergeOutStats.merge_output_statistics(
            os.path.join(self.test_working_directory), 1)

        self.assertTrue(
            filecmp.cmp(
                os.path.join(self.references_directory, "Output",
                             "Stats_LNOK.txt"),
                os.path.join(self.test_working_directory, "final",
                             "Stats_LNOK.txt")))
        self.assertTrue(
            filecmp.cmp(
                os.path.join(self.references_directory, "Output",
                             "Stats_LOK.txt"),
                os.path.join(self.test_working_directory, "final",
                             "Stats_LOK.txt")))
        self.assertTrue(
            filecmp.cmp(
                os.path.join(self.references_directory, "Output",
                             "Stats_VNOK.txt"),
                os.path.join(self.test_working_directory, "final",
                             "Stats_VNOK.txt")))
        self.assertTrue(
            filecmp.cmp(
                os.path.join(self.references_directory, "Output",
                             "Stats_VOK.txt"),
                os.path.join(self.test_working_directory, "final",
                             "Stats_VOK.txt")))
