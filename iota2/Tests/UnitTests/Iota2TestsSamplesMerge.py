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
Test sampler merge
"""
import os
import unittest
import shutil

IOTA2DIR = os.environ.get('IOTA2DIR')
IOTA2_DATATEST = os.path.join(os.environ.get('IOTA2DIR'), "data")


class iota_testMergeSamples(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        from iota2.Common import ServiceConfigFile as SCF
        # We initialize the expected mergeSamples for the function get_models()
        self.expectedOutputGetModels = [('1', ['T31TCJ'], 0),
                                        ('1', ['T31TCJ'], 1)]

        # Copy and remove files in the test folder
        if os.path.exists(IOTA2_DATATEST + '/test_vector/test_mergeSamples'):
            shutil.rmtree(IOTA2_DATATEST + '/test_vector/test_mergeSamples')
        shutil.copytree(IOTA2_DATATEST + '/references/mergeSamples/Input',
                        IOTA2_DATATEST + '/test_vector/test_mergeSamples')

        if not os.path.exists(IOTA2_DATATEST +
                              '/test_vector/test_mergeSamples/'
                              'samples_merge/samplesSelection/'):
            os.mkdir(IOTA2_DATATEST + '/test_vector/test_mergeSamples/'
                     'samples_merge/samplesSelection/')

        # We define several parameters for the configuration file
        self.cfg = SCF.serviceConfigFile(
            IOTA2_DATATEST + '/test_vector/test_mergeSamples/config.cfg')
        self.cfg.setParam(
            'chain', 'outputPath',
            IOTA2_DATATEST + '/test_vector/test_mergeSamples/samples_merge')
        self.cfg.setParam('chain', 'regionField', 'region')

    def test_getModels(self):
        from iota2.Sampling import SamplesMerge

        # We execute the function : get_models()
        output = SamplesMerge.get_models(
            IOTA2_DATATEST +
            '/test_vector/test_mergeSamples/get_models/formattingVectors',
            'region', 2)

        # We check the output values with the expected values
        self.assertEqual(self.expectedOutputGetModels[0][0], output[0][0])
        self.assertEqual(self.expectedOutputGetModels[0][1][0],
                         output[0][1][0])
        self.assertEqual(self.expectedOutputGetModels[0][2], output[0][2])
        self.assertEqual(self.expectedOutputGetModels[1][0], output[1][0])
        self.assertEqual(self.expectedOutputGetModels[1][1][0],
                         output[1][1][0])
        self.assertEqual(self.expectedOutputGetModels[1][2], output[1][2])

    def test_samplesMerge(self):
        from iota2.Sampling import SamplesMerge

        # We execute the function: samples_merge()

        output = SamplesMerge.get_models(
            IOTA2_DATATEST +
            '/test_vector/test_mergeSamples/get_models/formattingVectors',
            'region', 2)
        SamplesMerge.samples_merge(
            output[0], self.cfg.getParam('chain', 'outputPath'),
            self.cfg.getParam('chain', 'regionField'),
            self.cfg.getParam('chain', 'runs'),
            self.cfg.getParam('chain', 'enableCrossValidation'),
            self.cfg.getParam('argTrain', 'dempster_shafer_SAR_Opt_fusion'),
            None)

        # We check the produced files
        self.assertEqual(
            0,
            os.system(
                'diff ' + IOTA2_DATATEST +
                '/references/mergeSamples/Output/samples_region_1_seed_0.shp '
                + IOTA2_DATATEST +
                '/test_vector/test_mergeSamples/samples_merge/samplesSelection'
                '/samples_region_1_seed_0.shp'))
        self.assertEqual(
            0,
            os.system(
                'diff ' + IOTA2_DATATEST +
                '/references/mergeSamples/Output/samples_region_1_seed_0.prj '
                + IOTA2_DATATEST + '/test_vector/test_mergeSamples/'
                'samples_merge/samplesSelection/samples_region_1_seed_0.prj'))
        self.assertEqual(
            0,
            os.system(
                'diff ' + IOTA2_DATATEST +
                '/references/mergeSamples/Output/samples_region_1_seed_0.shx '
                + IOTA2_DATATEST + '/test_vector/test_mergeSamples/'
                'samples_merge/samplesSelection/samples_region_1_seed_0.shx'))


class iota_testGetModels(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        from iota2.Common import ServiceConfigFile as SCF
        # We initialize the expected mergeSamples for the function get_models()
        self.expectedOutputGetModels = [('1', ['T31TCJ'], 0),
                                        ('1', ['T31TCJ'], 1)]

        # Copy and remove files in the test folder
        if os.path.exists(IOTA2_DATATEST + '/test_vector/test_mergeSamples'):
            shutil.rmtree(IOTA2_DATATEST + '/test_vector/test_mergeSamples')
        shutil.copytree(IOTA2_DATATEST + '/references/mergeSamples/Input',
                        IOTA2_DATATEST + '/test_vector/test_mergeSamples')
        os.mkdir(
            IOTA2_DATATEST +
            '/test_vector/test_mergeSamples/samples_merge/samplesSelection/')
        # We define several parameters for the configuration file
        self.cfg = SCF.serviceConfigFile(
            IOTA2_DATATEST + '/test_vector/test_mergeSamples/config.cfg')
        self.cfg.setParam(
            'chain', 'outputPath',
            IOTA2_DATATEST + '/test_vector/test_mergeSamples/samples_merge')
        self.cfg.setParam('chain', 'regionField', 'region')

    def test_getModels(self):
        from iota2.Sampling import SamplesMerge

        # We execute the function : get_models()
        output = SamplesMerge.get_models(
            IOTA2_DATATEST +
            '/test_vector/test_mergeSamples/get_models/formattingVectors',
            'region', 2)

        # We check the output values with the expected values
        self.assertEqual(self.expectedOutputGetModels[0][0], output[0][0])
        self.assertEqual(self.expectedOutputGetModels[0][1][0],
                         output[0][1][0])
        self.assertEqual(self.expectedOutputGetModels[0][2], output[0][2])
        self.assertEqual(self.expectedOutputGetModels[1][0], output[1][0])
        self.assertEqual(self.expectedOutputGetModels[1][1][0],
                         output[1][1][0])
        self.assertEqual(self.expectedOutputGetModels[1][2], output[1][2])
