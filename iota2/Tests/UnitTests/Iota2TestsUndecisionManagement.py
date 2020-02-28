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
import unittest
import shutil
from iota2.Common import ServiceConfigFile as SCF

IOTA2DIR = os.environ.get('IOTA2DIR')
IOTA2_DATATEST = os.path.join(os.environ.get('IOTA2DIR'), "data")


class iota_test_undecision_management(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        """
        Prepare constant for testing
        """
        # definition of local variables
        self.fichierConfig = (
            IOTA2DIR + "/config/Config_4Tuiles_Multi_FUS_Confidence.cfg")
        self.test_vector = (IOTA2_DATATEST +
                            "/iota2_test_undecision_management/")
        self.pathOut = (IOTA2_DATATEST + "/iota2_test_undecision_management/"
                        "test_undecision_management/")
        self.pathTilesFeat = IOTA2_DATATEST + "/references/features/"
        self.shapeRegion = (
            IOTA2_DATATEST +
            "/references/GenerateRegionShape/region_need_To_env.shp")
        self.pathClassif = self.pathOut + "/classif"
        self.classifFinal = self.pathOut + "/final"
        self.refData = IOTA2_DATATEST + "/references/NoData/"
        self.cmdPath = self.pathOut + "/cmd"

        # test and creation of test_vector
        if not os.path.exists(self.test_vector):
            os.mkdir(self.test_vector)
        # test and creation of pathOut
        if not os.path.exists(self.pathOut):
            os.mkdir(self.pathOut)
        else:
            shutil.rmtree(self.pathOut)
            os.mkdir(self.pathOut)
        # test and creation of pathClassif
        if not os.path.exists(self.pathClassif):
            os.mkdir(self.pathClassif)
        if not os.path.exists(self.pathClassif + "/MASK"):
            os.mkdir(self.pathClassif + "/MASK")
        if not os.path.exists(self.pathClassif + "/tmpClassif"):
            os.mkdir(self.pathClassif + "/tmpClassif")
        # test and creation of classifFinal
        if not os.path.exists(self.classifFinal):
            os.mkdir(self.classifFinal)
        # test and creation of cmdPath
        if not os.path.exists(self.cmdPath):
            os.mkdir(self.cmdPath)
        if not os.path.exists(self.cmdPath + "/fusion"):
            os.mkdir(self.cmdPath + "/fusion")
        if not os.path.exists(self.pathOut + "/config_model"):
            os.mkdir(self.pathOut + "/config_model")
        src_files = os.listdir(self.refData + "/Input/Classif/MASK")
        for file_name in src_files:
            full_file_name = os.path.join(self.refData + "/Input/Classif/MASK",
                                          file_name)
            shutil.copy(full_file_name, self.pathClassif + "/MASK")

        src_files = os.listdir(self.refData + "/Input/Classif/classif")
        for file_name in src_files:
            full_file_name = os.path.join(
                self.refData + "/Input/Classif/classif/", file_name)
            shutil.copy(full_file_name, self.pathClassif)

        src_files = os.listdir(self.refData + "/Input/config_model")
        for file_name in src_files:
            full_file_name = os.path.join(self.refData + "/Input/config_model",
                                          file_name)
            shutil.copy(full_file_name, self.pathOut + "/config_model")

    def test_undecision_management(self):
        """
        Test undecision_management
        """
        from iota2.Classification import undecision_management as UM
        from iota2.Classification import Fusion as FUS
        from iota2.Common.Utils import run
        from iota2.Common import FileUtils as fut
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        shutil.copy(
            os.path.join(self.pathClassif,
                         "Classif_D0005H0002_model_1_seed_0.tif"),
            os.path.join(self.pathClassif,
                         "Classif_D0005H0002_model_1f2_seed_0.tif"))
        shutil.copy(
            os.path.join(self.pathClassif,
                         "Classif_D0005H0002_model_1_seed_0.tif"),
            os.path.join(self.pathClassif,
                         "Classif_D0005H0002_model_1f1_seed_0.tif"))

        shutil.copy(
            os.path.join(self.pathClassif,
                         "D0005H0002_model_1_confidence_seed_0.tif"),
            os.path.join(self.pathClassif,
                         "D0005H0002_model_1f2_confidence_seed_0.tif"))
        shutil.copy(
            os.path.join(self.pathClassif,
                         "D0005H0002_model_1_confidence_seed_0.tif"),
            os.path.join(self.pathClassif,
                         "D0005H0002_model_1f1_confidence_seed_0.tif"))
        field_region = cfg.getParam('chain', 'regionField')
        cmd_fus = FUS.fusion(
            self.pathClassif, 1, ["D0005H0002"],
            cfg.getParam('argClassification', 'fusionOptions'),
            cfg.getParam('chain', 'nomenclaturePath'),
            cfg.getParam('chain', 'regionPath'),
            cfg.getParam('argTrain', 'dempster_shafer_SAR_Opt_fusion'), None)
        for cmd in cmd_fus:
            run(cmd)

        fusion_files = fut.FileSearch_AND(self.pathClassif, True, "_FUSION_")
        print(fusion_files)
        pixtype = fut.getOutputPixType(
            cfg.getParam('chain', 'nomenclaturePath'))

        for fusionpath in fusion_files:

            UM.undecision_management(
                self.pathOut, fusionpath, field_region, self.pathTilesFeat,
                self.shapeRegion, self.pathOut,
                cfg.getParam('argClassification', 'noLabelManagement'), None,
                cfg.getParam("GlobChain", "features"),
                cfg.getParam("chain", "userFeatPath"), pixtype,
                cfg.getParam('chain', 'regionPath'),
                cfg.getParam("userFeat", "patterns"),
                cfg.getParam('argTrain', 'dempster_shafer_SAR_Opt_fusion'))
        # TODO: test intelligent
