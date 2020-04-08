# !/usr/bin/env python3
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
"""generate statistics by tiles, useful to select samples"""
import os
import shutil
import logging
from typing import Tuple, Optional, Union
from iota2.Common import OtbAppBank as otb
from iota2.Common import FileUtils as fut

LOGGER = logging.getLogger(__name__)


def region_tile(sample_sel_dir: str):
    """
    """
    tile_field_name = "tile_o"
    region_vectors = fut.FileSearch_AND(sample_sel_dir, True, ".shp")
    output = []
    region_vectors = sorted(region_vectors)
    for region_vector in region_vectors:
        tiles = fut.getFieldElement(region_vector,
                                    driverName="ESRI Shapefile",
                                    field=tile_field_name,
                                    mode="unique",
                                    elemType="str")
        region_name = os.path.splitext(
            os.path.basename(region_vector))[0].split("_")[2]
        seed = os.path.splitext(
            os.path.basename(region_vector))[0].split("_")[4]
        tiles = sorted(tiles)
        for tile in tiles:
            output.append((region_name, seed, tile))
    return output


def samples_stats(region_seed_tile: Tuple[str, str, str],
                  iota2_directory: str,
                  data_field: str,
                  working_directory: Optional[Union[str, None]] = None,
                  logger=LOGGER) -> str:
    """generate samples statistics by tiles

    Parameters
    ----------
    region_seed_tile: tuple
    iota2_directory: str
        iota2 output directory
    data_field: str
        data field in region database
    working_directory: str
        path to a working directory
    logger: logging
        root logger

    Return
    ------
    str
        file containing statistics from otbcli_PolygonClassStatistics
    """
    region, seed, tile = region_seed_tile
    samples_selection_dir = os.path.join(iota2_directory, "samplesSelection")
    tile_region_dir = os.path.join(iota2_directory, "shapeRegion")

    w_dir = samples_selection_dir
    if working_directory:
        w_dir = working_directory

    raster_mask = fut.FileSearch_AND(tile_region_dir, True,
                                     "region_" + region.split("f")[0] + "_",
                                     ".tif", tile)[0]
    region_vec = fut.FileSearch_AND(samples_selection_dir, True,
                                    "_region_" + region, "seed_" + seed,
                                    ".shp")[0]

    logger.info(
        f"Launch statistics on tile {tile} in region {region} run {seed}")
    region_tile_stats_name = f"{tile}_region_{region}_seed_{seed}_stats.xml"
    region_tile_stats = os.path.join(w_dir, region_tile_stats_name)
    polygon_stats_app = otb.CreatePolygonClassStatisticsApplication({
        "in":
        raster_mask,
        "mask":
        raster_mask,
        "vec":
        region_vec,
        "field":
        data_field,
        "out":
        region_tile_stats
    })
    polygon_stats_app.ExecuteAndWriteOutput()
    if working_directory:
        shutil.copy(region_tile_stats, samples_selection_dir)

    return region_tile_stats
