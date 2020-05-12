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
from typing import Optional
from collections import OrderedDict
from iota2.Common import ServiceConfigFile as SCF


class i2_builder():
    """
    class use to describe steps sequence and variable to use at each step (config)
    """
    def __init__(self,
                 cfg,
                 config_ressources,
                 hpc_working_directory: Optional[str] = "TMPDIR"):

        # config object
        #~ self.cfg = cfg
        self.cfg = cfg

        # working directory, HPC

        self.workingDirectory = os.getenv(hpc_working_directory)

        # steps definitions
        self.steps_group = OrderedDict()

        #build steps
        self.steps = None

        # pickle's path
        self.iota2_pickle = os.path.join(
            SCF.serviceConfigFile(self.cfg).getParam("chain", "outputPath"),
            "logs", "iota2.txt")

    def save_chain(self):
        """
        use dill to save chain instance
        """
        import dill
        if os.path.exists(self.iota2_pickle):
            os.remove(self.iota2_pickle)
        with open(self.iota2_pickle, 'wb') as fp:
            dill.dump(self, fp)

    def load_chain(self):
        import dill
        if os.path.exists(self.iota2_pickle):
            with open(self.iota2_pickle, 'rb') as fp:
                iota2_chain = dill.load(fp)
        else:
            iota2_chain = self
        return iota2_chain

    def sort_step(self):
        """
        use to establish which step is going to which step group
        """

        for step_place, step in enumerate(self.steps):
            self.steps_group[step.step_group][step_place +
                                              1] = step.step_description()

    def print_step_summarize(self,
                             start,
                             end,
                             show_resources=False,
                             checked="x",
                             log=False,
                             running_step=False,
                             running_sym='r'):
        """
        print iota2 steps that will be run
        """
        if log:
            summarize = "Full processing include the following steps (x : done; r : running; f : failed):\n"
        else:
            summarize = "Full processing include the following steps (checked steps will be run):\n"
        step_position = 0
        for group in list(self.steps_group.keys()):
            if len(self.steps_group[group]) > 0:
                summarize += "Group {}:\n".format(group)

            for key in self.steps_group[group]:
                highlight = "[ ]"
                if key >= start and key <= end:
                    highlight = "[{}]".format(checked)
                if key == end and running_step:
                    highlight = "[{}]".format(running_sym)
                summarize += "\t {} Step {}: {}".format(
                    highlight, key, self.steps_group[group][key])
                if show_resources:
                    cpu = self.steps[step_position].resources["cpu"]
                    ram = self.steps[step_position].resources["ram"]
                    walltime = self.steps[step_position].resources["walltime"]
                    resource_block_name = self.steps[step_position].resources[
                        "resource_block_name"]
                    resource_block_found = self.steps[step_position].resources[
                        "resource_block_found"]
                    log_identifier = self.steps[step_position].step_name
                    resource_miss = "" if resource_block_found else " -> MISSING"
                    summarize += "\n\t\t\tresources block name : {}{}\n\t\t\tcpu : {}\n\t\t\tram : {}\n\t\t\twalltime : {}\n\t\t\tlog identifier : {}".format(
                        resource_block_name, resource_miss, cpu, ram, walltime,
                        log_identifier)
                summarize += "\n"
                step_position += 1
        summarize += "\n"
        return summarize

    def get_dir(self):
        """
        usage : return iota2_directories
        """
        import os
        directories = [
            'classif', 'config_model', 'dataRegion', 'envelope',
            'formattingVectors', 'metaData', 'samplesSelection', 'stats',
            'cmd', 'dataAppVal', 'dimRed', 'final', 'learningSamples', 'model',
            'shapeRegion', "features"
        ]

        iota2_outputs_dir = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')

        return [os.path.join(iota2_outputs_dir, d) for d in directories]

    def get_steps_number(self):
        start = SCF.serviceConfigFile(self.cfg).getParam('chain', 'firstStep')
        end = SCF.serviceConfigFile(self.cfg).getParam('chain', 'lastStep')
        start_ind = list(self.steps_group.keys()).index(start)
        end_ind = list(self.steps_group.keys()).index(end)

        steps = []
        for key in list(self.steps_group.keys())[start_ind:end_ind + 1]:
            steps.append(self.steps_group[key])
        step_to_compute = [step for step_group in steps for step in step_group]
        return step_to_compute

    def build_steps(self, cfg, config_ressources=None):
        """
        build steps
        """
        raise NotImplementedError
