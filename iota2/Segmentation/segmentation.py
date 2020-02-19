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
import logging
from typing import Dict, Union, List, Optional

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())

sensors_params = Dict[str, Union[str, List[str], int]]


def slicSegmentation(tile_name: str,
                     output_path: str,
                     sensors_parameters: sensors_params,
                     ram: Optional[int] = 128,
                     working_dir: Optional[Union[str, None]] = None,
                     force_spw: Optional[Union[int, None]] = None,
                     logger=LOGGER):
    """generate segmentation using SLIC algorithm

    Parameters
    ----------
    tile_name : string
        tile's name
    output_path : string
        iota2 output path
    sensors_parameters : dict
        sensors parameters description
    ram : int
        available ram
    working_dir : string
        directory to store temporary data
    force_spw : int
        force segments' spatial width
    logger : logging
        root logger
    """
    import math
    import shutil
    from iota2.Common.GenerateFeatures import generateFeatures
    from iota2.Common.OtbAppBank import CreateSLICApplication
    from iota2.Common.OtbAppBank import getInputParameterOutput
    from iota2.Common.FileUtils import ensure_dir

    SLIC_NAME = "SLIC_{}.tif".format(tile_name)

    all_features, feat_labels, dep = generateFeatures(
        working_dir,
        tile_name,
        sar_optical_post_fusion=False,
        output_path=output_path,
        sensors_parameters=sensors_parameters,
        mode="usually")
    all_features.Execute()

    spx, _ = all_features.GetImageSpacing(
        getInputParameterOutput(all_features))

    tmp_dir = working_dir
    if working_dir is None:
        tmp_dir = os.path.join(output_path, "features", tile_name, "tmp",
                               "SLIC_TMPDIR")
    else:
        tmp_dir = os.path.join(working_dir, tile_name)

    ensure_dir(tmp_dir)

    slic_seg_path = os.path.join(output_path, "features", tile_name, "tmp",
                                 SLIC_NAME)

    features_ram_estimation = all_features.PropagateRequestedRegion(
        key="out", region=all_features.GetImageRequestedRegion("out"))
    # increase estimation...
    features_ram_estimation = features_ram_estimation * 1.5
    xy_tiles = math.ceil(
        math.sqrt(float(features_ram_estimation) / (float(ram) * 1024**2)))
    slic_parameters = {
        "in": all_features,
        "tmpdir": tmp_dir,
        "spw": force_spw if force_spw else int(spx),
        "tiling": "manual",
        "tiling.manual.ny": int(xy_tiles),
        "tiling.manual.nx": int(xy_tiles),
        "out": slic_seg_path
    }
    slic_seg = CreateSLICApplication(slic_parameters)

    if not os.path.exists(slic_seg_path):
        logger.info("Processing SLIC segmentation : {}\n\t\t\
                 with parameters : {}".format(tile_name, slic_parameters))
        slic_seg.ExecuteAndWriteOutput()

    if working_dir is None:
        shutil.rmtree(tmp_dir)
