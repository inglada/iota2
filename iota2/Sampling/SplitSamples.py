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
from typing import List, Optional, Dict, Union
from logging import Logger

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())


def get_ordered_learning_samples(learning_directory: str) -> List[str]:
    """
    scan learning directory and return a list of files ordered considering
    model and seed

    Parameters
    ----------
    learning_directory : str
        path to the learning directory

    Return
    ------
    list
        list of path
    """
    import operator
    from iota2.Common.FileUtils import FileSearch_AND

    tile_position = 0
    model_position = 2
    seed_position = 3

    learning_files = FileSearch_AND(learning_directory, False,
                                    "_Samples_learn.sqlite")
    files_indexed = [
        (c_file.split("_")[model_position], c_file.split("_")[tile_position],
         int(c_file.split("_")[seed_position].replace("seed", "")),
         os.path.join(learning_directory, "{}.sqlite".format(c_file)))
        for c_file in learning_files
    ]
    files_indexed_sorted = sorted(files_indexed,
                                  key=operator.itemgetter(0, 1, 2))
    return [learning_file for _, _, _, learning_file in files_indexed_sorted]


def split_superpixels_and_reference(
        vector_file: str,
        superpix_column: Optional[str] = "superpix",
        driver_in: Optional[str] = "SQLite",
        working_dir: Optional[str] = None,
        logger: Optional[logging.Logger] = LOGGER) -> None:
    """
    reference feature contains the value 0 in column 'superpix'
    Parameters
    ----------
    vector_file : string
                the input vector file
    superpix_column: string
                the column name for superpixels in vector_file
    driver : string
            the vector_file format
    Return
    ------
    None
    """
    import ogr
    import shutil

    from iota2.Common.Utils import run

    driver = ogr.GetDriverByName(driver_in)
    data_source = driver.Open(vector_file, 0)
    layer = data_source.GetLayer()
    table_name = layer.GetName()
    feat = layer.GetNextFeature()
    geom = feat.GetGeometryRef()
    spatial_ref = geom.GetSpatialReference()
    epsg_code = int(spatial_ref.GetAttrValue("AUTHORITY", 1))
    vectors_dir, vector_name = os.path.split(vector_file)

    tmp_dir = vectors_dir
    if working_dir:
        tmp_dir = working_dir

    superpix_db = os.path.join(
        tmp_dir, vector_name.replace("learn.sqlite", "SP.sqlite"))
    ref_db = os.path.join(tmp_dir,
                          vector_name.replace("learn.sqlite", "REF.sqlite"))

    logger.info(
        f"Extract superpixel samples from file {superpix_db} and save it "
        f"in {superpix_db}")
    sql = f"select * from {table_name} where {superpix_column}!={0}"
    cmd = (
        f'ogr2ogr -t_srs EPSG:{epsg_code} -s_srs EPSG:{epsg_code} -nln'
        f' {table_name} -f "{driver_in}" -sql "{sql}" {superpix_db} {vector_file}'
    )
    run(cmd)

    logger.info(
        f"Extract reference samples from file {vector_file} and save it"
        f" in {vector_file}")
    sql = f"select * from {table_name} where {superpix_column}={0}"
    cmd = (f'ogr2ogr -t_srs EPSG:{epsg_code} -s_srs EPSG:{epsg_code} '
           f'-nln {table_name} -f "{driver_in}" -sql "{sql}" '
           f'{ref_db} {vector_file}')
    run(cmd)
    shutil.move(ref_db, vector_file)
    if working_dir:
        shutil.copy(superpix_db, vectors_dir)
        os.remove(superpix_db)

    # TODO : replace og2ogr by geopandas ?
    # conn = sqlite3.connect(vector_file)
    # df = geopd.GeoDataFrame.from_postgis(sql, conn, geom_col="geometry")
    # conn_out = sqlite3.connect(vector_file.replace(".sqlite", "_V3.sqlite"))
    # df.to_sql(table_name, conn_out)
    return vector_file, os.path.join(vectors_dir,
                                     os.path.split(superpix_db)[-1])


