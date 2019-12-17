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
            raise Exception(
                "step '{}' already present in container".format(step.step_name)
            )
        # link steps
        if len(self.container) > 1:
            self.container[len(self.container) - 2].next_step = step
            step.previous_step = self.container[len(self.container) - 2]

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

    def __len__(self):
        return len(self.container)


def return_decorator(validate_function, type_string="<class 'function'>"):
    """
    This function is use as decorator to check output functions type

    Parameters
    ----------
    validate_function : function
        function to check
    type_string : string
        python's type as string
    """
    import functools

    @functools.wraps(validate_function)
    def decorator_wrapper(*function_args):
        accepted_return_type = accepted_return_type_tuple = type_string
        return_value = validate_function(*function_args)
        return_value_type = type(return_value)
        if str(return_value_type) != str(accepted_return_type):
            raise Exception(
                "function '{}' must return {} type instead of {}".format(
                    validate_function.__name__, accepted_return_type, return_value_type
                )
            )
        return return_value

    return decorator_wrapper


class Step(object):
    """
    This class is the definition of a IOTA² step. New steps must herit from
    """

    def __init__(self, cfg, cfg_resources_file, resources_block_name=None):
        """
        """
        from Common import ServiceConfigFile as SCF

        self.check_mandatory_methods()

        # attributes
        self.cfg = cfg
        self.step_name = self.build_step_name()
        self.step_group = ""

        # get resources needed
        self.resources = self.parse_resource_file(
            resources_block_name, cfg_resources_file
        )

        # define log path
        outputPath = SCF.serviceConfigFile(self.cfg).getParam("chain", "outputPath")
        log_dir = os.path.join(outputPath, "logs")
        self.logFile = os.path.join(log_dir, "{}_log.log".format(self.step_name))

        self.previous_step = None
        self.next_step = None

        # "waiting", "running", "success", "fail"
        self.step_status = "waiting"

    def parse_resource_file(self, step_name, cfg_resources_file):
        """
        parse a configuration file dedicated to reserve resources to HPC
        """
        from config import Config

        default_cpu = 1
        default_ram = "5gb"
        default_walltime = "00:10:00"
        default_process_min = 1
        default_process_max = -1

        cfg_resources = None
        if cfg_resources_file and os.path.exists(cfg_resources_file):
            cfg_resources = Config(cfg_resources_file)

        resource = {}
        cfg_step_resources = getattr(cfg_resources, str(step_name), {})
        resource["cpu"] = getattr(cfg_step_resources, "nb_cpu", default_cpu)
        resource["ram"] = getattr(cfg_step_resources, "ram", default_ram)
        resource["walltime"] = getattr(cfg_step_resources, "walltime", default_walltime)
        resource["process_min"] = getattr(
            cfg_step_resources, "process_min", default_process_min
        )
        resource["process_max"] = getattr(
            cfg_step_resources, "process_max", default_process_max
        )
        resource["resource_block_name"] = str(step_name)
        resource["resource_block_found"] = False
        if cfg_resources:
            resource["resource_block_found"] = str(step_name) in cfg_resources
        return resource

    def build_step_name(self):
        """
        strategy to build step name
        the name define logging ouput files and resources access
        """
        return self.__class__.__name__

    def check_attributes_type(self):
        """
        """
        mandatory_type = {"cfg": "str"}
        for attribute, value in list(self.__dict__.items()):
            if attribute in mandatory_type:
                if value.__class__.__name__ != str(mandatory_type[attribute]):
                    raise Exception(
                        "in {} class, attribute '{}' must be of type : {} not {}".format(
                            self.__class__.__name__,
                            attribute,
                            mandatory_type[attribute],
                            value.__class__.__name__,
                        )
                    )

    def check_mandatory_methods(self):
        """
        This method check if sub-class redefine mandatory methods
        """

        if not self.__class__.__name__ == "Step":
            # step_execute
            if self.step_execute.__code__ is Step.step_execute.__code__:
                err_mess = "'step_execute' method as to be define in : {} class ".format(
                    self.__class__
                )
                raise Exception(err_mess)
            else:
                # check step_execute output type
                self.step_execute = return_decorator(self.step_execute)

            # step_outputs
            if self.step_outputs.__code__ is Step.step_outputs.__code__:
                err_mess = "'step_outputs' method as to be define in : {} class ".format(
                    self.__class__
                )
                raise Exception(err_mess)

            # step_inputs
            if self.step_inputs.__code__ is Step.step_inputs.__code__:
                err_mess = "'step_inputs' method as to be define in : {} class ".format(
                    self.__class__
                )
                raise Exception(err_mess)

    def __str__(self):
        return "{}".format(self.step_name)

    def __repr__(self):
        return (
            "IOTA² step definition : \n"
            "\tname : {}\n"
            "\tgroup : {}\n"
            "\tcpu per tasks : {}\n"
            "\tram per tasks : {}\n"
            "\ttotal time to run tasks : {}\n"
            "\tstatus : {}\n"
            "\tprevious step's name : {}\n"
            "\tnext step's name : {}\n"
        ).format(
            self.step_name,
            self.step_group,
            self.resources["cpu"],
            self.resources["ram"],
            self.resources["walltime"],
            self.step_status,
            self.previous_step,
            self.next_step,
        )

    def step_description(self):
        return "quick step description"

    def step_connect(self, other_step):
        """
        the objective of this method is to connect two steps : inputs definition
        of the current step is the output definition of an other step (usually
        the previous one)
        """
        self.step_inputs = other_step.step_outputs

    def step_clean(self):
        """
        function call to clean files after the success of the step
        """
        # ~ print("{}.step_clean Not define".format(self.__class__.__name__))
        pass

    @classmethod
    def step_inputs(self):
        return [1, 2]

    @classmethod
    def step_outputs(self):
        return [1, 2]

    @classmethod
    def step_execute(cls):
        """
        method called to execute a step
        """
        return lambda x: x
