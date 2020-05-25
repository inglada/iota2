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
"""module dedicated to mosaic classifications in order to produce
final maps"""
import os
import re
import shutil
import argparse
import logging
import numpy as np
from osgeo import gdal
from typing import List
from osgeo.gdalconst import *

from iota2.Common import FileUtils as fu
from iota2.Common import CreateIndexedColorImage as color
from iota2.Common.rasterUtils import compress_raster

from iota2.Common.Utils import run

LOGGER = logging.getLogger(__name__)


def generate_diff_map(runs, all_tiles, path_wd, data_field, spatial_resolution,
                      path_test):
    """produce a map of well/bad classified learning/validation pixels
    """
    for seed in range(runs):
        for tile in all_tiles:
            val_tile = fu.FileSearch_AND(os.path.join(path_test, "dataAppVal"),
                                         True, tile, "_seed_" + str(seed) +
                                         "_val.sqlite")[0]
            learn_tile = fu.FileSearch_AND(
                os.path.join(path_test, "dataAppVal"), True, tile,
                "_seed_" + str(seed) + "_learn.sqlite")[0]
            classif = os.path.join(path_test, "final", "TMP",
                                   f"{tile}_seed_{seed}.tif")
            diff = os.path.join(path_test, "final", "TMP",
                                f"{tile}_seed_{seed}_CompRef.tif")
            working_directory = os.path.join(path_test, "final", "TMP")
            if path_wd:
                working_directory = path_wd
            compare_ref(val_tile, learn_tile, classif, diff, working_directory,
                        path_wd, data_field, spatial_resolution)

        all_diff = fu.FileSearch_AND(os.path.join(path_test, "final", "TMP"),
                                     True, f"_seed_{seed}_CompRef.tif")
        diff_seed = os.path.join(path_test, "final", f"diff_seed_{seed}.tif")
        if path_wd:
            diff_seed = os.path.join(working_directory,
                                     f"diff_seed_{seed}.tif")
        fu.assembleTile_Merge(all_diff,
                              spatial_resolution,
                              diff_seed,
                              ot="Byte")
        if path_wd:
            shutil.copy(
                working_directory + f"/diff_seed_{seed}.tif",
                os.path.join(path_test, "final", f"diff_seed_{seed}.tif"))


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


def BuildNbVoteCmd(classifTile, VoteMap):

    exp = []
    for i in range(len(classifTile)):
        exp.append("(im" + str(i + 1) + "b1!=0?1:0)")
    expVote = "+".join(exp)
    imgs = ' '.join(classifTile)
    cmd = 'otbcli_BandMath -il ' + imgs + ' -out ' + VoteMap + ' -exp "' + expVote + '"'
    return cmd


def BuildConfidenceCmd(finalTile,
                       classifTile,
                       confidence,
                       OutPutConfidence,
                       fact=100,
                       pixType="uint8"):

    if len(classifTile) != len(confidence):
        raise Exception(
            "number of confidence map and classifcation map must be the same")

    N = len(classifTile)
    exp = []
    for i in range(len(classifTile)):
        exp.append("(im" + str(i + 2) + "b1==0?0:im1b1!=im" + str(i + 2) +
                   "b1?1-im" + str(i + 2 + N) + "b1:im" + str(i + 2 + N) +
                   "b1)")
    #expConfidence="im1b1==0?0:("+"+".join(exp)+")/im"+str(2+2*N)+"b1"
    expConfidence = "im1b1==0?0:(" + "+".join(exp) + ")/" + str(
        len(classifTile))

    All = classifTile + confidence
    All = " ".join(All)

    cmd = 'otbcli_BandMath -ram 5120 -il ' + finalTile + ' ' + All + ' -out ' + OutPutConfidence + ' ' + pixType + ' -exp "' + str(
        fact) + '*(' + expConfidence + ')"'

    return cmd


