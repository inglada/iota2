#!/usr/bin/python
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

# python -m unittest Iota2TestsStatistics

import os
import sys
import shutil
import numpy as np
import unittest

IOTA2DIR = os.environ.get('IOTA2DIR')

if IOTA2DIR is None:
    raise Exception ("IOTA2DIR environment variable must be set")

# if all tests pass, remove 'iota2_tests_directory' which contains all
# sub-directory tests
RM_IF_ALL_OK = True

iota2_script = IOTA2DIR + "/scripts"
sys.path.append(iota2_script)

from Common import FileUtils as fut
from Tests.UnitTests import Iota2Tests as testutils
from simplification import ZonalStatsMPI as zsmpi
from simplification import computeStats as cs

class iota_testVectSimp(unittest.TestCase):
    # before launching tests
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.group_test_name = "iota_testVectSimp"
        self.iota2_tests_directory = os.path.join(IOTA2DIR, "data", self.group_test_name)
        self.all_tests_ok = []

        # Tests directory
        self.test_working_directory = None
        if os.path.exists(self.iota2_tests_directory):
            shutil.rmtree(self.iota2_tests_directory)
        os.mkdir(self.iota2_tests_directory)

        self.wd = os.path.join(self.iota2_tests_directory, "wd")
        self.out = os.path.join(self.iota2_tests_directory, "out")
        self.classif = os.path.join(IOTA2DIR, "data", "references/sampler/final/Classif_Seed_0.tif")
        self.validity = os.path.join(IOTA2DIR, "data", "references/sampler/final/PixelsValidity.tif")
        self.outfilestats = os.path.join(self.iota2_tests_directory, self.out, "stats.csv")
        self.outfilevector = os.path.join(self.iota2_tests_directory, self.out, "final.shp")
        self.vector = os.path.join(os.path.join(IOTA2DIR, "data", "references/posttreat/classif.shp"))
        self.refvector = os.path.join(os.path.join(IOTA2DIR, "data", "references/posttreat/final.shp"))
        #self.gdal = "/home/qt/thierionv/sources/gdal224/bin/"
        self.gdallib = os.environ.get('GDAL224DIR')

        if self.grasslib is None:
            raise Exception("GDAL224DIR not initialized (Version of gdal greater or equal to 2.2.4")


    # after launching all tests
    @classmethod
    def tearDownClass(self):
        print "{} ended".format(self.group_test_name)
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
        self.test_working_directory = os.path.join(self.iota2_tests_directory, test_name)
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

    def list2reason(self, exc_list):
        if exc_list and exc_list[-1][0] is self:
            return exc_list[-1][1]

    # after launching a test, remove test's data if test succeed
    def tearDown(self):
        result = getattr(self, '_outcomeForDoCleanups', self._resultForDoCleanups)
        error = self.list2reason(result.errors)
        failure = self.list2reason(result.failures)
        ok = not error and not failure
        self.all_tests_ok.append(ok)
        if ok:
            shutil.rmtree(self.test_working_directory)

    # Tests definitions
    def test_iota2_VectSimp(self):
        """Test how many samples must be add to the sample set
        """
        
        # test (Miss rastconf)
        zsmpi.computZonalStats(self.wd,[self.classif, rastconf, self.validity], self.vector, self.outfilestats, 1, "uint8", None, False, self.gdallib)
        cs.computeStats(self.vector, self.outfilestats, self.wd, self.outfilevector)
        self.assertTrue(testutils.compareVectorFile(self.outfilevector, self.refvector, 'coordinates', 'polygon', "ESRI Shapefile"), \
                        "Generated shapefile vector does not fit with shapefile reference file")

        # remove temporary folders
        if os.path.exists(self.wd):shutil.rmtree(self.wd, ignore_errors=True)
        if os.path.exists(self.out):shutil.rmtree(self.out, ignore_errors=True)



