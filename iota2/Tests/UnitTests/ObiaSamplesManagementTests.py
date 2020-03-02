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

# python -m unittest ObiaSamplesManagementTests

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


class iota_testObiaFormatSamples(unittest.TestCase):
    # before launching tests
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.group_test_name = "iota_testObiaFormatSamples"
        self.iota2_tests_directory = os.path.join(IOTA2DIR, "data",
                                                  self.group_test_name)
        self.all_tests_ok = []

        # References
        self.config_test = os.path.join(IOTA2DIR, "data", "references",
                                        "ObiaSplitSegmentationByTiles",
                                        "config_obia.cfg")
        self.in_seg = os.path.join(IOTA2DIR, "data", "references",
                                   "ObiaSplitSegmentationByTiles", "Input",
                                   "seg_input", "seg_input.tif")
        self.in_shapeRegionFolder = os.path.join(
            IOTA2DIR, "data", "references", "ObiaSplitSegmentationByTiles",
            "Input", "shapeRegion")
        self.in_enveloppeFolder = os.path.join(IOTA2DIR, "data", "references",
                                               "ObiaSplitSegmentationByTiles",
                                               "Input", "envelope")
        self.in_samplesSelection = os.path.join(IOTA2DIR, "data", "references",
                                                "ObiaLearningSamples", "Input",
                                                "samplesSelection")
        self.in_tiled_segmentation = os.path.join(IOTA2DIR, "data",
                                                  "references",
                                                  "ObiaLearningSamples",
                                                  "Input", "segmentation")
        self.splitTilesOutputFolder = os.path.join(
            IOTA2DIR, "data", "references", "ObiaSplitSegmentationByTiles",
            "Output", "segmentation")
        self.formatOutputFolder = os.path.join(IOTA2DIR, "data", "references",
                                               "ObiaLearningSamples", "Output",
                                               "segmentation")

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
        ok = not error and not failure

        self.all_tests_ok.append(ok)
        if ok:
            shutil.rmtree(self.test_working_directory)

    # Tests definitions
    def test_split_segmentation(self):
        """
        test spliting segmentation by tiles and regions(main function of splitSegmentationByTiles step)
        """
        from Sampling.SplitSamplesForOBIA import split_segmentation_by_tiles
        from Common import IOTA2Directory
        from Common import ServiceConfigFile as SCF
        from Common.FileUtils import serviceCompareVectorFile
        import glob

        # prepare test input
        cfg = SCF.serviceConfigFile(self.config_test)
        cfg.setParam("chain", "outputPath",
                     os.path.join(self.test_working_directory, "splitTest"))
        cfg.setParam("chain", "OBIA_segmentation_path", self.in_seg)

        # create IOTA2 directories
        IOTA2Directory.GenerateDirectories(cfg, check_inputs=False)
        shutil.rmtree(
            os.path.join(self.test_working_directory, "splitTest",
                         "shapeRegion"))
        shutil.rmtree(
            os.path.join(self.test_working_directory, "splitTest", "envelope"))
        shutil.copytree(
            self.in_shapeRegionFolder,
            os.path.join(self.test_working_directory, "splitTest",
                         "shapeRegion"))
        shutil.copytree(
            self.in_enveloppeFolder,
            os.path.join(self.test_working_directory, "splitTest", "envelope"))
        shutil.copy(
            self.in_seg,
            os.path.join(self.test_working_directory, "splitTest",
                         "seg_input.tif"))
        cfg.setParam(
            "chain", "OBIA_segmentation_path",
            os.path.join(self.test_working_directory, "splitTest",
                         "seg_input.tif"))
        # launch function
        split_segmentation_by_tiles(
            cfg,
            os.path.join(self.test_working_directory, "splitTest",
                         "seg_input.tif"),
            os.path.join(self.test_working_directory, "splitTest",
                         "segmentation"), 100)
        # assert
        shps_to_verify = glob.glob(
            os.path.join(self.splitTilesOutputFolder, '*', '*.shp'))
        compareVector = serviceCompareVectorFile()
        for shp in shps_to_verify:
            tile = os.path.basename(shp).split('_')[0]
            outShp = os.path.join(self.test_working_directory, "splitTest",
                                  "segmentation", tile, os.path.basename(shp))

            same = compareVector.testSameShapefiles(shp, outShp)
            self.assertTrue(
                same,
                msg="Splitting learning samples with segmentation  failed")

    def test_obia_learn_samples(self):
        """
        test intersecting learning samples with segments (main function of formatSamplesToSegmentation step)
        """
        from Sampling.SplitSamplesForOBIA import format_sample_to_segmentation
        from Common import IOTA2Directory
        from Common import ServiceConfigFile as SCF
        from Common.FileUtils import serviceCompareVectorFile
        from Sampling import SamplesMerge as samples_merge
        import glob

        # prepare test input
        cfg = SCF.serviceConfigFile(self.config_test)
        cfg.setParam(
            "chain", "outputPath",
            os.path.join(self.test_working_directory,
                         "formatLearningSamplesTest"))
        region_tiles_seed = [(1, ['T38KPD', 'T38KPE'], 0),
                             (1, ['T38KPD', 'T38KPE'], 1), (2, ['T38KPD'], 0),
                             (2, ['T38KPD'], 1)]

        # create IOTA2 directories
        IOTA2Directory.GenerateDirectories(cfg, check_inputs=False)
        shutil.rmtree(
            os.path.join(self.test_working_directory,
                         "formatLearningSamplesTest", "shapeRegion"))
        shutil.rmtree(
            os.path.join(self.test_working_directory,
                         "formatLearningSamplesTest", "samplesSelection"))
        shutil.rmtree(
            os.path.join(self.test_working_directory,
                         "formatLearningSamplesTest", "segmentation"))
        shutil.copytree(
            self.in_shapeRegionFolder,
            os.path.join(self.test_working_directory,
                         "formatLearningSamplesTest", "shapeRegion"))
        shutil.copytree(
            self.in_samplesSelection,
            os.path.join(self.test_working_directory,
                         "formatLearningSamplesTest", "samplesSelection"))
        shutil.copytree(
            self.in_tiled_segmentation,
            os.path.join(self.test_working_directory,
                         "formatLearningSamplesTest", "segmentation"))

        #launch function
        for x in region_tiles_seed:
            format_sample_to_segmentation(
                cfg, x,
                os.path.join(self.test_working_directory,
                             "formatLearningSamplesTest", "segmentation"))

        shps_to_verify = glob.glob(
            os.path.join(self.formatOutputFolder, '*.shp'))
        compareVector = serviceCompareVectorFile()
        for shp in shps_to_verify:
            outShp = os.path.join(self.test_working_directory,
                                  "formatLearningSamplesTest", "segmentation",
                                  os.path.basename(shp))

            same = compareVector.testSameShapefiles(shp, outShp)
            self.assertTrue(
                same,
                msg="Splitting learning samples with segmentation  failed")
