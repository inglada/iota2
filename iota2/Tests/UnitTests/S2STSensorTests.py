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
import numpy as np

IOTA2DIR = os.environ.get('IOTA2DIR')
RM_IF_ALL_OK = True

iota2_script = os.path.join(IOTA2DIR, "iota2")
sys.path.append(iota2_script)

from Common import FileUtils as fut

class iota_testS2STSensor(unittest.TestCase):
    #before launching tests
    @classmethod
    def setUpClass(self):

        # definition of local variables
        self.group_test_name = "iota_testS2STSensor"
        self.iota2_tests_directory = os.path.join(IOTA2DIR, "data", self.group_test_name)
        self.all_tests_ok = []
        self.test_working_directory = None
        if os.path.exists(self.iota2_tests_directory):
            shutil.rmtree(self.iota2_tests_directory)
        os.mkdir(self.iota2_tests_directory)

        self.config_test = os.path.join(IOTA2DIR, "config", "Config_4Tuiles_Multi_FUS_Confidence.cfg")
        
        # generate fake input data
        self.MTD_files = [os.path.join(IOTA2DIR, "data", "MTD_MSIL2A_20190506.xml"),
                          os.path.join(IOTA2DIR, "data", "MTD_MSIL2A_20190501.xml")]
        

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

        #Create test data

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

    def generate_data_tree(self, directory, MTD_S2ST_date, s2st_ext="jp2"):
        """generate a fake Sen2Cor data
        
        TODO : replace this function by downloading a Sen2Cor data from PEPS.

        Return
        ------
        products : list
            list of data ready to be generated
        """
        from xml.dom.minidom import parse
        import xml.dom.minidom
        from Common.FileUtils import ensure_dir

        ensure_dir(directory)

        DOMTree = xml.dom.minidom.parse(MTD_S2ST_date)
        collection = DOMTree.documentElement
        general_info_node = collection.getElementsByTagName("n1:General_Info")
        date_dir = general_info_node[0].getElementsByTagName('PRODUCT_URI')[0].childNodes[0].data

        products = []
        for Product_Organisation_nodes in general_info_node[0].getElementsByTagName('Product_Organisation'):
            img_list_nodes = Product_Organisation_nodes.getElementsByTagName("IMAGE_FILE")
            for img_list in img_list_nodes:
                new_prod = os.path.join(directory, date_dir, "{}.{}".format(img_list.childNodes[0].data,
                                                                            s2st_ext))
                new_prod_dir, _ = os.path.split(new_prod)
                ensure_dir(new_prod_dir)
                products.append(new_prod)
        return products


    def generate_data(self, MTD_files):
        """
        """
        from TestsUtils import arrayToRaster
        
        fake_raster = [np.array([[10, 55, 61],
                                 [100, 56, 42],
                                 [1, 42, 29]][::-1])]
        fake_scene_classification = [np.array([[2, 0, 4],
                                               [0, 4, 2],
                                               [1, 1, 10]][::-1])]
        for mtd in MTD_files:
            prod_list = self.generate_data_tree(os.path.join(self.test_working_directory, "T31TCJ"),
                                                mtd)
            for prod in prod_list:
                if '10m.jp2' in prod:
                    pixSize = 10
                if '20m.jp2' in prod:
                    pixSize = 20
                if '60m.jp2' in prod:
                    pixSize = 60
                if "_SCL_" in prod:
                    array_raster = fake_scene_classification
                else:
                    array_raster = fake_raster
                #~ output_driver has to be 'GTiff' even if S2ST are jp2
                arrayToRaster(array_raster, prod, output_driver="GTiff",
                              output_format="int",
                              pixSize=pixSize, originX=300000, originY = 4900020,
                              epsg_code=32631)

    #Tests definitions
    def test_Sensor(self):
        """
        """
        from config import Config
        from Common import IOTA2Directory
        from Common import ServiceConfigFile as SCF

        from Sensors.Sensors_container import Sensors_container
        from Common.FileUtils import FileSearch_AND
        from TestsUtils import rasterToArray
        from TestsUtils import compute_brightness_from_vector

        # s2 sen2cor data
        self.generate_data(self.MTD_files)

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
        cfg_test.chain.S2Path = "None"
        cfg_test.chain.S2_S2C_Path = S2ST_data
        cfg_test.chain.userFeatPath = "None"
        cfg_test.chain.regionField = 'region'
        cfg_test.argTrain.cropMix = False
        cfg_test.argTrain.samplesClassifMix = False
        cfg_test.argTrain.annualClassesExtractionSource = None
        cfg_test.GlobChain.useAdditionalFeatures = False
        cfg_test.GlobChain.writeOutputs = False
        cfg_test.save(open(config_path_test, 'w'))
        
        cfg = SCF.serviceConfigFile(config_path_test)
        IOTA2Directory.GenerateDirectories(cfg)

        # Launch test
        tile_name = "T31TCJ"
        working_dir = None
        sensors = Sensors_container(config_path_test, tile_name, working_dir)
        sensors.sensors_preprocess()

        # produce the time series
        time_s = sensors.get_sensors_time_series()
        for sensor_name ,((time_s_app, app_dep), features_labels) in time_s:
            time_s_app.ExecuteAndWriteOutput()
        # produce the time series gapFilled
        time_s_g = sensors.get_sensors_time_series_gapfilling()
        for sensor_name ,((time_s_g_app, app_dep), features_labels) in time_s_g:
            time_s_g_app.ExecuteAndWriteOutput()
        # produce features
        features = sensors.get_sensors_features()
        for sensor_name ,((features_app, app_dep), features_labels) in features:
            features_app.ExecuteAndWriteOutput()
        
        feature_array = rasterToArray(FileSearch_AND(os.path.join(testPath), True, "_Features.tif")[0])
        data_value, brightness_value = feature_array[:, 0, 2][0:-1], int(feature_array[:, 0, 2][-1])
        theorical_brightness = int(compute_brightness_from_vector(data_value))
        self.assertEqual(theorical_brightness, brightness_value)
