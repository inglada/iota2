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
""" Generate Confusion Matrix"""
import argparse
import os
import shutil
import logging
from logging import Logger
from typing import List, Tuple, Optional

from iota2.Common import FileUtils as fu

from iota2.Common.Utils import run

LOGGER = logging.getLogger(__name__)


def create_dummy_rasters(missing_tiles: List[str], runs: int,
                         output_path: str) -> None:
    """
    Parameters
    ----------
    missing_tiles: list(string)
    runs: int
    output_path: string
    Return
    ------
    None
    Notes
    -----
    use when mode is 'one_region' but there is no validations / learning
    samples into a specific tile
    """

    classifications_dir = os.path.join(output_path, "classif")
    final_dir = os.path.join(output_path, "final", "TMP")

    for tile in missing_tiles:
        classif_tile = fu.FileSearch_AND(classifications_dir, True,
                                         "Classif_" + str(tile))[0]
        for seed in range(runs):
            dummy_raster_name = tile + "_seed_" + str(seed) + "_CompRef.tif"
            dummy_raster = final_dir + "/" + dummy_raster_name
            dummy_raster_cmd = (f"gdal_merge.py -ot Byte -n 0 -createonly -o "
                                f"{ dummy_raster} {classif_tile}")
            run(dummy_raster_cmd)


def compare_ref(shape_ref: str, shape_learn: str, classif: str, diff: str,
                working_directory: str, path_wd: str, data_field: str,
                spatial_res: int):
    """
    Parameters
    ----------
    shape_ref: string
    shape_learn: string
    classif: string
    diff: string
    working_directory: string
    path_wd: string
    data_field: string
    spatial_res: string
    Return
    ------
    string
    """
    min_x, max_x, min_y, max_y = fu.getRasterExtent(classif)
    shape_raster_val = working_directory + os.sep + shape_ref.split(
        "/")[-1].replace(".sqlite", ".tif")
    shape_raster_learn = working_directory + os.sep + shape_learn.split(
        "/")[-1].replace(".sqlite", ".tif")

    # Rasterise val
    shape_ref_table_name = os.path.splitext(
        os.path.split(shape_ref)[-1])[0].lower()
    cmd = (f"gdal_rasterize -l {shape_ref_table_name} -a {data_field} -init 0 "
           f"-tr {spatial_res} {spatial_res} {shape_ref} {shape_raster_val} "
           f"-te {min_x} {min_y} {max_x} {max_y}")
    run(cmd)
    # Rasterise learn
    shape_learn_table_name = os.path.splitext(
        os.path.split(shape_learn)[-1])[0].lower()
    cmd = (
        f"gdal_rasterize -l {shape_learn_table_name} -a {data_field} -init "
        f"0 -tr {spatial_res} {spatial_res} {shape_learn} {shape_raster_learn}"
        f" -te {min_x} {min_y} {max_x} {max_y}")
    run(cmd)

    # diff val
    diff_val = working_directory + "/" + diff.split("/")[-1].replace(
        ".tif", "_val.tif")
    # reference identique -> 2  | reference != -> 1 | pas de reference -> 0
    cmd_val = (f'otbcli_BandMath -il {shape_raster_val} {classif} -out '
               f'{diff_val} uint8 -exp "im1b1==0?0:im1b1==im2b1?2:1"')
    run(cmd_val)
    os.remove(shape_raster_val)

    # diff learn
    diff_learn = working_directory + "/" + diff.split("/")[-1].replace(
        ".tif", "_learn.tif")
    # reference identique -> 4  | reference != -> 3 | pas de reference -> 0
    cmd_learn = (f'otbcli_BandMath -il {shape_raster_learn} {classif} -out '
                 f'{diff_learn} uint8 -exp "im1b1==0?0:im1b1==im2b1?4:3"')
    run(cmd_learn)
    os.remove(shape_raster_learn)

    # sum diff val + learn
    diff_tmp = working_directory + "/" + diff.split("/")[-1]
    cmd_sum = (f'otbcli_BandMath -il {diff_val} {diff_learn} -out {diff_tmp}'
               f' uint8 -exp "im1b1+im2b1"')
    run(cmd_sum)
    os.remove(diff_val)
    os.remove(diff_learn)

    if path_wd and not os.path.exists(diff):
        shutil.copy(diff_tmp, diff)
        os.remove(diff_tmp)

    return diff


