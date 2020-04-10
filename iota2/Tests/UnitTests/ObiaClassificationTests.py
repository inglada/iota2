# !/usr/bin/python
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

# python -m unittest ObiaClassificationTests

import os
import sys
import shutil
import unittest

IOTA2DIR = os.environ.get('IOTA2DIR')

if not IOTA2DIR:
    raise Exception("IOTA2DIR environment variable must be set")

# if all tests pass, remove 'iota2_tests_directory' which contains all
# sub-directory tests
RM_IF_ALL_OK = True

IOTA2_SCRIPTS = IOTA2DIR + "/iota2"
sys.path.append(IOTA2_SCRIPTS)

from Common import FileUtils as fut


class iota_testObiaClassification(unittest.TestCase):
    # before launching tests
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.group_test_name = "iota_testObiaClassification"
        self.iota2_tests_directory = os.path.join(IOTA2DIR, "data",
                                                  self.group_test_name)
        self.all_tests_ok = []

        # References
        self.config_test = os.path.join(IOTA2DIR, "data", "references",
                                        "ObiaClassification",
                                        "config_obia.cfg")
        self.in_seg = os.path.join(IOTA2DIR, "data", "references",
                                   "ObiaReassembleParts", "Input", "seg_input",
                                   "seg_input.tif")
        self.inTilesSamplesFolder = os.path.join(IOTA2DIR, "data",
                                                 "references",
                                                 "ObiaClassification", "Input",
                                                 "tilesSamples")
        self.inLearnSamplesFolder = os.path.join(IOTA2DIR, "data",
                                                 "references",
                                                 "ObiaClassification", "Input",
                                                 "learningSamples")
        self.inModelFolder = os.path.join(IOTA2DIR, "data", "references",
                                          "ObiaClassification", "Input",
                                          "model")
        self.inStatsFolder = os.path.join(IOTA2DIR, "data", "references",
                                          "ObiaClassification", "Input",
                                          "stats")
        self.inClassifFolder = os.path.join(IOTA2DIR, "data", "references",
                                            "ObiaReassembleParts", "Input",
                                            "classif")
        self.classifOutputFolder = os.path.join(IOTA2DIR, "data", "references",
                                                "ObiaClassification", "Output",
                                                "classif")
        self.classifOutput2Folder = os.path.join(IOTA2DIR, "data",
                                                 "references",
                                                 "ObiaReassembleParts",
                                                 "Output", "classif")
        self.runs = 2

        # Tests directory
        self.test_working_directory = None
        if os.path.exists(self.iota2_tests_directory):
            shutil.rmtree(self.iota2_tests_directory)
        os.mkdir(self.iota2_tests_directory)

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
        self.test_working_directory = os.path.join(self.iota2_tests_directory,
                                                   test_name)
        if os.path.exists(self.test_working_directory):
            shutil.rmtree(self.test_working_directory)
        os.mkdir(self.test_working_directory)

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
    def test_obia_classification(self):
        """
        test classification for obia workflow
        """
        from iota2.Classification.ObiaClassification import launchObiaClassification
        from iota2.Common import IOTA2Directory
        from iota2.Common.FileUtils import serviceCompareVectorFile
        import glob

        # create IOTA2 directories
        IOTA2Directory.generate_directories(self.test_working_directory,
                                            check_inputs=False,
                                            obia_seg_path=self.in_seg)
        shutil.rmtree(os.path.join(self.test_working_directory,
                                   "tilesSamples"))
        shutil.rmtree(
            os.path.join(self.test_working_directory, "learningSamples"))
        shutil.rmtree(os.path.join(self.test_working_directory, "model"))
        shutil.rmtree(os.path.join(self.test_working_directory, "stats"))
        shutil.copytree(
            self.inTilesSamplesFolder,
            os.path.join(self.test_working_directory, "tilesSamples"))
        shutil.copytree(
            self.inLearnSamplesFolder,
            os.path.join(self.test_working_directory, "learningSamples"))
        shutil.copytree(self.inModelFolder,
                        os.path.join(self.test_working_directory, "model"))
        shutil.copytree(self.inStatsFolder,
                        os.path.join(self.test_working_directory, "stats"))

        # launch function
        runs = [run for run in range(0, self.runs)]
        for run in runs:
            print("launch obia")
            launchObiaClassification(
                run, 2, "codecg", self.test_working_directory,
                os.path.join(self.test_working_directory, "classif"))
            print("end launch")
        # assert
        shps_to_verify = glob.glob(
            os.path.join(self.classifOutputFolder, '*', '*.shp'))
        compare_vector = serviceCompareVectorFile()
        for shp in shps_to_verify:
            tile = os.path.basename(shp).split('_')[0]
            out_shp = os.path.join(self.test_working_directory, "classif",
                                   tile, os.path.basename(shp))
            same = compare_vector.testSameShapefiles(shp, out_shp)
            self.assertTrue(
                same,
                msg="Splitting learning samples with segmentation  failed")

    def test_obia_reassemble_parts(self):
        """
        test reassemble parts to produce files suitable for standard worflow that follows classification (mosaic)
        """
        from iota2.Classification.ObiaClassification import reassembleParts
        from iota2.Common import IOTA2Directory

        from iota2.Common.FileUtils import serviceCompareImageFile
        import glob

        tiles = "T38KPD T38KPE".split(" ")
        # create IOTA2 directories
        IOTA2Directory.generate_directories(self.test_working_directory,
                                            check_inputs=False,
                                            obia_seg_path=self.in_seg)
        shutil.rmtree(os.path.join(self.test_working_directory, "classif"))
        shutil.rmtree(os.path.join(self.test_working_directory, "model"))
        shutil.copytree(self.inClassifFolder,
                        os.path.join(self.test_working_directory, "classif"))
        shutil.copytree(self.inModelFolder,
                        os.path.join(self.test_working_directory, "model"))

        # launch function
        runs = [run for run in range(0, self.runs)]
        for run in runs:
            reassembleParts(
                run, 2, tiles, "codecg", self.test_working_directory,
                self.in_seg,
                os.path.join(self.test_working_directory, "classif"))

        # assert
        tifs_to_verify = glob.glob(
            os.path.join(self.classifOutput2Folder, '*.tif'))
        compare_image = serviceCompareImageFile()
        for tif in tifs_to_verify:
            out_tif = os.path.join(self.test_working_directory, "classif",
                                   os.path.basename(tif))
            cmp_val = compare_image.gdalFileCompare(tif, out_tif)
            same = cmp_val == 0
            self.assertTrue(
                same,
                msg="Splitting learning samples with segmentation failed")