def removeInListByRegEx(InputList, RegEx):
    Outlist = []
    for elem in InputList:
        match = re.match(RegEx, elem)
        if not match:
            Outlist.append(elem)

    return Outlist


def proba_map_fusion(proba_map_list,
                     ram=128,
                     working_directory=None,
                     logger=LOGGER):
    """fusion of probabilities map

    Parameters
    ----------
    proba_map_list : list
        list of probabilities map to merge
    ram : int
        available ram in mb
    working_directory : string
        working directory absolute path
    """
    from iota2.Common.OtbAppBank import CreateBandMathXApplication
    model_pos = 3

    proba_map_fus_dir, proba_map_fus_name = os.path.split(proba_map_list[0])
    proba_map_fus_name = proba_map_fus_name.split("_")
    proba_map_fus_name[model_pos] = proba_map_fus_name[model_pos].split("f")[0]
    proba_map_fus_name = "_".join(proba_map_fus_name)

    exp = "({}) dv {}".format(
        "+".join(["im{}".format(i + 1) for i in range(len(proba_map_list))]),
        len(proba_map_list))
    proba_map_fus_path = os.path.join(proba_map_fus_dir, proba_map_fus_name)
    if working_directory:
        proba_map_fus_path = os.path.join(working_directory,
                                          proba_map_fus_name)
    logger.info("Fusion of probality maps : {} at {}".format(
        proba_map_list, proba_map_fus_path))
    proba_merge = CreateBandMathXApplication({
        "il": proba_map_list,
        "ram": str(ram),
        "out": proba_map_fus_path,
        "exp": exp
    })
    proba_merge.ExecuteAndWriteOutput()
    if working_directory:
        copy_target = os.path.join(proba_map_fus_dir, proba_map_fus_name)
        logger.debug("copy {} to {}".format(proba_map_fus_path, copy_target))
        shutil.copy(proba_map_fus_path, copy_target)
        os.remove(proba_map_fus_path)


