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

# python -m unittest SamplesSelectionTests

import os
import sys
import shutil
import unittest
from iota2.Common import FileUtils as fut

IOTA2DIR = os.environ.get('IOTA2DIR')

if not IOTA2DIR:
    raise Exception("IOTA2DIR environment variable must be set")

# if all tests pass, remove 'iota2_tests_directory' which contains all
# sub-directory tests
RM_IF_ALL_OK = True


class iota_testSamplesSelection(unittest.TestCase):
    # before launching tests
    @classmethod
    def setUpClass(cls):
        # definition of local variables
        cls.group_test_name = "iota_testSamplesSelection"
        cls.iota2_tests_directory = os.path.join(IOTA2DIR, "data",
                                                 cls.group_test_name)
        cls.all_tests_ok = []

        # References
        cls.config_test = os.path.join(
            IOTA2DIR, "config", "Config_4Tuiles_Multi_FUS_Confidence.cfg")
        cls.in_shape = os.path.join(IOTA2DIR, "data", "references",
                                    "selectionSamples", "Input",
                                    "samplesSelection",
                                    "samples_region_1_seed_0.shp")
        cls.in_xml = os.path.join(IOTA2DIR, "data", "references",
                                  "selectionSamples", "Input",
                                  "samplesSelection",
                                  "samples_region_1_seed_0.xml")
        cls.in_xml_merge = os.path.join(IOTA2DIR, "data", "references",
                                        "selectionSamples", "Input",
                                        "samplesSelection", "merge_stats.xml")
        cls.features_ref = os.path.join(IOTA2DIR, "data", "references",
                                        "selectionSamples", "Input",
                                        "features", "T31TCJ")
        cls.selection_ref = os.path.join(
            IOTA2DIR, "data", "references", "selectionSamples", "Input",
            "samplesSelection",
            "T31TCJ_samples_region_1_seed_0_selection.sqlite")

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
    def test_write_xml(self):
        """
        test writing of a statistics file
        """
        import collections
        import filecmp
        from iota2.Sampling.SamplesSelection import write_xml
        from TestsUtils import cmp_xml_stat_files

        # define inputs
        samples_per_class = collections.OrderedDict([("11", 5), ("12", 6),
                                                     ("211", 5), ("32", 3),
                                                     ("31", 4), ("51", 8),
                                                     ("34", 5), ("41", 9),
                                                     ("222", 4), ("221", 4)])
        samples_per_vector = collections.OrderedDict([("1", 4), ("0", 5),
                                                      ("3", 4), ("2", 4),
                                                      ("5", 6), ("4", 5),
                                                      ("7", 9), ("6", 8),
                                                      ("9", 5), ("8", 3)])
        xml_test = os.path.join(self.test_working_directory, "test.xml")

        # launch function
        write_xml(samples_per_class, samples_per_vector, xml_test)

        # assert
        self.assertTrue(cmp_xml_stat_files(self.in_xml, xml_test),
                        msg="merge xml statistics files failed")

    def test_merge_xml(self):
        """
        test writing of a statistics file
        """
        import collections
        import filecmp
        from iota2.Sampling.SamplesSelection import write_xml
        from iota2.Sampling.SamplesSelection import merge_write_stats
        from TestsUtils import cmp_xml_stat_files

        # define inputs
        samples_per_class = collections.OrderedDict([("11", 5), ("12", 6),
                                                     ("211", 5), ("32", 3),
                                                     ("31", 4), ("51", 8),
                                                     ("34", 5), ("41", 9),
                                                     ("222", 4), ("221", 4)])
        samples_per_vector = collections.OrderedDict([("1", 4), ("0", 5),
                                                      ("3", 4), ("2", 4),
                                                      ("5", 6), ("4", 5),
                                                      ("7", 9), ("6", 8),
                                                      ("9", 5), ("8", 3)])
        xml_test_1 = os.path.join(self.test_working_directory, "test_1.xml")
        xml_test_2 = os.path.join(self.test_working_directory, "test_2.xml")
        write_xml(samples_per_class, samples_per_vector, xml_test_1)
        write_xml(samples_per_class, samples_per_vector, xml_test_2)

        # launch function
        test_merge = os.path.join(self.test_working_directory,
                                  "test_merge.xml")
        merge_write_stats([xml_test_1, xml_test_2], test_merge)

        # assert
        self.assertTrue(cmp_xml_stat_files(self.in_xml_merge, test_merge),
                        msg="merge xml statistics files failed")

    def test_split_selection(self):
        """
        test dedicated to check if split_sel function works
        """
        from iota2.Sampling.SamplesSelection import split_sel
        from Iota2Tests import random_update
        from TestsUtils import rename_table

        # prepare test input
        test_vector_name = "samples_region_1_seed_0.sqlite"
        test_vector_table = "t31tcj_samples_region_1_seed_0_selection"
        test_vector = os.path.join(self.test_working_directory,
                                   test_vector_name)
        shutil.copy(self.selection_ref, test_vector)

        # update "nb_feat" features to a new "new_tile_name" tile's name
        nb_feat = 10
        new_tile_name = "T31TDJ"
        random_update(test_vector, test_vector_table, "tile_o", new_tile_name,
                      nb_feat)
        rename_table(test_vector,
                     old_table_name=test_vector_table,
                     new_table_name="output")
        # launch function
        new_files = split_sel(test_vector, ["T31TCJ", new_tile_name],
                              self.test_working_directory, "EPSG:2154")
        # assert
        nb_features_origin = len(
            fut.getFieldElement(self.selection_ref,
                                driverName="SQLite",
                                field="tile_o",
                                mode="all",
                                elemType="str"))
        nb_features_t31tcj = len(
            fut.getFieldElement(new_files[0],
                                driverName="SQLite",
                                field="tile_o",
                                mode="all",
                                elemType="str"))
        nb_features_t31tdj = len(
            fut.getFieldElement(new_files[1],
                                driverName="SQLite",
                                field="tile_o",
                                mode="all",
                                elemType="str"))
        self.assertTrue(nb_features_t31tdj == nb_feat,
                        msg="split samples selection failed")
        self.assertTrue(nb_features_origin == nb_features_t31tdj +
                        nb_features_t31tcj,
                        msg="split samples selection failed")

    def test_update_flags(self):
        """
        """
        from iota2.Sampling.SamplesSelection import update_flags

        # prepare test input
        test_vector_name = "T31TCJ_samples_region_1_seed_1_selection.sqlite"
        test_vector_table = "t31tcj_samples_region_1_seed_0_selection"
        test_vector = os.path.join(self.test_working_directory,
                                   test_vector_name)
        shutil.copy(self.selection_ref, test_vector)

        update_flags(test_vector, 2, table_name=test_vector_table)

        # assert
        updated_flag = "XXXX"
        nb_features_origin = len(
            fut.getFieldElement(self.selection_ref,
                                driverName="SQLite",
                                field="seed_0",
                                mode="all",
                                elemType="str"))
        features_test = fut.getFieldElement(test_vector,
                                            driverName="SQLite",
                                            field="seed_0",
                                            mode="all",
                                            elemType="str")
        nb_features_test_updated = features_test.count(updated_flag)
        self.assertTrue(nb_features_origin == nb_features_test_updated,
                        msg="update features failed")

    def test_samples_selection(self):
        """
        test sampling of a shape file (main function of SamplesSelection.py)
        """
        from iota2.Sampling.SamplesSelection import samples_selection
        from iota2.Common import IOTA2Directory
        from iota2.Common import ServiceConfigFile as SCF
        from iota2.Tests.UnitTests.Iota2Tests import compareSQLite
        from iota2.Common.FileUtils import cpShapeFile
        from iota2.Common import FileUtils as fut
        # prepare test input
        cfg = SCF.serviceConfigFile(self.config_test)
        cfg.setParam(
            "chain", "outputPath",
            os.path.join(self.test_working_directory, "samplesSelTest"))
        cfg.setParam("chain", "runs", 2)
        cfg.setParam("argTrain", "sampleSelection", {
            "sampler": "random",
            "strategy": "all"
        })
        # create IOTA2 directories
        IOTA2Directory.generate_directories(os.path.join(
            self.test_working_directory, "samplesSelTest"),
                                            check_inputs=False)
        shutil.copytree(
            self.features_ref,
            os.path.join(self.test_working_directory, "samplesSelTest",
                         "features", "T31TCJ"))
        shutil.copy(
            self.in_xml,
            os.path.join(self.test_working_directory, "samplesSelTest",
                         "samplesSelection",
                         "T31TCJ_region_1_seed_0_stats.xml"))
        _, in_shape_name = os.path.split(self.in_shape)
        in_shape_dir = os.path.join(self.test_working_directory,
                                    "samplesSelTest", "samplesSelection")
        in_shape = os.path.join(in_shape_dir, in_shape_name)
        cpShapeFile(self.in_shape.replace(".shp", ""),
                    in_shape.replace(".shp", ""),
                    extensions=[".prj", ".shp", ".dbf", ".shx"])

        #~ # launch function
        output_path = cfg.getParam("chain", "outputPath")
        runs = cfg.getParam('chain', 'runs')
        epsg = cfg.getParam('GlobChain', 'proj')
        random_seed = cfg.getParam('chain', 'random_seed')
        data_field = cfg.getParam('chain', 'dataField').lower()
        parameters = dict(cfg.getParam('argTrain', 'sampleSelection'))
        masks_name = "MaskCommunSL.tif"
        samples_selection(in_shape, self.test_working_directory, output_path,
                          runs, epsg, masks_name, parameters, data_field,
                          random_seed)
        #~ # assert
        selection_test = fut.FileSearch_AND(
            os.path.join(self.test_working_directory, "samplesSelTest"), True,
            os.path.basename(self.selection_ref))[0]
        same = compareSQLite(self.selection_ref,
                             selection_test,
                             CmpMode='coordinates')
        self.assertTrue(same, msg="sample selection generation failed")
