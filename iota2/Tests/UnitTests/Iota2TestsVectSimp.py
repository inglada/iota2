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

# python -m unittest Iota2TestsVectSimp

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

iota2_script = os.path.join(IOTA2DIR, "iota2")
sys.path.append(iota2_script)

from Common import FileUtils as fut
from Tests.UnitTests import TestsUtils as testutils
from simplification import VectAndSimp as vas

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
        self.rasterreg = os.path.join(IOTA2DIR, "data", "references/posttreat/classif_regul.tif")
        self.outfilename = os.path.join(self.iota2_tests_directory, self.out, "classif.shp")
        self.outfilenamesimp = os.path.join(self.iota2_tests_directory, self.out, "classifsimp.shp")
        self.outfilenamesmooth = os.path.join(self.iota2_tests_directory, self.out, "classifsmooth.shp")
        self.vector = os.path.join(os.path.join(IOTA2DIR, "data", "references/posttreat/vectors/classif.shp"))
        self.vectorsimp = os.path.join(os.path.join(IOTA2DIR, "data", "references/posttreat/vectors/classifsimp.shp"))
        self.vectorsmooth = os.path.join(os.path.join(IOTA2DIR, "data", "references/posttreat/vectors/classifsmooth.shp")) 
        self.grasslib = os.environ.get('GRASSDIR')

        if self.grasslib is None:
            raise Exception("GRASSDIR not initialized")

        if not os.path.exists(os.path.join(self.grasslib, 'bin')):
            raise Exception("GRASSDIR '%s' not well initialized"%(self.grasslib))

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
        if sys.version_info > (3, 4, 0):
            result = self.defaultTestResult()
            self._feedErrorsToResult(result, self._outcome.errors)
        else:
            result = getattr(self, '_outcomeForDoCleanups', self._resultForDoCleanups)
        error = self.list2reason(result.errors)
        failure = self.list2reason(result.failures)
        ok = not error and not failure

        self.all_tests_ok.append(ok)
        if ok:
            shutil.rmtree(self.test_working_directory)

    # Tests definitions
    def test_iota2_VectSimp(self):
        """Test polygonize, simplification and smoothing operations
        """
        
        # polygonize
        vas.topologicalPolygonize(self.wd, self.grasslib, self.rasterreg, True, self.outfilename)    
        self.assertTrue(testutils.compareVectorFile(self.vector, self.outfilename, 'coordinates', 'polygon', "ESRI Shapefile"), \
                        "Generated shapefile vector does not fit with shapefile reference file")

        # simplification
        vas.generalizeVector(self.wd, self.grasslib, self.outfilename, 10, "douglas" , out=self.outfilenamesimp)
        self.assertTrue(testutils.compareVectorFile(self.vectorsimp, self.outfilenamesimp, 'coordinates', 'polygon', "ESRI Shapefile"), \
                        "Generated shapefile vector does not fit with shapefile reference file")
         
        # smoothing
        vas.generalizeVector(self.wd, self.grasslib, self.outfilenamesimp, 10, "hermite" , out=self.outfilenamesmooth)
        self.assertTrue(testutils.compareVectorFile(self.vectorsmooth, self.outfilenamesmooth, 'coordinates', 'polygon', "ESRI Shapefile"), \
                        "Generated shapefile vector does not fit with shapefile reference file")        

        # remove temporary folders
        if os.path.exists(self.wd):shutil.rmtree(self.wd, ignore_errors=True)
        if os.path.exists(self.out):shutil.rmtree(self.out, ignore_errors=True)



