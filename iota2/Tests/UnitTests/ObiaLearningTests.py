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

# python -m unittest ObiaLearningTests

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


class iota_testObiaLearning(unittest.TestCase):
    # before launching tests
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.group_test_name = "iota_testObiaLearning"
        self.iota2_tests_directory = os.path.join(IOTA2DIR, "data",
                                                  self.group_test_name)
        self.all_tests_ok = []

        # References
        self.config_test = os.path.join(IOTA2DIR, "data", "references",
                                        "ObiaUnskewModel", "config_obia.cfg")
        self.inLearnSamplesFolder = os.path.join(IOTA2DIR, "data",
                                                 "references",
                                                 "ObiaUnskewModel", "Input",
                                                 "learningSamples")
        self.statsOutputFolder = os.path.join(IOTA2DIR, "data", "references",
                                              "ObiaUnskewModel", "Output",
                                              "stats")
        self.modelOutputFolder = os.path.join(IOTA2DIR, "data", "references",
                                              "ObiaUnskewModel", "Output",
                                              "model")
        # used to activate obia mode
        self.in_seg = os.path.join(IOTA2DIR, "data", "references",
                                   "ObiaReassembleParts", "Input", "seg_input",
                                   "seg_input.tif")

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
    def test_unskew_model(self):
        """
        test unskew model for classification based on learning features
        """
        from iota2.Learning.ModelUnskew import launch_unskew
        from iota2.Common import IOTA2Directory
        from iota2.Common.FileUtils import serviceCompareText
        import glob

        # prepare test input
        region_tiles_seed = [(1, ['T38KPD', 'T38KPE'], 0),
                             (1, ['T38KPD', 'T38KPE'], 1), (2, ['T38KPD'], 0),
                             (2, ['T38KPD'], 1)]

        # create IOTA2 directories
        IOTA2Directory.generate_directories(self.test_working_directory,
                                            check_inputs=False,
                                            obia_seg_path=self.in_seg)
        shutil.rmtree(
            os.path.join(self.test_working_directory, "learningSamples"))
        shutil.copytree(
            self.inLearnSamplesFolder,
            os.path.join(self.test_working_directory, "learningSamples"))

        # launch function
        cmd_list = launch_unskew(region_tiles_seed,
                                 self.test_working_directory)
        for cmd in cmd_list:
            os.system(cmd)

        # assert
        xmls_to_verify = glob.glob(
            os.path.join(self.statsOutputFolder, '*.xml'))
        compare_text = serviceCompareText()
        for xml in xmls_to_verify:
            out_xml = os.path.join(self.test_working_directory, "stats",
                                   os.path.basename(xml))
            same = compare_text.testSameText(xml, out_xml)
            self.assertTrue(same, msg="segmentation split generation failed")

    def test_learn_model(self):
        """
        test producing learning model for classification
        """
        from iota2.Learning.ObiaTrainingCmd import launch_obia_train_model
        from iota2.Common import IOTA2Directory
        from iota2.Common.FileUtils import serviceCompareText
        import glob

        # prepare test input
        data_field = "codecg"
        region_seed_tile = [(1, ['T38KPD', 'T38KPE'], 0),
                            (1, ['T38KPD', 'T38KPE'], 1), (2, ['T38KPD'], 0),
                            (2, ['T38KPD'], 1)]

        # create IOTA2 directories
        IOTA2Directory.generate_directories(self.test_working_directory,
                                            check_inputs=False,
                                            obia_seg_path=self.in_seg)
        shutil.rmtree(
            os.path.join(self.test_working_directory, "learningSamples"))
        shutil.copytree(
            self.inLearnSamplesFolder,
            os.path.join(self.test_working_directory, "learningSamples"))

        # launch function
        cmd_list = launch_obia_train_model(
            self.test_working_directory, data_field, region_seed_tile,
            os.path.join(self.test_working_directory, "cmd", "train"),
            os.path.join(self.test_working_directory, "model"), "rf",
            ' -classifier.rf.min 5 -classifier.rf.max 10'
            ' -classifier.rf.nbtrees 400')
        for cmd in cmd_list:
            os.system(cmd)

        # assert
        xmls_to_verify = glob.glob(
            os.path.join(self.modelOutputFolder, '*.xml'))
        compareText = serviceCompareText()
        for xml in xmls_to_verify:
            outXml = os.path.join(self.test_working_directory,
                                  "LearnModelTest", "model",
                                  os.path.basename(xml))
            same = compareText.testSameText(xml, outXml)
            self.assertTrue(same, msg="segmentation split generation failed")