def genGlobalConfidence(N, pathWd, spatialRes, proj, pathTest, classifMode,
                        AllTile: List[str], shapeRegion, ds_sar_opt,
                        proba_map_flag):
    """generate confidences ready to be mosaic
    """
    PROBAMAP_PATTERN = "PROBAMAP"
    tmpClassif = pathTest + "/classif/tmpClassif"
    pathToClassif = pathTest + "/classif"

    if pathWd:
        tmpClassif = pathWd + "/tmpClassif"

    if not os.path.exists(tmpClassif):
        run("mkdir " + tmpClassif)

    for seed in range(N):
        for tuile in AllTile:
            if shapeRegion is None:
                if classifMode == "separate":
                    confidence_pattern = os.path.join(
                        pathToClassif,
                        "{}*model*confidence_seed_{}*.tif".format(tuile, seed))
                    if ds_sar_opt:
                        confidence_pattern = os.path.join(
                            pathToClassif,
                            "{}*model*confidence_seed_{}*_DS.tif".format(
                                tuile, seed))
                    confidence = fu.fileSearchRegEx(confidence_pattern)
                    globalConf = tmpClassif + "/" + tuile + "_GlobalConfidence_seed_" + str(
                        seed) + ".tif"
                    globalConf_f = pathTest + "/final/TMP/" + tuile + "_GlobalConfidence_seed_" + str(
                        seed) + ".tif"
                    cmd = 'otbcli_BandMath -il ' + confidence[
                        0] + ' -out ' + globalConf + ' uint8 -exp "100*im1b1"'
                    run(cmd)
                    shutil.copyfile(globalConf, globalConf_f)
                    os.remove(globalConf)
                else:
                    raise Exception((
                        "if there is no region shape specify in the "
                        "configuration file, argClassification.classifMode must be set to 'separate'"
                    ))
            else:  #output Mode
                suffix = "*"
                if ds_sar_opt:
                    suffix = "*DS*"
                if classifMode != "separate":
                    classifTile = fu.fileSearchRegEx(
                        pathToClassif + "/Classif_" + tuile +
                        "*model_*f*_seed_" + str(seed) + suffix
                    )  # tmp tile (produce by each classifier, without nodata)
                    splitModel = []
                    for classif in classifTile:
                        model = classif.split("/")[-1].split("_")[3].split(
                            "f")[0]
                        try:
                            ind = splitModel.index(model)
                        except ValueError:
                            splitModel.append(model)
                    splitConfidence = []
                    confidence_all = fu.fileSearchRegEx(
                        pathToClassif + "/" + tuile +
                        "*model_*_confidence_seed_" + str(seed) + suffix)
                    confidence_withoutSplit = removeInListByRegEx(
                        confidence_all, ".*model_.*f.*_confidence." + suffix)
                    for model in splitModel:
                        classifTile = fu.fileSearchRegEx(
                            pathToClassif + "/Classif_" + tuile + "*model_" +
                            model + "f*_seed_" + str(seed) + suffix
                        )  # tmp tile (produce by each classifier, without nodata)
                        finalTile = pathToClassif + "/Classif_" + tuile + "_model_" + model + "_seed_" + str(
                            seed) + ".tif"
                        if ds_sar_opt:
                            finalTile = pathToClassif + "/Classif_" + tuile + "_model_" + model + "_seed_" + str(
                                seed) + "_DS.tif"
                        confidence = fu.fileSearchRegEx(pathToClassif + "/" +
                                                        tuile + "*model_" +
                                                        model +
                                                        "f*_confidence_seed_" +
                                                        str(seed) + suffix)
                        if proba_map_flag:
                            proba_map_fusion(proba_map_list=fu.fileSearchRegEx(
                                "{}/{}_{}_model_{}f*_seed_{}{}.tif".format(
                                    pathToClassif, PROBAMAP_PATTERN, tuile,
                                    model, seed, suffix)),
                                             working_directory=pathWd,
                                             ram=2000)
                        classifTile = sorted(classifTile)
                        confidence = sorted(confidence)
                        OutPutConfidence = tmpClassif + "/" + tuile + "_model_" + model + "_confidence_seed_" + str(
                            seed) + ".tif"
                        if ds_sar_opt:
                            OutPutConfidence = tmpClassif + "/" + tuile + "_model_" + model + "_confidence_seed_" + str(
                                seed) + "_DS.tif"
                        cmd = BuildConfidenceCmd(finalTile,
                                                 classifTile,
                                                 confidence,
                                                 OutPutConfidence,
                                                 fact=100,
                                                 pixType="uint8")
                        run(cmd)
                        splitConfidence.append(OutPutConfidence)

                    i = 0  #init
                    j = 0
                    exp1 = "+".join([
                        "im" + str(i + 1) + "b1"
                        for i in range(len(splitConfidence))
                    ])  #-> confidence from splited models are from 0 to 100
                    exp2 = "+".join([
                        "(100*im" + str(j + 1) + "b1)" for j in np.arange(
                            len(splitConfidence),
                            len(splitConfidence) +
                            len(confidence_withoutSplit))
                    ])  #-> confidence from NO-splited models are from 0 to 1
                    if not splitConfidence:
                        exp2 = "+".join([
                            "100*im" + str(j + 1) + "b1"
                            for j in range(len(confidence_withoutSplit))
                        ])
                    if exp1 and exp2:
                        exp = exp1 + "+" + exp2
                    if exp1 and not exp2:
                        exp = exp1
                    if not exp1 and exp2:
                        exp = exp2

                    confidence_list = splitConfidence + confidence_withoutSplit
                    AllConfidence = " ".join(confidence_list)

                    OutPutConfidence = tmpClassif + "/" + tuile + "_GlobalConfidence_seed_" + str(
                        seed) + ".tif"
                    cmd = 'otbcli_BandMath -il ' + AllConfidence + ' -out ' + OutPutConfidence + ' uint8 -exp "' + exp + '"'
                    run(cmd)
                    shutil.copy(OutPutConfidence, pathTest + "/final/TMP")
                    os.remove(OutPutConfidence)
                    #shutil.rmtree(tmpClassif)
                else:
                    confidence = fu.fileSearchRegEx(pathToClassif + "/" +
                                                    tuile +
                                                    "*model*confidence_seed_" +
                                                    str(seed) + suffix)
                    exp = "+".join([
                        "im" + str(i + 1) + "b1"
                        for i in range(len(confidence))
                    ])
                    AllConfidence = " ".join(confidence)
                    #for currentConf in confidence:
                    globalConf = tmpClassif + "/" + tuile + "_GlobalConfidence_seed_" + str(
                        seed) + ".tif"
                    globalConf_f = pathTest + "/final/TMP/" + tuile + "_GlobalConfidence_seed_" + str(
                        seed) + ".tif"
                    cmd = 'otbcli_BandMath -il ' + AllConfidence + ' -out ' + globalConf + ' uint8 -exp "100*(' + exp + ')"'
                    #print confidence
                    run(cmd)
                    shutil.copyfile(globalConf, globalConf_f)
                    os.remove(globalConf)


