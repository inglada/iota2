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
from collections import OrderedDict
from Common import ServiceConfigFile as SCF

class iota2():
    """
    class use to describe steps sequence and variable to use at each step (config)
    """
    def __init__(self, cfg, config_ressources):
        
        # config object
        #~ self.cfg = cfg
        self.cfg = cfg

        # working directory, HPC
        HPC_working_directory = "TMPDIR"
        self.workingDirectory = os.getenv(HPC_working_directory)

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

        # pickle's path
        self.iota2_pickle = os.path.join(SCF.serviceConfigFile(self.cfg).getParam("chain", "outputPath"),
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
        else :
            iota2_chain = self
        return iota2_chain

    def sort_step(self):
        """
        use to establish which step is going to which step group
        """
        
        for step_place, step in enumerate(self.steps):
            self.steps_group[step.step_group][step_place + 1] = step.step_description()

    def print_step_summarize(self, start, end):
        """
        print iota2 steps that will be run
        """
        summarize = "Full processing include the following steps (checked steps will be run):\n"
        for group in self.steps_group.keys():
            if len(self.steps_group[group]) > 0:
                summarize += "Group {}:\n".format(group)
            for key in self.steps_group[group]:
                highlight = "[ ]"
                if key >= start and key<=end:
                    highlight="[x]"
                summarize += "\t {} Step {}: {}\n".format(highlight, key ,
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

        iota2_outputs_dir = SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath')
        
        return [os.path.join(iota2_outputs_dir, d) for d in directories]

    def get_steps_number(self):
        start = SCF.serviceConfigFile(self.cfg).getParam('chain', 'firstStep')
        end = SCF.serviceConfigFile(self.cfg).getParam('chain', 'lastStep')
        start_ind = self.steps_group.keys().index(start)
        end_ind = self.steps_group.keys().index(end)
        steps = []
        for key in self.steps_group.keys()[start_ind:end_ind+1]:
            steps.append(self.steps_group[key])
        step_to_compute = [step for step_group in steps for step in step_group]
        return step_to_compute

    def build_steps(self, cfg, config_ressources=None):
        """
        build steps
        """
        import os
        from MPI import ressourcesByStep as iota2Ressources
        from Common import ServiceConfigFile as SCF

        if config_ressources:
            ressourcesByStep = iota2Ressources.iota2_ressources(config_ressources)
        else:
            ressourcesByStep = iota2Ressources.iota2_ressources()

        from Steps.IOTA2Step import StepContainer

        from Steps import (IOTA2DirTree, Sentinel1PreProcess,
                           CommonMasks, PixelValidity,
                           Envelope, genRegionVector)

        s_container = StepContainer()

        # class instance
        step_build_tree = IOTA2DirTree.IOTA2DirTree(cfg, config_ressources)
        step_S1_preproc = Sentinel1PreProcess.Sentinel1PreProcess(cfg,
                                                                  config_ressources,
                                                                  self.workingDirectory)
        step_CommonMasks = CommonMasks.CommonMasks(cfg,
                                                   config_ressources,
                                                   self.workingDirectory)
        step_pixVal = PixelValidity.PixelValidity(cfg,
                                                  config_ressources,
                                                  self.workingDirectory)
        step_env = Envelope.Envelope(cfg,
                                     config_ressources,
                                     self.workingDirectory)

        step_reg_vector = genRegionVector.genRegionVector(cfg,
                                                          config_ressources,
                                                          self.workingDirectory)
        # control variable
        Sentinel1 = SCF.serviceConfigFile(cfg).getParam('chain', 'S1Path')
        shapeRegion = SCF.serviceConfigFile(cfg).getParam('chain', 'regionPath')

        # build chain
        s_container.append(step_build_tree, "init")
        if not "None" in Sentinel1:
            s_container.append(step_S1_preproc, "init")
        s_container.append(step_CommonMasks, "init")
        s_container.append(step_pixVal, "init")

        s_container.append(step_env, "sampling")
        if not shapeRegion:
            s_container.append(step_reg_vector, "sampling")
        return s_container
