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

class iota_testOpticalSARFusion(unittest.TestCase):
    # before launching tests
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.group_test_name = "iota_testOpticalSARFusion"
        self.iota2_tests_directory = os.path.join(IOTA2DIR, "data", self.group_test_name)
        self.all_tests_ok = []

        # input data
        self.config_test = os.path.join(IOTA2DIR, "config", "Config_4Tuiles_Multi_FUS_Confidence.cfg")
        # CSV files
        self.sar_confusion = os.path.join(IOTA2DIR, "data", "references", "sar_confusion.csv")
        self.opt_confusion = os.path.join(IOTA2DIR, "data", "references", "opt_confusion.csv")
        # SAR classification
        self.sar_classif = np.array([[11, 12, 31],
                                     [42, 51, 11],
                                     [11, 43, 11]][::-1])
        # Optical classification
        self.optical_classif = np.array([[12, 42, 31],
                                         [11, 43, 51],
                                         [43, 51, 42]][::-1])
        # SAR confidence
        self.sar_confidence = np.array([[1, 2, 3],
                                        [4, 5, 6],
                                        [7, 8, 9]])
        # Optical confidence
        self.optical_confidence = np.array([[1, 2, 3],
                                            [4, 5, 6],
                                            [7, 8, 9]])
        # ds choice map
        self.choice_map = np.array([[1, 2, 3],
                                    [4, 5, 6],
                                    [7, 8, 9]])
        # References
        self.ds_fusion_ref = np.array([[11, 42, 31],
                                       [42, 43, 11],
                                       [11, 51, 11]][::-1])
        self.parameter_ref = [{'sar_classif': '/classif/Classif_T31TCJ_model_1_seed_1_SAR.tif',
                               'opt_model': '/dataAppVal/bymodels/model_1_seed_1.csv',
                               'opt_classif': '/classif/Classif_T31TCJ_model_1_seed_1.tif',
                               'sar_model': '/dataAppVal/bymodels/model_1_seed_1_SAR.csv'},
                              {'sar_classif': '/classif/Classif_T31TCJ_model_1_seed_0_SAR.tif',
                               'opt_model': '/dataAppVal/bymodels/model_1_seed_0.csv',
                               'opt_classif': '/classif/Classif_T31TCJ_model_1_seed_0.tif',
                               'sar_model': '/dataAppVal/bymodels/model_1_seed_0_SAR.csv'}]
        # consts
        self.classif_seed_pos = 5
        self.classif_tile_pos = 1
        self.classif_model_pos = 3

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
    def test_fusion_parameters(self):
        """
        TEST : Fusion.dempster_shafer_fusion_parameters
        """
        from Classification import Fusion
        from Common import IOTA2Directory
        from Common import ServiceConfigFile as SCF

        # define inputs
        cfg = SCF.serviceConfigFile(self.config_test)
        iota2_dir = os.path.join(self.test_working_directory, "fusionTest")
        cfg.setParam('chain', 'outputPath', iota2_dir)

        IOTA2Directory.GenerateDirectories(cfg)
        iota2_ds_confusions_dir = os.path.join(iota2_dir, "dataAppVal", "bymodels")
        fut.ensure_dir(iota2_ds_confusions_dir)
        # generate some fake data
        nb_seed = 2
        for i in range(nb_seed):
            fake_classif_opt = os.path.join(iota2_dir, "classif", "Classif_T31TCJ_model_1_seed_{}.tif".format(i))
            fake_classif_sar = os.path.join(iota2_dir, "classif", "Classif_T31TCJ_model_1_seed_{}_SAR.tif".format(i))
            fake_confidence_opt = os.path.join(iota2_dir, "classif", "T31TCJ_model_1_confidence_seed_{}.tif".format(i))
            fake_confidence_sar = os.path.join(iota2_dir, "classif", "T31TCJ_model_1_confidence_seed_{}_SAR.tif".format(i))
            fake_model_confusion_sar = os.path.join(iota2_ds_confusions_dir, "model_1_seed_{}_SAR.csv".format(i))
            fake_model_confusion_opt = os.path.join(iota2_ds_confusions_dir, "model_1_seed_{}.csv".format(i))

            with open(fake_classif_opt, "w") as new_file:
                new_file.write("TEST")
            with open(fake_classif_sar, "w") as new_file:
                new_file.write("TEST")
            with open(fake_confidence_opt, "w") as new_file:
                new_file.write("TEST")
            with open(fake_confidence_sar, "w") as new_file:
                new_file.write("TEST")
            with open(fake_model_confusion_sar, "w") as new_file:
                new_file.write("TEST")
            with open(fake_model_confusion_opt, "w") as new_file:
                new_file.write("TEST")

        parameters_test = Fusion.dempster_shafer_fusion_parameters(iota2_dir)
        # test_parameters depend of execution environement, remove local path is necessary
        for param_group in parameters_test:
            for key, value in param_group.items():
                param_group[key] = value.replace(iota2_dir, "")
        # assert
        self.assertTrue(all(param_group_test == param_group_ref for param_group_test, param_group_ref in zip(parameters_test, self.parameter_ref)),
                        msg="input parameters generation failed")

    def test_perform_fusion(self):
        """
        TEST : Fusion.perform_fusion
        """
        from Classification import Fusion

        # define inputs
        sar_raster = os.path.join(self.test_working_directory, "Classif_T31TCJ_model_1_seed_0_SAR.tif")
        opt_raster = os.path.join(self.test_working_directory, "Classif_T31TCJ_model_1_seed_0.tif")
        arrayToRaster(self.sar_classif, sar_raster)
        arrayToRaster(self.optical_classif, opt_raster)

        fusion_dic = {"sar_classif": sar_raster,
                      "opt_classif": opt_raster,
                      "sar_model": self.sar_confusion,
                      "opt_model": self.opt_confusion}

        # launch function
        ds_fusion_test = Fusion.perform_fusion(fusion_dic, mob="precision",
                                               classif_model_pos=self.classif_model_pos,
                                               classif_tile_pos=self.classif_tile_pos,
                                               classif_seed_pos=self.classif_seed_pos,
                                               workingDirectory=None)
        # assert
        ds_fusion_test = rasterToArray(ds_fusion_test)
        self.assertTrue(np.allclose(self.ds_fusion_ref, ds_fusion_test),
                        msg="fusion of classifications failed")

    def test_fusion_choice(self):
        """
        TEST : Fusion.compute_fusion_choice
        """
        self.assertTrue(True)

    def test_confidence_fusion(self):
        """
        TEST : Fusion.compute_confidence_fusion
        """
        self.assertTrue(True)

    def test_ds_fusion(self):
        """
        TEST : Fusion.dempster_shafer_fusion
        """
        self.assertTrue(True)
