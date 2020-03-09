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
"""
Test sampler applications
"""
import os
import unittest
import shutil
from config import Config
from iota2.Tests.UnitTests.tests_utils import tests_utils_vectors as TUV
from iota2.Common import FileUtils as fut
from iota2.Sampling import VectorSampler
from iota2.Common import IOTA2Directory
IOTA2DIR = os.environ.get('IOTA2DIR')
IOTA2_DATATEST = os.path.join(os.environ.get('IOTA2DIR'), "data")


class iota_testSamplerApplications(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.test_vector = os.path.join(IOTA2_DATATEST, "test_vector")
        if not os.path.exists(self.test_vector):
            os.mkdir(self.test_vector)

        self.referenceShape = (
            IOTA2_DATATEST +
            "/references/sampler/D0005H0002_polygons_To_Sample.shp")
        self.referenceShape_test = TUV.shape_reference_vector(
            self.referenceShape, "D0005H0002")
        self.configSimple_NO_bindings = (IOTA2_DATATEST +
                                         "/config/test_config.cfg")
        self.configSimple_bindings = (IOTA2_DATATEST +
                                      "/config/test_config_bindings.cfg")
        self.configSimple_bindings_uDateFeatures = (
            IOTA2_DATATEST + "/config/test_config_bindings_uDateFeatures.cfg")
        self.configCropMix_NO_bindings = (IOTA2_DATATEST +
                                          "/config/test_config_cropMix.cfg")
        self.configCropMix_bindings = (
            IOTA2_DATATEST + "/config/test_config_cropMix_bindings.cfg")
        self.configClassifCropMix_NO_bindings = (
            IOTA2_DATATEST + "/config/test_config_classifCropMix.cfg")
        self.configClassifCropMix_bindings = (
            IOTA2_DATATEST + "/config/test_config_classifCropMix_bindings.cfg")
        self.configPrevClassif = IOTA2_DATATEST + "/config/prevClassif.cfg"

        self.regionShape = os.path.join(IOTA2_DATATEST, "references",
                                        "region_need_To_env.shp")
        self.features = (IOTA2_DATATEST +
                         "/references/features/D0005H0002/Final/"
                         "SL_MultiTempGapF_Brightness_NDVI_NDWI__.tif")
        self.MNT = IOTA2_DATATEST + "/references/MNT/"
        self.expectedFeatures = {11: 74, 12: 34, 42: 19, 51: 147}
        self.SensData = IOTA2_DATATEST + "/L8_50x50"
        self.iota2_directory = os.environ.get('IOTA2DIR')

        self.selection_test = os.path.join(self.test_vector,
                                           "D0005H0002.sqlite")
        raster_ref = fut.FileSearch_AND(
            os.path.join(self.SensData, "D0005H0002"), True, ".TIF")[0]
        TUV.prepare_test_selection(self.referenceShape_test, raster_ref,
                                   self.selection_test, self.test_vector,
                                   "code")

    def test_samplerSimple_bindings(self):
        def prepareTestsFolder(workingDirectory=False):
            wD = None
            if not os.path.exists(self.test_vector):
                os.mkdir(self.test_vector)
            testPath = self.test_vector + "/simpleSampler_vector_bindings"
            if os.path.exists(testPath):
                shutil.rmtree(testPath)
            os.mkdir(testPath)
            os.mkdir(os.path.join(testPath, "features"))
            featuresOutputs = (self.test_vector +
                               "/simpleSampler_features_bindings")
            if os.path.exists(featuresOutputs):
                shutil.rmtree(featuresOutputs)
            os.mkdir(featuresOutputs)
            if workingDirectory:
                wD = self.test_vector + "/simpleSampler_bindingsTMP"
                if os.path.exists(wD):
                    shutil.rmtree(wD)
                os.mkdir(wD)
            return testPath, featuresOutputs, wD

        reference = (IOTA2_DATATEST +
                     "/references/sampler/D0005H0002_polygons_"
                     "To_Sample_Samples_ref_bindings.sqlite")
        SensData = IOTA2_DATATEST + "/L8_50x50"

        from iota2.Common import ServiceConfigFile as SCF
        from config import Config

        # load configuration file
        SCF.clearConfig()

        testPath, featuresOutputs, wD = prepareTestsFolder(True)
        config_path = os.path.join(self.iota2_directory, "config",
                                   "Config_4Tuiles_Multi_FUS_Confidence.cfg")

        config_path_test = os.path.join(wD, "Config_TEST.cfg")
        shutil.copy(config_path, config_path_test)
        L8_rasters = os.path.join(self.iota2_directory, "data", "L8_50x50")
        cfg_test = Config(open(config_path_test))
        cfg_test.chain.outputPath = testPath
        cfg_test.chain.listTile = "D0005H0002"
        cfg_test.chain.L8Path_old = L8_rasters
        cfg_test.chain.L8Path = "None"
        cfg_test.chain.userFeatPath = "None"
        cfg_test.chain.regionField = 'region'
        cfg_test.argTrain.cropMix = False
        cfg_test.argTrain.samplesClassifMix = False
        cfg_test.GlobChain.useAdditionalFeatures = False
        cfg_test.save(open(config_path_test, 'w'))

        os.mkdir(featuresOutputs + "/D0005H0002")
        os.mkdir(featuresOutputs + "/D0005H0002/tmp")
        tile = "D0005H0002"
        self.config = SCF.serviceConfigFile(config_path_test)
        """
        TEST :
        prepare data to gapFilling -> gapFilling -> features generation
        -> samples extraction
        with otb's applications connected in memory
        and compare resulting samples extraction with reference.
        """
        # launch test case

        data_field = self.config.getParam("chain", "dataField")
        output_path = self.config.getParam("chain", "outputPath")
        annual_crop = self.config.getParam("argTrain", 'annualCrop')
        crop_mix = self.config.getParam('argTrain', 'cropMix')
        auto_context_enable = self.config.getParam('chain',
                                                   'enable_autoContext')
        region_field = (self.config.getParam('chain', 'regionField')).lower()
        proj = self.config.getParam('GlobChain', 'proj')
        enable_cross_validation = self.config.getParam(
            'chain', 'enableCrossValidation')
        runs = self.config.getParam('chain', 'runs')
        samples_classif_mix = self.config.getParam('argTrain',
                                                   'samplesClassifMix')

        # annual_config_file = cfg.getParam('argTrain', "prevFeatures")
        # output_path_annual = SCF.serviceConfigFile(
        #    annual_config_file).getParam("chain", "outputPath")
        output_path_annual = None
        ram = 128
        w_mode = False
        folder_annual_features = self.config.getParam('argTrain',
                                                      'outputPrevFeatures')
        previous_classif_path = self.config.getParam(
            'argTrain', 'annualClassesExtractionSource')
        validity_threshold = self.config.getParam('argTrain',
                                                  'validityThreshold')
        target_resolution = self.config.getParam('chain', 'spatialResolution')
        sensors_params = SCF.iota2_parameters(
            config_path_test).get_sensors_parameters(tile)
        try:
            sar_optical_flag = self.config.getParam(
                "argTrain", "dempster_shafer_SAR_Opt_fusion")
        except Exception as exc:
            print(exc)
            sar_optical_flag = False

        VectorSampler.generate_samples({"usually": self.referenceShape_test},
                                       None,
                                       data_field,
                                       output_path,
                                       annual_crop,
                                       crop_mix,
                                       auto_context_enable,
                                       region_field,
                                       proj,
                                       enable_cross_validation,
                                       runs,
                                       sensors_params,
                                       sar_optical_flag,
                                       samples_classif_mix,
                                       output_path_annual,
                                       ram,
                                       w_mode,
                                       folder_annual_features,
                                       previous_classif_path,
                                       validity_threshold,
                                       target_resolution,
                                       sample_selection=self.selection_test)

        # assert
        test_vector = fut.fileSearchRegEx(testPath +
                                          "/learningSamples/*sqlite")[0]
        TUV.delete_useless_fields(test_vector)
        compare = TUV.compare_sqlite(test_vector,
                                     reference,
                                     cmp_mode='coordinates')
        self.assertTrue(compare)
        """
        TEST :
        prepare data to gapFilling -> gapFilling -> features generation -> samples extraction
        with otb's applications connected in memory and writing tmp files
        and compare resulting samples extraction with reference.
        """
        testPath, featuresOutputs, wD = prepareTestsFolder()
        config_path_test = os.path.join(testPath, "Config_TEST.cfg")
        shutil.copy(config_path, config_path_test)
        L8_rasters = os.path.join(self.iota2_directory, "data", "L8_50x50")
        cfg_test = Config(open(config_path_test))
        cfg_test.chain.outputPath = testPath
        cfg_test.chain.listTile = "D0005H0002"
        cfg_test.chain.L8Path_old = L8_rasters
        cfg_test.chain.L8Path = "None"
        cfg_test.chain.userFeatPath = "None"
        cfg_test.chain.regionField = 'region'
        cfg_test.argTrain.cropMix = False
        cfg_test.argTrain.samplesClassifMix = False
        cfg_test.GlobChain.useAdditionalFeatures = False
        cfg_test.GlobChain.writeOutputs = True
        cfg_test.save(open(config_path_test, 'w'))

        os.mkdir(os.path.join(featuresOutputs, "D0005H0002"))
        os.mkdir(os.path.join(featuresOutputs, "D0005H0002", "tmp"))

        # launch test case
        config_test = SCF.serviceConfigFile(config_path_test)
        data_field = config_test.getParam("chain", "dataField")
        output_path = config_test.getParam("chain", "outputPath")
        annual_crop = config_test.getParam("argTrain", 'annualCrop')
        crop_mix = config_test.getParam('argTrain', 'cropMix')
        auto_context_enable = config_test.getParam('chain',
                                                   'enable_autoContext')
        region_field = (config_test.getParam('chain', 'regionField')).lower()
        proj = config_test.getParam('GlobChain', 'proj')
        enable_cross_validation = config_test.getParam(
            'chain', 'enableCrossValidation')
        runs = config_test.getParam('chain', 'runs')
        samples_classif_mix = config_test.getParam('argTrain',
                                                   'samplesClassifMix')

        # annual_config_file = cfg.getParam('argTrain', "prevFeatures")
        # output_path_annual = SCF.serviceConfigFile(
        #    annual_config_file).getParam("chain", "outputPath")
        output_path_annual = None
        ram = 128
        w_mode = False
        folder_annual_features = config_test.getParam('argTrain',
                                                      'outputPrevFeatures')
        previous_classif_path = config_test.getParam(
            'argTrain', 'annualClassesExtractionSource')
        validity_threshold = config_test.getParam('argTrain',
                                                  'validityThreshold')
        target_resolution = config_test.getParam('chain', 'spatialResolution')
        sensors_params = SCF.iota2_parameters(
            config_path_test).get_sensors_parameters(tile)
        try:
            sar_optical_flag = config_test.getParam(
                "argTrain", "dempster_shafer_SAR_Opt_fusion")
        except Exception as exc:
            print(exc)
            sar_optical_flag = False
        VectorSampler.generate_samples({"usually": self.referenceShape_test},
                                       None,
                                       data_field,
                                       output_path,
                                       annual_crop,
                                       crop_mix,
                                       auto_context_enable,
                                       region_field,
                                       proj,
                                       enable_cross_validation,
                                       runs,
                                       sensors_params,
                                       sar_optical_flag,
                                       samples_classif_mix,
                                       output_path_annual,
                                       ram,
                                       w_mode,
                                       folder_annual_features,
                                       previous_classif_path,
                                       validity_threshold,
                                       target_resolution,
                                       sample_selection=self.selection_test)

        # assert
        test_vector = fut.fileSearchRegEx(testPath +
                                          "/learningSamples/*sqlite")[0]
        TUV.delete_useless_fields(test_vector)
        compare = TUV.compare_sqlite(test_vector,
                                     reference,
                                     cmp_mode='coordinates')
        self.assertTrue(compare)
        """
        TEST :
        prepare data to gapFilling -> gapFilling -> features generation -> samples extraction
        with otb's applications connected in memory, write all necessary
        tmp files in a working directory and compare resulting samples
        extraction with reference.
        """
        testPath, featuresOutputs, wD = prepareTestsFolder()
        config_path_test = os.path.join(testPath, "Config_TEST.cfg")
        shutil.copy(config_path, config_path_test)
        L8_rasters = os.path.join(self.iota2_directory, "data", "L8_50x50")
        cfg_test = Config(open(config_path_test))
        cfg_test.chain.outputPath = testPath
        cfg_test.chain.listTile = "D0005H0002"
        cfg_test.chain.L8Path_old = L8_rasters
        cfg_test.chain.L8Path = "None"
        cfg_test.chain.userFeatPath = "None"
        cfg_test.chain.regionField = 'region'
        cfg_test.argTrain.cropMix = False
        cfg_test.argTrain.samplesClassifMix = False
        cfg_test.GlobChain.useAdditionalFeatures = False
        cfg_test.GlobChain.writeOutputs = True
        cfg_test.save(open(config_path_test, 'w'))

        os.mkdir(os.path.join(featuresOutputs, "D0005H0002"))
        os.mkdir(os.path.join(featuresOutputs, "D0005H0002", "tmp"))
        config_test = SCF.serviceConfigFile(config_path_test)
        data_field = config_test.getParam("chain", "dataField")
        output_path = config_test.getParam("chain", "outputPath")
        annual_crop = config_test.getParam("argTrain", 'annualCrop')
        crop_mix = config_test.getParam('argTrain', 'cropMix')
        auto_context_enable = config_test.getParam('chain',
                                                   'enable_autoContext')
        region_field = (config_test.getParam('chain', 'regionField')).lower()
        proj = config_test.getParam('GlobChain', 'proj')
        enable_cross_validation = config_test.getParam(
            'chain', 'enableCrossValidation')
        runs = config_test.getParam('chain', 'runs')
        samples_classif_mix = config_test.getParam('argTrain',
                                                   'samplesClassifMix')

        # annual_config_file = cfg.getParam('argTrain', "prevFeatures")
        # output_path_annual = SCF.serviceConfigFile(
        #    annual_config_file).getParam("chain", "outputPath")
        output_path_annual = None
        ram = 128
        w_mode = False
        folder_annual_features = config_test.getParam('argTrain',
                                                      'outputPrevFeatures')
        previous_classif_path = config_test.getParam(
            'argTrain', 'annualClassesExtractionSource')
        validity_threshold = config_test.getParam('argTrain',
                                                  'validityThreshold')
        target_resolution = config_test.getParam('chain', 'spatialResolution')
        sensors_params = SCF.iota2_parameters(
            config_path_test).get_sensors_parameters(tile)
        try:
            sar_optical_flag = config_test.getParam(
                "argTrain", "dempster_shafer_SAR_Opt_fusion")
        except Exception as exc:
            print(exc)
            sar_optical_flag = False
        VectorSampler.generate_samples({"usually": self.referenceShape_test},
                                       wD,
                                       data_field,
                                       output_path,
                                       annual_crop,
                                       crop_mix,
                                       auto_context_enable,
                                       region_field,
                                       proj,
                                       enable_cross_validation,
                                       runs,
                                       sensors_params,
                                       sar_optical_flag,
                                       samples_classif_mix,
                                       output_path_annual,
                                       ram,
                                       w_mode,
                                       folder_annual_features,
                                       previous_classif_path,
                                       validity_threshold,
                                       target_resolution,
                                       sample_selection=self.selection_test)
        #~ self.config.setParam('GlobChain', 'writeOutputs', False)

        test_vector = fut.fileSearchRegEx(testPath +
                                          "/learningSamples/*sqlite")[0]
        TUV.delete_useless_fields(test_vector)
        compare = TUV.compare_sqlite(test_vector,
                                     reference,
                                     cmp_mode='coordinates')
        self.assertTrue(compare)

        #Test user features and additional features
        reference = IOTA2_DATATEST + "/references/sampler/D0005H0002_polygons_To_Sample_Samples_UserFeat_UserExpr.sqlite"
        """
        TEST :
        prepare data to gapFilling -> gapFilling -> features generation (userFeatures + userDayFeatures) -> samples extraction
        with otb's applications connected in memory, compare resulting sample to extraction with reference.
        """
        testPath, featuresOutputs, wD = prepareTestsFolder(
            workingDirectory=False)
        config_path_test = os.path.join(testPath, "Config_TEST.cfg")
        shutil.copy(config_path, config_path_test)
        L8_rasters = os.path.join(self.iota2_directory, "data", "L8_50x50")
        cfg_test = Config(open(config_path_test))
        cfg_test.chain.outputPath = testPath
        cfg_test.chain.listTile = "D0005H0002"
        cfg_test.chain.L8Path_old = L8_rasters
        cfg_test.chain.L8Path = "None"
        cfg_test.chain.userFeatPath = os.path.join(self.iota2_directory,
                                                   "data/references/MNT/")
        cfg_test.userFeat.arbo = "/*"
        cfg_test.userFeat.patterns = "MNT"
        cfg_test.chain.regionField = 'region'
        cfg_test.argTrain.cropMix = False
        cfg_test.argTrain.samplesClassifMix = False
        cfg_test.GlobChain.useAdditionalFeatures = False
        cfg_test.GlobChain.writeOutputs = True
        cfg_test.GlobChain.useAdditionalFeatures = True
        cfg_test.Landsat8_old.additionalFeatures = 'b1+b2,(b1-b2)/(b1+b2)'
        cfg_test.save(open(config_path_test, 'w'))
        os.mkdir(os.path.join(featuresOutputs, "D0005H0002"))
        os.mkdir(os.path.join(featuresOutputs, "D0005H0002", "tmp"))
        config_test = SCF.serviceConfigFile(config_path_test)
        data_field = config_test.getParam("chain", "dataField")
        output_path = config_test.getParam("chain", "outputPath")
        annual_crop = config_test.getParam("argTrain", 'annualCrop')
        crop_mix = config_test.getParam('argTrain', 'cropMix')
        auto_context_enable = config_test.getParam('chain',
                                                   'enable_autoContext')
        region_field = (config_test.getParam('chain', 'regionField')).lower()
        proj = config_test.getParam('GlobChain', 'proj')
        enable_cross_validation = config_test.getParam(
            'chain', 'enableCrossValidation')
        runs = config_test.getParam('chain', 'runs')
        samples_classif_mix = config_test.getParam('argTrain',
                                                   'samplesClassifMix')

        # annual_config_file = cfg.getParam('argTrain', "prevFeatures")
        # output_path_annual = SCF.serviceConfigFile(
        #    annual_config_file).getParam("chain", "outputPath")
        output_path_annual = None
        ram = 128
        w_mode = False
        folder_annual_features = config_test.getParam('argTrain',
                                                      'outputPrevFeatures')
        previous_classif_path = config_test.getParam(
            'argTrain', 'annualClassesExtractionSource')
        validity_threshold = config_test.getParam('argTrain',
                                                  'validityThreshold')
        target_resolution = config_test.getParam('chain', 'spatialResolution')
        sensors_params = SCF.iota2_parameters(
            config_path_test).get_sensors_parameters(tile)
        try:
            sar_optical_flag = config_test.getParam(
                "argTrain", "dempster_shafer_SAR_Opt_fusion")
        except Exception as exc:
            print(exc)
            sar_optical_flag = False
        VectorSampler.generate_samples({"usually": self.referenceShape_test},
                                       wD,
                                       data_field,
                                       output_path,
                                       annual_crop,
                                       crop_mix,
                                       auto_context_enable,
                                       region_field,
                                       proj,
                                       enable_cross_validation,
                                       runs,
                                       sensors_params,
                                       sar_optical_flag,
                                       samples_classif_mix,
                                       output_path_annual,
                                       ram,
                                       w_mode,
                                       folder_annual_features,
                                       previous_classif_path,
                                       validity_threshold,
                                       target_resolution,
                                       sample_selection=self.selection_test)

        test_vector = fut.fileSearchRegEx(testPath +
                                          "/learningSamples/*sqlite")[0]
        TUV.delete_useless_fields(test_vector)
        compare = TUV.compare_sqlite(test_vector,
                                     reference,
                                     cmp_mode='coordinates')
        self.assertTrue(compare)
        """
        TEST :
        prepare data to gapFilling -> gapFilling -> features generation (userFeatures + userDayFeatures) -> samples extraction
        with otb's applications connected in memory,
        write all necessary tmp files in a working directory
        and compare resulting sample extraction with reference.
        """
        testPath, featuresOutputs, wD = prepareTestsFolder(
            workingDirectory=True)
        config_path_test = os.path.join(testPath, "Config_TEST.cfg")
        shutil.copy(config_path, config_path_test)
        L8_rasters = os.path.join(self.iota2_directory, "data", "L8_50x50")
        cfg_test = Config(open(config_path_test))
        cfg_test.chain.outputPath = testPath
        cfg_test.chain.listTile = "D0005H0002"
        cfg_test.chain.L8Path_old = L8_rasters
        cfg_test.chain.L8Path = "None"
        cfg_test.chain.userFeatPath = os.path.join(self.iota2_directory,
                                                   "data/references/MNT/")
        cfg_test.userFeat.arbo = "/*"
        cfg_test.userFeat.patterns = "MNT"
        cfg_test.chain.regionField = 'region'
        cfg_test.argTrain.cropMix = False
        cfg_test.argTrain.samplesClassifMix = False
        cfg_test.GlobChain.useAdditionalFeatures = False
        cfg_test.GlobChain.writeOutputs = True
        cfg_test.GlobChain.useAdditionalFeatures = True
        cfg_test.Landsat8_old.additionalFeatures = 'b1+b2,(b1-b2)/(b1+b2)'
        cfg_test.save(open(config_path_test, 'w'))

        os.mkdir(os.path.join(featuresOutputs, "D0005H0002"))
        os.mkdir(os.path.join(featuresOutputs, "D0005H0002", "tmp"))
        config_test = SCF.serviceConfigFile(config_path_test)
        data_field = config_test.getParam("chain", "dataField")
        output_path = config_test.getParam("chain", "outputPath")
        annual_crop = config_test.getParam("argTrain", 'annualCrop')
        crop_mix = config_test.getParam('argTrain', 'cropMix')
        auto_context_enable = config_test.getParam('chain',
                                                   'enable_autoContext')
        region_field = (config_test.getParam('chain', 'regionField')).lower()
        proj = config_test.getParam('GlobChain', 'proj')
        enable_cross_validation = config_test.getParam(
            'chain', 'enableCrossValidation')
        runs = config_test.getParam('chain', 'runs')
        samples_classif_mix = config_test.getParam('argTrain',
                                                   'samplesClassifMix')

        # annual_config_file = cfg.getParam('argTrain', "prevFeatures")
        # output_path_annual = SCF.serviceConfigFile(
        #    annual_config_file).getParam("chain", "outputPath")
        output_path_annual = None
        ram = 128
        w_mode = False
        folder_annual_features = config_test.getParam('argTrain',
                                                      'outputPrevFeatures')
        previous_classif_path = config_test.getParam(
            'argTrain', 'annualClassesExtractionSource')
        validity_threshold = config_test.getParam('argTrain',
                                                  'validityThreshold')
        target_resolution = config_test.getParam('chain', 'spatialResolution')
        sensors_params = SCF.iota2_parameters(
            config_path_test).get_sensors_parameters(tile)
        try:
            sar_optical_flag = config_test.getParam(
                "argTrain", "dempster_shafer_SAR_Opt_fusion")
        except Exception as exc:
            print(exc)
            sar_optical_flag = False
        VectorSampler.generate_samples({"usually": self.referenceShape_test},
                                       wD,
                                       data_field,
                                       output_path,
                                       annual_crop,
                                       crop_mix,
                                       auto_context_enable,
                                       region_field,
                                       proj,
                                       enable_cross_validation,
                                       runs,
                                       sensors_params,
                                       sar_optical_flag,
                                       samples_classif_mix,
                                       output_path_annual,
                                       ram,
                                       w_mode,
                                       folder_annual_features,
                                       previous_classif_path,
                                       validity_threshold,
                                       target_resolution,
                                       sample_selection=self.selection_test)

        test_vector = fut.fileSearchRegEx(testPath +
                                          "/learningSamples/*sqlite")[0]
        TUV.delete_useless_fields(test_vector)
        compare = TUV.compare_sqlite(test_vector,
                                     reference,
                                     cmp_mode='coordinates')
        self.assertTrue(compare)

    def test_samplerCropMix_bindings(self):
        """
        TEST cropMix 1 algorithm
        using connected OTB applications :

        Step 1 : on non annual class
        prepare data to gapFilling -> gapFilling -> features generation -> samples extraction non annual

        Step 2 : on annual class
        prepare data to gapFilling -> gapFilling -> features generation -> samples extraction annual

        Step 3 : merge samples extration nonAnnual / annual

        Step 4 : compare the merged sample to reference
        """

        from iota2.Tests.UnitTests.tests_utils.tests_utils_rasters import prepare_annual_features

        def prepareTestsFolder(workingDirectory=False):

            testPath = self.test_vector + "/cropMixSampler_bindings/"
            if os.path.exists(testPath):
                shutil.rmtree(testPath)
            os.mkdir(testPath)
            os.mkdir(os.path.join(testPath, "features"))

            featuresNonAnnualOutputs = self.test_vector + "/cropMixSampler_featuresNonAnnual_bindings"
            if os.path.exists(featuresNonAnnualOutputs):
                shutil.rmtree(featuresNonAnnualOutputs)
            os.mkdir(featuresNonAnnualOutputs)
            os.mkdir(featuresNonAnnualOutputs + "/D0005H0002")
            os.mkdir(featuresNonAnnualOutputs + "/D0005H0002/tmp")

            featuresAnnualOutputs = self.test_vector + "/cropMixSampler_featuresAnnual_bindings"
            if os.path.exists(featuresAnnualOutputs):
                shutil.rmtree(featuresAnnualOutputs)
            os.mkdir(featuresAnnualOutputs)
            os.mkdir(featuresAnnualOutputs + "/D0005H0002")
            os.mkdir(featuresAnnualOutputs + "/D0005H0002/tmp")

            wD = self.test_vector + "/cropMixSampler_bindingsTMP"
            if os.path.exists(wD):
                shutil.rmtree(wD)
            wD = None
            if workingDirectory:
                wD = self.test_vector + "/cropMixSampler_bindingsTMP"
                os.mkdir(wD)
            return testPath, featuresNonAnnualOutputs, featuresAnnualOutputs, wD

        def generate_annual_config(directory, annualFeaturesPath,
                                   features_A_Outputs):

            config_path = os.path.join(
                IOTA2DIR, "config", "Config_4Tuiles_Multi_FUS_Confidence.cfg")
            annual_config_path = os.path.join(directory, "AnnualConfig.cfg")
            shutil.copy(config_path, annual_config_path)
            cfg = Config(open(annual_config_path))
            cfg.chain.listTile = 'D0005H0002'
            cfg.chain.L8Path_old = annualFeaturesPath
            cfg.chain.L8Path = "None"
            cfg.chain.userFeatPath = 'None'
            cfg.GlobChain.annualClassesExtractionSource = 'False'
            cfg.GlobChain.useAdditionalFeatures = False
            cfg.save(open(annual_config_path, 'w'))
            featuresPath = os.path.join(cfg.chain.outputPath, "features")
            if not os.path.exists(featuresPath):
                os.mkdir(featuresPath)

            return annual_config_path

        from iota2.Common import ServiceConfigFile as SCF

        featuresPath = IOTA2_DATATEST + "/references/features/"
        sensorData = IOTA2_DATATEST + "/L8_50x50"
        reference = IOTA2_DATATEST + "/references/sampler/D0005H0002_polygons_To_Sample_Samples_CropMix_bindings.sqlite"

        #prepare outputs test folders
        testPath, features_NA_Outputs, features_A_Outputs, wD = prepareTestsFolder(
            True)
        annualFeaturesPath = testPath + "/annualFeatures"

        #prepare annual configuration file
        annual_config_path = generate_annual_config(wD, annualFeaturesPath,
                                                    features_A_Outputs)

        testPath, features_NA_Outputs, features_A_Outputs, wD = prepareTestsFolder(
            True)

        # load configuration file
        SCF.clearConfig()

        config_path = os.path.join(self.iota2_directory, "config",
                                   "Config_4Tuiles_Multi_FUS_Confidence.cfg")
        self.config = SCF.serviceConfigFile(config_path)

        L8_rasters_non_annual = os.path.join(self.iota2_directory, "data",
                                             "L8_50x50")
        L8_rasters_annual = os.path.join(wD, "annualData")
        os.mkdir(L8_rasters_annual)
        #annual sensor data generation (pix annual = 2 * pix non_annual)
        prepare_annual_features(L8_rasters_annual,
                                L8_rasters_non_annual,
                                "CORR_PENTE",
                                rename=("2016", "2015"))
        #prepare annual configuration file
        annual_config_path = os.path.join(wD, "AnnualConfig.cfg")
        shutil.copy(self.config.pathConf, annual_config_path)

        cfg = Config(open(annual_config_path))
        cfg.chain.listTile = 'D0005H0002'
        cfg.chain.L8Path_old = L8_rasters_annual
        cfg.chain.L8Path = "None"
        cfg.chain.featuresPath = features_A_Outputs
        cfg.chain.userFeatPath = 'None'
        cfg.GlobChain.useAdditionalFeatures = False
        cfg.save(open(annual_config_path, 'w'))

        #fill up configuration file
        """
        TEST
        using a working directory and write temporary files on disk
        """
        #fill up configuration file
        config_path_test = os.path.join(wD, "Config_TEST.cfg")
        shutil.copy(config_path, config_path_test)
        L8_rasters = os.path.join(self.iota2_directory, "data", "L8_50x50")
        cfg_test = Config(open(config_path_test))
        cfg_test.chain.outputPath = testPath
        cfg_test.chain.listTile = "D0005H0002"
        cfg_test.chain.L8Path_old = L8_rasters_non_annual
        cfg_test.chain.L8Path = "None"
        cfg_test.chain.userFeatPath = "None"
        cfg_test.chain.regionField = 'region'
        cfg_test.argTrain.cropMix = True
        cfg_test.argTrain.samplesClassifMix = False
        cfg_test.argTrain.prevFeatures = annual_config_path
        cfg_test.GlobChain.useAdditionalFeatures = False
        cfg_test.GlobChain.writeOutputs = True
        cfg_test.save(open(config_path_test, 'w'))
        tile = "D0005H0002"
        config_test = SCF.serviceConfigFile(config_path_test)
        data_field = config_test.getParam("chain", "dataField")
        output_path = config_test.getParam("chain", "outputPath")
        annual_crop = config_test.getParam("argTrain", 'annualCrop')
        crop_mix = config_test.getParam('argTrain', 'cropMix')
        auto_context_enable = config_test.getParam('chain',
                                                   'enable_autoContext')
        region_field = (config_test.getParam('chain', 'regionField')).lower()
        proj = config_test.getParam('GlobChain', 'proj')
        enable_cross_validation = config_test.getParam(
            'chain', 'enableCrossValidation')
        runs = config_test.getParam('chain', 'runs')
        samples_classif_mix = config_test.getParam('argTrain',
                                                   'samplesClassifMix')

        annual_config_file = config_test.getParam('argTrain', "prevFeatures")
        output_path_annual = SCF.serviceConfigFile(
            annual_config_file).getParam("chain", "outputPath")
        ram = 128
        w_mode = False
        folder_annual_features = config_test.getParam('argTrain',
                                                      'outputPrevFeatures')
        previous_classif_path = config_test.getParam(
            'argTrain', 'annualClassesExtractionSource')
        validity_threshold = config_test.getParam('argTrain',
                                                  'validityThreshold')
        target_resolution = config_test.getParam('chain', 'spatialResolution')
        sensors_params = SCF.iota2_parameters(
            config_path_test).get_sensors_parameters(tile)
        try:
            sar_optical_flag = config_test.getParam(
                "argTrain", "dempster_shafer_SAR_Opt_fusion")
        except Exception as exc:
            print(exc)
            sar_optical_flag = False
        #Launch sampler
        VectorSampler.generate_samples({"usually": self.referenceShape_test},
                                       None,
                                       data_field,
                                       output_path,
                                       annual_crop,
                                       crop_mix,
                                       auto_context_enable,
                                       region_field,
                                       proj,
                                       enable_cross_validation,
                                       runs,
                                       sensors_params,
                                       sar_optical_flag,
                                       samples_classif_mix,
                                       output_path_annual,
                                       ram,
                                       w_mode,
                                       folder_annual_features,
                                       previous_classif_path,
                                       validity_threshold,
                                       target_resolution,
                                       sample_selection=self.selection_test)

        #compare to reference
        test_vector = fut.fileSearchRegEx(testPath +
                                          "/learningSamples/*sqlite")[0]
        TUV.delete_useless_fields(test_vector)
        compare = TUV.compare_sqlite(test_vector,
                                     reference,
                                     cmp_mode='coordinates',
                                     ignored_fields=["originfid"])
        self.assertTrue(compare)
        """
        TEST
        using a working directory and without temporary files
        """
        testPath, features_NA_Outputs, features_A_Outputs, wD = prepareTestsFolder(
            True)
        config_path_test = os.path.join(wD, "Config_TEST.cfg")
        shutil.copy(config_path, config_path_test)
        L8_rasters = os.path.join(self.iota2_directory, "data", "L8_50x50")
        cfg_test = Config(open(config_path_test))
        cfg_test.chain.outputPath = testPath
        cfg_test.chain.listTile = "D0005H0002"
        cfg_test.chain.L8Path_old = L8_rasters_non_annual
        cfg_test.chain.L8Path = "None"
        cfg_test.chain.userFeatPath = "None"
        cfg_test.chain.regionField = 'region'
        cfg_test.argTrain.cropMix = True
        cfg_test.argTrain.samplesClassifMix = False
        cfg_test.argTrain.prevFeatures = annual_config_path
        cfg_test.GlobChain.useAdditionalFeatures = False
        cfg_test.GlobChain.writeOutputs = False
        cfg_test.save(open(config_path_test, 'w'))
        config_test = SCF.serviceConfigFile(config_path_test)

        #annual sensor data generation (pix annual = 2 * pix non_annual)
        os.mkdir(L8_rasters_annual)
        prepare_annual_features(L8_rasters_annual,
                                L8_rasters_non_annual,
                                "CORR_PENTE",
                                rename=("2016", "2015"))
        #prepare annual configuration file
        annual_config_path = os.path.join(wD, "AnnualConfig.cfg")
        shutil.copy(self.config.pathConf, annual_config_path)

        cfg = Config(open(annual_config_path))
        cfg.chain.listTile = 'D0005H0002'
        cfg.chain.L8Path_old = L8_rasters_annual
        cfg.chain.L8Path = "None"
        cfg.chain.featuresPath = features_A_Outputs
        cfg.chain.userFeatPath = 'None'
        cfg.GlobChain.useAdditionalFeatures = False
        cfg.save(open(annual_config_path, 'w'))

        #Launch sampler
        data_field = config_test.getParam("chain", "dataField")
        output_path = config_test.getParam("chain", "outputPath")
        annual_crop = config_test.getParam("argTrain", 'annualCrop')
        crop_mix = config_test.getParam('argTrain', 'cropMix')
        auto_context_enable = config_test.getParam('chain',
                                                   'enable_autoContext')
        region_field = (config_test.getParam('chain', 'regionField')).lower()
        proj = config_test.getParam('GlobChain', 'proj')
        enable_cross_validation = config_test.getParam(
            'chain', 'enableCrossValidation')
        runs = config_test.getParam('chain', 'runs')
        samples_classif_mix = config_test.getParam('argTrain',
                                                   'samplesClassifMix')

        annual_config_file = config_test.getParam('argTrain', "prevFeatures")
        output_path_annual = SCF.serviceConfigFile(
            annual_config_file).getParam("chain", "outputPath")

        ram = 128
        w_mode = False
        folder_annual_features = config_test.getParam('argTrain',
                                                      'outputPrevFeatures')
        previous_classif_path = config_test.getParam(
            'argTrain', 'annualClassesExtractionSource')
        validity_threshold = config_test.getParam('argTrain',
                                                  'validityThreshold')
        target_resolution = config_test.getParam('chain', 'spatialResolution')
        sensors_params = SCF.iota2_parameters(
            config_path_test).get_sensors_parameters(tile)
        try:
            sar_optical_flag = config_test.getParam(
                "argTrain", "dempster_shafer_SAR_Opt_fusion")
        except Exception as exc:
            print(exc)
            sar_optical_flag = False
        VectorSampler.generate_samples({"usually": self.referenceShape_test},
                                       wD,
                                       data_field,
                                       output_path,
                                       annual_crop,
                                       crop_mix,
                                       auto_context_enable,
                                       region_field,
                                       proj,
                                       enable_cross_validation,
                                       runs,
                                       sensors_params,
                                       sar_optical_flag,
                                       samples_classif_mix,
                                       output_path_annual,
                                       ram,
                                       w_mode,
                                       folder_annual_features,
                                       previous_classif_path,
                                       validity_threshold,
                                       target_resolution,
                                       sample_selection=self.selection_test)

        test_vector = fut.fileSearchRegEx(testPath +
                                          "/learningSamples/*sqlite")[0]
        TUV.delete_useless_fields(test_vector)
        compare = TUV.compare_sqlite(test_vector,
                                     reference,
                                     cmp_mode='coordinates',
                                     ignored_fields=["originfid"])
        self.assertTrue(compare)
        """
        TEST
        without a working directory and without temporary files on disk
        """

        testPath, features_NA_Outputs, features_A_Outputs, wD = prepareTestsFolder(
            True)
        config_path_test = os.path.join(wD, "Config_TEST.cfg")
        shutil.copy(config_path, config_path_test)
        L8_rasters = os.path.join(self.iota2_directory, "data", "L8_50x50")
        cfg_test = Config(open(config_path_test))
        cfg_test.chain.outputPath = testPath
        cfg_test.chain.listTile = "D0005H0002"
        cfg_test.chain.L8Path_old = L8_rasters_non_annual
        cfg_test.chain.L8Path = "None"
        cfg_test.chain.userFeatPath = "None"
        cfg_test.chain.regionField = 'region'
        cfg_test.argTrain.cropMix = True
        cfg_test.argTrain.samplesClassifMix = False
        cfg_test.argTrain.prevFeatures = annual_config_path
        cfg_test.GlobChain.useAdditionalFeatures = False
        cfg_test.GlobChain.writeOutputs = False
        cfg_test.save(open(config_path_test, 'w'))
        config_test = SCF.serviceConfigFile(config_path_test)

        #annual sensor data generation (pix annual = 2 * pix non_annual)
        os.mkdir(L8_rasters_annual)
        prepare_annual_features(L8_rasters_annual,
                                L8_rasters_non_annual,
                                "CORR_PENTE",
                                rename=("2016", "2015"))
        #prepare annual configuration file
        annual_config_path = os.path.join(wD, "AnnualConfig.cfg")
        shutil.copy(self.config.pathConf, annual_config_path)

        cfg = Config(open(annual_config_path))
        cfg.chain.listTile = 'D0005H0002'
        cfg.chain.L8Path_old = L8_rasters_annual
        cfg.chain.L8Path = "None"
        cfg.chain.featuresPath = features_A_Outputs
        cfg.chain.userFeatPath = 'None'
        cfg.GlobChain.useAdditionalFeatures = False
        cfg.save(open(annual_config_path, 'w'))

        data_field = config_test.getParam("chain", "dataField")
        output_path = config_test.getParam("chain", "outputPath")
        annual_crop = config_test.getParam("argTrain", 'annualCrop')
        crop_mix = config_test.getParam('argTrain', 'cropMix')
        auto_context_enable = config_test.getParam('chain',
                                                   'enable_autoContext')
        region_field = (config_test.getParam('chain', 'regionField')).lower()
        proj = config_test.getParam('GlobChain', 'proj')
        enable_cross_validation = config_test.getParam(
            'chain', 'enableCrossValidation')
        runs = config_test.getParam('chain', 'runs')
        samples_classif_mix = config_test.getParam('argTrain',
                                                   'samplesClassifMix')

        annual_config_file = config_test.getParam('argTrain', "prevFeatures")
        output_path_annual = SCF.serviceConfigFile(
            annual_config_file).getParam("chain", "outputPath")

        ram = 128
        w_mode = False
        folder_annual_features = config_test.getParam('argTrain',
                                                      'outputPrevFeatures')
        previous_classif_path = config_test.getParam(
            'argTrain', 'annualClassesExtractionSource')
        validity_threshold = config_test.getParam('argTrain',
                                                  'validityThreshold')
        target_resolution = config_test.getParam('chain', 'spatialResolution')
        sensors_params = SCF.iota2_parameters(
            config_path_test).get_sensors_parameters(tile)
        try:
            sar_optical_flag = config_test.getParam(
                "argTrain", "dempster_shafer_SAR_Opt_fusion")
        except Exception as exc:
            print(exc)
            sar_optical_flag = False
        #Launch sampler
        VectorSampler.generate_samples({"usually": self.referenceShape_test},
                                       None,
                                       data_field,
                                       output_path,
                                       annual_crop,
                                       crop_mix,
                                       auto_context_enable,
                                       region_field,
                                       proj,
                                       enable_cross_validation,
                                       runs,
                                       sensors_params,
                                       sar_optical_flag,
                                       samples_classif_mix,
                                       output_path_annual,
                                       ram,
                                       w_mode,
                                       folder_annual_features,
                                       previous_classif_path,
                                       validity_threshold,
                                       target_resolution,
                                       sample_selection=self.selection_test)

        test_vector = fut.fileSearchRegEx(testPath +
                                          "/learningSamples/*sqlite")[0]
        TUV.delete_useless_fields(test_vector)
        compare = TUV.compare_sqlite(test_vector,
                                     reference,
                                     cmp_mode='coordinates',
                                     ignored_fields=["originfid"])
        self.assertTrue(compare)
        """
        TEST
        without a working directory and write temporary files on disk
        """
        self.config.setParam('GlobChain', 'writeOutputs', True)
        testPath, features_NA_Outputs, features_A_Outputs, wD = prepareTestsFolder(
            True)
        config_path_test = os.path.join(wD, "Config_TEST.cfg")
        shutil.copy(config_path, config_path_test)
        L8_rasters = os.path.join(self.iota2_directory, "data", "L8_50x50")
        cfg_test = Config(open(config_path_test))
        cfg_test.chain.outputPath = testPath
        cfg_test.chain.listTile = "D0005H0002"
        cfg_test.chain.L8Path_old = L8_rasters_non_annual
        cfg_test.chain.L8Path = "None"
        cfg_test.chain.userFeatPath = "None"
        cfg_test.chain.regionField = 'region'
        cfg_test.argTrain.cropMix = True
        cfg_test.argTrain.samplesClassifMix = False
        cfg_test.argTrain.prevFeatures = annual_config_path
        cfg_test.GlobChain.useAdditionalFeatures = False
        cfg_test.GlobChain.writeOutputs = True
        cfg_test.save(open(config_path_test, 'w'))
        config_test = SCF.serviceConfigFile(config_path_test)
        #annual sensor data generation (pix annual = 2 * pix non_annual)
        os.mkdir(L8_rasters_annual)
        prepare_annual_features(L8_rasters_annual,
                                L8_rasters_non_annual,
                                "CORR_PENTE",
                                rename=("2016", "2015"))
        #prepare annual configuration file
        annual_config_path = os.path.join(wD, "AnnualConfig.cfg")
        shutil.copy(self.config.pathConf, annual_config_path)

        cfg = Config(open(annual_config_path))
        cfg.chain.listTile = 'D0005H0002'
        cfg.chain.L8Path_old = L8_rasters_annual
        cfg.chain.L8Path = "None"
        cfg.chain.featuresPath = features_A_Outputs
        cfg.chain.userFeatPath = 'None'
        cfg.GlobChain.useAdditionalFeatures = False
        cfg.save(open(annual_config_path, 'w'))

        data_field = config_test.getParam("chain", "dataField")
        output_path = config_test.getParam("chain", "outputPath")
        annual_crop = config_test.getParam("argTrain", 'annualCrop')
        crop_mix = config_test.getParam('argTrain', 'cropMix')
        auto_context_enable = config_test.getParam('chain',
                                                   'enable_autoContext')
        region_field = (config_test.getParam('chain', 'regionField')).lower()
        proj = config_test.getParam('GlobChain', 'proj')
        enable_cross_validation = config_test.getParam(
            'chain', 'enableCrossValidation')
        runs = config_test.getParam('chain', 'runs')
        samples_classif_mix = config_test.getParam('argTrain',
                                                   'samplesClassifMix')

        annual_config_file = config_test.getParam('argTrain', "prevFeatures")
        output_path_annual = SCF.serviceConfigFile(
            annual_config_file).getParam("chain", "outputPath")

        ram = 128
        w_mode = False
        folder_annual_features = config_test.getParam('argTrain',
                                                      'outputPrevFeatures')
        previous_classif_path = config_test.getParam(
            'argTrain', 'annualClassesExtractionSource')
        validity_threshold = config_test.getParam('argTrain',
                                                  'validityThreshold')
        target_resolution = config_test.getParam('chain', 'spatialResolution')
        sensors_params = SCF.iota2_parameters(
            config_path_test).get_sensors_parameters(tile)
        try:
            sar_optical_flag = config_test.getParam(
                "argTrain", "dempster_shafer_SAR_Opt_fusion")
        except Exception as exc:
            print(exc)
            sar_optical_flag = False
        #Launch Sampling
        VectorSampler.generate_samples({"usually": self.referenceShape_test},
                                       None,
                                       data_field,
                                       output_path,
                                       annual_crop,
                                       crop_mix,
                                       auto_context_enable,
                                       region_field,
                                       proj,
                                       enable_cross_validation,
                                       runs,
                                       sensors_params,
                                       sar_optical_flag,
                                       samples_classif_mix,
                                       output_path_annual,
                                       ram,
                                       w_mode,
                                       folder_annual_features,
                                       previous_classif_path,
                                       validity_threshold,
                                       target_resolution,
                                       sample_selection=self.selection_test)

        #Compare vector produce to reference
        test_vector = fut.fileSearchRegEx(testPath +
                                          "/learningSamples/*sqlite")[0]
        TUV.delete_useless_fields(test_vector)
        compare = TUV.compare_sqlite(test_vector,
                                     reference,
                                     cmp_mode='coordinates',
                                     ignored_fields=["originfid"])
        self.assertTrue(compare)

    def test_samplerClassifCropMix_bindings(self):
        """
        TEST cropMix 2 algorithm

        Step 1 : on non Annual classes, select samples
        Step 2 : select randomly annual samples into a provided land cover map.
        Step 3 : merge samples from step 1 and 2
        Step 4 : Compute feature to samples.

        random part in this script could not be control, no reference vector can be done.
        Only number of features can be check.
        """
        from iota2.Common import ServiceConfigFile as SCF
        from iota2.Sampling import TileEnvelope as env
        from iota2.Sampling import TileArea as area
        from iota2.Common.Tools import CreateRegionsByTiles as RT
        from iota2.Sensors.ProcessLauncher import commonMasks
        from iota2.VectorTools.AddField import addField
        config_path = os.path.join(self.iota2_directory, "config",
                                   "Config_4Tuiles_Multi_FUS_Confidence.cfg")

        def prepareTestsFolder(workingDirectory=False):
            wD = None
            testPath = self.test_vector + "/classifCropMixSampler_bindings/"

            if os.path.exists(testPath):
                shutil.rmtree(testPath)
            os.mkdir(testPath)

            featuresOutputs = self.test_vector + "/classifCropMixSampler_features_bindings"
            if os.path.exists(featuresOutputs):
                shutil.rmtree(featuresOutputs)
            os.mkdir(featuresOutputs)

            if workingDirectory:
                wD = self.test_vector + "/classifCropMixSampler_bindingsTMP"
                if os.path.exists(wD):
                    shutil.rmtree(wD)
                os.mkdir(wD)
            return testPath, featuresOutputs, wD

        L8_rasters_old = os.path.join(self.iota2_directory, "data", "L8_50x50")
        classifications_path = os.path.join(self.iota2_directory, "data",
                                            "references", "sampler")

        testPath, featuresOutputs, wD = prepareTestsFolder(True)

        #rename reference shape
        vector = TUV.shape_reference_vector(self.referenceShape, "D0005H0002")

        # load configuration file
        SCF.clearConfig()

        self.config = SCF.serviceConfigFile(config_path)
        #fill up configuration file
        config_path_test = os.path.join(wD, "Config_TEST.cfg")
        shutil.copy(config_path, config_path_test)
        L8_rasters = os.path.join(self.iota2_directory, "data", "L8_50x50")
        cfg_test = Config(open(config_path_test))
        cfg_test.chain.outputPath = testPath
        cfg_test.chain.listTile = "D0005H0002"
        cfg_test.chain.L8Path_old = L8_rasters_old
        cfg_test.chain.L8Path = "None"
        cfg_test.chain.userFeatPath = "None"
        cfg_test.chain.regionField = 'region'
        cfg_test.argTrain.cropMix = True
        cfg_test.argTrain.samplesClassifMix = True
        cfg_test.argTrain.annualClassesExtractionSource = classifications_path
        cfg_test.GlobChain.useAdditionalFeatures = False
        cfg_test.GlobChain.writeOutputs = True
        cfg_test.save(open(config_path_test, 'w'))
        config_test = SCF.serviceConfigFile(config_path_test)
        """
        TEST
        with a working directory and with temporary files on disk
        """
        #generate IOTA output directory
        IOTA2Directory.generate_directories(testPath, check_inputs=False)
        tile = "D0005H0002"
        sensors_params = SCF.iota2_parameters(
            config_path_test).get_sensors_parameters(tile)
        #shapes genereation
        commonMasks(tile, testPath, sensors_params)
        env.generate_shape_tile(["D0005H0002"], None, testPath, 2154)
        shapeRegion = os.path.join(wD, "MyFakeRegion.shp")
        area.generate_region_shape(testPath + "/envelope", shapeRegion,
                                   "region", testPath, None)
        RT.createRegionsByTiles(shapeRegion, "region", testPath + "/envelope",
                                testPath + "/shapeRegion/", None)

        #launch sampling
        addField(vector, "region", "1", str)

        data_field = config_test.getParam("chain", "dataField")
        output_path = config_test.getParam("chain", "outputPath")
        annual_crop = config_test.getParam("argTrain", 'annualCrop')
        crop_mix = config_test.getParam('argTrain', 'cropMix')
        auto_context_enable = config_test.getParam('chain',
                                                   'enable_autoContext')
        region_field = (config_test.getParam('chain', 'regionField')).lower()
        proj = config_test.getParam('GlobChain', 'proj')
        enable_cross_validation = config_test.getParam(
            'chain', 'enableCrossValidation')
        runs = config_test.getParam('chain', 'runs')
        samples_classif_mix = config_test.getParam('argTrain',
                                                   'samplesClassifMix')

        # annual_config_file = config_test.getParam('argTrain', "prevFeatures")
        output_path_annual = None
        # output_path_annual = SCF.serviceConfigFile(
        #    annual_config_file).getParam("chain", "outputPath")

        ram = 128
        w_mode = False
        folder_annual_features = config_test.getParam('argTrain',
                                                      'outputPrevFeatures')
        previous_classif_path = config_test.getParam(
            'argTrain', 'annualClassesExtractionSource')
        validity_threshold = config_test.getParam('argTrain',
                                                  'validityThreshold')
        target_resolution = config_test.getParam('chain', 'spatialResolution')
        sensors_params = SCF.iota2_parameters(
            config_path_test).get_sensors_parameters(tile)
        try:
            sar_optical_flag = config_test.getParam(
                "argTrain", "dempster_shafer_SAR_Opt_fusion")
        except Exception as exc:
            print(exc)
            sar_optical_flag = False
        VectorSampler.generate_samples({"usually": vector},
                                       wD,
                                       data_field,
                                       output_path,
                                       annual_crop,
                                       crop_mix,
                                       auto_context_enable,
                                       region_field,
                                       proj,
                                       enable_cross_validation,
                                       runs,
                                       sensors_params,
                                       sar_optical_flag,
                                       samples_classif_mix,
                                       output_path_annual,
                                       ram,
                                       w_mode,
                                       folder_annual_features,
                                       previous_classif_path,
                                       validity_threshold,
                                       target_resolution,
                                       sample_selection=self.selection_test)
        test_vector = fut.fileSearchRegEx(testPath +
                                          "/learningSamples/*sqlite")[0]

        same = []
        for key, val in list(self.expectedFeatures.items()):
            if len(fut.getFieldElement(test_vector, 'SQLite', 'code',
                                       'all')) != self.expectedFeatures[key]:
                same.append(True)
            else:
                same.append(False)

        if False in same:
            self.assertTrue(False)
        else:
            self.assertTrue(True)
        """
        TEST
        with a working directory and without temporary files on disk
        """
        testPath, featuresOutputs, wD = prepareTestsFolder(True)

        config_path_test = os.path.join(wD, "Config_TEST.cfg")
        shutil.copy(config_path, config_path_test)
        L8_rasters = os.path.join(self.iota2_directory, "data", "L8_50x50")
        cfg_test = Config(open(config_path_test))
        cfg_test.chain.outputPath = testPath
        cfg_test.chain.listTile = "D0005H0002"
        cfg_test.chain.L8Path_old = L8_rasters_old
        cfg_test.chain.L8Path = "None"
        cfg_test.chain.userFeatPath = "None"
        cfg_test.chain.regionField = 'region'
        cfg_test.argTrain.cropMix = True
        cfg_test.argTrain.samplesClassifMix = True
        cfg_test.argTrain.annualClassesExtractionSource = classifications_path
        cfg_test.GlobChain.useAdditionalFeatures = False
        cfg_test.GlobChain.writeOutputs = False
        cfg_test.save(open(config_path_test, 'w'))
        config_test = SCF.serviceConfigFile(config_path_test)

        #generate IOTA output directory
        IOTA2Directory.generate_directories(testPath, check_inputs=False)

        #shapes genereation
        vector = TUV.shape_reference_vector(self.referenceShape, "D0005H0002")
        tile = "D0005H0002"
        sensors_params = SCF.iota2_parameters(
            config_path_test).get_sensors_parameters(tile)
        #shapes genereation
        commonMasks(tile, testPath, sensors_params)
        env.generate_shape_tile(["D0005H0002"], None, testPath, 2154)
        shapeRegion = os.path.join(wD, "MyFakeRegion.shp")
        area.generate_region_shape(testPath + "/envelope", shapeRegion,
                                   "region", testPath, None)
        RT.createRegionsByTiles(shapeRegion, "region", testPath + "/envelope",
                                testPath + "/shapeRegion/", None)

        addField(vector, "region", "1", str)

        data_field = config_test.getParam("chain", "dataField")
        output_path = config_test.getParam("chain", "outputPath")
        annual_crop = config_test.getParam("argTrain", 'annualCrop')
        crop_mix = config_test.getParam('argTrain', 'cropMix')
        auto_context_enable = config_test.getParam('chain',
                                                   'enable_autoContext')
        region_field = (config_test.getParam('chain', 'regionField')).lower()
        proj = config_test.getParam('GlobChain', 'proj')
        enable_cross_validation = config_test.getParam(
            'chain', 'enableCrossValidation')
        runs = config_test.getParam('chain', 'runs')
        samples_classif_mix = config_test.getParam('argTrain',
                                                   'samplesClassifMix')

        output_path_annual = None
        ram = 128
        w_mode = False
        folder_annual_features = config_test.getParam('argTrain',
                                                      'outputPrevFeatures')
        previous_classif_path = config_test.getParam(
            'argTrain', 'annualClassesExtractionSource')
        validity_threshold = config_test.getParam('argTrain',
                                                  'validityThreshold')
        target_resolution = config_test.getParam('chain', 'spatialResolution')
        sensors_params = SCF.iota2_parameters(
            config_path_test).get_sensors_parameters(tile)
        try:
            sar_optical_flag = config_test.getParam(
                "argTrain", "dempster_shafer_SAR_Opt_fusion")
        except Exception as exc:
            print(exc)
            sar_optical_flag = False

        VectorSampler.generate_samples({"usually": vector},
                                       wD,
                                       data_field,
                                       output_path,
                                       annual_crop,
                                       crop_mix,
                                       auto_context_enable,
                                       region_field,
                                       proj,
                                       enable_cross_validation,
                                       runs,
                                       sensors_params,
                                       sar_optical_flag,
                                       samples_classif_mix,
                                       output_path_annual,
                                       ram,
                                       w_mode,
                                       folder_annual_features,
                                       previous_classif_path,
                                       validity_threshold,
                                       target_resolution,
                                       sample_selection=self.selection_test)

        test_vector = fut.fileSearchRegEx(testPath +
                                          "/learningSamples/*sqlite")[0]
        same = []
        for key, val in list(self.expectedFeatures.items()):
            if len(fut.getFieldElement(test_vector, 'SQLite', 'code',
                                       'all')) != self.expectedFeatures[key]:
                same.append(True)
            else:
                same.append(False)

        if False in same:
            self.assertTrue(False)
        else:
            self.assertTrue(True)
        """
        TEST
        without a working directory and without temporary files on disk
        """
        testPath, featuresOutputs, wD = prepareTestsFolder(True)

        config_path_test = os.path.join(wD, "Config_TEST.cfg")
        shutil.copy(config_path, config_path_test)
        L8_rasters = os.path.join(self.iota2_directory, "data", "L8_50x50")
        cfg_test = Config(open(config_path_test))
        cfg_test.chain.outputPath = testPath
        cfg_test.chain.listTile = "D0005H0002"
        cfg_test.chain.L8Path_old = L8_rasters_old
        cfg_test.chain.L8Path = "None"
        cfg_test.chain.userFeatPath = "None"
        cfg_test.chain.regionField = 'region'
        cfg_test.argTrain.cropMix = True
        cfg_test.argTrain.samplesClassifMix = True
        cfg_test.argTrain.annualClassesExtractionSource = classifications_path
        cfg_test.GlobChain.useAdditionalFeatures = False
        cfg_test.GlobChain.writeOutputs = False
        cfg_test.save(open(config_path_test, 'w'))
        config_test = SCF.serviceConfigFile(config_path_test)

        #generate IOTA output directory
        IOTA2Directory.generate_directories(testPath, check_inputs=False)

        #shapes genereation
        vector = TUV.shape_reference_vector(self.referenceShape, "D0005H0002")
        tile = "D0005H0002"
        sensors_params = SCF.iota2_parameters(
            config_path_test).get_sensors_parameters(tile)
        commonMasks(tile, testPath, sensors_params)
        env.generate_shape_tile(["D0005H0002"], None, testPath, 2154)
        shapeRegion = os.path.join(wD, "MyFakeRegion.shp")
        area.generate_region_shape(testPath + "/envelope", shapeRegion,
                                   "region", testPath, None)
        RT.createRegionsByTiles(shapeRegion, "region", testPath + "/envelope",
                                testPath + "/shapeRegion/", None)

        addField(vector, "region", "1", str)

        data_field = config_test.getParam("chain", "dataField")
        output_path = config_test.getParam("chain", "outputPath")
        annual_crop = config_test.getParam("argTrain", 'annualCrop')
        crop_mix = config_test.getParam('argTrain', 'cropMix')
        auto_context_enable = config_test.getParam('chain',
                                                   'enable_autoContext')
        region_field = (config_test.getParam('chain', 'regionField')).lower()
        proj = config_test.getParam('GlobChain', 'proj')
        enable_cross_validation = config_test.getParam(
            'chain', 'enableCrossValidation')
        runs = config_test.getParam('chain', 'runs')
        samples_classif_mix = config_test.getParam('argTrain',
                                                   'samplesClassifMix')

        output_path_annual = None
        ram = 128
        w_mode = False
        folder_annual_features = config_test.getParam('argTrain',
                                                      'outputPrevFeatures')
        previous_classif_path = config_test.getParam(
            'argTrain', 'annualClassesExtractionSource')
        validity_threshold = config_test.getParam('argTrain',
                                                  'validityThreshold')
        target_resolution = config_test.getParam('chain', 'spatialResolution')
        sensors_params = SCF.iota2_parameters(
            config_path_test).get_sensors_parameters(tile)
        try:
            sar_optical_flag = config_test.getParam(
                "argTrain", "dempster_shafer_SAR_Opt_fusion")
        except Exception as exc:
            print(exc)
            sar_optical_flag = False

        VectorSampler.generate_samples({"usually": vector},
                                       None,
                                       data_field,
                                       output_path,
                                       annual_crop,
                                       crop_mix,
                                       auto_context_enable,
                                       region_field,
                                       proj,
                                       enable_cross_validation,
                                       runs,
                                       sensors_params,
                                       sar_optical_flag,
                                       samples_classif_mix,
                                       output_path_annual,
                                       ram,
                                       w_mode,
                                       folder_annual_features,
                                       previous_classif_path,
                                       validity_threshold,
                                       target_resolution,
                                       sample_selection=self.selection_test)

        test_vector = fut.fileSearchRegEx(testPath +
                                          "/learningSamples/*sqlite")[0]
        same = []
        for key, val in list(self.expectedFeatures.items()):
            if len(fut.getFieldElement(test_vector, 'SQLite', 'code',
                                       'all')) != self.expectedFeatures[key]:
                same.append(True)
            else:
                same.append(False)

        if False in same:
            self.assertTrue(False)
        else:
            self.assertTrue(True)
        """
        TEST
        without a working directory and with temporary files on disk
        """
        testPath, featuresOutputs, wD = prepareTestsFolder(True)
        config_path_test = os.path.join(wD, "Config_TEST.cfg")
        shutil.copy(config_path, config_path_test)
        L8_rasters = os.path.join(self.iota2_directory, "data", "L8_50x50")
        cfg_test = Config(open(config_path_test))
        cfg_test.chain.outputPath = testPath
        cfg_test.chain.listTile = "D0005H0002"
        cfg_test.chain.L8Path_old = L8_rasters_old
        cfg_test.chain.L8Path = "None"
        cfg_test.chain.userFeatPath = "None"
        cfg_test.chain.regionField = 'region'
        cfg_test.argTrain.cropMix = True
        cfg_test.argTrain.samplesClassifMix = True
        cfg_test.argTrain.annualClassesExtractionSource = classifications_path
        cfg_test.GlobChain.useAdditionalFeatures = False
        cfg_test.GlobChain.writeOutputs = True
        cfg_test.save(open(config_path_test, 'w'))
        config_test = SCF.serviceConfigFile(config_path_test)
        # generate IOTA output directory
        IOTA2Directory.generate_directories(testPath, check_inputs=False)

        # shapes genereation
        vector = TUV.shape_reference_vector(self.referenceShape, "D0005H0002")
        tile = "D0005H0002"
        sensors_params = SCF.iota2_parameters(
            config_path_test).get_sensors_parameters(tile)
        commonMasks(tile, testPath, sensors_params)
        env.generate_shape_tile(["D0005H0002"], None, testPath, 2154)
        shapeRegion = os.path.join(wD, "MyFakeRegion.shp")
        area.generate_region_shape(testPath + "/envelope", shapeRegion,
                                   "region", testPath, None)
        RT.createRegionsByTiles(shapeRegion, "region", testPath + "/envelope",
                                testPath + "/shapeRegion/", None)

        addField(vector, "region", "1", str)

        data_field = config_test.getParam("chain", "dataField")
        output_path = config_test.getParam("chain", "outputPath")
        annual_crop = config_test.getParam("argTrain", 'annualCrop')
        crop_mix = config_test.getParam('argTrain', 'cropMix')
        auto_context_enable = config_test.getParam('chain',
                                                   'enable_autoContext')
        region_field = (config_test.getParam('chain', 'regionField')).lower()
        proj = config_test.getParam('GlobChain', 'proj')
        enable_cross_validation = config_test.getParam(
            'chain', 'enableCrossValidation')
        runs = config_test.getParam('chain', 'runs')
        samples_classif_mix = config_test.getParam('argTrain',
                                                   'samplesClassifMix')

        output_path_annual = None

        ram = 128
        w_mode = False
        folder_annual_features = config_test.getParam('argTrain',
                                                      'outputPrevFeatures')
        previous_classif_path = config_test.getParam(
            'argTrain', 'annualClassesExtractionSource')
        validity_threshold = config_test.getParam('argTrain',
                                                  'validityThreshold')
        target_resolution = config_test.getParam('chain', 'spatialResolution')
        sensors_params = SCF.iota2_parameters(
            config_path_test).get_sensors_parameters(tile)
        try:
            sar_optical_flag = config_test.getParam(
                "argTrain", "dempster_shafer_SAR_Opt_fusion")
        except Exception as exc:
            print(exc)
            sar_optical_flag = False

        VectorSampler.generate_samples({"usually": vector},
                                       None,
                                       data_field,
                                       output_path,
                                       annual_crop,
                                       crop_mix,
                                       auto_context_enable,
                                       region_field,
                                       proj,
                                       enable_cross_validation,
                                       runs,
                                       sensors_params,
                                       sar_optical_flag,
                                       samples_classif_mix,
                                       output_path_annual,
                                       ram,
                                       w_mode,
                                       folder_annual_features,
                                       previous_classif_path,
                                       validity_threshold,
                                       target_resolution,
                                       sample_selection=self.selection_test)

        test_vector = fut.fileSearchRegEx(testPath +
                                          "/learningSamples/*sqlite")[0]
        same = []
        for key, val in list(self.expectedFeatures.items()):
            if len(fut.getFieldElement(test_vector, 'SQLite', 'code',
                                       'all')) != self.expectedFeatures[key]:
                same.append(True)
            else:
                same.append(False)

        if False in same:
            self.assertTrue(False)
        else:
            self.assertTrue(True)
