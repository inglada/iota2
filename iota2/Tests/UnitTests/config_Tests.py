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

# python -m unittest config_Tests
"""unittest s2 instance
"""
import os
import sys
import shutil
import unittest

IOTA2DIR = os.environ.get('IOTA2DIR')
RM_IF_ALL_OK = True


class iota2_test_config(unittest.TestCase):
    """Tests
    """
    #before launching tests
    @classmethod
    def setUpClass(cls):

        # definition of local variables
        cls.group_test_name = "iota2_test_config"
        cls.iota2_tests_directory = os.path.join(IOTA2DIR, "data",
                                                 cls.group_test_name)
        cls.all_tests_ok = []
        cls.test_working_directory = None
        if os.path.exists(cls.iota2_tests_directory):
            shutil.rmtree(cls.iota2_tests_directory)
        os.mkdir(cls.iota2_tests_directory)

        cls.config_test = os.path.join(
            IOTA2DIR, "config", "Config_4Tuiles_Multi_FUS_Confidence.cfg")

    # after launching tests
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
        #create directories
        test_name = self.id().split(".")[-1]
        self.test_working_directory = os.path.join(self.iota2_tests_directory,
                                                   test_name)
        if os.path.exists(self.test_working_directory):
            shutil.rmtree(self.test_working_directory)
        os.mkdir(self.test_working_directory)

    def list2reason(self, exc_list):
        """ list2reason
        """
        out = None
        if exc_list and exc_list[-1][0] is self:
            out = exc_list[-1][1]
        return out

    def tearDown(self):
        """ after launching a test, remove test's data if test succeed
        """
        if sys.version_info > (3, 4, 0):
            result = self.defaultTestResult()
            self._feedErrorsToResult(result, self._outcome.errors)
        else:
            result = getattr(self, '_outcomeForDoCleanups',
                             self._resultForDoCleanups)
        error = self.list2reason(result.errors)
        failure = self.list2reason(result.failures)
        test_ok = not (error or failure)

        self.all_tests_ok.append(test_ok)
        if test_ok:
            shutil.rmtree(self.test_working_directory)

    # Tests definitions
    def test_config_dictionaries(self):
        """check iota2_parameters class
        """
        from iota2.Common.ServiceConfigFile import iota2_parameters
        sensors_parameters = iota2_parameters(
            self.config_test).get_sensors_parameters("T31TCJ")
        self.assertTrue(len(sensors_parameters.keys()) == 3)
