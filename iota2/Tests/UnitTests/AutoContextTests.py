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

IOTA2_SCRIPT = os.path.join(IOTA2DIR, "iota2")
sys.path.append(IOTA2_SCRIPT)


class iota_testAutoContext(unittest.TestCase):
    # before launching tests
    @classmethod
    def setUpClass(cls):

        from iota2.Common.FileUtils import ensure_dir
        from TestsUtils import generate_fake_s2_data

        # definition of local variables
        cls.originX = 566377
        cls.originY = 6284029
        cls.group_test_name = "iota_testAutoContext"
        cls.iota2_tests_directory = os.path.join(IOTA2DIR, "data",
                                                 cls.group_test_name)
        cls.config_test = os.path.join(
            IOTA2DIR, "config", "Config_4Tuiles_Multi_FUS_Confidence.cfg")
        cls.ref_data = os.path.join(IOTA2DIR, "data", "references",
                                    "formatting_vectors", "Input",
                                    "formattingVectors", "T31TCJ.shp")
        cls.tile_name = "T31TCJ"
        cls.all_tests_ok = []
        cls.test_working_directory = None
        if os.path.exists(cls.iota2_tests_directory):
            shutil.rmtree(cls.iota2_tests_directory, ignore_errors=True)
        os.mkdir(cls.iota2_tests_directory)

        # generate permanent fake data
        cls.fake_data_dir = os.path.join(cls.iota2_tests_directory, "fake_s2")
        ensure_dir(cls.fake_data_dir)
        generate_fake_s2_data(cls.fake_data_dir, "T31TCJ",
                              ["20190909", "20190919", "20190929"])

    #after launching tests
    @classmethod
    def tearDownClass(self):
        print("{} ended".format(self.group_test_name))
        if RM_IF_ALL_OK and all(self.all_tests_ok):
            shutil.rmtree(self.iota2_tests_directory, ignore_errors=True)

    #before launching a test
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
        if exc_list and exc_list[-1][0] is self:
            return exc_list[-1][1]

    #after launching a test, remove test's data if test succeed
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
            shutil.rmtree(self.test_working_directory, ignore_errors=True)

    def generate_cfg_file(self, ref_cfg, test_cfg):
        """
        """
        from config import Config
        shutil.copy(ref_cfg, test_cfg)

        test_path = os.path.join(self.test_working_directory, "RUN")
        cfg_test = Config(open(test_cfg))
        cfg_test.chain.outputPath = test_path
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
        cfg_test.save(open(test_cfg, 'w'))
        return test_path

    def prepapre_data_ref(self, in_vector, out_vector, ref_img):
        """
        """
        from iota2.Common.OtbAppBank import CreateSampleSelectionApplication
        from iota2.Common.OtbAppBank import CreatePolygonClassStatisticsApplication

        stat = out_vector.replace(".sqlite", ".xml")
        CreatePolygonClassStatisticsApplication({
            "in": ref_img,
            "vec": in_vector,
            "field": "CODE",
            "out": stat
        }).ExecuteAndWriteOutput()
        CreateSampleSelectionApplication({
            "in": ref_img,
            "vec": in_vector,
            "field": "CODE",
            "strategy": "all",
            "instats": stat,
            "out": out_vector
        }).ExecuteAndWriteOutput()
        os.remove(stat)

    def prepare_autoContext_data_ref(self, slic_seg, config_path_test):
        """
        """
        from iota2.VectorTools.AddField import addField
        from iota2.Sampling.SuperPixelsSelection import merge_ref_super_pix
        from iota2.Sampling.SplitSamples import split_superpixels_and_reference
        from iota2.Common.FileUtils import FileSearch_AND
        from iota2.Common.OtbAppBank import CreateSampleSelectionApplication
        from iota2.Common.OtbAppBank import CreatePolygonClassStatisticsApplication
        from iota2.Common.OtbAppBank import CreateSampleExtractionApplication
        from iota2.Common.GenerateFeatures import generateFeatures
        from iota2.Common import ServiceConfigFile as SCF

        raster_ref = FileSearch_AND(self.fake_data_dir, True, ".tif")[0]
        CreatePolygonClassStatisticsApplication({
            "in":
            raster_ref,
            "vec":
            self.ref_data,
            "field":
            "CODE",
            "out":
            os.path.join(self.test_working_directory, "stats.xml")
        }).ExecuteAndWriteOutput()
        ref_sampled = os.path.join(
            self.test_working_directory,
            "T31TCJ_samples_region_1_seed_0_selection.sqlite")
        CreateSampleSelectionApplication({
            "in":
            raster_ref,
            "vec":
            self.ref_data,
            "field":
            "CODE",
            "strategy":
            "all",
            "instats":
            os.path.join(self.test_working_directory, "stats.xml"),
            "out":
            ref_sampled
        }).ExecuteAndWriteOutput()

        cfg = SCF.serviceConfigFile(config_path_test)
        features, feat_labels, dep = generateFeatures(None, "T31TCJ", cfg)
        extraction = CreateSampleExtractionApplication({
            "in": features,
            "vec": ref_sampled,
            "field": "code",
            "outfield.list.names": feat_labels,
            "outfield": "list"
        })
        extraction.ExecuteAndWriteOutput()

        addField(ref_sampled,
                 "newregion",
                 valueField="1",
                 valueType=str,
                 driver_name="SQLite")
        os.remove(os.path.join(self.test_working_directory, "stats.xml"))

        merge_ref_super_pix(
            {
                "selection_samples": ref_sampled,
                "SLIC": slic_seg
            }, "code", "superpix", "is_superpix", "newregion")

        learning_vector = os.path.join(
            self.test_working_directory,
            "T31TCJ_region_1_seed0_Samples_learn.sqlite")
        shutil.move(ref_sampled, learning_vector)

        ref, superpix = split_superpixels_and_reference(
            learning_vector, superpix_column="is_superpix")

        return learning_vector, superpix

    #Tests definitions
    def test_sampling_features_from_raster(self):
        """non-regression test, check the ability of adding features in database
        by sampling classification raster
        """
        import numpy as np
        from collections import Counter
        from iota2.Sampling.SuperPixelsSelection import move_annual_samples_position
        import TestsUtils

        mask_array = TestsUtils.fun_array("iota2_binary")
        random_classif_mask_path = os.path.join(self.test_working_directory,
                                                "Classif_Seed_0.tif")

        validity_array = np.full(mask_array.shape, 1)
        validity_path = os.path.join(self.test_working_directory,
                                     "PixelsValidity.tif")
        region_path = os.path.join(self.test_working_directory,
                                   "mask_region.tif")
        TestsUtils.arrayToRaster(validity_array,
                                 validity_path,
                                 pixSize=10,
                                 originX=self.originX,
                                 originY=self.originY)
        TestsUtils.arrayToRaster(validity_array,
                                 region_path,
                                 pixSize=10,
                                 originX=self.originX,
                                 originY=self.originY)

        ref_data_sampled = os.path.join(self.test_working_directory,
                                        "dataBase.sqlite")

        self.prepapre_data_ref(in_vector=self.ref_data,
                               out_vector=ref_data_sampled,
                               ref_img=region_path)

        # test : all annual labels are in dataBase and classifications
        labels = [12, 31, 32, 41, 211, 222]
        annual_labels = ["12", "31"]
        annual_labels_int = [int(elem) for elem in annual_labels]
        random_classif_array = np.random.choice(labels,
                                                size=mask_array.shape,
                                                replace=True)
        random_classif_array_mask = random_classif_array * mask_array
        TestsUtils.arrayToRaster(random_classif_array_mask,
                                 random_classif_mask_path,
                                 pixSize=10,
                                 originX=self.originX,
                                 originY=self.originY)
        move_annual_samples_position(
            samples_position=ref_data_sampled,
            dataField="code",
            annual_labels=annual_labels,
            classification_raster=random_classif_mask_path,
            validity_raster=validity_path,
            region_mask=region_path,
            validity_threshold=0,
            tile_origin_field_value=("tile_o", "T31TCJ"),
            seed_field_value=("seed_0", "learn"),
            region_field_value=("region", "1"))
        # assert
        raster_values = TestsUtils.compare_vector_raster(
            in_vec=ref_data_sampled,
            vec_field="code",
            field_values=annual_labels_int,
            in_img=random_classif_mask_path)
        values_counter = Counter(raster_values)
        exist_in_annual = [
            value in annual_labels_int for value in values_counter.keys()
        ]
        self.assertTrue(all(exist_in_annual))

        # test : only one annual label in dataBase
        labels = [12, 31, 32, 41, 211, 222]
        annual_labels = ["12"]
        annual_labels_int = [int(elem) for elem in annual_labels]
        random_classif_array = np.random.choice(labels,
                                                size=mask_array.shape,
                                                replace=True)
        random_classif_array_mask = random_classif_array * mask_array
        TestsUtils.arrayToRaster(random_classif_array_mask,
                                 random_classif_mask_path,
                                 pixSize=10,
                                 originX=self.originX,
                                 originY=self.originY)

        move_annual_samples_position(
            samples_position=ref_data_sampled,
            dataField="code",
            annual_labels=annual_labels,
            classification_raster=random_classif_mask_path,
            validity_raster=validity_path,
            region_mask=region_path,
            validity_threshold=0,
            tile_origin_field_value=("tile_o", "T31TCJ"),
            seed_field_value=("seed_0", "learn"),
            region_field_value=("region", "1"))
        # assert
        raster_values = TestsUtils.compare_vector_raster(
            in_vec=ref_data_sampled,
            vec_field="code",
            field_values=annual_labels_int,
            in_img=random_classif_mask_path)
        values_counter = Counter(raster_values)
        exist_in_annual = [
            value in annual_labels_int for value in values_counter.keys()
        ]
        self.assertTrue(all(exist_in_annual))

        # test : no annual labels in classifications
        labels = [12, 31, 32, 41, 211, 222]
        annual_labels = ["111", "112"]
        annual_labels_int = [int(elem) for elem in annual_labels]
        random_classif_array = np.random.choice(labels,
                                                size=mask_array.shape,
                                                replace=True)
        random_classif_array_mask = random_classif_array * mask_array
        TestsUtils.arrayToRaster(random_classif_array_mask,
                                 random_classif_mask_path,
                                 pixSize=10,
                                 originX=self.originX,
                                 originY=self.originY)

        move_annual_samples_position(
            samples_position=ref_data_sampled,
            dataField="code",
            annual_labels=annual_labels,
            classification_raster=random_classif_mask_path,
            validity_raster=validity_path,
            region_mask=region_path,
            validity_threshold=0,
            tile_origin_field_value=("tile_o", "T31TCJ"),
            seed_field_value=("seed_0", "learn"),
            region_field_value=("region", "1"))
        # assert
        raster_values = TestsUtils.compare_vector_raster(
            in_vec=ref_data_sampled,
            vec_field="code",
            field_values=annual_labels_int,
            in_img=random_classif_mask_path)
        values_counter = Counter(raster_values)
        self.assertTrue(len(values_counter) == 0)

    def test_slic(self):
        """non-regression test, check if SLIC could be performed
        """
        from iota2.Common import IOTA2Directory
        from iota2.Common import ServiceConfigFile as SCF
        from iota2.Segmentation import segmentation
        from iota2.Common.FileUtils import FileSearch_AND
        from iota2.Sensors.Sensors_container import sensors_container

        # config file
        config_path_test = os.path.join(self.test_working_directory,
                                        "Config_TEST.cfg")
        test_path = self.generate_cfg_file(self.config_test, config_path_test)

        IOTA2Directory.generate_directories(test_path, check_inputs=False)

        slic_working_dir = os.path.join(self.test_working_directory,
                                        "slic_tmp")
        iota2_dico = SCF.iota2_parameters(
            config_path_test).get_sensors_parameters(self.tile_name)
        sensors = sensors_container(self.tile_name, None,
                                    self.test_working_directory, **iota2_dico)
        sensors.sensors_preprocess()

        # Launch test
        segmentation.slicSegmentation(self.tile_name,
                                      config_path_test,
                                      ram=128,
                                      working_dir=slic_working_dir,
                                      force_spw=1)

        # as SLIC algorithm contains random variables, the raster's content
        # could not be tested
        self.assertTrue(len(
            FileSearch_AND(
                os.path.join(test_path, "features", self.tile_name, "tmp"),
                True, "SLIC_{}".format(self.tile_name))) == 1,
                        msg="SLIC algorithm failed")

    def test_train_and_classify(self):
        """test autoContext training
        """
        import re
        from iota2.Common import IOTA2Directory
        from iota2.Common import ServiceConfigFile as SCF
        from iota2.Common.FileUtils import FileSearch_AND
        from iota2.Common.FileUtils import getFieldElement
        from iota2.Segmentation import segmentation
        from iota2.Learning.trainAutoContext import train_autoContext
        from iota2.Classification.ImageClassifier import autoContext_launch_classif
        from iota2.Sensors.Sensors_container import sensors_container
        from iota2.Common.OtbAppBank import CreateBandMathApplication
        from iota2.Tests.UnitTests.TestsUtils import test_raster_unique_value

        # config file
        config_path_test = os.path.join(self.test_working_directory,
                                        "Config_TEST.cfg")
        test_path = self.generate_cfg_file(self.config_test, config_path_test)
        IOTA2Directory.generate_directories(test_path, check_inputs=False)
        autocontext_working_dir = os.path.join(self.test_working_directory,
                                               "autoContext_tmp")
        slic_working_dir = os.path.join(self.test_working_directory,
                                        "autoContext_tmp")
        iota2_dico = SCF.iota2_parameters(
            config_path_test).get_sensors_parameters(self.tile_name)
        sensors = sensors_container(self.tile_name, None,
                                    self.test_working_directory, **iota2_dico)
        sensors.sensors_preprocess()

        segmentation.slicSegmentation(self.tile_name,
                                      config_path_test,
                                      ram=128,
                                      working_dir=slic_working_dir,
                                      force_spw=1)

        slic_seg = FileSearch_AND(
            os.path.join(test_path, "features", self.tile_name, "tmp"), True,
            "SLIC_{}".format(self.tile_name))[0]

        train_auto_data_ref, superpix_data = self.prepare_autoContext_data_ref(
            slic_seg, config_path_test)

        parameter_dict = {
            "model_name": "1",
            "seed": "0",
            "list_learning_samples": [train_auto_data_ref],
            "list_superPixel_samples": [superpix_data],
            "list_tiles": ["T31TCJ"],
            "list_slic": [slic_seg]
        }
        # launch tests

        # training
        e = None
        try:
            train_autoContext(parameter_dict,
                              config_path_test,
                              RAM=128,
                              WORKING_DIR=autocontext_working_dir)
        except Exception as e:
            print(e)

        # Asserts training
        self.assertTrue(e is None, msg="train_autoContext failed")

        models = FileSearch_AND(os.path.join(test_path, "model"), True,
                                "model_it_", ".rf")
        self.assertTrue(len(models) == 4)

        # classification
        tile_raster = FileSearch_AND(self.fake_data_dir, True,
                                     "BINARY_MASK.tif")[0]
        tile_mask = os.path.join(autocontext_working_dir,
                                 "{}_tile_mask.tif".format(self.tile_name))
        CreateBandMathApplication({
            "il": [tile_raster],
            "out": tile_mask,
            "exp": "1"
        }).ExecuteAndWriteOutput()

        labels = getFieldElement(train_auto_data_ref,
                                 driverName="SQLite",
                                 field="code",
                                 mode="unique",
                                 elemType="str")
        parameters_dict = {
            "model_name":
            "1",
            "seed_num":
            0,
            "tile":
            self.tile_name,
            "tile_segmentation":
            slic_seg,
            "tile_mask":
            tile_mask,
            "labels_list":
            labels,
            "model_list":
            sorted(models,
                   key=lambda x: int(re.findall("\d", os.path.basename(x))[0]))
        }
        autoContext_launch_classif(parameters_dict,
                                   config_path_test,
                                   128,
                                   WORKING_DIR=autocontext_working_dir)

        # Asserts classifications
        classif = FileSearch_AND(os.path.join(test_path, "classif"), True,
                                 "Classif_T31TCJ_model_1_seed_0.tif")[0]
        confidence = FileSearch_AND(os.path.join(test_path, "classif"), True,
                                    "T31TCJ_model_1_confidence_seed_0.tif")[0]

        classif_unique_0 = test_raster_unique_value(classif, 0)
        confidence_unique_0 = test_raster_unique_value(confidence, 0)
        self.assertTrue(
            classif_unique_0 == False,
            msg=("AutoContext Classifications failed : classification contains"
                 " only 0 values"))
        self.assertTrue(
            confidence_unique_0 == False,
            msg=("AutoContext Classifications failed : confidence contains "
                 "only 0 values"))
