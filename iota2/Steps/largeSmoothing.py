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
from VectorTools import vector_functions as vf

class largeSmoothing(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "smoothing"
        super(largeSmoothing, self).__init__(cfg, cfg_resources_file, resources_block_name)

        # step variables
        self.RAM = 1024.0 * get_RAM(self.resources["ram"])
        self.workingDirectory = workingDirectory
        self.outputPath = SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath')
        self.grasslib = SCF.serviceConfigFile(self.cfg).getParam('Simplification', 'grasslib')
        self.hermite = SCF.serviceConfigFile(self.cfg).getParam('Simplification', 'hermite')
        self.mmu = SCF.serviceConfigFile(self.cfg).getParam('Simplification', 'mmu')
        self.outmos = os.path.join(self.outputPath, 'final', 'simplification', 'mosaic')
        self.clipfile = SCF.serviceConfigFile(self.cfg).getParam('Simplification', 'clipfile')
        self.clipfield = SCF.serviceConfigFile(self.cfg).getParam('Simplification', 'clipfield')
        self.grid = os.path.join(self.outputPath, 'final', 'simplification', 'grid.shp')
        self.epsg = int(ServiceConfigFile.serviceConfigFile(self.cfg).getParam('GlobChain', 'proj').split(":")[-1])
        
    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Hermite smoothing (Serialisation strategy)")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        if not os.path.exists(self.grid):
            return [[os.path.join(self.outmos, "classif_douglas.shp"), os.path.join(self.outmos, "classif_hermite.shp")]]
        else:
            listfid = vf.getFIDSpatialFilter(self.clipfile, self.grid, self.clipfield)            
            return [["%s/tile_%s_%s_douglas.shp"%(self.outmos, self.clipfield, x), "%s/tile_%s_%s_douglas_hermite.shp"%(self.outmos, self.clipfield, x)] for x in listfid]

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from simplification import VectAndSimp as vas

        tmpdir = os.path.join(self.outputPath, 'final', 'simplification', 'tmp')
        if self.workingDirectory:
            tmpdir = self.workingDirectory


        step_function = lambda x: vas.generalizeVector(tmpdir,
                                                       self.grasslib,
                                                       x[0],
                                                       self.hermite,
                                                       "hermite",
                                                       self.mmu,
                                                       out=x[1],
                                                       epsg=self.epsg)

        return step_function

    def step_outputs(self):
        """
        """
        pass