def gen_conf_matrix(path_classif: str, path_valid: str, runs: int,
                    data_field: str, path_to_cmd_confusion: str, path_wd: str,
                    path_test: str, spatial_res: int, list_tiles: List[str],
                    enable_cross_validation: bool) -> List[str]:
    """
    Parameters
    ----------
    path_classif: string
    path_valid: string
    runs: int
    data_field: string
    path_to_cmd_confusion: string
    path_wd: string
    Return
    ------
    list(string)
    """
    all_cmd = []
    path_tmp = os.path.join(path_classif, "TMP")

    # path_Test = cfg.getParam('chain', 'outputPath')
    # spatial_Res = cfg.getParam('chain', 'spatialResolution')
    # enable_Cross_Validation = cfg.getParam('chain', 'enableCrossValidation')

    working_directory = os.path.join(path_classif, "TMP")
    if path_wd:
        working_directory = path_wd

    all_tiles = []
    validation_files = fu.FileSearch_AND(path_valid, True, "_val.sqlite")
    for valid in validation_files:
        current_tile = valid.split("/")[-1].split("_")[0]
        try:
            all_tiles.index(current_tile)
        except ValueError:
            all_tiles.append(current_tile)

    for seed in range(runs):
        # recherche de tout les shapeFiles par seed, par tuiles pour
        # les fusionner
        for tile in all_tiles:
            seed_val = seed
            if enable_cross_validation:
                seed_val = runs - 1
            if enable_cross_validation and seed == runs - 1:
                continue
            val_tile = fu.FileSearch_AND(
                path_valid, True, tile,
                "_seed_" + str(seed_val) + "_val.sqlite")[0]
            learn_tile = fu.FileSearch_AND(
                path_valid, True, tile,
                "_seed_" + str(seed) + "_learn.sqlite")[0]
            path_directory = path_tmp
            cmd = (f'otbcli_ComputeConfusionMatrix -in {path_classif}/"'
                   f'"Classif_Seed_{seed}.tif -out {path_directory}/'
                   f'{tile}_seed_{seed}.csv'
                   f' -ref.vector.field {data_field.lower()} -ref vector '
                   f'-ref.vector.in {val_tile}')
            all_cmd.append(cmd)
            classif = path_tmp + "/" + tile + "_seed_" + str(seed) + ".tif"
            diff = path_tmp + "/" + tile + "_seed_" + str(
                seed) + "_CompRef.tif"

            compare_ref(val_tile, learn_tile, classif, diff, working_directory,
                        path_wd, data_field, spatial_res)

    fu.writeCmds(path_to_cmd_confusion + "/confusion.txt", all_cmd)

    if enable_cross_validation:
        runs = runs - 1
    for seed in range(runs):
        all_diff = fu.FileSearch_AND(path_tmp, True,
                                     f"_seed_{seed}_CompRef.tif")
        diff_seed = os.path.join(path_test, "final", f"diff_seed_{seed}.tif")
        if path_wd:
            diff_seed = os.path.join(working_directory,
                                     f"diff_seed_{seed}.tif")
        fu.assembleTile_Merge(all_diff, spatial_res, diff_seed, ot="Byte")
        if path_wd:
            shutil.copy(
                working_directory + f"/diff_seed_{seed}.tif",
                os.path.join(path_test, "final", f"diff_seed_{seed}.tif"))

    # Create dummy rasters if necessary
    tile_asked = list_tiles.split()
    missing_tiles = [elem for elem in tile_asked if elem not in all_tiles]
    create_dummy_rasters(missing_tiles, runs, path_test)

    return all_cmd


