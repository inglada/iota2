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

from Steps import IOTA2Step
from Cluster import get_RAM

def awesome_function(arg1, arg2):
    print ("My variable parameter : {} const parameter : {}".format(arg1, arg2))

class ThirdStep(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file):
        # heritage init
        super(ThirdStep, self).__init__(cfg, cfg_resources_file)

        # init


    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        return "This step will do something..."

    def step_inputs(self):
        """
        """
        return list(range(1, 3))

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        step_function = lambda x: awesome_function(x, "TUILE")
        return step_function

    def step_outputs(self):
        print ("no outputs")

    def step_clean(self):
        """
        """
        import os
        step_in = self.step_inputs()
        for in_file in step_in:
            if os.path.exists(in_file):
                os.remove(in_file)