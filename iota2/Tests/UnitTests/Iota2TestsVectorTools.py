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

# python -m unittest Iota2TestsVectorTools

import os
import unittest
import sys
import shutil
from iota2.Tests.UnitTests import TestsUtils as testutils
from iota2.VectorTools import AddFieldPerimeter as afp
from iota2.VectorTools import BufferOgr as bfo
from iota2.VectorTools import ChangeNameField as cnf
from iota2.VectorTools import vector_functions as vf
from iota2.VectorTools import spatialOperations as so
from iota2.VectorTools import checkGeometryAreaThreshField as check
from iota2.VectorTools import ConditionalFieldRecode as cfr
from iota2.VectorTools import splitByArea as sba
from iota2.VectorTools import MergeFiles as mf

IOTA2DIR = os.environ.get('IOTA2DIR')

if IOTA2DIR is None:
    raise Exception("IOTA2DIR environment variable must be set")

# if all tests pass, remove 'iota2_tests_directory' which contains all
# sub-directory tests
RM_IF_ALL_OK = True

# iota2_script = os.path.join(IOTA2DIR, "iota2")
# sys.path.append(iota2_script)


class iota_testVectortools(unittest.TestCase):
    # before launching tests
    @classmethod
    def setUpClass(cls):
        # definition of local variables
        cls.group_test_name = "iota_testVectortools"
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
        cls.classif = os.path.join(IOTA2DIR, "data",
                                   "references/vectortools/classif.shp")
        cls.inter = os.path.join(IOTA2DIR, "data",
                                 "references/vectortools/region.shp")
        cls.classifwd = os.path.join(cls.out, "classif.shp")
        cls.classifout = os.path.join(IOTA2DIR, "data",
                                      "references/vectortools/classifout.shp")
        cls.outinter = os.path.join(cls.wd, "inter.shp")

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
        ok = not error and not failure

        self.all_tests_ok.append(ok)
        if ok:
            shutil.rmtree(self.test_working_directory)

    # Tests definitions
    def test_iota2_vectortools(self):
        """Test how many samples must be add to the sample set
        """

        # Add Field
        for ext in ['.shp', '.dbf', '.shx', '.prj']:
            shutil.copyfile(
                os.path.splitext(self.classif)[0] + ext,
                os.path.splitext(self.classifwd)[0] + ext)

        afp.addFieldPerimeter(self.classifwd)
        tmpbuff = os.path.join(self.wd, "tmpbuff.shp")
        bfo.bufferPoly(self.classifwd, tmpbuff, -10)
        for ext in ['.shp', '.dbf', '.shx', '.prj']:
            shutil.copyfile(
                os.path.splitext(tmpbuff)[0] + ext,
                os.path.splitext(self.classifwd)[0] + ext)

        cnf.changeName(self.classifwd, "Classe", "class")
        self.assertEqual(vf.getNbFeat(self.classifwd), 144,
                         "Number of features does not fit")
        self.assertEqual(vf.getFields(self.classifwd), [
            'Validmean', 'Validstd', 'Confidence', 'Hiver', 'Ete', 'Feuillus',
            'Coniferes', 'Pelouse', 'Landes', 'UrbainDens', 'UrbainDiff',
            'ZoneIndCom', 'Route', 'PlageDune', 'SurfMin', 'Eau', 'GlaceNeige',
            'Prairie', 'Vergers', 'Vignes', 'Perimeter', 'class'
        ], "List of fields does not fit")
        self.assertEqual(
            vf.ListValueFields(self.classifwd, "class"),
            ['11', '12', '211', '222', '31', '32', '36', '42', '43', '51'],
            "Values of field 'class' do not fit")
        self.assertEqual(
            vf.getFieldType(self.classifwd, "class"), str,
            "Type of field 'class' (%s) do not fit, 'str' expected" %
            (vf.getFieldType(self.classifwd, "class")))

        cfr.conFieldRecode(self.classifwd, "class", "mask", 11, 0)
        so.intersectSqlites(self.classifwd, self.inter, self.wd, self.outinter,
                            2154, "intersection", [
                                'class', 'Validmean', 'Validstd', 'Confidence',
                                'ID', 'Perimeter', 'Aire', "mask"
                            ])
        check.checkGeometryAreaThreshField(self.outinter, 100, 1,
                                           self.classifwd)
        self.assertEqual(vf.getNbFeat(self.classifwd), 102,
                         "Number of features does not fit")

        sba.extractFeatureFromShape(self.classifwd, 3, "mask", self.wd)
        mf.mergeVectors([
            os.path.join(self.wd, "classif0_0.shp"),
            os.path.join(self.wd, "classif0_1.shp"),
            os.path.join(self.wd, "classif0_2.shp")
        ], self.classifwd)
        self.assertEqual(vf.getFirstLayer(self.classifwd), 'classif',
                         "Layer does not exist in this shapefile")

        self.assertTrue(
            testutils.compareVectorFile(self.classifwd, self.classifout,
                                        'coordinates', 'polygon',
                                        "ESRI Shapefile"),
            "Generated shapefile vector does not fit with shapefile reference file"
        )
