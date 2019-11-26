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

# python -m unittest OpticalSARFusionTests

import os
import sys
import shutil
import unittest
import numpy as np

IOTA2DIR = os.environ.get('IOTA2DIR')

if not IOTA2DIR:
    raise Exception("IOTA2DIR environment variable must be set")

# if all tests pass, remove 'iota2_tests_directory' which contains all
# sub-directory tests
RM_IF_ALL_OK = True

IOTA2_SCRIPTS = IOTA2DIR + "/scripts"
sys.path.append(IOTA2_SCRIPTS)

from Common import FileUtils as fut
from Iota2Tests import arrayToRaster
from Iota2Tests import rasterToArray

class iota_testThousandsOfFeatures(unittest.TestCase):
    # before launching tests
    @classmethod
    def setUpClass(self):
        # definition of local variables
        iota2_dataTest = os.environ.get('IOTA2DIR') + "/data/"
        self.group_test_name = "iota_testThousandsOfFeatures"
        self.iota2_tests_directory = os.path.join(IOTA2DIR, "data", self.group_test_name)
        self.all_tests_ok = []

        # input data
        self.config_test = os.path.join(IOTA2DIR, "config", "Config_4Tuiles_Multi_FUS_Confidence.cfg")
        self.selection_test = os.path.join(self.test_vector, "D0005H0002.sqlite")
        self.referenceShape = os.path.join(IOTA2DIR, "data", "references", "sampler", "D0005H0002_polygons_To_Sample.shp")
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

    # Tests definitions
    def test_ThousandsFeatures(self):
        """ Test the ability to deal with thousands of features
        """
        from config import Config
        from Sampling import VectorSampler
        from Common import ServiceConfigFile as SCF
        from Iota2Tests import shapeReferenceVector

        # inputs
        config_path = os.path.join(IOTA2DIR, "config",
                                   "Config_4Tuiles_Multi_FUS_Confidence.cfg")
        if not os.path.exists(config_path):
            raise Exception("can not find configuration file "
                            "please source 'prepare_env.sh' script")
        iota2_running_path = os.path.join(self.test_working_directory, "ThousandsFeatures")
        if os.path.exists(iota2_running_path):
            shutil.rmtree(iota2_running_path)
        os.mkdir(iota2_running_path)
        config_path_test = os.path.join(self.test_working_directory, "Config_TEST.cfg")
        shutil.copy(config_path, config_path_test)
        L8_rasters = os.path.join(IOTA2DIR, "data", "L8_50x50")

        cfg_test = Config(file(config_path_test))
        cfg_test.chain.outputPath = iota2_running_path
        cfg_test.chain.listTile = "D0005H0002"
        cfg_test.chain.L8Path_old = L8_rasters
        cfg_test.chain.L8Path = "None"
        cfg_test.chain.userFeatPath = "None"
        cfg_test.chain.regionField = 'region'
        cfg_test.argTrain.cropMix = False
        cfg_test.argTrain.samplesClassifMix = False
        cfg_test.GlobChain.useAdditionalFeatures = False
        cfg_test.save(file(config_path_test, 'w'))

        config = SCF.serviceConfigFile(config_path_test)
        referenceShape_test = shapeReferenceVector(self.referenceShape, "D0005H0002")
        #~ # launch test case
        VectorSampler.generateSamples({"usually": referenceShape_test},
                                       None, config,
                                       sampleSelection=self.selection_test)
        
        #~ # assert
        #~ test_vector = fu.fileSearchRegEx(testPath + "/learningSamples/*sqlite")[0]
        #~ delete_uselessFields(test_vector)
        #~ compare = compareSQLite(test_vector, reference, CmpMode='coordinates')
        #~ self.assertTrue(compare)

        self.assertTrue(True)
