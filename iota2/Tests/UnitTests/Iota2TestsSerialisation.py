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

# python -m unittest Iota2TestsSerialisation

import os
import sys
import shutil
import unittest
import numpy as np
from iota2.Tests.UnitTests import TestsUtils as testutils
from iota2.simplification import searchCrownTile as sct
from iota2.simplification import buildCrownRaster as bcr
from iota2.simplification import GridGenerator as gridg

IOTA2DIR = os.environ.get('IOTA2DIR')

if IOTA2DIR is None:
    raise Exception("IOTA2DIR environment variable must be set")

# if all tests pass, remove 'iota2_tests_directory' which contains all
# sub-directory tests
RM_IF_ALL_OK = True


class iota_testSerialisation(unittest.TestCase):
    # before launching tests
    @classmethod
    def setUpClass(cls):
        # definition of local variables
        cls.group_test_name = "iota_testSerialisation"
        cls.iota2_tests_directory = os.path.join(IOTA2DIR, "data",
                                                 cls.group_test_name)
        cls.all_tests_ok = []

        # Tests directory
        cls.test_working_directory = None
        if os.path.exists(cls.iota2_tests_directory):
            shutil.rmtree(cls.iota2_tests_directory)
        os.mkdir(cls.iota2_tests_directory)

        cls.rasterclump = os.path.join(
            os.path.join(IOTA2DIR, "data",
                         "references/posttreat/clump32bits.tif"))
        cls.raster = os.path.join(
            os.path.join(IOTA2DIR, "data",
                         "references/posttreat/classif_clump.tif"))
        cls.wd = os.path.join(cls.iota2_tests_directory, "wd")
        cls.out = os.path.join(cls.iota2_tests_directory, "out")
        cls.outpathtile = os.path.join(cls.iota2_tests_directory, cls.out,
                                       "tiles")
        cls.outfile = os.path.join(cls.iota2_tests_directory, cls.out,
                                   "grid.shp")
        cls.outfileref = os.path.join(
            os.path.join(IOTA2DIR, "data", "references/posttreat/grid.shp"))
        cls.outseria = os.path.join(cls.iota2_tests_directory, cls.out,
                                    "tiles/crown_0.tif")
        cls.outtile = os.path.join(cls.iota2_tests_directory, cls.out,
                                   "tiles/tile_0.tif")
        cls.outseriaref = os.path.join(
            os.path.join(IOTA2DIR, "data",
                         "references/posttreat/tiles/crown_0.tif"))
        cls.outtileref = os.path.join(
            os.path.join(IOTA2DIR, "data",
                         "references/posttreat/tiles/tile_0.tif"))
        #cls.outfilevect = os.path.join(cls.iota2_tests_directory, cls.out, "classif.shp")
        #cls.outfilevectname = os.path.join(cls.iota2_tests_directory, cls.out, "classifmontagne.shp")
        #cls.vector = os.path.join(os.path.join(IOTA2DIR, "data", "references/posttreat/classifmontagne.shp"))
        #cls.clipfile = os.path.join(os.path.join(IOTA2DIR, "data", "references/posttreat/region.shp"))
        cls.grasslib = os.environ.get('GRASSDIR')

        if cls.grasslib is None:
            raise Exception("GRASSDIR not initialized")

        if not os.path.exists(os.path.join(cls.grasslib, 'bin')):
            raise Exception("GRASSDIR '%s' not well initialized" %
                            (cls.grasslib))

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

        if os.path.exists(self.out):
            shutil.rmtree(self.out, ignore_errors=True)
            os.mkdir(self.out)
        else:
            os.mkdir(self.out)

        if os.path.exists(self.outpathtile):
            shutil.rmtree(self.outpathtile, ignore_errors=True)
            os.mkdir(self.outpathtile)
        else:
            os.mkdir(self.outpathtile)

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
    def test_iota2_serialisation(self):
        """Test Serialisation process
        """

        # Grid generation test
        gridg.grid_generate(self.outfile, 2, 2154, self.rasterclump)
        self.assertTrue(testutils.compareVectorFile(self.outfile, self.outfileref, 'coordinates', 'polygon', "ESRI Shapefile"), \
                        "Generated grid shapefile vector does not fit with reference file")

        # Crown entities test
        sct.searchCrownTile(self.wd, self.raster, self.rasterclump, 128,
                            self.outfileref, self.outpathtile, 1, 0)

        outtest = testutils.rasterToArray(self.outseria)
        outref = testutils.rasterToArray(self.outseriaref)
        self.assertTrue(np.array_equal(outtest, outref))

        # Crown building test
        bcr.manageBlocks(self.outpathtile, 0, 20, self.wd, self.outpathtile,
                         128)

        outtest = testutils.rasterToArray(self.outtile)
        outtileref = testutils.rasterToArray(self.outtileref)
        self.assertTrue(np.array_equal(outtest, outtileref))

        # remove temporary folders
        if os.path.exists(self.wd): shutil.rmtree(self.wd, ignore_errors=True)
        if os.path.exists(self.out):
            shutil.rmtree(self.out, ignore_errors=True)
