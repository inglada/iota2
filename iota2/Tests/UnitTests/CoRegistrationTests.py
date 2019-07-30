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

# python -m unittest CoRegistrationTests

import os
import sys
import shutil
import unittest
import glob

IOTA2DIR = os.environ.get('IOTA2DIR')
RM_IF_ALL_OK = True

iota2_script = os.path.join(IOTA2DIR, "iota2")
sys.path.append(iota2_script)

from Common.Tools import CoRegister

class iota_testCoRegistration(unittest.TestCase):
    # before launching tests
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.group_test_name = "iota_testCoRegistration"
        self.iota2_tests_directory = os.path.join(IOTA2DIR, "data", self.group_test_name)
        self.all_tests_ok = []

        # References
        self.config_test = os.path.join(IOTA2DIR, "data", "config", "test_config_coregister.cfg")
        self.datadir = os.path.join(IOTA2DIR, "data", "references", "CoRegister", "sensor_data")

        # Tests directory
        self.test_working_directory = None
        if os.path.exists(self.iota2_tests_directory):
            shutil.rmtree(self.iota2_tests_directory)
        os.mkdir(self.iota2_tests_directory)
    
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

    # after launching all tests
    @classmethod
    def tearDownClass(self):
        print("{} ended".format(self.group_test_name))

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

    def test_fitnessScore_Coregister(self):
        """
        TEST 
        """
        expected = ['20170203', '20170223']
        output = [CoRegister.fitnessDateScore("20170216", os.path.join(self.datadir, "T38KPD"), 'S2'),
                  CoRegister.fitnessDateScore("20170216", os.path.join(self.datadir, "T38KPE"), 'S2')]
        self.assertTrue(all([ex == out for ex, out in zip(expected, output)]))

    def test_launch_CoRegister(self):
        """
        TEST
        """
        from config import Config
        from Common.FileUtils import ensure_dir

        test_config = os.path.join(self.test_working_directory, os.path.basename(self.config_test))
        shutil.copy(self.config_test, test_config)

        # prepare test's inputs
        datadir_test = os.path.join(self.test_working_directory, "input_data")
        shutil.copytree(self.datadir, datadir_test)

        cfg_coregister = Config(open(test_config))
        cfg_coregister.chain.outputPath = self.test_working_directory
        cfg_coregister.chain.S2Path = datadir_test
        cfg_coregister.save(open(test_config, 'w'))
        ensure_dir(os.path.join(self.test_working_directory, "features", "T38KPD"))

        # T38KPD's coregistration 
        CoRegister.launch_coregister("T38KPD", test_config, None, False)
        dateFolders = glob.glob(os.path.join(datadir_test, "T38KPD", "*"))
        geomsFiles = glob.glob(os.path.join(datadir_test, "T38KPD", "*", "*.geom"))
        # assert
        self.assertTrue(len(dateFolders)==len(geomsFiles))

        # T38KPE's coregistration
        ensure_dir(os.path.join(self.test_working_directory, "features", "T38KPE"))        
        CoRegister.launch_coregister("T38KPE", test_config, None, False)
        # assert
        dateFolders = glob.glob(os.path.join(datadir_test, "T38KPE", "*"))
        geomsFiles = glob.glob(os.path.join(datadir_test, "T38KPE", "*", "*.geom"))        
        self.assertTrue(len(dateFolders)==len(geomsFiles))
