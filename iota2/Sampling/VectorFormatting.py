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
The vector formatting module
"""
import argparse
import logging
import os
import shutil
from typing import List, Optional

LOGGER = logging.getLogger(__name__)


def split_vector_by_region(in_vect: str,
                           output_dir: str,
                           region_field: str,
                           runs: Optional[int] = 1,
                           driver: Optional[str] = "ESRI shapefile",
                           proj_in: Optional[str] = "EPSG:2154",
                           proj_out: Optional[str] = "EPSG:2154",
                           mode: Optional[str] = "usually") -> List[str]:
    """
    create new files by regions in input vector.

    Parameters
    ----------
    in_vect : string
        input vector path
    output_dir : string
        path to output directory
    region_field : string
        field in in_vect describing regions
    driver : string
        ogr driver
    proj_in : string
        input projection
    proj_out : string
        output projection
    mode : string
        define if we split SAR sensor to the other
    Return
    ------
    list
        paths to new output vectors
    """
    from iota2.Common import FileUtils as fut
    from iota2.Common.Utils import run
    output_paths = []

    # const
    tile_pos = 0
    learn_flag = "learn"
    table_name = "output"

    vec_name = os.path.split(in_vect)[-1]
    tile = vec_name.split("_")[tile_pos]
    extent = os.path.splitext(vec_name)[-1]

    regions = fut.getFieldElement(in_vect,
                                  driverName=driver,
                                  field=region_field,
                                  mode="unique",
                                  elemType="str")

    table = vec_name.split(".")[0]
    if driver != "ESRI shapefile":
        table = "output"
    # split vector
    for seed in range(runs):
        fields_to_keep = ",".join([
            elem for elem in fut.get_all_fields_in_shape(in_vect, "SQLite")
            if "seed_" not in elem
        ])
        for region in regions:
            out_vec_name_learn = "_".join([
                tile, "region", region, "seed" + str(seed), "Samples_learn_tmp"
            ])
            if mode != "usually":
                out_vec_name_learn = "_".join([
                    tile, "region", region, "seed" + str(seed), "Samples",
                    "SAR", "learn_tmp"
                ])
            output_vec_learn = os.path.join(output_dir,
                                            out_vec_name_learn + extent)
            seed_clause_learn = f"seed_{seed}='{learn_flag}'"
            region_clause = f"{region_field}='{region}'"
            # split vectors by runs and learning sets
            sql_cmd_learn = (f"select * FROM {table} WHERE {seed_clause_learn}"
                             f" AND {region_clause}")
            cmd = (f'ogr2ogr -t_srs {proj_out} -s_srs {proj_in} -nln {table}'
                   f' -f "{driver}" -sql "{sql_cmd_learn}" {output_vec_learn} '
                   f'{in_vect}')
            run(cmd)

            # drop useless column
            sql_clause = f"select GEOMETRY,{fields_to_keep} from {table_name}"
            output_vec_learn_out = output_vec_learn.replace("_tmp", "")

            cmd = (
                f"ogr2ogr -s_srs {proj_in} -t_srs {proj_out} -dialect "
                f"'SQLite' -f 'SQLite' -nln {table_name} -sql '{sql_clause}' "
                f"{output_vec_learn_out} {output_vec_learn}")
            run(cmd)
            output_paths.append(output_vec_learn_out)
            os.remove(output_vec_learn)

    return output_paths


def create_tile_region_masks(tile_region: str, region_field: str,
                             tile_name: str, output_directory: str,
                             origin_name: str, img_ref: str) -> None:
    """
    Parameters
    ----------
    tile_region : string
        path to a SQLite file containing polygons. Each feature is a region
    region_field : string
        region's field
    tile_name : string
        current tile name
    output_directory : string
        directory to save masks
    origin_name : string
        region's field vector file name
    img_ref : string
        path to a tile reference image
    """
    from iota2.Common import FileUtils as fut
    from iota2.Common import OtbAppBank as otb
    from iota2.Common.Utils import run
    all_regions_tmp = fut.getFieldElement(tile_region,
                                          driverName="SQLite",
                                          field=region_field.lower(),
                                          mode="unique",
                                          elemType="str")
    # transform sub region'name into complete region
    # (region '1f1' become region '1')
    all_regions = []
    for region in all_regions_tmp:
        reg = region.split("f")[0]
        all_regions.append(reg)
    region = None
    for region in all_regions:
        output_name = f"{origin_name}_region_{region}_{tile_name}.shp"
        output_path = os.path.join(output_directory, output_name)
        db_name = (os.path.splitext(os.path.basename(tile_region))[0]).lower()
        cmd = (
            f"ogr2ogr -f 'ESRI Shapefile' -sql \"SELECT * FROM {db_name}"
            f" WHERE {region_field}='{region}'\" {output_path} {tile_region}")
        run(cmd)

        path, _ = os.path.splitext(output_path)
        tile_region_raster = "{}.tif".format(path)
        tile_region_app = otb.CreateRasterizationApplication({
            "in":
            output_path,
            "out":
            tile_region_raster,
            "im":
            img_ref,
            "mode":
            "binary",
            "pixType":
            "uint8",
            "background":
            "0",
            "mode.binary.foreground":
            "1"
        })
        tile_region_app.ExecuteAndWriteOutput()


def keep_fields(vec_in: str,
                vec_out: str,
                fields: Optional[List[str]] = [],
                proj_in: Optional[int] = 2154,
                proj_out: Optional[int] = 2154) -> None:
    """
    use to extract fields of an input SQLite file

    Parameters
    ----------
    vec_in : string
        input SQLite vector File
    vec_out : string
        output SQLite vector File
    fields : list
        list of fields to keep
    proj_in : int
        input projection
    proj_out : int
        output projection
    """
    from iota2.VectorTools.vector_functions import get_geom_column_name
    from iota2.Common.Utils import run
    table_in = (os.path.splitext(os.path.split(vec_in)[-1])[0]).lower()
    table_out = (os.path.splitext(os.path.split(vec_out)[-1])[0]).lower()

    _, ext = os.path.splitext(vec_in)
    driver_vec_in = "ESRI Shapefile"
    if "sqlite" in ext:
        driver_vec_in = "SQLite"
    geom_column_name = get_geom_column_name(vec_in, driver=driver_vec_in)
    sql_clause = (f"select {geom_column_name},"
                  f"{','.join(fields)} from {table_in}")
    cmd = (f"ogr2ogr -s_srs EPSG:{proj_in} -t_srs EPSG:{proj_out} -dialect "
           f"'SQLite' -f 'SQLite' -nln {table_out} -sql '{sql_clause}' "
           f"{vec_out} {vec_in}")
    run(cmd)


def split_by_sets(vector: str,
                  seeds: int,
                  split_directory: str,
                  proj_in: int,
                  proj_out: int,
                  tile_name: str,
                  cross_valid: Optional[bool] = False,
                  split_ground_truth: Optional[bool] = True) -> List[str]:
    """
    use to create new vector file by learning / validation sets

    Parameters
    ----------
    vector : string
        path to a shape file containg ground truth
    seeds : int
        number of run
    split_directory : string
        output directory
    proj_in : int
        input projection
    proj_out : int
        output projection
    tile_name : string
        tile's name
    crossValid : bool
        flag to enable cross validation
    splitGroundTruth : bool
        flat to split ground truth
    """
    from iota2.Common import FileUtils as fut
    from iota2.Common.Utils import run
    out_vectors = []

    valid_flag = "validation"
    learn_flag = "learn"
    tile_origin_field_name = "tile_o"

    vector_layer_name = (os.path.splitext(
        os.path.split(vector)[-1])[0]).lower()

    # predict fields to keep
    fields_to_rm = ["seed_" + str(seed) for seed in range(seeds)]
    fields_to_rm.append(tile_origin_field_name)
    all_fields = fut.get_all_fields_in_shape(vector)
    fields = [
        field_name for field_name in all_fields
        if field_name not in fields_to_rm
    ]

    # start split
    for seed in range(seeds):
        valid_clause = f"seed_{seed}='{valid_flag}'"
        learn_clause = f"seed_{seed}='{learn_flag}'"

        sql_cmd_valid = (f"select * FROM {vector_layer_name}"
                         f" WHERE {valid_clause}")
        output_vec_valid_name = "_".join(
            [tile_name, "seed_" + str(seed), "val"])
        output_vec_valid_name_tmp = "_".join(
            [tile_name, "seed_" + str(seed), "val", "tmp"])
        output_vec_valid_tmp = os.path.join(
            split_directory, output_vec_valid_name_tmp + ".sqlite")
        output_vec_valid = os.path.join(split_directory,
                                        output_vec_valid_name + ".sqlite")
        cmd_valid = (f'ogr2ogr -t_srs EPSG:{proj_out} -s_srs EPSG:{proj_in} '
                     f'-nln {output_vec_valid_name_tmp} -f "SQLite" -sql '
                     f'"{sql_cmd_valid}" {output_vec_valid_tmp} {vector}')

        sql_cmd_learn = "select * FROM {} WHERE {}".format(
            vector_layer_name, learn_clause)
        output_vec_learn_name = "_".join(
            [tile_name, "seed_" + str(seed), "learn"])
        output_vec_learn_name_tmp = "_".join(
            [tile_name, "seed_" + str(seed), "learn", "tmp"])
        output_vec_learn_tmp = os.path.join(
            split_directory, output_vec_learn_name_tmp + ".sqlite")
        output_vec_learn = os.path.join(split_directory,
                                        output_vec_learn_name + ".sqlite")
        cmd_learn = (
            f'ogr2ogr -t_srs EPSG:{proj_out} -s_srs EPSG:{proj_in} '
            f'-nln {output_vec_learn_name_tmp} -f "SQLite" -sql "{sql_cmd_learn}"'
            f' {output_vec_learn_tmp} {vector}')
        if cross_valid is False:
            if split_ground_truth:
                run(cmd_valid)
                # remove useless fields
                keep_fields(output_vec_valid_tmp,
                            output_vec_valid,
                            fields=fields,
                            proj_in=proj_in,
                            proj_out=proj_out)
                os.remove(output_vec_valid_tmp)
            run(cmd_learn)
            # remove useless fields
            keep_fields(output_vec_learn_tmp,
                        output_vec_learn,
                        fields=fields,
                        proj_in=proj_in,
                        proj_out=proj_out)
            os.remove(output_vec_learn_tmp)

            if split_ground_truth is False:
                shutil.copy(output_vec_learn, output_vec_valid)

            out_vectors.append(output_vec_valid)
            out_vectors.append(output_vec_learn)

        else:
            if seed < seeds - 1:
                run(cmd_learn)
                keep_fields(output_vec_learn_tmp,
                            output_vec_learn,
                            fields=fields,
                            proj_in=proj_in,
                            proj_out=proj_out)
                out_vectors.append(output_vec_learn)
                os.remove(output_vec_learn_tmp)
            elif seed == seeds - 1:
                run(cmd_valid)
                keep_fields(output_vec_valid_tmp,
                            output_vec_valid,
                            fields=fields,
                            proj_in=proj_in,
                            proj_out=proj_out)
                out_vectors.append(output_vec_valid)
                os.remove(output_vec_valid_tmp)
    return out_vectors


def built_where_sql_exp(sample_id_to_extract: List[int], clause: str):
    """
    PARAMETERS
    ----------
    sample_id_to_extract: List[int]
    clause: string
    RETURN
    ------
    string: a sql expression
    """
    from iota2.Common import FileUtils as fut
    import math
    if clause not in ["in", "not in"]:
        raise Exception("clause must be 'in' or 'not in'")
    sql_limit = 1000.0
    sample_id_to_extract = list(map(str, sample_id_to_extract))
    sample_id_to_extract = fut.splitList(
        sample_id_to_extract,
        nbSplit=int(math.ceil(float(len(sample_id_to_extract)) / sql_limit)))
    list_fid = [
        f"fid {clause} ({','.join(chunk)})" for chunk in sample_id_to_extract
    ]
    sql_exp = " OR ".join(list_fid)
    return sql_exp


def extract_maj_vote_samples(vec_in: str,
                             vec_out: str,
                             ratio_to_keep: float,
                             data_field: str,
                             region_field: str,
                             driver_name: Optional[str] = "ESRI Shapefile"):
    """
    dedicated to extract samples by class according to a ratio.
    Samples are remove from vec_in and place in vec_out

    Parameters
    ----------
    vec_in : string
        path to a shapeFile (.shp)
    vec_out : string
        path to a sqlite (.sqlite)
    ratio_to_keep [float]
        percentage of samples to extract ratio_to_keep = 0.1
        mean extract 10% of each class in each regions
    dataField : string
        field containing class labels
    regionField : string
        field containing regions labels
    driver_name : string
        OGR driver
    """
    from osgeo import ogr
    from iota2.Common import FileUtils as fut
    from iota2.Sampling import SplitInSubSets as subset
    from iota2.Common.Utils import run
    class_avail = fut.getFieldElement(vec_in,
                                      driverName=driver_name,
                                      field=data_field,
                                      mode="unique",
                                      elemType="int")
    region_avail = fut.getFieldElement(vec_in,
                                       driverName=driver_name,
                                       field=region_field,
                                       mode="unique",
                                       elemType="str")

    driver = ogr.GetDriverByName(driver_name)
    source = driver.Open(vec_in, 1)
    layer = source.GetLayer(0)

    sample_id_to_extract, _ = subset.get_random_poly(layer, data_field,
                                                     class_avail,
                                                     ratio_to_keep,
                                                     region_field,
                                                     region_avail)

    # Create new file with targeted FID
    fid_samples_in = built_where_sql_exp(sample_id_to_extract, clause="in")
    cmd = f"ogr2ogr -where '{fid_samples_in}' -f 'SQLite' {vec_out} {vec_in}"
    run(cmd)

    # remove in vec_in targeted FID
    vec_in_rm = vec_in.replace(".shp", "_tmp.shp")
    fid_samples_not_in = built_where_sql_exp(sample_id_to_extract,
                                             clause="not in")
    cmd = f"ogr2ogr -where '{fid_samples_not_in}' {vec_in_rm} {vec_in}"
    run(cmd)

    fut.removeShape(vec_in.replace(".shp", ""),
                    [".prj", ".shp", ".dbf", ".shx"])

    cmd = f"ogr2ogr {vec_in} {vec_in_rm}"
    run(cmd)

    fut.removeShape(vec_in_rm.replace(".shp", ""),
                    [".prj", ".shp", ".dbf", ".shx"])


def vector_formatting(
        tile_name: str,
        output_path: str,
        ground_truth_vec: str,
        data_field: str,
        cloud_threshold: float,
        ratio: float,
        random_seed: int,
        enable_cross_validation: bool,
        enable_split_ground_truth: bool,
        fusion_merge_all_validation: bool,
        runs: int,
        epsg: int,
        region_field: str,
        merge_final_classifications: Optional[bool] = False,
        merge_final_classifications_ratio: Optional[float] = None,
        region_vec: Optional[str] = None,
        working_directory=None,
        logger=LOGGER) -> None:
    """
    dedicated to extract samples by class according to a ratio
    or a fold number.

    Parameters
    ----------
    tile_name: str
        tile name
    output_path: str
        iota2 output path
    ground_truth_vec: str
        path to the ground truth database
    data_field: str
        field into the database contining class labels
    cloud_threshold: float
        cloud threshold to pick up polygons in database
    ratio: float
        ratio between learning and validation samples-set
    random_seed: int
        initialize the random seed
    enable_cross_validation: bool
        is iota2 cross validation enable ? TODO : remove
        this parameter
    enable_split_ground_truth: bool,
        flag to split input database in learning and validation
        samples-set
    fusion_merge_all_validation: bool
        flag to merge all classifications
    runs: int
        number of random learning/validation samples-set
    epsg: int
        epsg code
    region_field: str
        region field in region database
    merge_final_classifications: bool
        inform if finals classifications will be merged
    merge_final_classifications_ratio : float
        ratio of samples to extract by tile and by region
        in order to compute confusion matrix on classification fusion
    region_vec: str
        region database
    working_directory : str
        path to a working directory
    logger: logging
        root logger
    """
    from iota2.Common import FileUtils as fut
    from iota2.VectorTools import spatialOperations as intersect
    from iota2.VectorTools import ChangeNameField
    from iota2.Sampling import SplitInSubSets as subset
    from iota2.VectorTools.AddField import addField
    # const
    tile_field = "tile_o"
    formatting_directory = os.path.join(output_path, "formattingVectors")
    if working_directory:
        formatting_directory = working_directory
    output_name = tile_name + ".shp"

    output = os.path.join(formatting_directory, output_name)
    features_directory = os.path.join(output_path, "features")
    cloud_vec = os.path.join(features_directory, tile_name,
                             f"CloudThreshold_{cloud_threshold}.shp")
    tile_env_vec = os.path.join(output_path, "envelope", f"{tile_name}.shp")

    region_field = region_field.lower()
    split_directory = os.path.join(output_path, "dataAppVal")
    final_directory = os.path.join(output_path, "final")

    if not region_vec:
        region_vec = os.path.join(output_path, "MyRegion.shp")
    if merge_final_classifications:
        wd_maj_vote = os.path.join(final_directory,
                                   "merge_final_classifications")
        if working_directory:
            wd_maj_vote = working_directory

    output_driver = "SQlite"
    if os.path.splitext(os.path.basename(output))[-1] == ".shp":
        output_driver = "ESRI Shapefile"

    work_dir = os.path.join(output_path, "formattingVectors")
    if working_directory:
        work_dir = working_directory

    work_dir = os.path.join(work_dir, tile_name)
    try:
        os.mkdir(work_dir)
    except OSError:
        logger.warning(f"{work_dir} allready exists")

    # log
    logger.info(f"formatting vector for tile : {tile_name}")
    logger.debug(f"output : {output}")
    logger.debug(f"groundTruth : {ground_truth_vec}")
    logger.debug(f"cloud : {cloud_vec}")
    logger.debug(f"region : {region_vec}")
    logger.debug(f"tile envelope : {tile_env_vec}")
    logger.debug(f"data field : {data_field}")
    logger.debug(f"region field : {region_field}")
    logger.debug(f"ratio : {ratio}")
    logger.debug(f"seeds : {runs}")
    logger.debug(f"epsg : {epsg}")
    logger.debug(f"workingDirectory : {work_dir}")

    img_ref = fut.FileSearch_AND(os.path.join(features_directory, tile_name),
                                 True, ".tif")[0]

    logger.info("launch intersection between tile's envelope and regions")
    tile_region = os.path.join(work_dir, "tileRegion_" + tile_name + ".sqlite")
    region_tile_intersection = intersect.intersectSqlites(tile_env_vec,
                                                          region_vec,
                                                          work_dir,
                                                          tile_region,
                                                          epsg,
                                                          "intersection",
                                                          [region_field],
                                                          vectformat='SQLite')
    if not region_tile_intersection:
        error_msg = (
            f"there is no intersections between the tile '{tile_name}' "
            f"and the region shape '{region_vec}'")
        logger.critical(error_msg)
        raise Exception(error_msg)

    region_vector_name = os.path.splitext(os.path.basename(region_vec))[0]
    create_tile_region_masks(tile_region, region_field, tile_name,
                             os.path.join(output_path, "shapeRegion"),
                             region_vector_name, img_ref)

    logger.info(
        "launch intersection between tile's envelopeRegion and groundTruth")
    tile_region_ground_truth = os.path.join(
        work_dir, "tileRegionGroundTruth_" + tile_name + ".sqlite")

    if intersect.intersectSqlites(tile_region,
                                  ground_truth_vec,
                                  work_dir,
                                  tile_region_ground_truth,
                                  epsg,
                                  "intersection",
                                  [data_field, region_field, "ogc_fid"],
                                  vectformat='SQLite') is False:
        warning_msg = (
            f"there si no intersections between the tile "
            f"'{tile_name}' and the ground truth '{ground_truth_vec}'")
        logger.warning(warning_msg)
        return None

    logger.info("remove un-usable samples")

    intersect.intersectSqlites(tile_region_ground_truth,
                               cloud_vec,
                               work_dir,
                               output,
                               epsg,
                               "intersection",
                               [data_field, region_field, "t2_ogc_fid"],
                               vectformat='SQLite')

    os.remove(tile_region)
    os.remove(tile_region_ground_truth)

    # rename field t2_ogc_fid to originfig which correspond
    # to the polygon number
    ChangeNameField.changeName(output, "t2_ogc_fid", "originfid")

    if merge_final_classifications and fusion_merge_all_validation is False:
        maj_vote_sample_tile_name = "{}_majvote.sqlite".format(tile_name)
        maj_vote_sample_tile = os.path.join(wd_maj_vote,
                                            maj_vote_sample_tile_name)
        if enable_cross_validation is False:
            extract_maj_vote_samples(output,
                                     maj_vote_sample_tile,
                                     merge_final_classifications_ratio,
                                     data_field,
                                     region_field,
                                     driver_name="ESRI Shapefile")

    logger.info(f"split {output} in {runs} subsets with the ratio {ratio}")
    subset.splitInSubSets(output,
                          data_field,
                          region_field,
                          ratio,
                          runs,
                          output_driver,
                          crossValidation=enable_cross_validation,
                          splitGroundTruth=enable_split_ground_truth,
                          random_seed=random_seed)

    addField(output,
             tile_field,
             tile_name,
             valueType=str,
             driver_name=output_driver)

    split_dir = split_directory
    if working_directory:
        split_dir = work_dir

    # splits by learning and validation sets (use in validations steps)
    output_splits = split_by_sets(output,
                                  runs,
                                  split_dir,
                                  epsg,
                                  epsg,
                                  tile_name,
                                  cross_valid=enable_cross_validation,
                                  split_ground_truth=enable_split_ground_truth)
    if working_directory:
        if output_driver == "SQLite":
            shutil.copy(output, os.path.join(output_path, "formattingVectors"))
            os.remove(output)

        elif output_driver == "ESRI Shapefile":
            fut.cpShapeFile(output.replace(".shp", ""),
                            os.path.join(output_path, "formattingVectors"),
                            [".prj", ".shp", ".dbf", ".shx"], True)
            fut.removeShape(output.replace(".shp", ""),
                            [".prj", ".shp", ".dbf", ".shx"])

        for current_split in output_splits:
            shutil.copy(current_split, os.path.join(output_path, "dataAppVal"))
            os.remove(current_split)

        if (merge_final_classifications and enable_cross_validation is False
                and fusion_merge_all_validation is False):
            shutil.copy(
                maj_vote_sample_tile,
                os.path.join(final_directory, "merge_final_classifications"))


if __name__ == "__main__":
    from iota2.Common.FileUtils import str2bool
    FUNC_DESCRIPTION = (
        "This function is dedicated to intersects some vector files "
        "and then, prepare them to sampling")

    PARSER = argparse.ArgumentParser(description=FUNC_DESCRIPTION)

    vector_formatting(ARGS.tile_name, ARGS.output_path, ARGS.ground_truth_vec,
                      ARGS.data_field, ARGS.cloud_threshold, ARGS.ratio,
                      ARGS.random_seed, ARGS.enable_cross_validation,
                      ARGS.enable_split_ground_truth,
                      ARGS.fusion_merge_all_validation, ARGS.runs, ARGS.epsg,
                      ARGS.region_field, ARGS.merge_final_classifications,
                      ARGS.merge_final_classifications_ratio, ARGS.region_vec,
                      ARGS.working_directory)

    PARSER.add_argument("-tile_name",
                        dest="tile_name",
                        help="tile's name",
                        required=True)
    PARSER.add_argument("-output_path",
                        dest="output_path",
                        help="path to iota2 output path",
                        required=True)
    PARSER.add_argument("-ground_truth",
                        dest="ground_truth_vec",
                        help="input database",
                        required=True)
    PARSER.add_argument("-data_field",
                        dest="data_field",
                        help="field containing labels in database",
                        required=True)
    PARSER.add_argument("-cloud_threshold",
                        dest="cloud_threshold",
                        help="cloud threshold to pick-up polygons",
                        type=int,
                        default=1,
                        required=False)
    PARSER.add_argument("-ratio",
                        dest="ratio",
                        help="ratio between learning and validation polygons",
                        required=False)
    PARSER.add_argument("-random_seed",
                        dest="random_seed",
                        type=int,
                        default=1,
                        help="initialize random seed",
                        required=False)
    PARSER.add_argument("-enable_cross_validation",
                        dest="enable_cross_validation",
                        help="is iota2 cross validation enable",
                        type=str2bool,
                        default=False,
                        required=False)
    PARSER.add_argument(
        "-enable_split_ground_truth",
        dest="enable_split_ground_truth",
        help=
        "flag to split input database in learning and validation samples-set",
        type=str2bool,
        required=False)
    PARSER.add_argument("-fusion_merge_all_validation",
                        dest="fusion_merge_all_validation",
                        help="flag to merge all classification",
                        default=False,
                        type=str2bool,
                        required=False)
    PARSER.add_argument(
        "-runs",
        dest="runs",
        help="number of random learning/validation samples-set ]0;1[",
        type=float,
        required=True)
    PARSER.add_argument("-epsg",
                        dest="epsg",
                        help="epsg code",
                        type=int,
                        required=True)
    PARSER.add_argument("-region_field",
                        dest="region_field",
                        help="region field in region database",
                        required=True)
    PARSER.add_argument("-merge_final_classifications",
                        dest="merge_final_classifications",
                        help="inform if finals classifications will be merged",
                        type=str2bool,
                        default=False,
                        required=False)
    PARSER.add_argument("-merge_final_classifications_ratio",
                        dest="merge_final_classifications_ratio",
                        help=("ratio of samples to extract by tile and by "
                              "region in order to compute confusion matrix "
                              "on classification fusion"),
                        type=str2bool,
                        required=False)
    PARSER.add_argument("-region_vec",
                        dest="region_vec",
                        help="region database",
                        required=True)
    PARSER.add_argument("-working_directory",
                        dest="working_directory",
                        help="path to a working directory",
                        default=None,
                        required=False)
    ARGS = PARSER.parse_args()

    vector_formatting(ARGS.tile_name, ARGS.output_path, ARGS.ground_truth_vec,
                      ARGS.data_field, ARGS.cloud_threshold, ARGS.ratio,
                      ARGS.random_seed, ARGS.enable_cross_validation,
                      ARGS.enable_split_ground_truth,
                      ARGS.fusion_merge_all_validation, ARGS.runs, ARGS.epsg,
                      ARGS.region_field, ARGS.merge_final_classifications,
                      ARGS.merge_final_classifications_ratio, ARGS.region_vec,
                      ARGS.working_directory)
