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

from Steps import IOTA2Step
from Cluster import get_RAM
from Common import ServiceConfigFile as SCF


class largeVectorization(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "vectorisation"
        super(
            largeVectorization,
            self).__init__(
            cfg,
            cfg_resources_file,
            resources_block_name)

        # step variables
        self.RAM = 1024.0 * get_RAM(self.resources["ram"])
        self.workingDirectory = workingDirectory
        self.outputPath = SCF.serviceConfigFile(
            self.cfg).getParam(
            'chain', 'outputPath')
        self.grasslib = SCF.serviceConfigFile(
            self.cfg).getParam(
            'Simplification', 'grasslib')
        self.mmu = SCF.serviceConfigFile(
            self.cfg).getParam(
            'Simplification', 'mmu')
        self.lcfield = SCF.serviceConfigFile(
            self.cfg).getParam(
            'Simplification', 'lcfield')
        self.clipfile = SCF.serviceConfigFile(
            self.cfg).getParam(
            'Simplification', 'clipfile')
        self.clipfield = SCF.serviceConfigFile(
            self.cfg).getParam(
            'Simplification', 'clipfield')
        self.clipvalue = SCF.serviceConfigFile(
            self.cfg).getParam(
            'Simplification', 'clipvalue')
        self.outprefix = SCF.serviceConfigFile(
            self.cfg).getParam(
            'Simplification', 'outprefix')
        self.douglas = SCF.serviceConfigFile(
            self.cfg).getParam(
            'Simplification', 'douglas')
        self.hermite = SCF.serviceConfigFile(
            self.cfg).getParam(
            'Simplification', 'hermite')
        self.angle = SCF.serviceConfigFile(
            self.cfg).getParam(
            'Simplification', 'angle')
        self.shapeRegion = SCF.serviceConfigFile(
            self.cfg).getParam(
            'chain', 'regionPath')
        self.field_Region = SCF.serviceConfigFile(
            self.cfg).getParam(
            'chain', 'regionField')

        self.checkvalue = False
        if not self.clipfile:
            if self.shapeRegion:
                self.clipfile = self.shapeRegion
            else:
                self.clipfile = os.path.join(self.outputPath, 'MyRegion.shp')
            self.clipfield = self.field_Region
            self.checkvalue = True
        else:
            if self.clipvalue is None:
                self.checkvalue = True

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = (
            "Vectorisation and simplification of classification (Serialisation strategy)")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from simplification import MergeTileRasters as mtr
        return mtr.getListValues(self.checkvalue, self.clipfile, self.clipfield,
                                 os.path.join(self.outputPath, 'final',
                                              'simplification', 'vectors'),
                                 self.outprefix, self.clipvalue)

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from simplification import MergeTileRasters as mtr
        tmpdir = os.path.join(
            self.outputPath,
            'final',
            'simplification',
            'tmp')
        if self.workingDirectory:
            tmpdir = self.workingDirectory

        outfilegrid = os.path.join(self.outputPath, 'final', 'simplification',
                                   'grid.shp')
        outfilevect = os.path.join(self.outputPath, 'final', 'simplification',
                                   'vectors', '%s_.shp' % (self.outprefix))
        outserial = os.path.join(self.outputPath, 'final', 'simplification',
                                 'tiles')

        def step_function(x): return mtr.tilesRastersMergeVectSimp(tmpdir,
                                                                   outfilegrid,
                                                                   outfilevect,
                                                                   self.grasslib,
                                                                   self.mmu,
                                                                   self.lcfield,
                                                                   self.clipfile,
                                                                   self.clipfield,
                                                                   x,
                                                                   "FID",
                                                                   "tile_",
                                                                   outserial,
                                                                   self.douglas,
                                                                   self.hermite,
                                                                   self.angle)
        return step_function

    def step_outputs(self):
        """
        """
        pass
