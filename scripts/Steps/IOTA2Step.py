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

from Cluster import get_RAM

class StepContainer(object):
    """
    this class is dedicated to contains Step
    """
    def __init__(self):
        self.container = [] 

    def append(self, step, step_group=""):
        if not step in self.container:
            self.container.append(step)
            step.step_group = step_group
        else:
            raise Exception("step '{}' already present in container".format(step.step_name))

    def __contains__(self, step_ask):
        """
        The __contains__ method is based on step's name
        """
        return any([step.step_name == step_ask.step_name for step in self.container])

    def __setitem__(self, index, val):
        self.container[index] = val
    def __getitem__(self, index):
        return self.container[index]

    def __str__(self):
        return "[{}]".format(", ".join(step.step_name for step in self.container))


class Step(object):
    """
    This class is the definition of a IOTA² step. New steps must herit from Step
    """
    def __init__(self, cfg, name="IOTA2_step", cpu=1, ram="4gb", walltime="00:10:00"):
        self.check_mandatory_methods()
        
        self.step_name = name
        self.step_group = ""
        # resources
        self.cpu = cpu
        self.ram = get_RAM(ram)
        self.walltime = walltime
        
        outputPath = cfg.getParam('chain', 'outputPath')
        log_dir = os.path.join(outputPath, "logs")
        self.logFile = os.path.join(log_dir, "{}_log.log".format(self.step_name))

    def check_mandatory_methods(self):
        """
        This methdo check if sub-class redefine mandatory methods
        
        """
        # step_execute
        if self.step_execute.__code__ is Step.step_execute.__code__:
            err_mess = "'step_execute' method as to be define in : {} class ".format(self.__class__)
            raise Exception(err_mess)

        # step_outputs
        if self.step_outputs.__code__ is Step.step_outputs.__code__:
            err_mess = "'step_outputs' method as to be define in : {} class ".format(self.__class__)
            raise Exception(err_mess)

        # step_inputs
        if self.step_inputs.__code__ is Step.step_inputs.__code__:
            err_mess = "'step_inputs' method as to be define in : {} class ".format(self.__class__)
            raise Exception(err_mess)

    def __str__(self):
        return "{}".format(self.step_name)
    def __repr__(self):
        return ("IOTA² step definition : \n"
                "\tname : {}\n"
                "\tgroup : {}\n"
                "\tcpu per tasks : {}\n"
                "\tram per tasks : {}\n"
                "\ttotal time to run tasks : {}\n").format(self.step_name,
                                                           self.step_group,
                                                           self.cpu,
                                                           self.ram,
                                                           self.walltime)
    def step_description():
        return "quick step description"

    def step_connect(self, other_step):
        """
        the objective of this method is to connect two steps : inputs definition 
        of the current step is the output definition of an other step (usually
        the previous one)
        """
        self.step_inputs = other_step.step_outputs

    @classmethod
    def step_inputs():
        print "Step.step_inputs method"
        return [0]
    @classmethod
    def step_outputs():
        print "Step.step_inputs method"
        pass
    @classmethod
    def step_execute(cls):
        """
        method called to execute a step
        """
        print "Step.step_execute method"
        pass