def classification_shaping(path_classif: str, runs: int, path_out: str,
                           path_wd: str, classif_mode: str, path_test: str,
                           ds_sar_opt: bool, proj: int, nomenclature_path: str,
                           output_statistics: bool, spatial_resolution: float,
                           proba_map_flag: bool, region_shape: str,
                           color_path: str, data_field: str,
                           tiles_from_cfg: List[str]) -> None:
    """function use to mosaic rasters and to produce final maps

    path_classif: str
        directory where as classifications
    runs: int
        number of random learning/validation samples-set
    path_out: str
        output directory
    path_wd: str
        working directory
    classif_mode: str
        fusion of classifications ?
    path_test: str
        iota2 output directory
    ds_sar_opt: bool
        flag to inform if SAR and optical post-classification workflow
        is enable
    proj: int
        epsg code
    nomenclature_path: str
        nomenclature path
    output_statistics: bool
        flag to enable output statistics
    spatial_resolution: float
        output's spatial resolution
    proba_map_flag: bool
        flag to inform if probability map was produce
    region_shape: str
        region shapeFile path
    color_path: str
        color table file
    data_field : str
        data field in the ground truth database
    tiles_from_cfg : list
        list of tiles asked in the iota2 configuration file
    """

    if path_wd is None:
        tmp = path_out + "/TMP"
        if not os.path.exists(path_out + "/TMP"):
            os.mkdir(tmp)
    else:
        tmp = path_wd
        if not os.path.exists(path_out + "/TMP"):
            os.mkdir(path_out + "/TMP")

    all_tiles = list(
        set([
            classif.split("_")[1] for classif in fu.FileSearch_AND(
                path_test + "/classif", False, "Classif", ".tif")
        ]))

    pix_type = fu.getOutputPixType(nomenclature_path)
    features_path = os.path.join(path_test, "features")
    all_tmp_folder = fu.fileSearchRegEx(path_test + "/TMPFOLDER*")
    if all_tmp_folder:
        for tmp_folder in all_tmp_folder:
            shutil.rmtree(tmp_folder)

    suffix = "*"
    if ds_sar_opt:
        suffix = "*DS*"
    genGlobalConfidence(runs, path_wd, spatial_resolution, proj, path_test,
                        classif_mode, all_tiles, region_shape, ds_sar_opt,
                        proba_map_flag)
    if region_shape and classif_mode == "fusion":
        old_classif = fu.fileSearchRegEx(path_test +
                                         "/classif/Classif_*_model_*f*_seed_" +
                                         suffix + ".tif")
        for rm in old_classif:
            if not os.path.exists(path_test + "/final/TMP/OLDCLASSIF"):
                os.mkdir(path_test + "/final/TMP/OLDCLASSIF")
            run("mv " + rm + " " + path_test + "/final/TMP/OLDCLASSIF")

    classification = []
    confidence = []
    proba_map = []
    cloud = []
    for seed in range(runs):
        classification.append([])
        confidence.append([])
        cloud.append([])
        sort = []
        if proba_map_flag:
            proba_map_list = fu.fileSearchRegEx(
                path_test + "/classif/PROBAMAP_*_model_*_seed_" + str(seed) +
                suffix + ".tif")
            proba_map_list = removeInListByRegEx(
                proba_map_list, ".*model_.*f.*_seed." + suffix)
            proba_map.append(proba_map_list)
        if classif_mode == "separate" or region_shape:
            all_classif_seed = fu.FileSearch_AND(path_classif, True, ".tif",
                                                 "Classif",
                                                 "seed_" + str(seed))
            if ds_sar_opt:
                all_classif_seed = fu.FileSearch_AND(path_classif, True,
                                                     ".tif", "Classif",
                                                     "seed_" + str(seed),
                                                     "DS.tif")
            ind = 1
        elif classif_mode == "fusion":
            all_classif_seed = fu.FileSearch_AND(
                path_classif, True, "_FUSION_NODATA_seed" + str(seed) + ".tif")
            if ds_sar_opt:
                all_classif_seed = fu.FileSearch_AND(
                    path_classif, True,
                    "_FUSION_NODATA_seed" + str(seed) + "_DS.tif")
            ind = 0
        for tile in all_classif_seed:
            sort.append((tile.split("/")[-1].split("_")[ind], tile))
        sort = fu.sortByFirstElem(sort)
        for tile, paths in sort:
            exp = ""
            all_cl = ""
            all_cl_rm = []
            for i in range(len(paths)):
                all_cl = all_cl + paths[i] + " "
                all_cl_rm.append(paths[i])
                if i < len(paths) - 1:
                    exp = exp + "im" + str(i + 1) + "b1 + "
                else:
                    exp = exp + "im" + str(i + 1) + "b1"
            path_cl_final = tmp + "/" + tile + "_seed_" + str(seed) + ".tif"
            classification[seed].append(path_cl_final)
            cmd = 'otbcli_BandMath -il ' + all_cl + '-out ' + path_cl_final + ' ' + pix_type + ' -exp "' + exp + '"'
            run(cmd)

            tile_confidence = path_out + "/TMP/" + tile + "_GlobalConfidence_seed_" + str(
                seed) + ".tif"
            confidence[seed].append(tile_confidence)
            cloud_tile = fu.FileSearch_AND(features_path + "/" + tile, True,
                                           "nbView.tif")[0]
            classif_tile = tmp + "/" + tile + "_seed_" + str(seed) + ".tif"
            cloud_tile_priority = path_test + "/final/TMP/" + tile + "_Cloud.tif"
            cloud_tile_priority_tmp = tmp + "/" + tile + "_Cloud.tif"
            cloud_tile_priority_stats_ok = path_test + "/final/TMP/" + tile + "_Cloud_StatsOK.tif"
            cloud_tile_priority_tmp_stats_ok = tmp + "/" + tile + "_Cloud_StatsOK.tif"
            cloud[seed].append(cloud_tile_priority)
            if not os.path.exists(cloud_tile_priority):
                cmd_cloud = f'otbcli_BandMath -il {cloud_tile}  {classif_tile} -out {cloud_tile_priority_tmp} int16 -exp "im2b1>0?im1b1:0"'
                run(cmd_cloud)
                if output_statistics:
                    cmd_cloud = 'otbcli_BandMath -il ' + cloud_tile + ' ' + classif_tile + ' -out ' + cloud_tile_priority_tmp_stats_ok + ' int16 -exp "im2b1>0?im1b1:-1"'
                    run(cmd_cloud)
                    if path_wd:
                        shutil.copy(cloud_tile_priority_tmp_stats_ok,
                                    cloud_tile_priority_stats_ok)
                        os.remove(cloud_tile_priority_tmp_stats_ok)

                if path_wd:
                    shutil.copy(cloud_tile_priority_tmp, cloud_tile_priority)
                    os.remove(cloud_tile_priority_tmp)

    if path_wd is not None:
        run("cp -a " + tmp + "/* " + path_out + "/TMP")

    for seed in range(runs):
        assemble_folder = path_test + "/final"
        if path_wd:
            assemble_folder = path_wd
        classif_mosaic_tmp = "{}/Classif_Seed_{}_tmp.tif".format(
            assemble_folder, seed)
        classif_mosaic_compress = "{}/Classif_Seed_{}.tif".format(
            assemble_folder, seed)
        fu.assembleTile_Merge(classification[seed],
                              spatial_resolution,
                              classif_mosaic_tmp,
                              "Byte" if pix_type == "uint8" else "Int16",
                              co={
                                  "COMPRESS": "LZW",
                                  "BIGTIFF": "YES"
                              })
        compress_raster(classif_mosaic_tmp, classif_mosaic_compress)
        os.remove(classif_mosaic_tmp)
        if path_wd:
            shutil.copy(path_wd + "/Classif_Seed_" + str(seed) + ".tif",
                        path_test + "/final")
            os.remove(path_wd + "/Classif_Seed_" + str(seed) + ".tif")

        confidence_mosaic_tmp = assemble_folder + "/Confidence_Seed_" + str(
            seed) + "_tmp.tif"
        confidence_mosaic_compress = assemble_folder + "/Confidence_Seed_" + str(
            seed) + ".tif"
        fu.assembleTile_Merge(confidence[seed],
                              spatial_resolution,
                              confidence_mosaic_tmp,
                              "Byte",
                              co={
                                  "COMPRESS": "LZW",
                                  "BIGTIFF": "YES"
                              })
        compress_raster(confidence_mosaic_tmp, confidence_mosaic_compress)
        os.remove(confidence_mosaic_tmp)
        if path_wd:
            shutil.copy(path_wd + "/Confidence_Seed_" + str(seed) + ".tif",
                        path_test + "/final")
            os.remove(path_wd + "/Confidence_Seed_" + str(seed) + ".tif")

        color.CreateIndexedColorImage(
            path_test + "/final/Classif_Seed_" + str(seed) + ".tif",
            color_path,
            output_pix_type=gdal.GDT_Byte
            if pix_type == "uint8" else gdal.GDT_UInt16)

        if proba_map_flag:
            proba_map_mosaic_tmp = os.path.join(
                assemble_folder, "ProbabilityMap_seed_{}_tmp.tif".format(seed))
            proba_map_mosaic_compress = os.path.join(
                assemble_folder, "ProbabilityMap_seed_{}.tif".format(seed))
            fu.assembleTile_Merge(proba_map[seed],
                                  spatial_resolution,
                                  proba_map_mosaic_tmp,
                                  "Int16",
                                  co={
                                      "COMPRESS": "LZW",
                                      "BIGTIFF": "YES"
                                  })
            compress_raster(proba_map_mosaic_tmp, proba_map_mosaic_compress)
            os.remove(proba_map_mosaic_tmp)
            if path_wd:
                shutil.copy(proba_map_mosaic_compress, path_test + "/final")
                os.remove(proba_map_mosaic_compress)

    cloud_mosaic_tmp = assemble_folder + "/PixelsValidity_tmp.tif"
    cloud_mosaic_compress = assemble_folder + "/PixelsValidity.tif"
    fu.assembleTile_Merge(cloud[0],
                          spatial_resolution,
                          cloud_mosaic_tmp,
                          "Byte",
                          co={
                              "COMPRESS": "LZW",
                              "BIGTIFF": "YES"
                          })
    compress_raster(cloud_mosaic_tmp, cloud_mosaic_compress)
    os.remove(cloud_mosaic_tmp)
    if path_wd:
        shutil.copy(path_wd + "/PixelsValidity.tif", path_test + "/final")
        os.remove(path_wd + "/PixelsValidity.tif")

    generate_diff_map(runs, all_tiles, path_wd, data_field, spatial_resolution,
                      path_test)
    missing_tiles = [elem for elem in all_tiles if elem not in tiles_from_cfg]
    create_dummy_rasters(missing_tiles, runs, path_test)


