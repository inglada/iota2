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

from collections import OrderedDict


class iota2():
    """
    class use to describe steps sequence and variable to use at each step (config)
    """
    def __init__(self, cfg, config_ressources):
        # config object
        self.cfg = cfg
        
        # working directory, HPC
        self.HPC_working_directory = "TMPDIR"
        
        # steps definitions
        self.steps_group = OrderedDict()

        self.steps_group["init"] = OrderedDict()
        self.steps_group["sampling"] = OrderedDict()
        self.steps_group["dimred"] = OrderedDict()
        self.steps_group["learning"] = OrderedDict()
        self.steps_group["classification"] = OrderedDict()
        self.steps_group["mosaic"] = OrderedDict()
        self.steps_group["validation"] = OrderedDict()

        # build steps
        self.steps = self.build_steps(self.cfg, config_ressources)
        self.sort_step()

    def sort_step(self):
        """
        use to establish which step is going to which step group
        """
        
        for step_place, step in enumerate(self.steps):
            self.steps_group[step.step_group][step_place] = step.step_description()

    def print_step_summarize(self, start, end):
        """
        print iota2 steps that will be run
        """
        summarize = "Full processing include the following steps (checked steps will be run): "
        for group in self.steps_group.keys():
            summarize += "Group {}:\n".format(group)
            for key in self.steps_group[group]:
                highlight = "[ ]"
                if key >= start and key<=end:
                    highlight="[x]"
                summarize += "\t {} Step {}: {}\n".format(highlight, key + 1 ,
                                                          self.steps_group[group][key])
        summarize += "\n"
        return summarize

    def get_dir(self):
        """
        usage : return iota2_directories
        """
        import os
        directories = ['classif', 'config_model', 'dataRegion', 'envelope',
                       'formattingVectors', 'metaData', 'samplesSelection',
                       'stats', 'cmd', 'dataAppVal', 'dimRed', 'final',
                       'learningSamples', 'model', 'shapeRegion', "features"]

        iota2_outputs_dir = self.cfg.getParam('chain', 'outputPath')
        
        return [os.path.join(iota2_outputs_dir, d) for d in directories]

    def get_steps_number(self):
        
        start = self.cfg.getParam('chain', 'firstStep')
        end = self.cfg.getParam('chain', 'lastStep')
        start_ind = self.steps_group.keys().index(start)
        end_ind = self.steps_group.keys().index(end)
        steps = []
        for key in self.steps_group.keys()[start_ind:end_ind+1]:
            print self.steps_group[key]
            steps.append(self.steps_group[key])
        step_to_compute = [step for step_group in steps for step in step_group]
        return step_to_compute


    def build_steps(self, cfg, config_ressources=None):
        """
        build steps
        """
        import os
        # get variable from configuration file
        PathTEST = cfg.getParam('chain', 'outputPath')
 
        from Steps.IOTA2Step import StepContainer
        from Steps import FirstStep
        from Steps import SecondStep

        s_container = StepContainer()
        
        step_container = []
        log_dir = os.path.join(PathTEST, "logs")

        myStep = FirstStep.FirstStep(log_dir)
        otherStep = SecondStep.SecondStep(log_dir)
        s_container.append(myStep, "init")
        s_container.append(otherStep, "init")
        return s_container
