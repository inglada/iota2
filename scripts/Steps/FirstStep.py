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

#~ def returns(*accepted_return_type_tuple):
    #~ '''
    #~ '''
    #~ import functools
    #~ def return_decorator(validate_function):
        #~ # No return type has been specified.
        #~ if len(accepted_return_type_tuple) == 0:
            #~ raise TypeError('You must specify a return type.')

        #~ @functools.wraps(validate_function)
        #~ def decorator_wrapper(*function_args):
            #~ # More than one return type has been specified.
            #~ if len(accepted_return_type_tuple) > 1:
                #~ raise TypeError('You must specify one return type.')

            #~ accepted_return_type = accepted_return_type_tuple[0]
            #~ return_value = validate_function(*function_args)
            #~ return_value_type = type(return_value)
            
            #~ if not str(return_value_type) == str(accepted_return_type):
                #~ raise Exception("function '{}' must return {} type instead of {}".format(validate_function.__name__,
                                                                                         #~ accepted_return_type,
                                                                                         #~ return_value_type))

            #~ return return_value
        #~ return decorator_wrapper
    #~ return return_decorator


class FirstStep(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, name="FirstStep"):
        # heritage init
        super(FirstStep, self).__init__(cfg, cfg_resources_file)

        # init
        self.step_name = name

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

    


        