if __name__ == "__main__":
    from iota2.Common.FileUtils import str2bool
    PARSER = argparse.ArgumentParser(
        description=
        "This function shape classifications (fake fusion and tiles priority)")
    PARSER.add_argument(
        "-path.classif",
        help=
        "path to the folder which ONLY contains classification images (mandatory)",
        dest="path_classif",
        required=True)
    PARSER.add_argument("-N",
                        dest="runs",
                        help="number of random sample(mandatory)",
                        type=int,
                        required=True)
    PARSER.add_argument(
        "-path.out",
        help=
        "path to the folder which will contains all final classifications (mandatory)",
        dest="path_out",
        required=True)
    PARSER.add_argument("--wd",
                        dest="path_wd",
                        help="path to the working directory",
                        default=None,
                        required=False)
    PARSER.add_argument("-classif_mode",
                        dest="classif_mode",
                        help="fusion of classifications",
                        default="separate",
                        required=False)
    PARSER.add_argument("-iota2_directory",
                        dest="path_test",
                        help="iota2 output directory",
                        required=True)
    PARSER.add_argument("-ds_sar_opt",
                        dest="ds_sar_opt",
                        help="is post-classification workflow enable ?",
                        type=str2bool,
                        default=False,
                        required=True)
    PARSER.add_argument("-proj",
                        dest="proj",
                        help="projection",
                        type=int,
                        required=True)
    PARSER.add_argument("-nomencalture_path",
                        dest="nomencalture_path",
                        help="nomencalture path",
                        type=str,
                        required=True)
    PARSER.add_argument("-output_statistics",
                        dest="output_statistics",
                        help="is output_statistics enable ?",
                        type=str2bool,
                        default=True)
    PARSER.add_argument("-spatial_resolution",
                        dest="spatial_resolution",
                        help="output spatial resolution",
                        type=float,
                        required=True)
    PARSER.add_argument("-proba_map_flag",
                        dest="proba_map_flag",
                        help="is probability map produced",
                        type=str2bool,
                        default=False)
    PARSER.add_argument("-region_shape",
                        dest="region_shape",
                        help="region shapeFile file",
                        type=str,
                        required=True)
    PARSER.add_argument("-color_path",
                        dest="color_path",
                        help="color table file",
                        type=str,
                        required=True)
    PARSER.add_argument("-data_field",
                        dest="data_field",
                        help="data field in ground truth database",
                        type=str,
                        required=True)
    PARSER.add_argument("-tiles_from_cfg",
                        dest="tiles_from_cfg",
                        help="every expected tiles",
                        type=str,
                        nargs="+",
                        required=True)
    ARGS = PARSER.parse_args()

    classification_shaping(path_classif=ARGS.path_classif,
                           runs=ARGS.runs,
                           path_out=ARGS.path_out,
                           path_wd=ARGS.path_wd,
                           classif_mode=ARGS.classif_mode,
                           path_test=ARGS.path_test,
                           ds_sar_opt=ARGS.ds_sar_opt,
                           proj=ARGS.proj,
                           nomenclature_path=ARGS.nomenclature_path,
                           output_statistics=ARGS.output_statistics,
                           spatial_resolution=ARGS.spatial_resolution,
                           proba_map_flag=ARGS.proba_map_flag,
                           region_shape=ARGS.region_shape,
                           color_path=ARGS.color_path,
                           data_field=ARGS.data_field,
                           tiles_from_cfg=ARGS.tiles_from_cfg)
