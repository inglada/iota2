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

import unittest
import os
import sys
import filecmp
from iota2.Common import FileUtils as fu
from iota2.Sampling import DimensionalityReduction as DR
import iota2.Common.ServiceConfigFile as SCF

IOTA2DIR = os.environ.get('IOTA2DIR')
IOTA2_SCRIPT = os.path.join(IOTA2DIR, "iota2")
sys.path.append(IOTA2_SCRIPT)

IOTA2_DATATEST = IOTA2DIR + "/data/"


class DimensionalityReductionTests(unittest.TestCase):
    def setUp(self):
        self.input_sample_file_name = IOTA2_DATATEST + 'dim_red_samples.sqlite'
        self.target_dimension = 6
        self.fl_date = [
            'landsat8_b1_20140118', 'landsat8_b2_20140118',
            'landsat8_b3_20140118', 'landsat8_b4_20140118',
            'landsat8_b5_20140118', 'landsat8_b6_20140118',
            'landsat8_b7_20140118', 'landsat8_ndvi_20140118',
            'landsat8_ndwi_20140118', 'landsat8_brightness_20140118'
        ]
        self.stats_file = os.path.join(IOTA2_DATATEST, 'dim_red_stats.xml')
        self.test_stats_file = os.path.join(IOTA2_DATATEST, 'tmp', 'stats.xml')
        self.output_model_file_name = os.path.join(IOTA2_DATATEST, 'model.pca')
        self.test_output_model_file_name = os.path.join(
            IOTA2_DATATEST, 'tmp', 'model.pca')
        self.reduced_output_file_name = os.path.join(IOTA2_DATATEST,
                                                     'reduced.sqlite')
        self.test_reduced_output_file_name = os.path.join(
            IOTA2_DATATEST, 'tmp', 'reduced.sqlite')
        self.test_joint_reduced_file = os.path.join(IOTA2_DATATEST, 'tmp',
                                                    'joint.sqlite')
        self.joint_reduced_file = os.path.join(IOTA2_DATATEST, 'joint.sqlite')
        self.output_sample_file_name = 'reduced_output_samples.sqlite'
        self.test_output_sample_file_name = ('reduced_output_'
                                             'samples_test.sqlite')
        self.config_file = os.path.join(
            IOTA2DIR, "config", "Config_4Tuiles_Multi_FUS_Confidence.cfg")
        self.cfg = SCF.serviceConfigFile(self.config_file)

    def test_get_available_features(self):

        expected = '20140118'
        (feats, meta_data_fields) = DR.get_available_features(
            self.input_sample_file_name)
        self.assertEqual(feats['landsat8']['brightness'][0], expected)

        expected = 'b1'
        (feats, meta_data_fields) = DR.get_available_features(
            self.input_sample_file_name, 'date', 'sensor')
        self.assertEqual(feats['20141017']['landsat8'][0], expected)

        expected = 'landsat8'
        (feats, meta_data_fields) = DR.get_available_features(
            self.input_sample_file_name, 'date', 'band')
        self.assertEqual(feats['20141118']['b2'][0], expected)

    def test_generate_feature_list_global(self):
        expected = [[
            'landsat8_b1_20140118', 'landsat8_b2_20140118',
            'landsat8_b3_20140118', 'landsat8_b4_20140118',
            'landsat8_b5_20140118', 'landsat8_b6_20140118',
            'landsat8_b7_20140118', 'landsat8_b1_20140203',
            'landsat8_b2_20140203', 'landsat8_b3_20140203',
            'landsat8_b4_20140203', 'landsat8_b5_20140203',
            'landsat8_b6_20140203', 'landsat8_b7_20140203',
            'landsat8_b1_20140219', 'landsat8_b2_20140219',
            'landsat8_b3_20140219', 'landsat8_b4_20140219',
            'landsat8_b5_20140219', 'landsat8_b6_20140219',
            'landsat8_b7_20140219', 'landsat8_b1_20140307',
            'landsat8_b2_20140307', 'landsat8_b3_20140307',
            'landsat8_b4_20140307', 'landsat8_b5_20140307',
            'landsat8_b6_20140307', 'landsat8_b7_20140307',
            'landsat8_b1_20140323', 'landsat8_b2_20140323',
            'landsat8_b3_20140323', 'landsat8_b4_20140323',
            'landsat8_b5_20140323', 'landsat8_b6_20140323',
            'landsat8_b7_20140323'
        ]]

        (feat_list, _) = DR.build_features_lists(self.input_sample_file_name,
                                                 'global')
        self.assertEqual(expected[0], feat_list[0][:len(expected[0])])

    def test_generate_feature_list_date(self):
        (feat_list, _) = DR.build_features_lists(self.input_sample_file_name,
                                                 'date')
        self.assertEqual(self.fl_date, feat_list[0])

    def test_generate_feature_list_band(self):
        # second spectral band
        expected = [
            'landsat8_b2_20140118', 'landsat8_b2_20140203',
            'landsat8_b2_20140219', 'landsat8_b2_20140307',
            'landsat8_b2_20140323', 'landsat8_b2_20140408',
            'landsat8_b2_20140424', 'landsat8_b2_20140510',
            'landsat8_b2_20140526', 'landsat8_b2_20140611',
            'landsat8_b2_20140627', 'landsat8_b2_20140713',
            'landsat8_b2_20140729', 'landsat8_b2_20140814',
            'landsat8_b2_20140830', 'landsat8_b2_20140915',
            'landsat8_b2_20141001', 'landsat8_b2_20141017',
            'landsat8_b2_20141102', 'landsat8_b2_20141118',
            'landsat8_b2_20141204', 'landsat8_b2_20141220',
            'landsat8_b2_20141229'
        ]
        (feat_list, _) = DR.build_features_lists(self.input_sample_file_name,
                                                 'band')
        self.assertEqual(expected, feat_list[1])

    def test_compute_feature_statistics(self):
        """test compute feature statistics"""
        DR.compute_feature_statistics(self.input_sample_file_name,
                                      self.test_stats_file, self.fl_date)
        self.assertTrue(filecmp.cmp(self.test_stats_file,
                                    self.stats_file,
                                    shallow=False),
                        msg="Stats files don't match")

    def test_train_dimensionality_reduction(self):
        """test train dimensionality reduction"""
        DR.train_dimensionality_reduction(self.input_sample_file_name,
                                          self.test_output_model_file_name,
                                          self.fl_date, self.target_dimension,
                                          self.stats_file)
        self.assertTrue(filecmp.cmp(self.test_output_model_file_name,
                                    self.output_model_file_name,
                                    shallow=False),
                        msg="Model files don't match")

    def test_apply_dimensionality_reduction(self):
        """test apply dimensionality reduction"""
        from iota2.Tests.UnitTests.tests_utils import tests_utils_vectors as VU

        output_features = ['reduced_' + str(x) for x in range(6)]

        DR.apply_dimensionality_reduction(self.input_sample_file_name,
                                          self.test_reduced_output_file_name,
                                          self.output_model_file_name,
                                          self.fl_date,
                                          output_features,
                                          stats_file=self.stats_file,
                                          writing_mode='overwrite')

        self.assertTrue(VU.compare_sqlite(self.test_reduced_output_file_name,
                                          self.reduced_output_file_name,
                                          cmp_mode="coordinates"),
                        msg="Joined files don't match")

    def test_join_reduced_sample_files(self):
        """test join reduced sample files"""
        from iota2.Tests.UnitTests.tests_utils import tests_utils_vectors as VU

        feat_list = [
            self.reduced_output_file_name, self.reduced_output_file_name
        ]
        output_features = [f'reduced_{x + 1}' for x in range(5)]
        DR.join_reduced_sample_files(feat_list, self.test_joint_reduced_file,
                                     output_features)

        self.assertTrue(VU.compare_sqlite(self.test_joint_reduced_file,
                                          self.joint_reduced_file,
                                          cmp_mode="coordinates"),
                        msg="Joined files don't match")

    def test_sample_file_pca_reduction(self):
        """test sample file PCA reduction"""
        from iota2.Tests.UnitTests.tests_utils import tests_utils_vectors as VU

        test_test_output_sample_file_name = (IOTA2_DATATEST + os.sep +
                                             self.test_output_sample_file_name)
        DR.sample_file_pca_reduction(self.input_sample_file_name,
                                     test_test_output_sample_file_name,
                                     'date',
                                     self.target_dimension,
                                     tmp_dir=os.path.join(
                                         IOTA2_DATATEST, "tmp"))

        self.assertTrue(VU.compare_sqlite(test_test_output_sample_file_name,
                                          os.path.join(
                                              IOTA2_DATATEST,
                                              self.output_sample_file_name),
                                          cmp_mode="coordinates"),
                        msg="Output sample files don't match")

    def test_build_channel_groups(self):
        """test build channel groups"""
        chan_group = DR.build_channel_groups(
            "sensor_date", self.cfg.getParam("chain", "outputPath"))
        expected = [[
            'Channel1', 'Channel2', 'Channel3', 'Channel4', 'Channel5',
            'Channel6', 'Channel7', 'Channel162', 'Channel185', 'Channel208'
        ],
                    [
                        'Channel8', 'Channel9', 'Channel10', 'Channel11',
                        'Channel12', 'Channel13', 'Channel14', 'Channel163',
                        'Channel186', 'Channel209'
                    ],
                    [
                        'Channel15', 'Channel16', 'Channel17', 'Channel18',
                        'Channel19', 'Channel20', 'Channel21', 'Channel164',
                        'Channel187', 'Channel210'
                    ],
                    [
                        'Channel22', 'Channel23', 'Channel24', 'Channel25',
                        'Channel26', 'Channel27', 'Channel28', 'Channel165',
                        'Channel188', 'Channel211'
                    ],
                    [
                        'Channel29', 'Channel30', 'Channel31', 'Channel32',
                        'Channel33', 'Channel34', 'Channel35', 'Channel166',
                        'Channel189', 'Channel212'
                    ],
                    [
                        'Channel36', 'Channel37', 'Channel38', 'Channel39',
                        'Channel40', 'Channel41', 'Channel42', 'Channel167',
                        'Channel190', 'Channel213'
                    ],
                    [
                        'Channel43', 'Channel44', 'Channel45', 'Channel46',
                        'Channel47', 'Channel48', 'Channel49', 'Channel168',
                        'Channel191', 'Channel214'
                    ],
                    [
                        'Channel50', 'Channel51', 'Channel52', 'Channel53',
                        'Channel54', 'Channel55', 'Channel56', 'Channel169',
                        'Channel192', 'Channel215'
                    ],
                    [
                        'Channel57', 'Channel58', 'Channel59', 'Channel60',
                        'Channel61', 'Channel62', 'Channel63', 'Channel170',
                        'Channel193', 'Channel216'
                    ],
                    [
                        'Channel64', 'Channel65', 'Channel66', 'Channel67',
                        'Channel68', 'Channel69', 'Channel70', 'Channel171',
                        'Channel194', 'Channel217'
                    ],
                    [
                        'Channel71', 'Channel72', 'Channel73', 'Channel74',
                        'Channel75', 'Channel76', 'Channel77', 'Channel172',
                        'Channel195', 'Channel218'
                    ],
                    [
                        'Channel78', 'Channel79', 'Channel80', 'Channel81',
                        'Channel82', 'Channel83', 'Channel84', 'Channel173',
                        'Channel196', 'Channel219'
                    ],
                    [
                        'Channel85', 'Channel86', 'Channel87', 'Channel88',
                        'Channel89', 'Channel90', 'Channel91', 'Channel174',
                        'Channel197', 'Channel220'
                    ],
                    [
                        'Channel92', 'Channel93', 'Channel94', 'Channel95',
                        'Channel96', 'Channel97', 'Channel98', 'Channel175',
                        'Channel198', 'Channel221'
                    ],
                    [
                        'Channel99', 'Channel100', 'Channel101', 'Channel102',
                        'Channel103', 'Channel104', 'Channel105', 'Channel176',
                        'Channel199', 'Channel222'
                    ],
                    [
                        'Channel106', 'Channel107', 'Channel108', 'Channel109',
                        'Channel110', 'Channel111', 'Channel112', 'Channel177',
                        'Channel200', 'Channel223'
                    ],
                    [
                        'Channel113', 'Channel114', 'Channel115', 'Channel116',
                        'Channel117', 'Channel118', 'Channel119', 'Channel178',
                        'Channel201', 'Channel224'
                    ],
                    [
                        'Channel120', 'Channel121', 'Channel122', 'Channel123',
                        'Channel124', 'Channel125', 'Channel126', 'Channel179',
                        'Channel202', 'Channel225'
                    ],
                    [
                        'Channel127', 'Channel128', 'Channel129', 'Channel130',
                        'Channel131', 'Channel132', 'Channel133', 'Channel180',
                        'Channel203', 'Channel226'
                    ],
                    [
                        'Channel134', 'Channel135', 'Channel136', 'Channel137',
                        'Channel138', 'Channel139', 'Channel140', 'Channel181',
                        'Channel204', 'Channel227'
                    ],
                    [
                        'Channel141', 'Channel142', 'Channel143', 'Channel144',
                        'Channel145', 'Channel146', 'Channel147', 'Channel182',
                        'Channel205', 'Channel228'
                    ],
                    [
                        'Channel148', 'Channel149', 'Channel150', 'Channel151',
                        'Channel152', 'Channel153', 'Channel154', 'Channel183',
                        'Channel206', 'Channel229'
                    ],
                    [
                        'Channel155', 'Channel156', 'Channel157', 'Channel158',
                        'Channel159', 'Channel160', 'Channel161', 'Channel184',
                        'Channel207', 'Channel230'
                    ]]
        self.assertEqual(expected, chan_group)

    def test_apply_dimensionality_reduction_to_feature_stack(self):
        """test Apply Dimensionality Reduction To Feature Stack"""
        image_stack = IOTA2_DATATEST + '/230feats.tif'
        model_list = [self.output_model_file_name] * len(
            DR.build_channel_groups("sensor_date",
                                    self.cfg.getParam("chain", "outputPath")))
        (app, _) = DR.apply_dimensionality_reduction_to_feature_stack(
            "sensor_date", self.cfg.getParam("chain", "outputPath"),
            image_stack, model_list)
        app.SetParameterString(
            "out", os.path.join(IOTA2_DATATEST, "tmp", "reducedStack.tif"))
        app.ExecuteAndWriteOutput()

    def test_apply_dimensionality_reduction_to_feature_stack_pipeline(self):
        """"""
        inimage = IOTA2_DATATEST + '/230feats.tif'
        import otbApplication as otb
        app = otb.Registry.CreateApplication("ExtractROI")
        app.SetParameterString("in", inimage)
        app.Execute()
        model_list = [self.output_model_file_name] * len(
            DR.build_channel_groups("sensor_date",
                                    self.cfg.getParam("chain", "outputPath")))
        (appdr, _) = DR.apply_dimensionality_reduction_to_feature_stack(
            "sensor_date", self.cfg.getParam("chain", "outputPath"), app,
            model_list)
        appdr.SetParameterString(
            "out",
            os.path.join(IOTA2_DATATEST, "tmp", "reducedStackPipeline.tif"))
        appdr.ExecuteAndWriteOutput()


if __name__ == '__main__':
    unittest.main()
