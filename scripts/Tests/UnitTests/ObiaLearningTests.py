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

class iota_testObiaLearning(unittest.TestCase):
    # before launching tests
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.group_test_name = "iota_testObiaLearning"
        self.iota2_tests_directory = os.path.join(IOTA2DIR, "data", self.group_test_name)
        self.all_tests_ok = []

        # References
        self.config_test = os.path.join(IOTA2DIR, "data", "references",
                                     "ObiaUnskewModel",
                                     "config_obia.cfg")
        self.inLearnSamplesFolder = os.path.join(IOTA2DIR, "data", "references",
                                     "ObiaUnskewModel", "Input",
                                     "learningSamples")
        self.statsOutputFolder = os.path.join(IOTA2DIR, "data", "references",
                                     "ObiaUnskewModel", "Output",
                                     "stats")
        self.modelOutputFolder = os.path.join(IOTA2DIR, "data", "references",
                                     "ObiaUnskewModel", "Output",
                                     "model")

        # Tests directory
        self.test_working_directory = None
        if os.path.exists(self.iota2_tests_directory):
            shutil.rmtree(self.iota2_tests_directory)
        os.mkdir(self.iota2_tests_directory)

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
    def test_unskew_model(self):
        """
        test unskew model for classification based on learning features
        """
        from Learning.ModelUnskew import launchUnskew
        from Common import IOTA2Directory
        from Common import ServiceConfigFile as SCF
        from Common.FileUtils import serviceCompareText
        import glob

        # prepare test input
        cfg = SCF.serviceConfigFile(self.config_test)
        cfg.setParam("chain", "outputPath", os.path.join(self.test_working_directory, "UnskewModelTest"))
        region_tiles_seed = [ (1,['T38KPD','T38KPE'],0) , (1,['T38KPD','T38KPE'],1) , (2,['T38KPD'],0) , (2,['T38KPD'],1) ]

        # create IOTA2 directories
        IOTA2Directory.GenerateDirectories(cfg)
        shutil.rmtree(os.path.join(self.test_working_directory, "UnskewModelTest", "learningSamples"))
        shutil.copytree(self.inLearnSamplesFolder, os.path.join(self.test_working_directory, "UnskewModelTest", "learningSamples"))

        # launch function
        cmd_list = launchUnskew(region_tiles_seed, cfg)
        for cmd in cmd_list:
            os.system(cmd)

        # assert
        xmls_to_verify = glob.glob(os.path.join(self.statsOutputFolder,'*.xml'))
        compareText = serviceCompareText()
        for xml in xmls_to_verify:
            outXml = os.path.join(self.test_working_directory, "UnskewModelTest", "stats",os.path.basename(xml))
            same = compareText.testSameText(xml, outXml)
            self.assertTrue(same, msg="segmentation split generation failed")

    def test_learn_model(self):
        """
        test producing learning model for classification
        """
        from Learning.ObiaTrainingCmd import launchObiaTrainModel
        from Common import IOTA2Directory
        from Common import ServiceConfigFile as SCF
        from Common.FileUtils import serviceCompareText
        import glob

        # prepare test input
        cfg = SCF.serviceConfigFile(self.config_test)
        cfg.setParam("chain", "outputPath", os.path.join(self.test_working_directory, "LearnModelTest"))
        output_path = cfg.getParam('chain', 'outputPath')
        data_field = cfg.getParam('chain', 'dataField')
        region_seed_tile = [ (1,['T38KPD','T38KPE'],0) , (1,['T38KPD','T38KPE'],1) , (2,['T38KPD'],0) , (2,['T38KPD'],1) ]

        # create IOTA2 directories
        IOTA2Directory.GenerateDirectories(cfg)
        shutil.rmtree(os.path.join(self.test_working_directory, "LearnModelTest", "learningSamples"))
        shutil.copytree(self.inLearnSamplesFolder, os.path.join(self.test_working_directory, "LearnModelTest", "learningSamples"))

        # launch function
        cmd_list = launchObiaTrainModel(cfg, 
                                       data_field,
                                       region_seed_tile,
                                       os.path.join(output_path, "cmd", "train"),
                                       os.path.join(output_path, "model"),
                                       os.path.join(self.test_working_directory, "model"))
        for cmd in cmd_list:
            os.system(cmd)

        # assert
        xmls_to_verify = glob.glob(os.path.join(self.modelOutputFolder,'*.xml'))
        compareText = serviceCompareText()
        for xml in xmls_to_verify:
            outXml = os.path.join(self.test_working_directory, "LearnModelTest", "model",os.path.basename(xml))
            same = compareText.testSameText(xml, outXml)
            self.assertTrue(same, msg="segmentation split generation failed")