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

# python -m unittest ObiaZonalStatisticsTests

import os
import sys
import shutil
import unittest

IOTA2DIR = os.environ.get('IOTA2DIR')

if not IOTA2DIR:
    raise Exception("IOTA2DIR environment variable must be set")

# if all tests pass, remove 'iota2_tests_directory' which contains all
# sub-directory tests
RM_IF_ALL_OK = True

IOTA2_SCRIPTS = IOTA2DIR + "/iota2"
sys.path.append(IOTA2_SCRIPTS)

from iota2.Common import FileUtils as fut


class iota_testObiaZonalStatistics(unittest.TestCase):
    # before launching tests
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.group_test_name = "iota_testObiaZonalStatistics"
        self.iota2_tests_directory = os.path.join(IOTA2DIR, "data",
                                                  self.group_test_name)
        self.all_tests_ok = []

        # References
        self.config_test = os.path.join(IOTA2DIR, "data", "references",
                                        "ObiaLearningZonalStatistics",
                                        "config_obia.cfg")
        self.inLearnSamplesFolder = os.path.join(
            IOTA2DIR, "data", "references", "ObiaLearningZonalStatistics",
            "Input", "segmentation")
        self.in_seg = os.path.join(IOTA2DIR, "data", "references",
                                   "ObiaSplitSegmentationByTiles", "Input",
                                   "seg_input", "seg_input.tif")
        self.inTilesSamplesFolder = os.path.join(IOTA2DIR, "data",
                                                 "references",
                                                 "ObiaTilesZonalStatistics",
                                                 "Input", "segmentation")
        self.inSensorFolder = os.path.join(IOTA2DIR, "data", "references",
                                           "ObiaLearningZonalStatistics",
                                           "Input", "sensor_data")
        self.inRegionFolder = os.path.join(IOTA2DIR, "data", "references",
                                           "ObiaTilesZonalStatistics", "Input",
                                           "shapeRegion")
        self.learningSamplesOutputFolder = os.path.join(
            IOTA2DIR, "data", "references", "ObiaLearningZonalStatistics",
            "Output", "learningSamples")
        self.tilesSamplesOutputFolder = os.path.join(IOTA2DIR, "data",
                                                     "references",
                                                     "ObiaLearningSamples",
                                                     "Output", "tilesSamples")

        # Tests directory
        self.test_working_directory = None
        if os.path.exists(self.iota2_tests_directory):
            shutil.rmtree(self.iota2_tests_directory)
        os.mkdir(self.iota2_tests_directory)

    # after launching all tests
    @classmethod
    def tearDownClass(self):
        print("{} ended".format(self.group_test_name))
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
        self.test_working_directory = os.path.join(self.iota2_tests_directory,
                                                   test_name)
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
            result = getattr(self, '_outcomeForDoCleanups',
                             self._resultForDoCleanups)
        error = self.list2reason(result.errors)
        failure = self.list2reason(result.failures)
        ok = not error and not failure

        self.all_tests_ok.append(ok)
        if ok:
            shutil.rmtree(self.test_working_directory)

    # Tests definitions
    def test_learning_zonal_statistics(self):
        """
        test compute statistics for segment of learning samples
        """
        from iota2.Sampling.SamplesZonalStatistics import learning_samples_zonal_statistics
        from iota2.Common import IOTA2Directory
        from iota2.Common import ServiceConfigFile as SCF
        from iota2.Common.FileUtils import serviceCompareVectorFile
        import glob

        # prepare test input
        with open(self.config_test) as f:
            txt = ''
            for l in f:
                if ' outputPath' in l:
                    txt += (l.split(":")[0] + ":'" +
                            self.test_working_directory + "'\n")
                elif 'S2Path' in l:
                    txt += (l.split(":")[0] + ":'" + os.path.join(
                        self.test_working_directory, "sensor_data") + "'\n")
                else:
                    txt += l
        with open(self.config_test, 'w') as f:
            f.write(txt)
        sensors_parameters = SCF.iota2_parameters(
            self.config_test).get_sensors_parameters("T38KPD")
        # cfg = SCF.serviceConfigFile(self.config_test)
        region_tiles_seed = [(1, ['T38KPD', 'T38KPE'], 0),
                             (1, ['T38KPD', 'T38KPE'], 1), (2, ['T38KPD'], 0),
                             (2, ['T38KPD'], 1)]

        # create IOTA2 directories
        IOTA2Directory.generate_directories(self.test_working_directory,
                                            check_inputs=False,
                                            obia_seg_path=self.in_seg)
        shutil.rmtree(os.path.join(self.test_working_directory,
                                   "segmentation"))
        shutil.copytree(
            self.inLearnSamplesFolder,
            os.path.join(self.test_working_directory, "segmentation"))
        shutil.copytree(
            self.inSensorFolder,
            os.path.join(self.test_working_directory, "sensor_data"))

        # launch function
        for x in region_tiles_seed:
            learning_samples_zonal_statistics(
                self.test_working_directory, x, sensors_parameters,
                os.path.join(self.test_working_directory, "learningSamples"))
        # assert
        shps_to_verify = glob.glob(
            os.path.join(self.learningSamplesOutputFolder, '*.shp'))
        compare_vector = serviceCompareVectorFile()
        for shp in shps_to_verify:
            out_shp = os.path.join(self.test_working_directory,
                                   "learningSamples", os.path.basename(shp))
            same = compare_vector.testSameShapefiles(shp, out_shp)
            self.assertTrue(same, msg="segmentation split generation failed")

    # Tests definitions
    def test_tiles_zonal_statistics(self):
        """
        test compute statistics for segment of each tile
        """
        from iota2.Sampling.SamplesZonalStatistics import tile_samples_zonal_statistics
        from iota2.Common import IOTA2Directory
        from iota2.Common import ServiceConfigFile as SCF
        from iota2.Common.FileUtils import serviceCompareVectorFile
        import glob

        # prepare test input
        with open(self.config_test) as f:
            txt = ''
            for l in f:
                if ' outputPath' in l:
                    txt += (l.split(":")[0] + ":'" +
                            self.test_working_directory + "'\n")
                elif 'S2Path' in l:
                    txt += (l.split(":")[0] + ":'" + os.path.join(
                        self.test_working_directory, "sensor_data") + "'\n")
                else:
                    txt += l
        with open(self.config_test, 'w') as f:
            f.write(txt)

        # cfg = SCF.serviceConfigFile(self.config_test)
        tiles = ['T38KPD', 'T38KPE']
        region_path = None
        sensors_parameters = SCF.iota2_parameters(
            self.config_test).get_sensors_parameters("T38KPD")
        # create IOTA2 directories
        IOTA2Directory.generate_directories(self.test_working_directory,
                                            check_inputs=False,
                                            obia_seg_path=self.in_seg)
        shutil.rmtree(os.path.join(self.test_working_directory,
                                   "segmentation"))
        shutil.rmtree(os.path.join(self.test_working_directory, "shapeRegion"))
        shutil.copytree(
            self.inTilesSamplesFolder,
            os.path.join(self.test_working_directory, "segmentation"))
        shutil.copytree(
            self.inSensorFolder,
            os.path.join(self.test_working_directory, "sensor_data"))
        shutil.copytree(
            self.inRegionFolder,
            os.path.join(self.test_working_directory, "shapeRegion"))

        # launch function
        for tile in tiles:
            tile_samples_zonal_statistics(
                self.test_working_directory, tile, sensors_parameters,
                region_path,
                os.path.join(self.test_working_directory, "tilesSamples"))
        # assert
        for tile in tiles:
            shps_to_verify = glob.glob(
                os.path.join(self.tilesSamplesOutputFolder, tile, '*.shp'))
            compare_vector = serviceCompareVectorFile()
            for shp in shps_to_verify:
                out_shp = os.path.join(self.test_working_directory,
                                       "tilesSamples", tile,
                                       os.path.basename(shp))
                same = compare_vector.testSameShapefiles(shp, out_shp)
                self.assertTrue(same,
                                msg="segmentation split generation failed")

    def test_additional_parameter(self):
        """
        test Zonal Statistic application with the "inzone.vector.iddatafield" parameter
        """
        import otbApplication as otb

        app = otb.Registry.CreateApplication("ZonalStatistics")
        if app is None:
            result = False
        else:
            try:
                app.SetParameterString("inzone.vector.iddatafield", "test")
                result = True
            except RunTimeError:
                result = False
        self.assertTrue(
            result,
            msg=
            'ZonalStatistics application has no iddatafield parameter, please apply ZonalStatistics patch and recompile OTB'
        )
