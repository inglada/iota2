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
import sys
from Common import ServiceConfigFile
from Common.Tools import checkDataBase
from Common.FileUtils import is_writable_directory


def check_iota2_inputs(configuration_file_path: str):
    """check inputs in order to achieve a iota2 run
    """

    i2_cfg = ServiceConfigFile.serviceConfigFile(configuration_file_path)
    i2_output_path = i2_cfg.getParam('chain', 'outputPath')
    ground_truth = i2_cfg.getParam('chain', 'groundTruth')
    region_shape = i2_cfg.getParam('chain', 'regionPath')
    data_field = i2_cfg.getParam('chain', 'dataField')
    region_field = i2_cfg.getParam('chain', 'regionField')
    epsg = i2_cfg.getParam('GlobChain', 'proj').split(":")[-1]

    # check input vectors
    gt_errors = checkDataBase.check_ground_truth(ground_truth,
                                                 "",
                                                 data_field,
                                                 epsg,
                                                 do_corrections=False,
                                                 display=False)
    if region_shape is not None:
        regions_errors = checkDataBase.check_region_shape(region_shape,
                                                          "",
                                                          region_field,
                                                          epsg,
                                                          do_corrections=False,
                                                          display=False)

    # ~ check if outputPath can be reach
    error_output_i2_dir = is_writable_directory(i2_output_path)
    print(os.access(i2_output_path, os.W_OK))
    
    # check Sensors paths

    # check if the intersection of the ground truth, the region shape, tiles is not empty

    # ~ errors = gt_errors + regions_errors
    # ~ if errors:
        # ~ sys.tracebacklimit = 0
        # ~ raise Exception("\n".join(["ERROR : {}".format(error.msg) for error in errors]))
