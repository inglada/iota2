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

# python -m unittest Iota2TestsRegularisation

from simplification import manageRegularization as mr
from simplification import Regularization as regu
import TestsUtils as testutils
from Common import FileUtils as fut
import os
import sys
import shutil
import numpy as np
import unittest

IOTA2DIR = os.environ.get("IOTA2DIR")

if IOTA2DIR is None:
    raise Exception("IOTA2DIR environment variable must be set")

# if all tests pass, remove 'iota2_tests_directory' which contains all
# sub-directory tests
RM_IF_ALL_OK = True

iota2_script = os.path.join(IOTA2DIR, "iota2")
sys.path.append(iota2_script)


class iota_testRegularisation(unittest.TestCase):
    # before launching tests
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.group_test_name = "iota_testRegularisation"
        self.iota2_tests_directory = os.path.join(
            IOTA2DIR, "data", self.group_test_name
        )
        self.all_tests_ok = []

        # Tests directory
        self.test_working_directory = None
        if os.path.exists(self.iota2_tests_directory):
            shutil.rmtree(self.iota2_tests_directory)
        os.mkdir(self.iota2_tests_directory)

        self.raster10m = os.path.join(
            IOTA2DIR, "data", "references/sampler/final/Classif_Seed_0.tif"
        )
        self.rasterregref = os.path.join(
            IOTA2DIR, "data", "references/posttreat/classif_regul.tif"
        )
        self.nomenclature = os.path.join(
            IOTA2DIR, "data", "references/posttreat/nomenclature_17.cfg"
        )
        self.wd = os.path.join(self.iota2_tests_directory, "wd")
        self.out = os.path.join(self.iota2_tests_directory, "out")
        self.tmp = os.path.join(self.iota2_tests_directory, "tmp")
        self.outfile = os.path.join(
            self.iota2_tests_directory, self.out, "classif_regul.tif"
        )
        # self.inland = os.path.join(IOTA2DIR, "data", "references/posttreat/masque_mer.shp")

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

        if os.path.exists(self.out):
            shutil.rmtree(self.out, ignore_errors=True)
            os.mkdir(self.out)
        else:
            os.mkdir(self.out)

        if os.path.exists(self.tmp):
            shutil.rmtree(self.tmp, ignore_errors=True)
            os.mkdir(self.tmp)
        else:
            os.mkdir(self.tmp)

    def list2reason(self, exc_list):
        if exc_list and exc_list[-1][0] is self:
            return exc_list[-1][1]

    # after launching a test, remove test's data if test succeed
    def tearDown(self):
        if sys.version_info > (3, 4, 0):
            result = self.defaultTestResult()
            self._feedErrorsToResult(result, self._outcome.errors)
        else:
            result = getattr(self, "_outcomeForDoCleanups", self._resultForDoCleanups)
        error = self.list2reason(result.errors)
        failure = self.list2reason(result.failures)
        ok = not error and not failure

        self.all_tests_ok.append(ok)
        if ok:
            shutil.rmtree(self.test_working_directory)

    # Tests definitions
    def test_iota2_regularisation(self):
        """Test regularization
        """

        rules = mr.getMaskRegularisation(self.nomenclature)

        for rule in rules:
            mr.adaptRegularization(
                self.wd,
                self.raster10m,
                os.path.join(self.tmp, rule[2]),
                "1000",
                rule,
                2,
            )

        rasters = fut.FileSearch_AND(self.tmp, True, "mask", ".tif")
        mr.mergeRegularization(self.tmp, rasters, 10, self.outfile, "1000")

        # test
        outtest = testutils.rasterToArray(self.outfile)
        outref = testutils.rasterToArray(self.rasterregref)

        self.assertTrue(np.array_equal(outtest, outref))

        # remove temporary folders
        if os.path.exists(self.wd):
            shutil.rmtree(self.wd, ignore_errors=True)
        if os.path.exists(self.out):
            shutil.rmtree(self.out, ignore_errors=True)
