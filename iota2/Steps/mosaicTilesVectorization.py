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

from iota2.Steps import IOTA2Step
from iota2.Common import ServiceConfigFile as SCF
from iota2.VectorTools import vector_functions as vf


class mosaicTilesVectorization(IOTA2Step.Step):
    def __init__(self, cfg, cfg_resources_file, workingDirectory=None):
        # heritage init
        resources_block_name = "mosaictiles"
        super(mosaicTilesVectorization, self).__init__(cfg, cfg_resources_file,
                                                       resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.outputPath = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')
        self.shapeRegion = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'regionPath')
        self.field_Region = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'regionField')
        self.clipfile = SCF.serviceConfigFile(self.cfg).getParam(
            'Simplification', 'clipfile')
        self.clipfield = SCF.serviceConfigFile(self.cfg).getParam(
            'Simplification', 'clipfield')
        self.clipvalue = SCF.serviceConfigFile(self.cfg).getParam(
            'Simplification', 'clipvalue')
        self.outprefix = SCF.serviceConfigFile(self.cfg).getParam(
            'Simplification', 'outprefix')
        self.outserial = os.path.join(self.outputPath, 'final',
                                      'simplification', 'tiles')
        self.outfilegrid = os.path.join(self.outputPath, 'final',
                                        'simplification', 'grid.shp')
        self.outmos = os.path.join(self.outputPath, 'final', 'simplification',
                                   'mosaic')
        self.outfilevect = os.path.join(self.outputPath, 'final',
                                        'simplification', 'vectors')
        self.grid = os.path.join(self.outputPath, 'final', 'simplification',
                                 'grid.shp')

        if self.workingDirectory is None:
            self.tmpdir = os.path.join(self.outputPath, 'final',
                                       'simplification', 'tmp')
        else:
            self.tmpdir = self.workingDirectory

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

    @classmethod
    def step_description(cls):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Mosaic raster tiles for serialisation strategy)")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """

        return vf.getFIDSpatialFilter(self.clipfile, self.grid, self.clipfield)

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """

        from iota2.simplification import MergeTileRasters as mtr
        self.tmpdir = os.path.join(self.outputPath, 'final', 'simplification',
                                   'tmp')
        if self.workingDirectory:
            self.tmpdir = self.workingDirectory

        step_function = lambda x: mtr.mergeTileRaster(
            self.tmpdir, self.clipfile, self.clipfield, x, self.outfilegrid,
            self.outserial, "FID", "tile_", self.outmos)
        return step_function

    def step_outputs(self):
        """
        """
        pass
