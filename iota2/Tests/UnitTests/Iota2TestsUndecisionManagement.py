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
"""
Test of undecision_management for post classification fusion
"""
import os
import sys
import unittest
import shutil
from iota2.Common import ServiceConfigFile as SCF
RM_IF_ALL_OK = True
IOTA2DIR = os.environ.get('IOTA2DIR')


class iota_test_undecision_management(unittest.TestCase):
    "test undecision management in post classification fusion"

    @classmethod
    def setUpClass(cls):
        """
        Prepare constant for testing
        """
        cls.group_test_name = "iota_Iota2UndecisionManagement"
        cls.iota2_tests_directory = os.path.join(IOTA2DIR, "data",
                                                 cls.group_test_name)
        cls.all_tests_ok = []

        # Tests directory
        cls.test_working_directory = None
        if os.path.exists(cls.iota2_tests_directory):
            shutil.rmtree(cls.iota2_tests_directory)
        os.mkdir(cls.iota2_tests_directory)

    # after launching all tests
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
        # self.test_working_directory is the diretory dedicated to each tests
        # it changes for each tests
        test_name = self.id().split(".")[-1]
        self.test_working_directory = os.path.join(self.iota2_tests_directory,
                                                   test_name)
        if os.path.exists(self.test_working_directory):
            shutil.rmtree(self.test_working_directory)
        # os.mkdir(self.test_working_directory)

    def list2reason(self, exc_list):
        if exc_list and exc_list[-1][0] is self:
            return exc_list[-1][1]

    # after launching a test, remove test's data if test succeed
    def tearDown(self):
        if sys.version_info > (3, 4, 0):
            result = self.defaultTestResult()
            self._feedErrorsToResult(result, self._outcome.errors)
        else:
            result = getattr(self, "_outcomeForDoCleanups",
                             self._resultForDoCleanups)

        error = self.list2reason(result.errors)
        failure = self.list2reason(result.failures)
        ok = not (error or failure)

        self.all_tests_ok.append(ok)
        if ok:
            shutil.rmtree(self.test_working_directory)

    def test_undecision_management(self):
        """
        Test undecision_management
        """
        import filecmp
        from iota2.Classification import undecision_management as UM
        from iota2.Classification import Fusion as FUS
        from iota2.Common.Utils import run
        from iota2.Common import FileUtils as fut

        shutil.copytree(
            os.path.join(IOTA2DIR, "data", "references", "NoData", "Input",
                         "Classif"), self.test_working_directory)
        shutil.copytree(
            os.path.join(IOTA2DIR, "data", "references", "NoData", "Input",
                         "config_model"),
            os.path.join(self.test_working_directory, "config_model"))
        if not os.path.exists(
                os.path.join(self.test_working_directory, "cmd", "fusion")):
            os.makedirs(
                os.path.join(self.test_working_directory, "cmd", "fusion"))
        shutil.copy(
            os.path.join(self.test_working_directory, "classif",
                         "Classif_D0005H0002_model_1_seed_0.tif"),
            os.path.join(self.test_working_directory, "classif",
                         "Classif_D0005H0002_model_1f2_seed_0.tif"))
        shutil.copy(
            os.path.join(self.test_working_directory, "classif",
                         "Classif_D0005H0002_model_1_seed_0.tif"),
            os.path.join(self.test_working_directory, "classif",
                         "Classif_D0005H0002_model_1f1_seed_0.tif"))

        shutil.copy(
            os.path.join(self.test_working_directory, "classif",
                         "D0005H0002_model_1_confidence_seed_0.tif"),
            os.path.join(self.test_working_directory, "classif",
                         "D0005H0002_model_1f2_confidence_seed_0.tif"))
        shutil.copy(
            os.path.join(self.test_working_directory, "classif",
                         "D0005H0002_model_1_confidence_seed_0.tif"),
            os.path.join(self.test_working_directory, "classif",
                         "D0005H0002_model_1f1_confidence_seed_0.tif"))

        cmd_fus = FUS.fusion(
            os.path.join(self.test_working_directory, "classif"), 1,
            ["D0005H0002"], '-nodatalabel 0 -method majorityvoting',
            os.path.join(IOTA2DIR, "data", "references", "nomenclature.txt"),
            os.path.join(IOTA2DIR, "data", "regionShape",
                         "4Tiles.shp"), False, None)
        for cmd in cmd_fus:
            run(cmd)

        fusion_files = fut.FileSearch_AND(
            os.path.join(self.test_working_directory, "classif"), True,
            "_FUSION_")
        print(fusion_files)
        pixtype = fut.getOutputPixType(
            os.path.join(IOTA2DIR, "data", "references", "nomenclature.txt"))

        for fusionpath in fusion_files:

            UM.undecision_management(
                self.test_working_directory, fusionpath, "region",
                os.path.join(IOTA2DIR, "data", "references", "features"),
                os.path.join(IOTA2DIR, "data", "references",
                             "GenerateRegionShape", "region_need_To_env.shp"),
                "maxConfidence", None, ["NDVI", "NDWI", "Brightness"],
                '../../../../MNT_L8Grid', pixtype,
                os.path.join(IOTA2DIR, "data", "regionShape",
                             "4Tiles.shp"), "ALT,ASP,SLP", False)
        # TODO: test intelligent
        self.assertTrue(
            filecmp.cmp(
                os.path.join(self.test_working_directory, "classif",
                             "D0005H0002_FUSION_model_1_seed_0.tif"),
                os.path.join(IOTA2DIR, "data", "references", "NoData",
                             "Output",
                             "D0005H0002_FUSION_model_1_seed_0.tif")))
