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

class FirstStep(IOTA2Step.Step):
    def __init__(self, cfg, name="FirstStep", cpu=1, ram="4gb", walltime="00:30:00"):
        # heritage init
        super(FirstStep, self).__init__()

        # init
        self.step_name = name
        self.cpu = cpu
        self.ram = get_RAM(ram)
        self.walltime = walltime

        outputPath = cfg.getParam('chain', 'outputPath')
        log_dir = os.path.join(outputPath, "logs")
        self.logFile = os.path.join(log_dir, "{}_log.log".format(self.step_name))

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        return "This step will do something cool"

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        return range(1, 20)

    def step_execute(self, workingDirectory=None):
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
        print "RIEN"

    


        