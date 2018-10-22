#!/usr/bin/python
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

import IOTA2Step
from Cluster import get_RAM

def awesome_function(arg1, arg2):
    print "arg1 : {} et arg2 : {}".format(arg1, arg2)

class SecondStep(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, name="SecondStep"):
        # heritage init
        super(SecondStep, self).__init__(cfg, cfg_resources_file)

        # init
        self.step_name = name

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        return "This step will do something really really cool"

    def step_inputs(self):
        return range(1, 5)

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
        return range(1, 10)

    


        