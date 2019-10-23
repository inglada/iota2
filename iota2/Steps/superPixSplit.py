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
from typing import Optional, TypeVar, Generic

from Steps import IOTA2Step
from Common import ServiceConfigFile as SCF
from Cluster import get_RAM

class superPixSplit(IOTA2Step.Step):
    def __init__(self,
                 cfg: str,
                 cfg_resources_file: str,
                 workingDirectory: Optional[str] = None) -> None:
        """set up the step
        """
        # heritage init
        resources_block_name = "superPixSplit"
        super(superPixSplit, self).__init__(cfg, cfg_resources_file, resources_block_name)

        # step variables
        self.workingDirectory = workingDirectory
        self.execution_dir = SCF.serviceConfigFile(self.cfg).getParam('chain', 'outputPath')
        self.is_superPix_field = "is_super_pix"
        self.region_field = SCF.serviceConfigFile(self.cfg).getParam('chain', 'regionField')
        self.ram = 1024.0 * get_RAM(self.resources["ram"])

    def step_description(self):
        """
        function use to print a short description of the step's purpose
        """
        description = ("Generate two data sets, one dedicated to superpixels one to reference data")
        return description

    def step_inputs(self):
        """
        Return
        ------
            the return could be and iterable or a callable
        """
        from Sampling.SplitSamples import get_ordered_learning_samples
        return get_ordered_learning_samples(os.path.join(self.execution_dir, "learningSamples"))

    def step_execute(self):
        """
        Return
        ------
        lambda
            the function to execute as a lambda function. The returned object
            must be a lambda function.
        """
        from Sampling.SplitSamples import split_superpixels_and_reference
        step_function = lambda x: split_superpixels_and_reference(x,
                                                                  superpix_column=self.is_superPix_field,
                                                                  working_dir=self.workingDirectory)
        return step_function

    def step_outputs(self):
        """
        """
        pass
