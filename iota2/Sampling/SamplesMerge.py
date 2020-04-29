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
"""
The samples merge module
"""
import logging
import os
from typing import Optional, List, Tuple

from iota2.Common import FileUtils as fut

LOGGER = logging.getLogger(__name__)


def get_models(formatting_vector_directory: str, region_field: str,
               runs: int) -> List[Tuple[str, List[str], int]]:
    """
    usage :
    describe samples spatial repartition
    function use to determine with shapeFile as to be merged in order to
    compute statistics thanks to otb_SampleSelection

    OUT:
    regions_tiles_seed [list] :
    example
    regions_tiles_seed = [('1', ['T1', 'T2'], 0), ('1', ['T1', T2], 1),
                          ('2', ['T2', 'T3], 0), ('2', ['T2', 'T3], 1)]
    mean the region '1' is present in tiles 'T1' and 'T2' in run 0 and 1
    and region '2' in 'T2', 'T3' in runs 0 and 1
    """
    # the way of getting region could be improve ?
    tiles = fut.FileSearch_AND(formatting_vector_directory, True, ".shp")
    region_tile = []
    all_regions_in_run = []
    for tile in tiles:
        all_regions = []
        tile_name = os.path.splitext(os.path.basename(tile))[0]
        r_tmp = fut.getFieldElement(tile,
                                    driverName="ESRI Shapefile",
                                    field=region_field,
                                    mode="unique",
                                    elemType="str")
        for r_tile in r_tmp:
            if r_tile not in all_regions:
                all_regions.append(r_tile)

        for region in all_regions:
            if region not in all_regions_in_run:
                all_regions_in_run.append(region)
            region_tile.append((region, tile_name))

    region_tile_tmp = dict(fut.sortByFirstElem(region_tile))
    region_tile_dic = {}
    for region, region_tiles in list(region_tile_tmp.items()):
        region_tile_dic[region] = list(set(region_tiles))

    all_regions_in_run = sorted(all_regions_in_run)
    regions_tiles_seed = [(region, region_tile_dic[region], run)
                          for run in range(runs)
                          for region in all_regions_in_run]
    return regions_tiles_seed


def extract_poi(tile_vector: str,
                region: str,
                seed: int,
                region_field: str,
                poi: str,
                poi_val: str,
                force_seed_field: Optional[bool] = None) -> None:
    """
    Extract Polygon Of Interest
    Parameters
    ----------
    tile_vector: string
    region: string
    seed: int
    region_field: str
    poi: str
    poi_val: str
    force_seed_field: bool
    Return
    ------
    None
    """
    from iota2.Common.Utils import run
    learn_flag = "learn"
    validation_flag = "validation"
    seed_field = "seed_{}".format(seed)
    cmd = (f"ogr2ogr -where \"{region_field}='{region}' AND {seed_field}"
           f"='{learn_flag}'\" {poi} {tile_vector}")
    run(cmd)
    if poi_val:
        if force_seed_field:
            seed_field = force_seed_field
        cmd = (f"ogr2ogr -where \"{region_field}='{region}' AND {seed_field}="
               f"'{validation_flag}'\" {poi_val} {tile_vector}")
        run(cmd)


def samples_merge(region_tiles_seed: str, output_path: str, region_field: str,
                  runs: int, enable_cross_validation: bool,
                  ds_sar_opt_flag: bool, working_directory: str) -> None:
    """
    to a given region and seed, extract features through tiles
    then merge features to a new file
    """

    region, tiles, seed = region_tiles_seed

    formatting_vec_dir = os.path.join(output_path, "formattingVectors")
    samples_selection_dir = os.path.join(output_path, "samplesSelection")
    learn_val_dir = os.path.join(output_path, "dataAppVal")

    by_models_val = os.path.join(learn_val_dir, "bymodels")
    if not os.path.exists(by_models_val):
        try:
            os.mkdir(by_models_val)
        except OSError:
            pass
    wd_val = by_models_val
    work_dir = samples_selection_dir

    if working_directory:
        work_dir = working_directory
        wd_val = working_directory

    cross_validation_field = None
    if ds_sar_opt_flag and enable_cross_validation:
        cross_validation_field = "seed_{}".format(runs - 1)

    vector_region = []
    vector_region_val = []
    for tile in tiles:
        vector_tile = fut.FileSearch_AND(formatting_vec_dir, True, tile,
                                         ".shp")[0]
        poi_name = f"{tile}_region_{region}_seed_{seed}_samples.shp"
        poi_learn = os.path.join(work_dir, poi_name)
        poi_val = None
        # if SAR and Optical post-classification fusion extract validation
        # samples
        if ds_sar_opt_flag:
            poi_val_name = f"{tile}_region_{region}_seed_{seed}_samples_val.shp"
            poi_val = os.path.join(wd_val, poi_val_name)
            vector_region_val.append(poi_val)
        extract_poi(vector_tile, region, seed, region_field, poi_learn,
                    poi_val, cross_validation_field)
        vector_region.append(poi_learn)

    merged_poi_name = f"samples_region_{region}_seed_{seed}"
    merged_poi = fut.mergeVectors(merged_poi_name, work_dir, vector_region)

    for vector_r in vector_region:
        fut.removeShape(vector_r.replace(".shp", ""),
                        [".prj", ".shp", ".dbf", ".shx"])

    if working_directory:
        fut.cpShapeFile(merged_poi.replace(".shp", ""),
                        samples_selection_dir,
                        [".prj", ".shp", ".dbf", ".shx"],
                        spe=True)
        if ds_sar_opt_flag:
            for vector_validation in vector_region_val:
                if os.path.exists(vector_validation):
                    fut.cpShapeFile(vector_validation.replace(".shp", ""),
                                    by_models_val,
                                    [".prj", ".shp", ".dbf", ".shx"],
                                    spe=True)
