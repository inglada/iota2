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

class Regularization(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        super(Regularization, self).__init__(cfg, cfg_resources_file)

        # step variables
        self.RAM = 1024.0 * get_RAM(self.resources["ram"])
        self.CPU = self.resources["cpu"]
        self.workingDirectory = workingDirectory
        self.outputPath = SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath')
        self.rastclass = SCF.serviceConfigFile(self.cfg).getParam('Simplification', 'classification')
        self.seed = SCF.serviceConfigFile(self.cfg).getParam('Simplification', 'seed')
        self.umc1 = SCF.serviceConfigFile(self.cfg).getParam('Simplification', 'umc1')
        self.inland = SCF.serviceConfigFile(self.cfg).getParam('Simplification', 'inland')
        self.rssize = SCF.serviceConfigFile(self.cfg).getParam('Simplification', 'rssize')
        self.umc2 = SCF.serviceConfigFile(self.cfg).getParam('Simplification', 'umc2')

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("regularisation of classification raster")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        rastclass = self.rastclass
        if rastclass is None:
            if self.seed is not None:
                rastclass = os.path.join(self.outputPath, 'final', 'Classif_Seed_{}.tif'.format(seed))
            else:
                if os.path.exists(os.path.join(self.outputPath, 'final', 'Classifications_fusion.tif')):
                    rastclass = os.path.join(self.outputPath, 'final', 'Classifications_fusion.tif')
                else:
                    rastclass = os.path.join(self.outputPath, 'final', 'Classif_Seed_0.tif')

        return [rastclass]

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from simplification import Regularization as regul

        tmpdir = self.workingDirectory
        if tmpdir is None:
            tmpdir = os.path.join(self.outputPath, 'final', 'simplification',
                                  'tmp')
        outfilereg = os.path.join(self.outputPath, 'final', 'simplification',
                                  'classif_regul.tif')
        step_function = lambda x: regul.OSORegularization(x,
                                                          self.umc1,
                                                          self.CPU,
                                                          tmpdir,
                                                          outfilereg,
                                                          str(self.RAM),
                                                          self.inland,
                                                          self.rssize,
                                                          self.umc2)
        return step_function

    def step_outputs(self):
        """
        """
        pass
