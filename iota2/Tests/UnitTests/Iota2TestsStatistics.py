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

# python -m unittest Iota2TestsStatistics

import os
import sys
import shutil
import unittest
import filecmp
from iota2.Tests.UnitTests import TestsUtils as testutils
from iota2.Tests.UnitTests.tests_utils import tests_utils_rasters as TUR

from iota2.simplification import ZonalStats as zs
IOTA2DIR = os.environ.get('IOTA2DIR')

if IOTA2DIR is None:
    raise Exception("IOTA2DIR environment variable must be set")

# if all tests pass, remove 'iota2_tests_directory' which contains all
# sub-directory tests
RM_IF_ALL_OK = True

IOTA2SCRIPT = os.path.join(IOTA2DIR, "iota2")
sys.path.append(IOTA2SCRIPT)


class iota_test_zonal_stats(unittest.TestCase):
    """Test zonal stats functions """
    # before launching tests
    @classmethod
    def setUpClass(cls):
        # definition of local variables
        cls.group_test_name = "iota_testZonalStats"
        cls.iota2_tests_directory = os.path.join(IOTA2DIR, "data",
                                                 cls.group_test_name)
        cls.all_tests_ok = []

        # Tests directory
        cls.test_working_directory = None
        if os.path.exists(cls.iota2_tests_directory):
            shutil.rmtree(cls.iota2_tests_directory)
        os.mkdir(cls.iota2_tests_directory)

        cls.wd = os.path.join(cls.iota2_tests_directory, "wd/")
        cls.out = os.path.join(cls.iota2_tests_directory, "out/")
        cls.classif = os.path.join(
            IOTA2DIR, "data", "references/sampler/final/Classif_Seed_0.tif")
        cls.validity = os.path.join(
            IOTA2DIR, "data", "references/sampler/final/PixelsValidity.tif")
        cls.confid = os.path.join(
            IOTA2DIR, "data", "references/sampler/final/PixelsValidity.tif")
        cls.vector = os.path.join(
            IOTA2DIR, "data", "references/posttreat/vectors/classifsmooth.shp")
        cls.vectorstats = os.path.join(cls.iota2_tests_directory, cls.out,
                                       "classifstats.shp")
        cls.vectorstatsiota2 = os.path.join(cls.iota2_tests_directory, cls.out,
                                            "classifiota2.shp")
        cls.outzip = os.path.join(cls.iota2_tests_directory, cls.out,
                                  "classif.zip")
        cls.statslist = {1: "rate", 2: "statsmaj", 3: "statsmaj"}
        cls.nomenclature = os.path.join(
            IOTA2DIR, "data", "references/posttreat/nomenclature_17.cfg")

        cls.outzipref = os.path.join(
            IOTA2DIR, "data", "references/posttreat/vectors/classif.zip")

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
        ok_test = not error and not failure

        self.all_tests_ok.append(ok_test)
        if ok_test:
            shutil.rmtree(self.test_working_directory)

    # Tests definitions
    def test_iota2_samples_statistics(self):
        """test generation of statistics by tiles
        """
        from iota2.Sampling.SamplesStat import samples_stats
        from iota2.Common.FileUtils import ensure_dir

        ensure_dir(
            os.path.join(self.test_working_directory, "samplesSelection"))
        ensure_dir(os.path.join(self.test_working_directory, "shapeRegion"))

        raster_ref = os.path.join(self.test_working_directory,
                                  "RASTER_REF.tif")
        arr_test = TUR.fun_array("iota2_binary")
        TUR.array_to_raster(arr_test,
                            raster_ref,
                            origin_x=566377,
                            origin_y=6284029)

        shutil.copy(
            raster_ref,
            os.path.join(self.test_working_directory, "shapeRegion",
                         "T31TCJ_region_1_.tif"))

        references_directory = os.path.join(IOTA2DIR, "data", "references")
        region_shape = os.path.join(references_directory, "region_target.shp")
        shutil.copy(
            region_shape,
            os.path.join(
                os.path.join(self.test_working_directory, "samplesSelection",
                             "T31TCJ_region_1_seed_0.shp")))
        shutil.copy(
            region_shape.replace(".shp", ".shx"),
            os.path.join(
                os.path.join(self.test_working_directory, "samplesSelection",
                             "T31TCJ_region_1_seed_0.shx")))
        shutil.copy(
            region_shape.replace(".shp", ".dbf"),
            os.path.join(
                os.path.join(self.test_working_directory, "samplesSelection",
                             "T31TCJ_region_1_seed_0.dbf")))
        shutil.copy(
            region_shape.replace(".shp", ".prj"),
            os.path.join(
                os.path.join(self.test_working_directory, "samplesSelection",
                             "T31TCJ_region_1_seed_0.prj")))

        test_statistics = samples_stats(
            region_seed_tile=("1", "0", "T31TCJ"),
            iota2_directory=self.test_working_directory,
            data_field="region",
            working_directory=None)
        self.assertTrue(
            filecmp.cmp(
                os.path.join(IOTA2DIR, "data", "references",
                             "T31TCJ_region_1_seed_0_stats.xml"),
                test_statistics))

    def test_iota2_statistics(self):
        """Test vector statistics computing
        """
        # Statistics test
        params = zs.splitVectorFeatures(self.vector, self.wd, 1)
        zs.zonalstats(self.wd, [self.classif, self.confid, self.validity],
                      params,
                      self.vectorstats,
                      self.statslist,
                      classes=self.nomenclature)

        zs.osoFormatting(self.vectorstats, self.nomenclature,
                         self.vectorstatsiota2)

        zs.compressShape(self.vectorstatsiota2, self.outzip)

        # Final integration test
        os.system("unzip %s -d %s" % (self.outzipref, self.wd))
        for ext in ['.shp', '.dbf', '.shx', '.prj', '.cpg']:
            os.remove(os.path.splitext(self.vectorstatsiota2)[0] + ext)

        os.system("unzip %s -d %s" % (self.outzip, self.out))

        self.assertTrue(
            testutils.compareVectorFile(
                os.path.join(self.out, "classifiota2.shp"),
                os.path.join(self.wd, "classifiota2.shp"), 'coordinates',
                'polygon', "ESRI Shapefile"),
            "Generated shapefile vector does not fit with shapefile "
            "reference file")

        # remove temporary folders
        if os.path.exists(self.wd):
            shutil.rmtree(self.wd, ignore_errors=True)
        if os.path.exists(self.out):
            shutil.rmtree(self.out, ignore_errors=True)
