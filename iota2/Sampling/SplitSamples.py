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

import argparse
import os
import logging
from typing import List, Optional

from Common import ServiceConfigFile as SCF
from Common import FileUtils as fut
from Common.Utils import run
from Sampling import SplitInSubSets as subset

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


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
    from Common.FileUtils import FileSearch_AND

    TILE_POSITION = 0
    MODEL_POSITION = 2
    SEED_POSITION = 3

    learning_files = FileSearch_AND(learning_directory, False,
                                    "_Samples_learn.sqlite")
    files_indexed = [
        (c_file.split("_")[MODEL_POSITION], c_file.split("_")[TILE_POSITION],
         int(c_file.split("_")[SEED_POSITION].replace("seed", "")),
         os.path.join(learning_directory, "{}.sqlite".format(c_file)))
        for c_file in learning_files
    ]
    files_indexed_sorted = sorted(files_indexed,
                                  key=operator.itemgetter(0, 1, 2))
    return [learning_file for _, _, _, learning_file in files_indexed_sorted]


def split_superpixels_and_reference(
        vector_file: str,
        superpix_column: Optional[str] = "superpix",
        DRIVER: Optional[str] = "SQLite",
        working_dir: Optional[str] = None,
        logger: Optional[logging.Logger] = logger) -> None:
    """
    reference feature contains the value 0 in column 'superpix'
    """
    #~ import sqlite3
    import ogr
    import shutil

    from Common.Utils import run

    driver = ogr.GetDriverByName(DRIVER)
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
        "Extract superpixel samples from file {} and save it in {}".format(
            superpix_db, superpix_db))
    sql = "select * from {} where {}!={}".format(table_name, superpix_column,
                                                 0)
    cmd = 'ogr2ogr -t_srs EPSG:{} -s_srs EPSG:{} -nln {} -f "{}" -sql "{}" {} {}'.format(
        epsg_code, epsg_code, table_name, DRIVER, sql, superpix_db,
        vector_file)
    run(cmd)

    logger.info(
        "Extract reference samples from file {} and save it in {}".format(
            vector_file, vector_file))
    sql = "select * from {} where {}={}".format(table_name, superpix_column, 0)
    cmd = 'ogr2ogr -t_srs EPSG:{} -s_srs EPSG:{} -nln {} -f "{}" -sql "{}" {} {}'.format(
        epsg_code, epsg_code, table_name, DRIVER, sql, ref_db, vector_file)
    run(cmd)
    shutil.move(ref_db, vector_file)
    if working_dir:
        shutil.copy(superpix_db, vectors_dir)
        os.remove(superpix_db)

    # TODO : replace og2ogr by geopandas ?
    #~ conn = sqlite3.connect(vector_file)
    #~ df = geopd.GeoDataFrame.from_postgis(sql, conn, geom_col="geometry")
    #~ conn_out = sqlite3.connect(vector_file.replace(".sqlite", "_V3.sqlite"))
    #~ df.to_sql(table_name, conn_out)
    return vector_file, os.path.join(vectors_dir,
                                     os.path.split(superpix_db)[-1])


def get_regions_area(vectors, regions, formatting_vectors_dir,
                     workingDirectory, region_field):
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
    import sqlite3 as db
    tmp_data = []
    #init dict
    dico_region_area = {}
    dico_region_tile = {}
    for reg in regions:
        dico_region_area[reg] = 0.0
        dico_region_tile[reg] = []

    for vector in vectors:
        #move vectors to sqlite (faster format)
        transform_dir = formatting_vectors_dir
        if workingDirectory:
            transform_dir = workingDirectory
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
            sql_clause = "SELECT AREA(GEOMFROMWKB(GEOMETRY)) FROM {} WHERE {}={}".format(
                table_name, region_field, current_region)
            cursor.execute(sql_clause)
            res = cursor.fetchall()

            dico_region_area[current_region] += sum([area[0] for area in res])

            if vector not in dico_region_tile[current_region]:
                dico_region_tile[current_region].append(sqlite_vector)

        conn = cursor = None

    return dico_region_area, dico_region_tile, tmp_data


def get_splits_regions(areas, region_threshold):
    """
    return regions which must be split
    """
    import math
    dic = {}  #{'region':Nsplits,..}
    for region, area in list(areas.items()):
        fold = int(math.ceil(area / (region_threshold * 1e6)))
        if fold > 1:
            dic[region] = fold
    return dic


def get_FID_values(vector_path, dataField, regionField, region, value):
    """
    """
    import sqlite3 as db
    conn = db.connect(vector_path)
    cursor = conn.cursor()
    table_name = (os.path.splitext(os.path.basename(vector_path))[0]).lower()

    sql_clause = "SELECT ogc_fid FROM {} WHERE {}={} AND {}='{}'".format(
        table_name, dataField, value, regionField, region)
    cursor.execute(sql_clause)
    FIDs = cursor.fetchall()
    conn = cursor = None
    return [fid[0] for fid in FIDs]


def update_vector(vector_path, regionField, new_regions_dict, logger=logger):
    """
    """
    #const
    sqlite3_query_limit = 1000.0

    import math
    import sqlite3 as db
    conn = db.connect(vector_path)
    cursor = conn.cursor()
    table_name = (os.path.splitext(os.path.basename(vector_path))[0]).lower()

    for new_region_name, FIDs in list(new_regions_dict.items()):
        nb_sub_split_SQLITE = int(math.ceil(len(FIDs) / sqlite3_query_limit))
        sub_FID_sqlite = fut.splitList(FIDs, nb_sub_split_SQLITE)

        subFid_clause = []
        for subFID in sub_FID_sqlite:
            subFid_clause.append("(ogc_fid in ({}))".format(", ".join(
                map(str, subFID))))
        fid_clause = " OR ".join(subFid_clause)
        sql_clause = "UPDATE {} SET {}='{}' WHERE {}".format(
            table_name, regionField, new_region_name, fid_clause)
        logger.debug("update fields")
        logger.debug(sql_clause)

        cursor.execute(sql_clause)
        conn.commit()

    conn = cursor = None


