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


class mergeRegularization(IOTA2Step.Step):
    def __init__(
        self,
        cfg,
        cfg_resources_file,
        stepname=None,
        output=None,
        umc=None,
        resample=None,
        water=None,
        workingDirectory=None,
    ):
        # heritage init
        resources_block_name = "mergeregularisation"
        super(mergeRegularization, self).__init__(
            cfg, cfg_resources_file, resources_block_name
        )

        # step variables
        if stepname:
            self.step_name = stepname

        self.RAM = 1024.0 * get_RAM(self.resources["ram"])
        self.CPU = self.resources["cpu"]
        self.workingDirectory = workingDirectory
        self.outputPath = SCF.serviceConfigFile(self.cfg).getParam(
            "chain", "outputPath"
        )
        self.resample = resample
        self.water = water
        self.umc = umc
        self.output = output
        self.tmpdir = os.path.join(
            self.outputPath, "final", "simplification", "tmp"
        )

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = "Majority regularisation of adaptive-regularized raster"
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """

        from Common import FileUtils as fut

        listout = fut.FileSearch_AND(self.tmpdir, True, "mask", ".tif")

        return [listout]

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from simplification import manageRegularization as mr

        tmpdir = self.workingDirectory
        if tmpdir is None:
            tmpdir = os.path.join(
                self.outputPath, "final", "simplification", "tmp"
            )

        if not self.output:
            output = os.path.join(tmpdir, "regul1.tif")
        else:
            output = self.output

        step_function = lambda x: mr.mergeRegularization(
            tmpdir,
            x,
            self.umc,
            output,
            str(self.RAM),
            self.resample,
            self.water,
        )

        return step_function

    def step_outputs(self):
        """
        """
        pass

    def step_clean(self):
        """
        """
        from Common import FileUtils as fut

        for filetoremove in fut.FileSearch_AND(
            self.tmpdir, True, "mask", ".tif"
        ):
            os.remove(filetoremove)

        if os.path.exists(
            os.path.join(
                self.outputPath, "final", "simplification", "classif_regul.tif"
            )
        ):
            os.remove(os.path.join(self.tmpdir, "regul1.tif"))
