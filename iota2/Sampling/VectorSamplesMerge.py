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
"""The vector Samples Merge module"""
import argparse
import os
import shutil
import logging
from logging import Logger
from typing import List, Optional
from iota2.Common import FileUtils as fu

LOGGER = logging.getLogger(__name__)


def split_vectors_by_regions(path_list: List[str]) -> List[str]:
    """
    split vectors by regions
    IN:
        path_list [list(str)]: list of path
    OUT:
        list[str] : the list of vector by region
    """
    regions_position = 2
    seed_position = 3

    output = []
    seed_vector_ = fu.sortByFirstElem([
        (os.path.split(vec)[-1].split("_")[seed_position], vec)
        for vec in path_list
    ])
    seed_vector = [seed_vector for seed, seed_vector in seed_vector_]

    for current_seed in seed_vector:
        region_vector = [(os.path.split(vec)[-1].split("_")[regions_position],
                          vec) for vec in current_seed]
        region_vector_sorted_ = fu.sortByFirstElem(region_vector)
        region_vector_sorted = [
            r_vectors for region, r_vectors in region_vector_sorted_
        ]
        for seed_vect_region in region_vector_sorted:
            output.append(seed_vect_region)
    return output


def tile_vectors_to_models(iota2_learning_samples_dir: str) -> List[str]:
    """
    use to feed vector_samples_merge function

    Parameters
    ----------
    iota2_learning_samples_dir : string
        path to "learningSamples" iota² directory
    sep_sar_opt : bool
        flag use to inform if SAR data has to be computed separately

    Return
    ------
    list
        list of list of vectors to be merged to form a vector by model
    """
    vectors = fu.FileSearch_AND(iota2_learning_samples_dir, True,
                                "Samples_learn.sqlite")
    vectors_sar = fu.FileSearch_AND(iota2_learning_samples_dir, True,
                                    "Samples_SAR_learn.sqlite")

    return split_vectors_by_regions(
        vectors) + split_vectors_by_regions(vectors_sar)


def check_duplicates(sqlite_file: str,
                     logger: Optional[Logger] = LOGGER) -> None:
    """
    check_duplicates
    Parameters
    ----------
    sqlite_file : string
        the input sqlite file
    Return
    ------
    None
    """
    import sqlite3 as lite
    conn = lite.connect(sqlite_file)
    cursor = conn.cursor()
    sql_clause = ("select * from output where ogc_fid in (select min(ogc_fid)"
                  " from output group by GEOMETRY having count(*) >= 2);")
    cursor.execute(sql_clause)
    results = cursor.fetchall()

    if results:
        sql_clause = (
            "delete from output where ogc_fid in (select min(ogc_fid)"
            " from output group by GEOMETRY having count(*) >= 2);")
        cursor.execute(sql_clause)
        conn.commit()
        logger.warning(f"{len(results)} were removed in {sqlite_file}")


def clean_repo(output_path: str, logger: Optional[Logger] = LOGGER):
    """
    remove from the directory learningSamples all unnecessary files
    """
    learning_content = os.listdir(output_path + "/learningSamples")
    for c_content in learning_content:
        c_path = output_path + "/learningSamples/" + c_content
        if os.path.isdir(c_path):
            try:
                shutil.rmtree(c_path)
            except OSError:
                logger.debug(f"{c_path} does not exists")


def is_sar(path: str, sar_pos: Optional[int] = 5) -> bool:
    """
    Check if the input image is a SAR product
    Parameters
    ----------
    path: string
        the input image
    Return
    bool
    ------
    """
    return os.path.basename(path).split("_")[sar_pos] == "SAR"


#def vectorSamplesMerge(cfg, vectorList, logger=logger):
def vector_samples_merge(vector_list: List[str],
                         output_path: str,
                         logger: Optional[Logger] = LOGGER) -> None:
    """

    Parameters
    ----------
    vector_list : List[string]
    output_path : string
    Return
    ------

    """
    regions_position = 2
    seed_position = 3

    clean_repo(output_path)

    current_model = os.path.split(
        vector_list[0])[-1].split("_")[regions_position]
    seed = os.path.split(vector_list[0])[-1].split("_")[seed_position].replace(
        "seed", "")

    shape_out_name = (f"Samples_region_{current_model}_seed{seed}_learn")

    if is_sar(vector_list[0]):
        shape_out_name = shape_out_name + "_SAR"

    logger.info(f"Vectors to merge in {shape_out_name}")
    logger.info("\n".join(vector_list))

    fu.mergeSQLite(shape_out_name,
                   os.path.join(output_path, "learningSamples"), vector_list)

    check_duplicates(
        os.path.join(os.path.join(output_path, "learningSamples"),
                     shape_out_name + ".sqlite"))


if __name__ == "__main__":

    PARSER = argparse.ArgumentParser(
        description="This function merge sqlite to perform training step")
    PARSER.add_argument("-output_path",
                        help="path to output directory (mandatory)",
                        dest="output_path",
                        required=True)
    PARSER.add_argument("-vector_list",
                        nargs='+',
                        help="list of vectorFiles to merge (mandatory)",
                        dest="vector_list",
                        required=True)

    ARGS = PARSER.parse_args()
    vector_samples_merge(ARGS.vector_list, ARGS.output_path)
