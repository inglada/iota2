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
            path_directory = path_tmp
            cmd = (f'otbcli_ComputeConfusionMatrix -in {path_classif}/"'
                   f'"Classif_Seed_{seed}.tif -out {path_directory}/'
                   f'{tile}_seed_{seed}.csv'
                   f' -ref.vector.field {data_field.lower()} -ref vector '
                   f'-ref.vector.in {val_tile}')
            all_cmd.append(cmd)

    fu.writeCmds(path_to_cmd_confusion + "/confusion.txt", all_cmd)
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