def confusion_sar_optical_parameter(iota2_dir: str,
                                    logger: Optional[Logger] = LOGGER):
    """
    return a list of tuple containing the classification and the associated
    shapeFile to compute a confusion matrix
    """
    ref_vectors_dir = os.path.join(iota2_dir, "dataAppVal", "bymodels")
    classifications_dir = os.path.join(iota2_dir, "classif")

    vector_seed_pos = 4
    vector_tile_pos = 0
    vector_model_pos = 2
    classif_seed_pos = 5
    classif_tile_pos = 1
    classif_model_pos = 3

    vectors = fu.FileSearch_AND(ref_vectors_dir, True, ".shp")
    classifications = fu.FileSearch_AND(classifications_dir, True, "Classif",
                                        "model", "seed", ".tif")

    group = []
    for vector in vectors:
        vec_name = os.path.basename(vector)
        seed = vec_name.split("_")[vector_seed_pos]
        tile = vec_name.split("_")[vector_tile_pos]
        model = vec_name.split("_")[vector_model_pos]
        key = (seed, tile, model)
        fields = fu.get_all_fields_in_shape(vector)
        if len(
                fu.getFieldElement(vector,
                                   driverName="ESRI Shapefile",
                                   field=fields[0],
                                   mode="all",
                                   elemType="str")) != 0:
            group.append((key, vector))
    for classif in classifications:
        classif_name = os.path.basename(classif)
        seed = classif_name.split("_")[classif_seed_pos].split(".tif")[0]
        tile = classif_name.split("_")[classif_tile_pos]
        model = classif_name.split("_")[classif_model_pos]
        key = (seed, tile, model)
        group.append((key, classif))
    # group by keys
    groups_param_buff = [param for key, param in fu.sortByFirstElem(group)]
    groups_param = []
    # check if all parameter to find are found.
    for group in groups_param_buff:
        if len(group) != 3:
            logger.debug(f"all parameter to use Dempster-Shafer fusion, "
                         f"not found : {group}")
        else:
            groups_param.append(group)

    # output
    output_parameters = []
    for param in groups_param:
        for sub_param in param:
            if ".shp" in sub_param:
                ref_vector = sub_param
            elif "SAR.tif" in sub_param:
                classif_sar = sub_param
            elif ".tif" in sub_param and "SAR.tif" not in sub_param:
                classif_opt = sub_param
        output_parameters.append((ref_vector, classif_opt))
        output_parameters.append((ref_vector, classif_sar))

    return output_parameters


def confusion_sar_optical(ref_vector: Tuple[str, str],
                          data_field: str,
                          ram: Optional[int] = 128,
                          logger: Optional[Logger] = LOGGER):
    """
    function use to compute a confusion matrix dedicated to the D-S
    classification fusion.

    Parameter
    ---------
    ref_vector : tuple
        tuple containing (reference vector, classification raster)
    dataField : string
        labels fields in reference vector
    ram : int
        ram dedicated to produce the confusion matrix (OTB's pipeline size)
    LOGGER : logging
        root logger
    """
    from iota2.Common import OtbAppBank

    ref_vector, classification = ref_vector
    csv_out = ref_vector.replace(".shp", ".csv")
    if "SAR.tif" in classification:
        csv_out = csv_out.replace(".csv", "_SAR.csv")
    if os.path.exists(csv_out):
        os.remove(csv_out)

    confusion_parameters = {
        "in": classification,
        "out": csv_out,
        "ref": "vector",
        "ref.vector.in": ref_vector,
        "ref.vector.field": data_field.lower(),
        "ram": str(0.8 * ram)
    }

    confusion_matrix = OtbAppBank.CreateComputeConfusionMatrixApplication(
        confusion_parameters)

    logger.info(f"Launch : {csv_out}")
    confusion_matrix.ExecuteAndWriteOutput()
    logger.debug(f"{csv_out} done")


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(
        description="this function create a confusion matrix")
    PARSER.add_argument(
        "-path.classif",
        help=("path to the folder which contains classification "
              "images (mandatory)"),
        dest="pathClassif",
        required=True)
    PARSER.add_argument(
        "-path.valid",
        help=("path to the folder which contains validation samples"
              " (with priority) (mandatory)"),
        dest="path_valid",
        required=True)
    PARSER.add_argument("-N",
                        dest="N",
                        help="number of random sample(mandatory)",
                        required=True,
                        type=int)
    PARSER.add_argument("-data.field",
                        dest="dataField",
                        help="data's field into data shape (mandatory)",
                        required=True)
    PARSER.add_argument(
        "-confusion.out.cmd",
        dest="pathToCmdConfusion",
        help=("path where all confusion cmd will be stored in a text file"
              "(mandatory)"),
        required=True)
    PARSER.add_argument("--wd",
                        dest="path_wd",
                        help="path to the working directory",
                        default=None,
                        required=False)
    PARSER.add_argument("-output_path",
                        help="path to the output directory (mandatory)",
                        dest="output_path",
                        required=True)
    PARSER.add_argument("-spatial_res",
                        help="the spatial resolution (mandatory)",
                        dest="spatial_res",
                        required=True)
    PARSER.add_argument(
        "-list_tiles",
        help="the list of tiles separated by space (mandatory)",
        dest="list_tiles",
        required=True)
    PARSER.add_argument("-cross_val",
                        help="activate cross validation ",
                        dest="cross_val",
                        default=False,
                        required=False)
    ARGS = PARSER.parse_args()

    gen_conf_matrix(ARGS.pathClassif, ARGS.path_valid, ARGS.N, ARGS.dataField,
                    ARGS.pathToCmdConfusion, ARGS.path_wd, ARGS.output_path,
                    ARGS.spatial_res, ARGS.list_tiles, ARGS.cross_val)
