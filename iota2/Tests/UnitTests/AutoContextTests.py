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

import os
import sys
import shutil
import unittest

IOTA2DIR = os.environ.get('IOTA2DIR')
RM_IF_ALL_OK = True

iota2_script = os.path.join(IOTA2DIR, "iota2")
sys.path.append(iota2_script)

from Common import FileUtils as fut

class iota_testAutoContext(unittest.TestCase):
    #before launching tests
    @classmethod
    def setUpClass(self):

        from Common.FileUtils import ensure_dir
        from TestsUtils import generate_fake_s2_data

        # definition of local variables
        self.group_test_name = "iota_testAutoContext"
        self.iota2_tests_directory = os.path.join(IOTA2DIR, "data", self.group_test_name)
        self.config_test = os.path.join(IOTA2DIR, "config", "Config_4Tuiles_Multi_FUS_Confidence.cfg")
        self.all_tests_ok = []
        self.test_working_directory = None
        if os.path.exists(self.iota2_tests_directory):
            shutil.rmtree(self.iota2_tests_directory)
        os.mkdir(self.iota2_tests_directory)

        # generate permanent fake data
        self.fake_data_dir = os.path.join(self.iota2_tests_directory, "fake_s2")
        ensure_dir(self.fake_data_dir)
        generate_fake_s2_data(self.fake_data_dir, "T31TCJ", ["20190909", "20190919", "20190929"])

    #after launching tests
    @classmethod
    def tearDownClass(self):
        print("{} ended".format(self.group_test_name))
        if RM_IF_ALL_OK and all(self.all_tests_ok):
            shutil.rmtree(self.iota2_tests_directory)

    #before launching a test
    def setUp(self):
        """
        create test environement (directories)
        """
        #create directories
        test_name = self.id().split(".")[-1]
        self.test_working_directory = os.path.join(self.iota2_tests_directory, test_name)
        if os.path.exists(self.test_working_directory):
            shutil.rmtree(self.test_working_directory)
        os.mkdir(self.test_working_directory)

    def list2reason(self, exc_list):
        if exc_list and exc_list[-1][0] is self:
            return exc_list[-1][1]

    #after launching a test, remove test's data if test succeed
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

    #Tests definitions
    def test_SLIC(self):
        """non-regression test, check if SLIC could be performed
        """
        from config import Config
        from Common import IOTA2Directory
        from Common import ServiceConfigFile as SCF
        from Segmentation import segmentation
        from Sensors.Sensors_container import Sensors_container
        from Common.FileUtils import FileSearch_AND
        
        tile_name = "T31TCJ"

        # config file
        config_path_test = os.path.join(self.test_working_directory, "Config_TEST.cfg")
        shutil.copy(self.config_test, config_path_test)

        S2ST_data = self.test_working_directory
        testPath = os.path.join(self.test_working_directory, "RUN")
        cfg_test = Config(open(config_path_test))
        cfg_test.chain.outputPath = testPath
        cfg_test.chain.listTile = "T31TCJ"
        cfg_test.chain.L8Path_old = "None"
        cfg_test.chain.L8Path = "None"
        cfg_test.chain.S2Path = self.fake_data_dir
        cfg_test.chain.S2_S2C_Path = "None"
        cfg_test.chain.userFeatPath = "None"
        cfg_test.chain.regionField = 'region'
        cfg_test.chain.enable_autoContext = True
        cfg_test.argTrain.cropMix = False
        cfg_test.argTrain.samplesClassifMix = False
        cfg_test.argTrain.annualClassesExtractionSource = None
        cfg_test.GlobChain.useAdditionalFeatures = False
        cfg_test.GlobChain.writeOutputs = False
        cfg_test.save(open(config_path_test, 'w'))

        cfg = SCF.serviceConfigFile(config_path_test)
        IOTA2Directory.GenerateDirectories(cfg)
        slic_working_dir = os.path.join(self.test_working_directory, "slic_tmp")
        sensors = Sensors_container(config_path_test, tile_name, None)
        sensors.sensors_preprocess()

        # Launch test
        segmentation.slicSegmentation(tile_name, config_path_test, ram=128, working_dir=slic_working_dir, force_spw=1)
        
        # as SLIC algorithm contains random variables, the raster's content could
        # not be tested
        self.assertTrue(len(FileSearch_AND(os.path.join(testPath,
                                                        "features",
                                                        tile_name,
                                                        "tmp"),
                                           True,
                                           "SLIC_{}".format(tile_name)))==1,
                        msg="SLIC algorithm failed")
    
    def test_train(self):
        """
        """
        #~ /home/uz/vincenta/IOTA2/data/references/formatting_vectors/Input/formattingVectors/T31TCJ.shp