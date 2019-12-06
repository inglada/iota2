#!/usr/bin/env python3
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

from Steps import IOTA2Step
from Cluster import get_RAM
from Common import ServiceConfigFile as SCF

class Regularization(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, umc, logname=None, workingDirectory=None):
        # heritage init
        resources_block_name = "regularisation"
        super(Regularization, self).__init__(cfg, cfg_resources_file, resources_block_name)

        
        # step variables
        if logname:
            self.logFile = logname

        self.RAM = 1024.0 * get_RAM(self.resources["ram"])
        self.CPU = self.resources["cpu"]
        self.workingDirectory = workingDirectory
        self.outputPath = SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath')
        self.rastclass = SCF.serviceConfigFile(self.cfg).getParam('Simplification', 'classification')
        self.seed = SCF.serviceConfigFile(self.cfg).getParam('Simplification', 'seed')
        self.umc = umc
        self.outtmpdir = os.path.join(self.outputPath, 'final', 'simplification', 'tmp')
        
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

        from simplification import manageNomenclature as mn
        
        rastclass = self.rastclass
        if not os.path.exists(os.path.join(self.outtmpdir, 'regul1.tif')):
            if rastclass is None:
                if self.seed is not None:
                    rastclass = os.path.join(self.outputPath, 'final', 'Classif_Seed_{}.tif'.format(seed))
                else:
                    if os.path.exists(os.path.join(self.outputPath, 'final', 'Classifications_fusion.tif')):
                        rastclass = os.path.join(self.outputPath, 'final', 'Classifications_fusion.tif')
                    else:
                        rastclass = os.path.join(self.outputPath, 'final', 'Classif_Seed_0.tif')
        else:
            rastclass = os.path.join(self.outtmpdir, 'regul1.tif')
                    
        rules = mn.getMaskRegularisation("/home/qt/thierionv/dev/iota2/iota2/simplification/nomenclature.cfg")

        scenarios = [[rastclass, rule] for rule in rules]

        return scenarios

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from simplification import manageNomenclature as mn

        if self.workingDirectory:
            self.tmpdir = self.workingDirectory        

        #outfilereg = os.path.join(self.outputPath, 'final', 'simplification','classif_regul.tif')
        
        step_function = lambda x: mn.adaptRegularization(self.tmpdir,
                                                         x[0],
                                                         os.path.join(self.outtmpdir, x[1][2]),
                                                         str(self.RAM),
                                                         x[1],
                                                         self.umc)

        return step_function

    def step_outputs(self):
        """
        """
        pass

    def step_clean(self):
        """
        """
        
        pass
