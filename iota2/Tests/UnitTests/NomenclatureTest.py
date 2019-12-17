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

# python -m unittest NomenclatureTest

from simplification import nomenclature as nom
from Tests.UnitTests import Iota2Tests as testutils
from Common import FileUtils as fut
import os
import sys
import shutil
import numpy as np
import unittest
import filecmp

IOTA2DIR = os.environ.get("IOTA2DIR")

if IOTA2DIR is None:
    raise Exception("IOTA2DIR environment variable must be set")

# if all tests pass, remove 'iota2_tests_directory' which contains all
# sub-directory tests
RM_IF_ALL_OK = True

iota2_script = os.path.join(IOTA2DIR, "iota2")
sys.path.append(iota2_script)


class iota_NomenclatureTest(unittest.TestCase):
    # before launching tests
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.group_test_name = "iota_NomenclatureTest"
        self.iota2_tests_directory = os.path.join(
            IOTA2DIR, "data", self.group_test_name
        )
        self.all_tests_ok = []

        # Tests directory
        self.test_working_directory = None
        if os.path.exists(self.iota2_tests_directory):
            shutil.rmtree(self.iota2_tests_directory)
        os.mkdir(self.iota2_tests_directory)

        self.wd = os.path.join(self.iota2_tests_directory, "wd")
        self.refnomenc = os.path.join(
            IOTA2DIR, "data", "references/posttreat/nomenclature.txt"
        )
        self.refqml = os.path.join(
            IOTA2DIR, "data", "references/posttreat/style.qml"
        )
        self.refqmlout = os.path.join(
            IOTA2DIR, "data", "references/posttreat/styleraster.qml"
        )
        self.qml = os.path.join(
            self.iota2_tests_directory, self.wd, "style.qml"
        )

    # after launching all tests
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
        # self.test_working_directory is the diretory dedicated to each tests
        # it changes for each tests

        test_name = self.id().split(".")[-1]
        self.test_working_directory = os.path.join(
            self.iota2_tests_directory, test_name
        )
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
    def test_iota2_Nomenclature(self):
        """Test Nomenclature instanciation and exportation
        """

        # test
        expected_codes = [
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
            20,
            21,
            22,
            23,
        ]
        tabnom = nom.getClassesFromVectorQML(self.refqml)
        nomenc = nom.Iota2Nomenclature(tabnom)
        nomenc.createRasterQML(self.qml, "classe", 1)
        self.assertEqual(len(nomenc), 23)
        self.assertEqual(
            len(open(self.qml, "r").read()),
            len(open(self.refqmlout, "r").read()),
        )
        self.assertEqual(nomenc.getCode(1), expected_codes)

        # remove temporary folders
        if os.path.exists(self.wd):
            shutil.rmtree(self.wd, ignore_errors=True)