def get_regions_area(vectors: List[str], regions: List[str],
                     formatting_vectors_dir: str, working_directory: [str],
                     region_field: [str]) -> Dict[str, List[str]]:
    """
    usage : get all models polygons area
    IN
    vectors [list of strings] : path to vector file
    regions [list of string] : all possible regions
    formatting_vectors_dir [string] : path to /iota2/formattingVectors
    workingDirectory [string]
    region_field [string]

    OUT
    dico_region_area [dict] : dictionnary containing area by region's key
    """
    from iota2.Common.Utils import run
    from iota2.Common import FileUtils as fut
    import sqlite3 as db
    tmp_data = []
    # init dict
    dico_region_area = {}
    dico_region_tile = {}
    for reg in regions:
        dico_region_area[reg] = 0.0
        dico_region_tile[reg] = []

    for vector in vectors:
        # move vectors to sqlite (faster format)
        transform_dir = formatting_vectors_dir
        if working_directory:
            transform_dir = working_directory
        transform_vector_name = os.path.split(vector)[-1].replace(
            ".shp", ".sqlite")
        sqlite_vector = os.path.join(transform_dir, transform_vector_name)
        cmd = "ogr2ogr -f 'SQLite' {} {}".format(sqlite_vector, vector)
        run(cmd)
        tmp_data.append(sqlite_vector)
        region_vector = fut.getFieldElement(sqlite_vector,
                                            driverName="SQLite",
                                            field=region_field,
                                            mode="unique",
                                            elemType="str")
        conn = db.connect(sqlite_vector)
        conn.enable_load_extension(True)
        conn.load_extension("mod_spatialite")
        cursor = conn.cursor()
        table_name = (transform_vector_name.replace(".sqlite", "")).lower()
        for current_region in region_vector:
            sql_clause = (
                f"SELECT AREA(GEOMFROMWKB(GEOMETRY)) FROM "
                f"{table_name} WHERE {region_field}={current_region}")
            cursor.execute(sql_clause)
            res = cursor.fetchall()

            dico_region_area[current_region] += sum(area[0] for area in res)

            if vector not in dico_region_tile[current_region]:
                dico_region_tile[current_region].append(sqlite_vector)

        conn = cursor = None

    return dico_region_area, dico_region_tile, tmp_data


def get_splits_regions(areas, region_threshold):
    """
    return regions which must be split
    """
    import math
    dic = {}  # {'region':Nsplits,..}
    for region, area in list(areas.items()):
        fold = int(math.ceil(area / (region_threshold * 1e6)))
        if fold > 1:
            dic[region] = fold
    return dic


def get_fid_values(vector_path: str, data_field: str, region_field: str,
                   region: str, value: int) -> List[str]:
    """
    Parameters
    ----------
    vector_path: string
    data_field: string
    region_field: string
    region: string
    value: int
    Return
    ------
    list[string]
    """
    import sqlite3 as db
    conn = db.connect(vector_path)
    cursor = conn.cursor()
    table_name = (os.path.splitext(os.path.basename(vector_path))[0]).lower()

    sql_clause = (
        f"SELECT ogc_fid FROM {table_name} WHERE {data_field}={value}"
        f" AND {region_field}='{region}'")
    cursor.execute(sql_clause)
    fids = cursor.fetchall()
    conn = cursor = None
    return [fid[0] for fid in fids]


def update_vector(vector_path: str,
                  region_field: str,
                  new_regions_dict: Dict[str, str],
                  logger: Optional[Logger] = LOGGER) -> None:
    """
    Parameters
    ----------
    vector_path: string
    region_field: string
    new_regions_dict: dict[str,str]
    Return
    ------
    None
    """
    from iota2.Common import FileUtils as fut
    # const
    sqlite3_query_limit = 1000.0

    import math
    import sqlite3 as db
    conn = db.connect(vector_path)
    cursor = conn.cursor()
    table_name = (os.path.splitext(os.path.basename(vector_path))[0]).lower()

    for new_region_name, fids in list(new_regions_dict.items()):
        nb_sub_split_sqlite = int(math.ceil(len(fids) / sqlite3_query_limit))
        sub_fid_sqlite = fut.splitList(fids, nb_sub_split_sqlite)

        sub_fid_clause = []
        for sub_fid in sub_fid_sqlite:
            sub_fid_clause.append("(ogc_fid in ({}))".format(", ".join(
                map(str, sub_fid))))
        fid_clause = " OR ".join(sub_fid_clause)
        sql_clause = (f"UPDATE {table_name} SET {region_field}="
                      f"'{new_region_name}' WHERE {fid_clause}")
        logger.debug("update fields")
        logger.debug(sql_clause)

        cursor.execute(sql_clause)
        conn.commit()

    conn = cursor = None


def split(regions_split: Dict[str, int], regions_tiles: Dict[str, List[str]],
          data_field: str, region_field: str) -> List[str]:
    """
    function dedicated to split to huge regions in sub-regions
    Parameters
    ----------
    regions_split: dict[string, int]
    regions_tiles: dict[str, List[str]]
    Return
    ------
    list(str)
    """
    from iota2.Common import FileUtils as fut
    updated_vectors = []

    for region, fold in list(regions_split.items()):
        vector_paths = regions_tiles[region]
        for vec in vector_paths:
            # init dict new regions
            new_regions_dict = {}
            for sub_fold in range(fold):
                # new region's name are define here
                new_regions_dict["{}f{}".format(region, sub_fold + 1)] = []

            # get possible class
            class_vector = fut.getFieldElement(vec,
                                               driverName="SQLite",
                                               field=data_field,
                                               mode="unique",
                                               elemType="str")
            dic_class = {}
            # get FID values for all class of current region into
            # the current tile
            for c_class in class_vector:
                dic_class[c_class] = get_fid_values(vec, data_field,
                                                    region_field, region,
                                                    c_class)

            nb_feat = 0
            for _, fid_cl in list(dic_class.items()):
                if fid_cl:
                    fid_folds = fut.splitList(fid_cl, fold)
                    # fill new_regions_dict
                    for i, fid_fold in enumerate(fid_folds):
                        new_regions_dict[f"{region}f{i+1}"] += fid_fold
                nb_feat += len(fid_cl)
            update_vector(vec, region_field, new_regions_dict)
            if vec not in updated_vectors:
                updated_vectors.append(vec)

    return updated_vectors


