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
import sys
import logging

from Common import ServiceError
from Common import ServiceConfigFile
from Common.Tools import checkDataBase
from Common.FileUtils import is_writable_directory

logger = logging.getLogger(__name__)


def check_iota2_inputs(configuration_file_path: str):
    """check inputs in order to achieve a iota2 run

    the function check :
        - the ground truth
        - the region shape
        - if an intersection exists between data
        - reachable path
    TODO :
        - check corrupted data
        - check if all expected sensors data exists, new sensors methods ?
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
    # check if outputPath can be reach
    error_output_i2_dir = is_writable_directory(i2_output_path)
    path_errors = []
    if not error_output_i2_dir:
        path_errors.append(ServiceError.directoryError(i2_output_path))

    # check if the intersection of the ground truth, the region shape, tiles is not empty

    errors = gt_errors + regions_errors + path_errors
    if errors:
        sys.tracebacklimit = 0
        errors_sum = "\n".join(["ERROR : {}".format(error.msg) for error in errors])
        logger.error(errors_sum)
        raise Exception(errors_sum)
