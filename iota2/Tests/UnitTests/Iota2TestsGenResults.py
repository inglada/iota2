# !/usr/bin/env python3
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
"""Test GenResults"""
# python -m unittest Iota2TestsGenResults
import os
import sys
import shutil
import unittest

# if all tests pass, remove 'iota2_tests_directory' which contains all
# sub-directory tests
RM_IF_ALL_OK = True
IOTA2DIR = os.environ.get('IOTA2DIR')


class iota2_tests_gen_results(unittest.TestCase):
    """Test gen results module functions"""
    # before launching tests
    @classmethod
    def setUpClass(cls):
        # definition of local variables
        cls.group_test_name = "iota_Iota2TestsGenResults"
        cls.iota2_tests_directory = os.path.join(IOTA2DIR, "data",
                                                 cls.group_test_name)
        cls.all_tests_ok = []
        # We initialize parameters for the configuration file
        cls.classif_final = os.path.join(cls.iota2_tests_directory, 'final')
        cls.nomenclature_path = os.path.join(cls.iota2_tests_directory,
                                             'nomenclature.txt')

        # Tests directory
        cls.test_working_directory = None
        if os.path.exists(cls.iota2_tests_directory):
            shutil.rmtree(cls.iota2_tests_directory)
        # os.mkdir(cls.iota2_tests_directory)
        shutil.copytree(
            os.path.join(IOTA2DIR, "data", "references", "genResults",
                         "Input"), cls.iota2_tests_directory)
        # We remove the file RESULTS.txt
        if os.path.exists(os.path.join(cls.classif_final, 'RESULTS.txt')):
            os.remove(os.path.join(cls.classif_final, 'RESULTS.txt'))

        if os.path.exists(
                os.path.join(cls.classif_final, 'TMP',
                             'Classif_Seed_1_sq.csv')):
            os.remove(
                os.path.join(cls.classif_final, 'TMP',
                             'Classif_Seed_1_sq.csv'))
        if os.path.exists(
                os.path.join(cls.classif_final, 'TMP',
                             'Classif_Seed_0_sq.csv')):
            os.remove(
                os.path.join(cls.classif_final, 'TMP',
                             'Classif_Seed_0_sq.csv'))

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
            result = getattr(self, "_outcomeForDoCleanups",
                             self._resultForDoCleanups)

        error = self.list2reason(result.errors)
        failure = self.list2reason(result.failures)
        ok_test = not error and not failure

        self.all_tests_ok.append(ok_test)
        if ok_test:
            shutil.rmtree(self.test_working_directory)

    def test_gen_results(self):
        '''
        TEST genResults method
        '''
        from iota2.Validation import GenResults as GR
        # we execute the function genResults()
        GR.genResults(self.classif_final, self.nomenclature_path)

        # We check we have the same produced file that the expected file

        outfile = os.path.join(IOTA2DIR, 'data', 'references', 'genResults',
                               'Output', 'RESULTS.txt')
        self.assertEqual(
            0,
            os.system(f"diff {outfile} "
                      f"{os.path.join(self.classif_final,'RESULTS.txt')}"))

    def test_results_utils(self):
        """
        test results utils
        """
        from iota2.Validation import ResultsUtils as resU
        import numpy as np

        conf_mat_array = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

        norm_ref_ref = np.array([[0.16666667, 0.33333333, 0.5],
                                 [0.26666667, 0.33333333, 0.4],
                                 [0.29166667, 0.33333333, 0.375]])

        norm_prod_ref = np.array([[0.08333333, 0.13333333, 0.16666667],
                                  [0.33333333, 0.33333333, 0.33333333],
                                  [0.58333333, 0.53333333, 0.5]])

        norm_ref_test = resU.normalize_conf(conf_mat_array, norm="ref")
        self.assertTrue(np.allclose(norm_ref_ref, norm_ref_test),
                        msg="problem with the normalization by ref")

        norm_prod_test = resU.normalize_conf(conf_mat_array, norm="prod")
        self.assertTrue(np.allclose(norm_prod_ref, norm_prod_test),
                        msg="problem with the normalization by prod")

    def test_get_coeff(self):
        """
        test confusion matrix coefficients computation
        """
        from iota2.Validation import ResultsUtils as resU
        from collections import OrderedDict

        # construct input
        confusion_matrix = OrderedDict([
            (1, OrderedDict([(1, 50.0), (2, 78.0), (3, 41.0)])),
            (2, OrderedDict([(1, 20.0), (2, 52.0), (3, 31.0)])),
            (3, OrderedDict([(1, 27.0), (2, 72.0), (3, 98.0)]))
        ])
        k_ref = 0.15482474945066724
        oa_ref = 0.42643923240938164
        p_ref = OrderedDict([(1, 0.5154639175257731), (2, 0.25742574257425743),
                             (3, 0.5764705882352941)])
        r_ref = OrderedDict([(1, 0.2958579881656805), (2, 0.5048543689320388),
                             (3, 0.49746192893401014)])
        f_ref = OrderedDict([(1, 0.3759398496240602), (2, 0.3409836065573771),
                             (3, 0.5340599455040872)])

        k_test, oa_test, p_test, r_test, f_test = resU.get_coeff(
            confusion_matrix)

        self.assertTrue(k_ref == k_test, msg="Kappa computation is broken")
        self.assertTrue(oa_test == oa_ref,
                        msg="Overall accuracy computation is broken")
        self.assertTrue(p_test == p_ref, msg="Precision computation is broken")
        self.assertTrue(r_test == r_ref, msg="Recall computation is broken")
        self.assertTrue(f_test == f_ref, msg="F-Score computation is broken")