def split(regions_split, regions_tiles, dataField, regionField):
    """
    function dedicated to split to huge regions in sub-regions
    """
    import sqlite3 as db
    updated_vectors = []

    for region, fold in list(regions_split.items()):
        vector_paths = regions_tiles[region]
        for vec in vector_paths:
            #init dict new regions
            new_regions_dict = {}
            for f in range(fold):
                #new region's name are define here
                new_regions_dict["{}f{}".format(region, f + 1)] = []

            #get possible class
            class_vector = fut.getFieldElement(vec,
                                               driverName="SQLite",
                                               field=dataField,
                                               mode="unique",
                                               elemType="str")
            dic_class = {}
            #get FID values for all class of current region into the current tile
            for c_class in class_vector:
                dic_class[c_class] = get_FID_values(vec, dataField,
                                                    regionField, region,
                                                    c_class)

            nb_feat = 0
            for class_name, FID_cl in list(dic_class.items()):
                if FID_cl:
                    FID_folds = fut.splitList(FID_cl, fold)
                    #fill new_regions_dict
                    for i, fid_fold in enumerate(FID_folds):
                        new_regions_dict["{}f{}".format(region,
                                                        i + 1)] += fid_fold
                nb_feat += len(FID_cl)
            update_vector(vec, regionField, new_regions_dict)
            if vec not in updated_vectors:
                updated_vectors.append(vec)

    return updated_vectors


def transform_to_shape(sqlite_vectors, formatting_vectors_dir):
    """
    """
    out = []
    for sqlite_vector in sqlite_vectors:
        out_name = os.path.splitext(os.path.basename(sqlite_vector))[0]
        out_path = os.path.join(formatting_vectors_dir,
                                "{}.shp".format(out_name))
        if os.path.exists(out_path):
            fut.removeShape(out_path.replace(".shp", ""),
                            [".prj", ".shp", ".dbf", ".shx"])
        cmd = "ogr2ogr -f 'ESRI Shapefile' {} {}".format(
            out_path, sqlite_vector)
        run(cmd)
        out.append(out_path)
    return out


def update_learningValination_sets(new_regions_shapes, dataAppVal_dir,
                                   dataField, regionField, ratio, seeds, epsg,
                                   enableCrossValidation, random_seed):
    """
    """
    from Sampling.VectorFormatting import split_by_sets

    for new_region_shape in new_regions_shapes:
        tile_name = os.path.splitext(os.path.basename(new_region_shape))[0]
        vectors_to_rm = fut.FileSearch_AND(dataAppVal_dir, True, tile_name)
        for vect in vectors_to_rm:
            os.remove(vect)
        #remove seeds fields
        subset.splitInSubSets(new_region_shape,
                              dataField,
                              regionField,
                              ratio,
                              seeds,
                              "ESRI Shapefile",
                              crossValidation=enableCrossValidation,
                              random_seed=random_seed)

        output_splits = split_by_sets(new_region_shape,
                                      seeds,
                                      dataAppVal_dir,
                                      epsg,
                                      epsg,
                                      tile_name,
                                      crossValid=enableCrossValidation)


def splitSamples(cfg, workingDirectory=None, logger=logger):
    """
    """
    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)

    #const
    iota2_dir = cfg.getParam('chain', 'outputPath')
    dataField = cfg.getParam('chain', 'dataField')
    enableCrossValidation = cfg.getParam('chain', 'enableCrossValidation')
    region_threshold = float(cfg.getParam('chain', 'mode_outside_RegionSplit'))
    region_field = (cfg.getParam('chain', 'regionField')).lower()
    regions_pos = -2

    formatting_vectors_dir = os.path.join(iota2_dir, "formattingVectors")
    shape_region_dir = os.path.join(iota2_dir, "shapeRegion")
    ratio = float(cfg.getParam('chain', 'ratio'))
    random_seed = cfg.getParam('chain', 'random_seed')
    seeds = int(cfg.getParam('chain', 'runs'))
    epsg = int((cfg.getParam('GlobChain', 'proj')).split(":")[-1])
    vectors = fut.FileSearch_AND(formatting_vectors_dir, True, ".shp")

    #get All possible regions by parsing shapeFile's name
    shapes_region = fut.FileSearch_AND(shape_region_dir, True, ".shp")
    regions = list(
        set([
            os.path.split(shape)[-1].split("_")[regions_pos]
            for shape in shapes_region
        ]))

    #compute region's area
    areas, regions_tiles, data_to_rm = get_regions_area(
        vectors, regions, formatting_vectors_dir, workingDirectory,
        region_field)

    #get how many sub-regions must be created by too huge regions.
    regions_split = get_splits_regions(areas, region_threshold)

    for region_name, area in list(areas.items()):
        logger.info("region : {} , area : {}".format(region_name, area))

    updated_vectors = split(regions_split, regions_tiles, dataField,
                            region_field)

    #transform sqlites to shape file, according to input data format
    new_regions_shapes = transform_to_shape(updated_vectors,
                                            formatting_vectors_dir)
    for data in data_to_rm:
        os.remove(data)

    dataAppVal_dir = os.path.join(iota2_dir, "dataAppVal")
    update_learningValination_sets(new_regions_shapes, dataAppVal_dir,
                                   dataField, region_field, ratio, seeds, epsg,
                                   enableCrossValidation, random_seed)
