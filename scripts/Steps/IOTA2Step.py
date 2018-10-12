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
from Cluster import get_RAM


class Step(object):
    """
    This class is the definition of a IOTA² step. New steps must herit from Step
    """
    def __init__(self, name="IOTA2_step", cpu=1, ram="4gb", walltime="00:10:00"):
        self.step_name = name
        self.cpu = cpu
        self.ram = get_RAM(ram)
        self.walltime = walltime
        self.check_mandatory_methods()

    def check_mandatory_methods(self):
        #execute
        if self.execute.__code__ is Step.execute.__code__:
            err_mess = "execute function as to be define in : {} class ".format(self.__class__)
            print err_mess
        #check_inputs
        if self.expected_outputs.__code__ is Step.expected_outputs.__code__:
            err_mess = "expected_outputs function as to be define in : {} class ".format(self.__class__)
            print err_mess
    def __str__(self):
        return "IOTA² step : {}".format(self.step_name)
    def __repr__(self):
        return ("IOTA² step definition : \n"
                "\tname : {}\n"
                "\tcpu per tasks : {}\n"
                "\tram per tasks : {}\n"
                "\ttotal time to run tasks : {}\n").format(self.step_name,
                                                           self.cpu,
                                                           self.ram,
                                                           self.walltime)
    @classmethod
    def check_inputs():
        pass
    @classmethod
    def expected_outputs():
        pass
    @classmethod
    def execute(cls):
        pass