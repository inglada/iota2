#!/usr/bin/env python3
#-*- coding: utf-8 -*-

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

# python -m unittest NomenclatureTest

import os
import sys
import shutil
import unittest

from iota2.simplification import nomenclature as nom

IOTA2DIR = os.environ.get('IOTA2DIR')

if IOTA2DIR is None:
    raise Exception("IOTA2DIR environment variable must be set")

# if all tests pass, remove 'iota2_tests_directory' which contains all
# sub-directory tests
RM_IF_ALL_OK = True


class iota_NomenclatureTest(unittest.TestCase):
    # before launching tests
    @classmethod
    def setUpClass(cls):
        # definition of local variables
        cls.group_test_name = "iota_NomenclatureTest"
        cls.iota2_tests_directory = os.path.join(IOTA2DIR, "data",
                                                 cls.group_test_name)
        cls.all_tests_ok = []

        # Tests directory
        cls.test_working_directory = None
        if os.path.exists(cls.iota2_tests_directory):
            shutil.rmtree(cls.iota2_tests_directory)
        os.mkdir(cls.iota2_tests_directory)

        cls.wd = os.path.join(cls.iota2_tests_directory, "wd")
        cls.refnomenc = os.path.join(IOTA2DIR, "data",
                                     "references/posttreat/nomenclature.txt")
        cls.refqml = os.path.join(IOTA2DIR, "data",
                                  "references/posttreat/style.qml")
        cls.refqmlout = os.path.join(IOTA2DIR, "data",
                                     "references/posttreat/styleraster.qml")
        cls.qml = os.path.join(cls.iota2_tests_directory, cls.wd, "style.qml")

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

        if os.path.exists(self.wd):
            shutil.rmtree(self.wd, ignore_errors=True)
            os.mkdir(self.wd)
        else:
            os.mkdir(self.wd)

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
        ok = not error and not failure

        self.all_tests_ok.append(ok)
        if ok:
            shutil.rmtree(self.test_working_directory)

    # Tests definitions
    def test_iota2_Nomenclature(self):
        """Test Nomenclature instanciation and exportation
        """

        # test
        expected_codes = [
            1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
            20, 21, 22, 23
        ]
        tabnom = nom.getClassesFromVectorQML(self.refqml)
        nomenc = nom.Iota2Nomenclature(tabnom)
        nomenc.createRasterQML(self.qml, "classe", 1)
        self.assertEqual(len(nomenc), 23)
        self.assertEqual(len(open(self.qml, 'r').read()),
                         len(open(self.refqmlout, 'r').read()))
        self.assertEqual(nomenc.getCode(1), expected_codes)

        # remove temporary folders
        if os.path.exists(self.wd): shutil.rmtree(self.wd, ignore_errors=True)