def transform_to_shape(sqlite_vectors: List[str],
                       formatting_vectors_dir: str) -> List[str]:
    """
    Parameters
    ----------
    sqlite_vectors: list(str)
    formatting_vectors_dir: str
    Return
    ------
    list(str)
    """
    from iota2.Common import FileUtils as fut
    from iota2.Common.Utils import run
    out = []
    for sqlite_vector in sqlite_vectors:
        out_name = os.path.splitext(os.path.basename(sqlite_vector))[0]
        out_path = os.path.join(formatting_vectors_dir, f"{out_name}.shp")
        if os.path.exists(out_path):
            fut.removeShape(out_path.replace(".shp", ""),
                            [".prj", ".shp", ".dbf", ".shx"])
        cmd = f"ogr2ogr -f 'ESRI Shapefile' {out_path} {sqlite_vector}"
        run(cmd)
        out.append(out_path)
    return out


# def update_learningValination_sets(new_regions_shapes, dataAppVal_dir,
def update_learning_validation_sets(new_regions_shapes: List[str],
                                    data_app_val_dir: str, data_field: str,
                                    region_field: str, ratio: float,
                                    seeds: int, epsg: str,
                                    enable_cross_validation: bool,
                                    random_seed: int) -> None:
    """
    Parameters
    ----------
    new_regions_shapes: list(string)
    data_app_val_dir: string
    data_field: string
    region_field: string
    ratio: float
    seeds: intersect
    epsg: string
    enable_cross_validation: bool
    random_seed: int
    Return
    ------

    """
    from iota2.Sampling.VectorFormatting import split_by_sets
    from iota2.Sampling import SplitInSubSets as subset
    from iota2.Common import FileUtils as fut
    for new_region_shape in new_regions_shapes:
        tile_name = os.path.splitext(os.path.basename(new_region_shape))[0]
        vectors_to_rm = fut.FileSearch_AND(data_app_val_dir, True, tile_name)
        for vect in vectors_to_rm:
            os.remove(vect)
        # remove seeds fields
        subset.splitInSubSets(new_region_shape,
                              data_field,
                              region_field,
                              ratio,
                              seeds,
                              "ESRI Shapefile",
                              crossValidation=enable_cross_validation,
                              random_seed=random_seed)

        split_by_sets(new_region_shape,
                      seeds,
                      data_app_val_dir,
                      epsg,
                      epsg,
                      tile_name,
                      cross_valid=enable_cross_validation)


# def splitSamples(cfg, workingDirectory=None, logger=logger):
def split_samples(output_path: str,
                  data_field: str,
                  enable_cross_validation: bool,
                  region_threshold: Union[str, float],
                  region_field: str,
                  ratio: float,
                  random_seed: int,
                  runs: int,
                  epsg: Union[str, int],
                  workingDirectory: Optional[str] = None,
                  logger: Optional[Logger] = LOGGER):
    """
    """
    from iota2.Common import FileUtils as fut
    # const
    regions_pos = -2
    if isinstance(epsg, str):
        epsg = int(epsg.split(":")[-1])
    if isinstance(region_threshold, str):
        region_threshold = float(region_threshold)
    formatting_vectors_dir = os.path.join(output_path, "formattingVectors")
    shape_region_dir = os.path.join(output_path, "shapeRegion")
    vectors = fut.FileSearch_AND(formatting_vectors_dir, True, ".shp")

    # get All possible regions by parsing shapeFile's name
    shapes_region = fut.FileSearch_AND(shape_region_dir, True, ".shp")
    regions = list(
        {
            os.path.split(shape)[-1].split("_")[regions_pos]
            for shape in shapes_region
        }
    )


    # compute region's area
    areas, regions_tiles, data_to_rm = get_regions_area(
        vectors, regions, formatting_vectors_dir, workingDirectory,
        region_field)

    # get how many sub-regions must be created by too huge regions.
    regions_split = get_splits_regions(areas, region_threshold)

    for region_name, area in list(areas.items()):
        logger.info(f"region : {region_name} , area : {area}")

    updated_vectors = split(regions_split, regions_tiles, data_field,
                            region_field)

    # transform sqlites to shape file, according to input data format
    new_regions_shapes = transform_to_shape(updated_vectors,
                                            formatting_vectors_dir)
    for data in data_to_rm:
        os.remove(data)

    data_app_val_dir = os.path.join(output_path, "dataAppVal")
    update_learning_validation_sets(new_regions_shapes, data_app_val_dir,
                                    data_field, region_field, ratio, runs,
                                    epsg, enable_cross_validation, random_seed)
