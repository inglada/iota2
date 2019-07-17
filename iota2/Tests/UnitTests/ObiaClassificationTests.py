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

# python -m unittest splitSegmentationByTilesTests

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

IOTA2_SCRIPTS = IOTA2DIR + "/scripts"
sys.path.append(IOTA2_SCRIPTS)

from Common import FileUtils as fut

class iota_testObiaClassification(unittest.TestCase):
    # before launching tests
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.group_test_name = "iota_testObiaClassification"
        self.iota2_tests_directory = os.path.join(IOTA2DIR, "data", self.group_test_name)
        self.all_tests_ok = []

        # References
        self.config_test = os.path.join(IOTA2DIR, "data", "references",
                                     "ObiaClassification",
                                     "config_obia.cfg")
        self.in_seg = os.path.join(IOTA2DIR, "data", "references",
                                     "ObiaReassembleParts", "Input",
                                     "seg_input","seg_input.tif")
        self.inTilesSamplesFolder = os.path.join(IOTA2DIR, "data", "references",
                                     "ObiaClassification", "Input",
                                     "tilesSamples")
        self.inLearnSamplesFolder = os.path.join(IOTA2DIR, "data", "references",
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
        self.classifOutput2Folder = os.path.join(IOTA2DIR, "data", "references",
                                     "ObiaReassembleParts", "Output",
                                     "classif")
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
        self.test_working_directory = os.path.join(self.iota2_tests_directory, test_name)
        if os.path.exists(self.test_working_directory):
            shutil.rmtree(self.test_working_directory)
        os.mkdir(self.test_working_directory)

    def list2reason(self, exc_list):
        if exc_list and exc_list[-1][0] is self:
            return exc_list[-1][1]

    # after launching a test, remove test's data if test succeed
    def tearDown(self):
        result = getattr(self, '_outcomeForDoCleanups', self._resultForDoCleanups)
        error = self.list2reason(result.errors)
        failure = self.list2reason(result.failures)
        test_ok = not error and not failure
        self.all_tests_ok.append(test_ok)
        if test_ok:
            shutil.rmtree(self.test_working_directory)

    # Tests definitions
    def test_obia_classification(self):
        """
        test classification for obia workflow
        """
        from Classification.ObiaClassification import launchObiaClassification
        from Common import IOTA2Directory
        from Common import ServiceConfigFile as SCF
        from Common.FileUtils import serviceCompareVectorFile
        import glob

        # prepare test input
        cfg = SCF.serviceConfigFile(self.config_test)
        cfg.setParam("chain", "outputPath", os.path.join(self.test_working_directory, "ObiaClassificationTest"))

        # create IOTA2 directories
        IOTA2Directory.GenerateDirectories(cfg)
        shutil.rmtree(os.path.join(self.test_working_directory, "ObiaClassificationTest", "tilesSamples"))
        shutil.rmtree(os.path.join(self.test_working_directory, "ObiaClassificationTest", "learningSamples"))
        shutil.rmtree(os.path.join(self.test_working_directory, "ObiaClassificationTest", "model"))
        shutil.rmtree(os.path.join(self.test_working_directory, "ObiaClassificationTest", "stats"))
        shutil.copytree(self.inTilesSamplesFolder, os.path.join(self.test_working_directory, "ObiaClassificationTest", "tilesSamples"))
        shutil.copytree(self.inLearnSamplesFolder, os.path.join(self.test_working_directory, "ObiaClassificationTest", "learningSamples"))
        shutil.copytree(self.inModelFolder, os.path.join(self.test_working_directory, "ObiaClassificationTest", "model"))
        shutil.copytree(self.inStatsFolder, os.path.join(self.test_working_directory, "ObiaClassificationTest", "stats"))

        # launch function
        runs = [run for run in range(0, self.runs)]
        for run in runs :
            launchObiaClassification(run, 2, cfg, os.path.join(self.test_working_directory,"ObiaClassificationTest", "classif"))

        # assert
        shps_to_verify = glob.glob(os.path.join(self.classifOutputFolder,'*','*.shp'))
        compareVector = serviceCompareVectorFile()
        for shp in shps_to_verify:
            tile = os.path.basename(shp).split('_')[0]
            outShp = os.path.join(self.test_working_directory, "ObiaClassificationTest", "classif", tile, os.path.basename(shp))
            same = compareVector.testSameShapefiles(shp, outShp)
            self.assertTrue(same, msg="Splitting learning samples with segmentation  failed")

    def test_obia_reassemble_parts(self):
        """
        test reassemble parts to produce files suitable for standard worflow that follows classification (mosaic)
        """
        from Classification.ObiaClassification import reassembleParts
        from Common import IOTA2Directory
        from Common import ServiceConfigFile as SCF
        from Common.FileUtils import serviceCompareImageFile
        import glob

        # prepare test input
        cfg = SCF.serviceConfigFile(self.config_test)
        cfg.setParam("chain", "outputPath", os.path.join(self.test_working_directory, "ObiaReassembleTest"))
        cfg.setParam("chain", "OBIA_segmentation_path", self.in_seg)

        # create IOTA2 directories
        IOTA2Directory.GenerateDirectories(cfg)
        shutil.rmtree(os.path.join(self.test_working_directory, "ObiaReassembleTest", "classif"))
        shutil.rmtree(os.path.join(self.test_working_directory, "ObiaReassembleTest", "model"))
        shutil.copytree(self.inClassifFolder, os.path.join(self.test_working_directory, "ObiaReassembleTest", "classif"))
        shutil.copytree(self.inModelFolder, os.path.join(self.test_working_directory, "ObiaReassembleTest", "model"))

        # launch function
        runs = [run for run in range(0, self.runs)]
        for run in runs :
            reassembleParts(run, 2, cfg, os.path.join(self.test_working_directory, "ObiaReassembleTest", "classif"))

        # assert
        tifs_to_verify = glob.glob(os.path.join(self.classifOutput2Folder,'*.tif'))
        compareImage = serviceCompareImageFile()
        for tif in tifs_to_verify:
            outTif = os.path.join(self.test_working_directory, "ObiaReassembleTest", "classif", os.path.basename(tif))
            nb = compareImage.gdalFileCompare(tif, outTif)
            if nb == 0: 
                same = True
            else :
                same = False
            self.assertTrue(same, msg="Splitting learning samples with segmentation  failed")