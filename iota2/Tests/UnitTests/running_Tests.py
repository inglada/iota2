#!/usr/bin/env python3
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

# python -m unittest running_Tests
"""
Tests dedicated to launch iota2 runs
"""
import os
import sys
import shutil
import unittest

from iota2.Common.Utils import run

IOTA2DIR = os.environ.get('IOTA2DIR')

if not IOTA2DIR:
    raise Exception("IOTA2DIR environment variable must be set")

# if all tests pass, remove 'iota2_tests_directory' which contains all
# sub-directory tests
RM_IF_ALL_OK = True

IOTA2_SCRIPTS = os.path.join(IOTA2DIR, "iota2")
sys.path.append(IOTA2_SCRIPTS)


class iota_tests_runs_case(unittest.TestCase):
    """
    Tests dedicated to launch iota2 runs
    """
    # before launching tests
    @classmethod
    def setUpClass(cls):
        # definition of local variables
        cls.group_test_name = "iota_tests_runs_case"
        cls.iota2_tests_directory = os.path.join(IOTA2DIR, "data",
                                                 cls.group_test_name)
        cls.all_tests_ok = []

        # input data
        cls.config_ref = os.path.join(IOTA2DIR, "data", "references",
                                      "running_iota2", "i2_config.cfg")
        cls.ground_truth_path = os.path.join(IOTA2DIR, "data", "references",
                                             "running_iota2",
                                             "ground_truth.shp")
        cls.nomenclature_path = os.path.join(IOTA2DIR, "data", "references",
                                             "running_iota2",
                                             "nomenclature.txt")
        cls.color_path = os.path.join(IOTA2DIR, "data", "references",
                                      "running_iota2", "color.txt")
        # Tests directory
        cls.test_working_directory = None
        if os.path.exists(cls.iota2_tests_directory):
            shutil.rmtree(cls.iota2_tests_directory)
        os.mkdir(cls.iota2_tests_directory)

    @classmethod
    def tearDownClass(cls):
        """after launching all tests"""
        print("{} ended".format(cls.group_test_name))
        if RM_IF_ALL_OK and all(cls.all_tests_ok):
            shutil.rmtree(cls.iota2_tests_directory)

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
        """list2reason"""
        out = None
        if exc_list and exc_list[-1][0] is self:
            out = exc_list[-1][1]
        return out

    def tearDown(self):
        """after launching a test, remove test's data if test succeed"""
        result = self.defaultTestResult()
        self._feedErrorsToResult(result, self._outcome.errors)
        error = self.list2reason(result.errors)
        failure = self.list2reason(result.failures)
        ok_test = not error and not failure

        self.all_tests_ok.append(ok_test)
        if ok_test:
            shutil.rmtree(self.test_working_directory)

    # Tests definitions
    def test_s2_theia_run(self):
        """
        Tests iota2's run using s2 (theia format)
        """
        from config import Config
        from iota2.Common.FileUtils import FileSearch_AND
        import iota2.Tests.UnitTests.tests_utils.tests_utils_rasters as TUR
        import iota2.Tests.UnitTests.tests_utils.tests_utils_iota2 as TUI
        # prepare inputs data
        tile_name = "T31TCJ"
        running_output_path = os.path.join(self.test_working_directory,
                                           "test_results")
        fake_s2_theia_dir = os.path.join(self.test_working_directory,
                                         "s2_data")
        TUR.generate_fake_s2_data(fake_s2_theia_dir,
                                  tile_name,
                                  ["20200101", "20200112", "20200127"],
                                  res=10.0)
        config_test = os.path.join(self.test_working_directory,
                                   "i2_config_s2_l2a.cfg")
        shutil.copy(self.config_ref, config_test)
        cfg_test = Config(open(config_test))
        cfg_test.chain.outputPath = running_output_path
        cfg_test.chain.S2Path = fake_s2_theia_dir
        cfg_test.chain.dataField = "code"
        cfg_test.chain.listTile = tile_name
        cfg_test.chain.groundTruth = self.ground_truth_path
        cfg_test.chain.nomenclaturePath = self.nomenclature_path
        cfg_test.chain.colorTable = self.color_path
        cfg_test.save(open(config_test, 'w'))

        # Launch the chain
        TUI.iota2_test_launcher(config_test)
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "Classif_Seed_0_ColorIndexed.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "Classif_Seed_0.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "Confidence_Seed_0.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "Confusion_Matrix_Classif_Seed_0.png"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "diff_seed_0.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "PixelsValidity.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "RESULTS.txt"))

    def test_s2_s2c_run(self):
        """
        Tests iota2's run using s2 (peps format)
        """
        from config import Config
        from iota2.Common.FileUtils import FileSearch_AND
        import iota2.Tests.UnitTests.tests_utils.tests_utils_rasters as TUR
        import iota2.Tests.UnitTests.tests_utils.tests_utils_iota2 as TUI
        # prepare inputs data
        tile_name = "T31TCJ"
        mtd_files = [
            os.path.join(IOTA2DIR, "data", "MTD_MSIL2A_20190501.xml"),
            os.path.join(IOTA2DIR, "data", "MTD_MSIL2A_20190506.xml")
        ]
        running_output_path = os.path.join(self.test_working_directory,
                                           "test_results")
        fake_s2_s2c_dir = os.path.join(self.test_working_directory,
                                       "s2_s2c_data")

        TUR.generate_fake_s2_s2c_data(
            fake_s2_s2c_dir,
            tile_name,
            mtd_files,
            res=10.0,
            fake_raster=TUR.fun_array("iota2_binary"),
            fake_scene_classification=1 + TUR.fun_array("iota2_binary") * 2,
            origin_x=566377.0,
            origin_y=6284029.0,
            epsg_code=2154)

        config_test = os.path.join(self.test_working_directory,
                                   "i2_config_s2_s2c.cfg")
        shutil.copy(self.config_ref, config_test)
        cfg_test = Config(open(config_test))
        cfg_test.chain.outputPath = running_output_path
        cfg_test.chain.S2_S2C_Path = fake_s2_s2c_dir
        cfg_test.chain.dataField = "code"
        cfg_test.chain.listTile = tile_name
        cfg_test.chain.groundTruth = self.ground_truth_path
        cfg_test.chain.nomenclaturePath = self.nomenclature_path
        cfg_test.chain.colorTable = self.color_path
        cfg_test.save(open(config_test, 'w'))

        # Launch the chain
        TUI.iota2_test_launcher(config_test)

        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "Classif_Seed_0_ColorIndexed.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "Classif_Seed_0.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "Confidence_Seed_0.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "Confusion_Matrix_Classif_Seed_0.png"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "diff_seed_0.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "PixelsValidity.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "RESULTS.txt"))

    def test_l8_run(self):
        """
        Tests iota2's run using l8 (theia format)
        """
        from config import Config
        from iota2.Common.FileUtils import FileSearch_AND
        import iota2.Tests.UnitTests.tests_utils.tests_utils_rasters as TUR
        import iota2.Tests.UnitTests.tests_utils.tests_utils_iota2 as TUI
        # prepare inputs data
        tile_name = "T31TCJ"
        running_output_path = os.path.join(self.test_working_directory,
                                           "test_results")
        fake_l8_theia_dir = os.path.join(self.test_working_directory,
                                         "l8_data")
        TUR.generate_fake_l8_data(fake_l8_theia_dir,
                                  tile_name,
                                  ["20200101", "20200112", "20200127"],
                                  res=30.0)
        config_test = os.path.join(self.test_working_directory,
                                   "i2_config_l8.cfg")
        shutil.copy(self.config_ref, config_test)
        cfg_test = Config(open(config_test))
        cfg_test.chain.outputPath = running_output_path
        cfg_test.chain.L8Path = fake_l8_theia_dir
        cfg_test.chain.dataField = "code"
        cfg_test.chain.listTile = tile_name
        cfg_test.chain.groundTruth = self.ground_truth_path
        cfg_test.chain.nomenclaturePath = self.nomenclature_path
        cfg_test.chain.colorTable = self.color_path
        cfg_test.chain.spatialResolution = 30
        cfg_test.save(open(config_test, 'w'))

        # Launch the chain
        TUI.iota2_test_launcher(config_test)

        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "Classif_Seed_0_ColorIndexed.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "Classif_Seed_0.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "Confidence_Seed_0.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "Confusion_Matrix_Classif_Seed_0.png"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "diff_seed_0.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "PixelsValidity.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "RESULTS.txt"))

    def test_l8_old_run(self):
        """
        Tests iota2's run using l8 (peps format)
        """
        from config import Config
        from iota2.Common.FileUtils import FileSearch_AND
        import iota2.Tests.UnitTests.tests_utils.tests_utils_rasters as TUR
        import iota2.Tests.UnitTests.tests_utils.tests_utils_iota2 as TUI
        # prepare inputs data
        tile_name = "D0005H0002"
        running_output_path = os.path.join(self.test_working_directory,
                                           "test_results")
        fake_l8_old_dir = os.path.join(self.test_working_directory,
                                       "l8_old_data")
        TUR.generate_fake_l8_old_data(fake_l8_old_dir,
                                      tile_name,
                                      ["20200101", "20200112", "20200127"],
                                      res=30.0)
        config_test = os.path.join(self.test_working_directory,
                                   "i2_config_l8_old.cfg")
        shutil.copy(self.config_ref, config_test)
        cfg_test = Config(open(config_test))
        cfg_test.chain.outputPath = running_output_path
        cfg_test.chain.L8Path_old = fake_l8_old_dir
        cfg_test.chain.dataField = "code"
        cfg_test.chain.listTile = tile_name
        cfg_test.chain.groundTruth = self.ground_truth_path
        cfg_test.chain.nomenclaturePath = self.nomenclature_path
        cfg_test.chain.colorTable = self.color_path
        cfg_test.chain.spatialResolution = 30
        cfg_test.save(open(config_test, 'w'))

        # Launch the chain
        TUI.iota2_test_launcher(config_test)

        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "Classif_Seed_0_ColorIndexed.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "Classif_Seed_0.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "Confidence_Seed_0.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "Confusion_Matrix_Classif_Seed_0.png"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "diff_seed_0.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "PixelsValidity.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "RESULTS.txt"))

    def test_l5_old_run(self):
        """
        Tests iota2's run using l5 (peps format)
        """
        from config import Config
        from iota2.Common.FileUtils import FileSearch_AND
        import iota2.Tests.UnitTests.tests_utils.tests_utils_rasters as TUR
        import iota2.Tests.UnitTests.tests_utils.tests_utils_iota2 as TUI
        # prepare inputs data
        tile_name = "D0005H0002"
        running_output_path = os.path.join(self.test_working_directory,
                                           "test_results")
        fake_l5_old_dir = os.path.join(self.test_working_directory,
                                       "l5_old_data")
        TUR.generate_fake_l5_old_data(fake_l5_old_dir,
                                      tile_name,
                                      ["20200101", "20200112", "20200127"],
                                      res=30.0)
        config_test = os.path.join(self.test_working_directory,
                                   "i2_config_l5_old.cfg")
        shutil.copy(self.config_ref, config_test)
        cfg_test = Config(open(config_test))
        cfg_test.chain.outputPath = running_output_path
        cfg_test.chain.L5Path_old = fake_l5_old_dir
        cfg_test.chain.dataField = "code"
        cfg_test.chain.listTile = tile_name
        cfg_test.chain.groundTruth = self.ground_truth_path
        cfg_test.chain.nomenclaturePath = self.nomenclature_path
        cfg_test.chain.colorTable = self.color_path
        cfg_test.chain.spatialResolution = 30
        cfg_test.save(open(config_test, 'w'))

        # Launch the chain
        TUI.iota2_test_launcher(config_test)

        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "Classif_Seed_0_ColorIndexed.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "Classif_Seed_0.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "Confidence_Seed_0.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "Confusion_Matrix_Classif_Seed_0.png"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "diff_seed_0.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "PixelsValidity.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "RESULTS.txt"))

    def test_s2_l3a_run(self):
        """
        Tests iota2's run using s2_l3a (theia format)
        """
        from config import Config
        from iota2.Common.FileUtils import FileSearch_AND
        import iota2.Tests.UnitTests.tests_utils.tests_utils_rasters as TUR
        import iota2.Tests.UnitTests.tests_utils.tests_utils_iota2 as TUI
        # prepare inputs data
        tile_name = "T31TCJ"
        running_output_path = os.path.join(self.test_working_directory,
                                           "test_results")
        fake_s2_l3a_dir = os.path.join(self.test_working_directory, "s2_data")
        TUR.generate_fake_s2_l3a_data(fake_s2_l3a_dir,
                                      tile_name,
                                      ["20200101", "20200112", "20200127"],
                                      res=10.0)
        config_test = os.path.join(self.test_working_directory,
                                   "i2_config_s2_l3a.cfg")
        shutil.copy(self.config_ref, config_test)
        cfg_test = Config(open(config_test))
        cfg_test.chain.outputPath = running_output_path
        cfg_test.chain.S2_L3A_Path = fake_s2_l3a_dir
        cfg_test.chain.dataField = "code"
        cfg_test.chain.listTile = tile_name
        cfg_test.chain.groundTruth = self.ground_truth_path
        cfg_test.chain.nomenclaturePath = self.nomenclature_path
        cfg_test.chain.colorTable = self.color_path
        cfg_test.save(open(config_test, 'w'))

        # Launch the chain
        TUI.iota2_test_launcher(config_test)

        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "Classif_Seed_0_ColorIndexed.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "Classif_Seed_0.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "Confidence_Seed_0.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "Confusion_Matrix_Classif_Seed_0.png"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "diff_seed_0.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "PixelsValidity.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "RESULTS.txt"))

    def test_s2_theia_custom_features_run(self):
        """
        Tests iota2's run using s2 (theia format) 
        and custom features
        """
        from config import Config
        from iota2.Common.FileUtils import FileSearch_AND
        import iota2.Tests.UnitTests.tests_utils.tests_utils_rasters as TUR
        import iota2.Tests.UnitTests.tests_utils.tests_utils_iota2 as TUI
        # prepare inputs data
        tile_name = "T31TCJ"
        running_output_path = os.path.join(self.test_working_directory,
                                           "test_results")
        fake_s2_theia_dir = os.path.join(self.test_working_directory,
                                         "s2_data")
        TUR.generate_fake_s2_data(fake_s2_theia_dir,
                                  tile_name,
                                  ["20200101", "20200112", "20200127"],
                                  res=10.0)
        config_test = os.path.join(self.test_working_directory,
                                   "i2_config_s2_l2a.cfg")
        shutil.copy(self.config_ref, config_test)
        cfg_test = Config(open(config_test))
        cfg_test.chain.outputPath = running_output_path
        cfg_test.chain.S2Path = fake_s2_theia_dir
        cfg_test.chain.dataField = "code"
        cfg_test.chain.listTile = tile_name
        cfg_test.chain.groundTruth = self.ground_truth_path
        cfg_test.chain.nomenclaturePath = self.nomenclature_path
        cfg_test.chain.colorTable = self.color_path
        cfg_test.external_features.module = os.path.join(
            IOTA2DIR, "data", "numpy_features", "user_custom_function.py")
        cfg_test.external_features.functions = "get_cari get_ndsi"
        cfg_test.external_features.number_of_chunks = 1
        cfg_test.save(open(config_test, 'w'))

        # Launch the chain
        TUI.iota2_test_launcher(config_test)
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "Classif_Seed_0_ColorIndexed.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "Classif_Seed_0.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "Confidence_Seed_0.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "Confusion_Matrix_Classif_Seed_0.png"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "diff_seed_0.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "PixelsValidity.tif"))
        self.assertTrue(
            FileSearch_AND(os.path.join(running_output_path, "final"), True,
                           "RESULTS.txt"))
