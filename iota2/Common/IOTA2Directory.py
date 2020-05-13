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
"""Generate iota² output tree"""
import os
import shutil
from typing import Optional, List

from iota2.Common.verifyInputs import check_iota2_inputs


def generate_directories(root: str,
                         check_inputs: Optional[bool] = True,
                         merge_final_classifications: Optional[bool] = False,
                         ground_truth: Optional[str] = None,
                         region_shape: Optional[str] = None,
                         data_field: Optional[str] = None,
                         region_field: Optional[str] = None,
                         epsg: Optional[int] = None,
                         sensor_path: Optional[str] = None,
                         tiles: Optional[List[str]] = None) -> None:
    """
    generate IOTA2 output directories

    Parameters
    ----------
    root : str
        iota2 output path
    check_inputs : bool
        flag to check iota2 user inputs, if this flag is True,
        every parameters are MANDATORY
    merge_final_classifications : bool
        flag to generate the directory dedicated to receive the
        fusion of final classifications
    ground_truth : str
        ground truth path
    region_shape : str
        region shapeFile path
    data_field : str
        data field in ground truth database
    region_field : str
        region field in region shapeFile
    epsg : int
        target projection
    sensor_path : str
        path to a directory containg sensors data split
        by tiles
    tiles : list
        list of tiles
    """
    from iota2.Common.FileUtils import ensure_dir

    if check_inputs:
        check_iota2_inputs(root, ground_truth, region_shape, data_field,
                           region_field, epsg, sensor_path, tiles)

    ensure_dir(root)

    if os.path.exists(root + "/samplesSelection"):
        shutil.rmtree(root + "/samplesSelection")
    os.mkdir(root + "/samplesSelection")
    if os.path.exists(root + "/model"):
        shutil.rmtree(root + "/model")
    os.mkdir(root + "/model")
    if os.path.exists(root + "/formattingVectors"):
        shutil.rmtree(root + "/formattingVectors")
    os.mkdir(root + "/formattingVectors")
    if os.path.exists(root + "/config_model"):
        shutil.rmtree(root + "/config_model")
    os.mkdir(root + "/config_model")
    if os.path.exists(root + "/envelope"):
        shutil.rmtree(root + "/envelope")
    os.mkdir(root + "/envelope")
    if os.path.exists(root + "/classif"):
        shutil.rmtree(root + "/classif")
    os.mkdir(root + "/classif")
    if os.path.exists(root + "/shapeRegion"):
        shutil.rmtree(root + "/shapeRegion")
    os.mkdir(root + "/shapeRegion")
    if os.path.exists(root + "/final"):
        shutil.rmtree(root + "/final")
    os.mkdir(root + "/final")
    os.mkdir(root + "/final/vectors")
    os.mkdir(root + "/final/simplification")
    os.mkdir(root + "/final/simplification/tiles")
    os.mkdir(root + "/final/simplification/vectors")
    os.mkdir(root + "/final/simplification/mosaic")
    os.mkdir(root + "/final/simplification/tmp")
    if os.path.exists(root + "/features"):
        shutil.rmtree(root + "/features")
    os.mkdir(root + "/features")
    if os.path.exists(root + "/dataRegion"):
        shutil.rmtree(root + "/dataRegion")
    os.mkdir(root + "/dataRegion")
    if os.path.exists(root + "/learningSamples"):
        shutil.rmtree(root + "/learningSamples")
    os.mkdir(root + "/learningSamples")
    if os.path.exists(root + "/dataAppVal"):
        shutil.rmtree(root + "/dataAppVal")
    os.mkdir(root + "/dataAppVal")
    if os.path.exists(root + "/stats"):
        shutil.rmtree(root + "/stats")
    os.mkdir(root + "/stats")

    if os.path.exists(root + "/cmd"):
        shutil.rmtree(root + "/cmd")
    os.mkdir(root + "/cmd")
    os.mkdir(root + "/cmd/stats")
    os.mkdir(root + "/cmd/train")
    os.mkdir(root + "/cmd/cla")
    os.mkdir(root + "/cmd/confusion")
    os.mkdir(root + "/cmd/features")
    os.mkdir(root + "/cmd/fusion")
    os.mkdir(root + "/cmd/splitShape")

    if merge_final_classifications:
        if os.path.exists(root + "/final/merge_final_classifications"):
            shutil.rmtree(root + "/final/merge_final_classifications")
        os.mkdir(root + "/final/merge_final_classifications")


def generate_features_maps_directories(root: str) -> None:
    """
    generate output directories for write features maps

    Parameters
    ----------
    root : str
        iota2 output path
    """
    from iota2.Common.FileUtils import ensure_dir

    ensure_dir(root)

    if os.path.exists(root + "/final"):
        shutil.rmtree(root + "/final")
    os.mkdir(root + "/final")
    if os.path.exists(root + "/features"):
        shutil.rmtree(root + "/features")
    os.mkdir(root + "/features")
    if os.path.exists(root + "/customF"):
        shutil.rmtree(root + "/customF")
    os.mkdir(root + "/customF")
