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

from iota2.Common import FileUtils as fut


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
        from iota2.Sampling.SplitSamplesForOBIA import split_segmentation_by_tiles
        from iota2.Common import IOTA2Directory
        from iota2.Common import ServiceConfigFile as SCF
        from iota2.Common.FileUtils import serviceCompareVectorFile
        import glob

        # prepare test input
        # values readed from original config fiel self.config_test
        tiles = 'T38KPD T38KPE'.split(" ")
        epsg = 32738
        region_path = None  # No field for regionPath in file
        # cfg = SCF.serviceConfigFile(self.config_test)
        # cfg.setParam("chain", "outputPath",
        #            os.path.join(self.test_working_directory, "splitTest"))
        # cfg.setParam("chain", "OBIA_segmentation_path", self.in_seg)

        # create IOTA2 directories
        IOTA2Directory.generate_directories(self.test_working_directory,
                                            check_inputs=False,
                                            obia_seg_path=self.in_seg)
        shutil.rmtree(os.path.join(self.test_working_directory, "shapeRegion"))
        shutil.rmtree(os.path.join(self.test_working_directory, "envelope"))
        shutil.copytree(
            self.in_shapeRegionFolder,
            os.path.join(self.test_working_directory, "shapeRegion"))
        shutil.copytree(self.in_enveloppeFolder,
                        os.path.join(self.test_working_directory, "envelope"))
        shutil.copy(self.in_seg,
                    os.path.join(self.test_working_directory, "seg_input.tif"))
        segmentation = os.path.join(self.test_working_directory,
                                    "seg_input.tif")
        # launch function
        split_segmentation_by_tiles(self.test_working_directory,
                                    tiles,
                                    segmentation,
                                    epsg,
                                    os.path.join(self.test_working_directory,
                                                 "segmentation"),
                                    region_path=region_path,
                                    size=100)
        # assert
        shps_to_verify = glob.glob(
            os.path.join(self.splitTilesOutputFolder, '*', '*.shp'))
        compare_vector = serviceCompareVectorFile()
        for shp in shps_to_verify:
            tile = os.path.basename(shp).split('_')[0]
            out_shp = os.path.join(self.test_working_directory, "segmentation",
                                   tile, os.path.basename(shp))

            same = compare_vector.testSameShapefiles(shp, out_shp)
            self.assertTrue(
                same,
                msg="Splitting learning samples with segmentation  failed")

    def test_obia_learn_samples(self):
        """
        test intersecting learning samples with segments 
        (main function of formatSamplesToSegmentation step)
        """
        from iota2.Sampling.SplitSamplesForOBIA import format_sample_to_segmentation
        from iota2.Common import IOTA2Directory
        from iota2.Common.FileUtils import serviceCompareVectorFile
        import glob

        # prepare test input
        # cfg = SCF.serviceConfigFile(self.config_test)
        # cfg.setParam(
        #     "chain", "outputPath",
        #     os.path.join(self.test_working_directory,
        #                  "formatLearningSamplesTest"))
        region_tiles_seed = [(1, ['T38KPD', 'T38KPE'], 0),
                             (1, ['T38KPD', 'T38KPE'], 1), (2, ['T38KPD'], 0),
                             (2, ['T38KPD'], 1)]
        region_path = None
        # create IOTA2 directories
        IOTA2Directory.generate_directories(self.test_working_directory,
                                            check_inputs=False,
                                            obia_seg_path=self.in_seg)
        shutil.rmtree(os.path.join(self.test_working_directory, "shapeRegion"))
        shutil.rmtree(
            os.path.join(self.test_working_directory, "samplesSelection"))
        shutil.rmtree(os.path.join(self.test_working_directory,
                                   "segmentation"))
        shutil.copytree(
            self.in_shapeRegionFolder,
            os.path.join(self.test_working_directory, "shapeRegion"))
        shutil.copytree(
            self.in_samplesSelection,
            os.path.join(self.test_working_directory, "samplesSelection"))
        shutil.copytree(
            self.in_tiled_segmentation,
            os.path.join(self.test_working_directory, "segmentation"))

        # launch function
        for param in region_tiles_seed:
            format_sample_to_segmentation(self.test_working_directory,
                                          param,
                                          os.path.join(
                                              self.test_working_directory,
                                              "segmentation"),
                                          region_path=region_path)

        shps_to_verify = glob.glob(
            os.path.join(self.formatOutputFolder, '*.shp'))
        compare_vector = serviceCompareVectorFile()
        for shp in shps_to_verify:
            out_shp = os.path.join(self.test_working_directory, "segmentation",
                                   os.path.basename(shp))

            same = compare_vector.testSameShapefiles(shp, out_shp)
            self.assertTrue(
                same,
                msg="Splitting learning samples with segmentation  failed")
