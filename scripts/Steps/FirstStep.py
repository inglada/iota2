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
from Common import ServiceConfigFile as SCF 

def awesome_function(arg1, arg2, config):
   
    my_internal_config = SCF.serviceConfigFile(config)
    print "arg1 : {} et arg2 : {} ett {}".format(arg1, arg2, my_internal_config.getParam("chain", "outputPath"))
    print "Une valeur par defaut : {}".format(my_internal_config.getParam("chain", "logConsoleLevel"))

class FirstStep(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file):
        # heritage init
        super(FirstStep, self).__init__(cfg, cfg_resources_file)

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
        return range(1, 10)

    def step_execute(self, workingDirectory=None):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """

        step_function = lambda x: awesome_function(x, "TUILE", self.cfg)
        return step_function

    def step_outputs(self):
        print "RIEN"

    


        