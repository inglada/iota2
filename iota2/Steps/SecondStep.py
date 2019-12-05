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
import os

from Steps import IOTA2Step
from Cluster import get_RAM


def write_something(directory, name):

    # unfortunally, tmp files are needed for each 'name'
    with open(os.path.join(directory, "TMP_{}".format(name)), "w") as new_file:
        new_file.write("tmp results : {}".format(name))

    # then, write the important results in a file.
    with open(os.path.join(directory, name), "w") as new_file:
        new_file.write("name : {}".format(name))


class SecondStep(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file):
        # heritage init
        super(SecondStep, self).__init__(cfg, cfg_resources_file)

        # init
        self.output_dir = "/home/uz/vincenta/tmp/"

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        return "This step will do something really really cool"

    def step_inputs(self):
        """
        will create 4 new files
        """
        names = ["test_dummy_{}.txt".format(i + 1) for i in range(4)]
        return names

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """

        def step_function(x): return write_something(self.output_dir, x)
        return step_function

    def step_outputs(self):
        from Common import FileUtils
        return FileUtils.FileSearch_AND(
            self.output_dir, True, "test_dummy_", ".txt")

    def step_clean(self):
        """
        """
        import os
        from Common import FileUtils

        tmp_files = FileUtils.FileSearch_AND(
            self.output_dir, True, "TMP", "test_dummy_", ".txt")
        for tmp_file in tmp_files:
            os.remove(tmp_file)
