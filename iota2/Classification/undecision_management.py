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
This module handle undecision after post classification fusion
"""
import argparse
import os
import shutil
from typing import List, Optional, Tuple
from iota2.Common import FileUtils as fu
from iota2.Common.Utils import run


def get_model_in_classif(item: str) -> str:
    """
    Parameters
    ----------
    item: string to be splitted
    Return
    ------
    string: model name
    """
    return item.split("_")[-3]


def get_model_in_mask(item: str) -> str:
    """
    Parameters
    ----------
    item: string to be splitted
    Return
    ------
    string: model name
    """
    return item.split("_")[-2]


def gen_mask_region_by_tile(field_region: str,
                            stack_ind: str,
                            working_dir: str,
                            current_tile: str,
                            all_model: str,
                            shp_rname: str,
                            path_to_img: str,
                            path_test: str,
                            path_to_config: str,
                            path_wd: Optional[str] = None) -> List[str]:
    """
    Parameters
    ----------
    field_region: string
    stack_ind: string
    working_dir: string
    current_tile: string
    all_model: string
    shp_rname: string
    path_to_image: string
    path_test: string
    path_wd: string
    path_to_config: string
        config file containing which model is associated to a given tile
    Return
    ------
    list(str)
    """
    model_tile = []
    for path in all_model:
        current_model = path.split("/")[-1].split("_")[1]
        tiles = fu.getListTileFromModel(current_model, path_to_config)
        model = path.split("/")[-1].split("_")[1]
        for tile in tiles:
            # get the model which learn the current tile
            if tile == current_tile:
                model_tile.append(model)
            path_to_feat = os.path.join(path_to_img, tile, "Final", stack_ind)
            mask_shp = os.path.join(path_test, "shapeRegion",
                                    f"{shp_rname}_region_{model}_{tile}.shp")
            mask_tif = os.path.join(
                working_dir, f"{shp_rname}_region_{model}_{tile}_NODATA.tif")
            mask_tif_f = os.path.join(
                path_test, "classif", "MASK",
                f"{shp_rname}_region_{model}_{tile}_NODATA.tif")
            # Create mask
            if not os.path.exists(mask_tif_f):
                cmd_raster = (
                    f"otbcli_Rasterization -in {mask_shp} -mode attribute "
                    f"-mode.attribute.field {field_region} -im {path_to_feat}"
                    f" -out {mask_tif}")

                run(cmd_raster)
                if path_wd is not None:
                    cmd = "cp " + mask_tif + " " + path_test + "/classif/MASK"
                    run(cmd)
    return model_tile


def concat_classifs_one_tile(seed: str,
                             current_tile: str,
                             path_test: str,
                             model_tile: str,
                             concat_out: str,
                             path_wd: Optional[str] = None) -> str:
    """
    Parameters
    ----------
    path_wd: string
    seed: string
    current_tile: string
    path_test: string
    model_tile: string
    concat_out: string
    Return
    ------
    string
    """
    classif_fusion = []

    for model in model_tile:
        classif_fusion.append(
            os.path.join(
                path_test, "classif", f"Classif_{current_tile}_model_"
                f"{model}_seed_{seed}.tif"))

    if len(classif_fusion) == 1:
        cmd = f"cp {classif_fusion[0]} {concat_out}"
        run(cmd)
    else:
        # in order to match images and their mask
        classif_fusion_sort = sorted(classif_fusion, key=get_model_in_classif)
        string_cl_fus = " ".join(classif_fusion_sort)
        path_to_directory = os.path.join(path_test, "classif")
        if path_wd is not None:
            path_to_directory = path_wd

        cmd = (f"otbcli_ConcatenateImages -ram 128 -il {string_cl_fus} -out "
               f"{os.path.join(path_to_directory,concat_out.split('/')[-1])}")
        run(cmd)

        if not os.path.exists(concat_out):
            cmd = (f"cp {os.path.join(path_wd, concat_out.split('/')[-1])} "
                   f"{os.path.join(path_test , 'classif')}")
            run(cmd)

    return concat_out


def concat_region_one_tile(path_test: str, classif_fusion_mask: str,
                           path_wd: str, tile_mask_concat: str) -> str:
    """
    Parameters
    ----------
    path_test: string
    classif_fusion_mask: string
    path_wd: string
    tile_mask_concat: string
    Return
    ------
    string
    """
    # TileMask_concat = pathTest+"/classif/"+currentTile+"_MASK.tif"
    if len(classif_fusion_mask) == 1 and not os.path.exists(tile_mask_concat):
        shutil.copy(classif_fusion_mask[0], tile_mask_concat)
    elif len(classif_fusion_mask) != 1 and not os.path.exists(
            tile_mask_concat):
        # in order to match images and their mask
        classif_fusion_mask_sort = sorted(classif_fusion_mask,
                                          key=get_model_in_mask)
        string_cl_fus = " ".join(classif_fusion_mask_sort)

        path_directory = os.path.join(path_test, "classif")
        if path_wd is not None:
            path_directory = path_wd
        cmd = (
            f"otbcli_ConcatenateImages -ram 128 -il {string_cl_fus} -out "
            f"{os.path.join(path_directory, tile_mask_concat.split('/')[-1])}")
        run(cmd)

        if path_wd is not None:
            cmd = (
                f"cp {os.path.join(path_wd, tile_mask_concat.split('/')[-1])}"
                f"{os.path.join(path_test, 'classif')}")
            run(cmd)
    return tile_mask_concat


def build_confidence_exp(img_classif_fusion: str, img_confidence: str,
                         img_classif: str) -> Tuple[str, str]:
    """
    IN :
        imgClassif_FUSION [string] : path to the classification merged with or
                                     without pixels with no label
        imgConfidence [list string] : paths to confidence map
        imgClassif [list string] : paths to images of classifications

    OUT :
        exp [string] : Mathematical expression
        il [string] : input img list to give to otbcli_BandMath

    WARNING: the list of images of classifications and the list of confidence
              map must have the same order.
        example :
            classif = ["cl1","cl2","cl3","cl4"]
            confidences = ["c1","c2","c3","c4"]

            'c1' must be the confidence map of the classification 'cl1' etc...
    """

    if len(img_confidence) != len(img_classif):
        raise Exception(
            "Error, the list of classification and the list of confidence map "
            "must have the same length")
    im_conf = []
    im_class = []
    im_ref = "im" + str(2 * len(img_confidence) + 1) + "b1"

    for i in range(len(img_confidence)):
        im_conf.append(f"im{i + 1}b1")
    for i in range(len(img_confidence), 2 * len(img_confidence)):
        im_class.append(f"im{i + 1}b1")
    # (c1>c2 and c1>c3 and c1>c4)?cl1:(c2>c1 and c2>c3 and c2>c4)?cl2:etc...
    # (c1>c2)?cl1:(c2>c1)?:cl2:0
    exp = im_ref + "!=0?" + im_ref + ":"
    for i, _ in enumerate(im_conf):
        tmp = []
        for j, _ in enumerate(im_conf):
            if im_conf[i] != im_conf[j]:
                tmp.append(im_conf[i] + ">" + im_conf[j])
        exp_tmp = " and ".join(tmp)
        exp += "(" + exp_tmp + ")?" + im_class[i] + ":"

    exp += im_class[0]

    # build images list
    il_str = ""
    for i, _ in enumerate(img_confidence):
        il_str += " " + img_confidence[i]
    for i, _ in enumerate(img_classif):
        il_str += " " + img_classif[i]
    il_str += " " + img_classif_fusion

    return exp, il_str


def get_nb_split_shape(model: str, config_model_path: str) -> int:
    """
    Parameters
    ----------
    model: string
    config_model_path: string
                     configuration file
    Return
    ------
    """
    from config import Config
    cfg = Config(config_model_path)
    fold = []

    for model_tile in cfg.AllModel:
        model_name = model_tile.modelName
        if model_name.split("f")[0] == model and len(
                model_name.split("f")) > 1:
            fold.append(int(model_name.split("f")[-1]))
    return max(fold)


# def noData(pathTest, pathFusion, fieldRegion, pathToImg, pathToRegion, N, cfg,
def undecision_management(path_test: str,
                          path_fusion: str,
                          field_region: str,
                          path_to_img: str,
                          path_to_region: str,
                          output_path: str,
                          no_label_management: str,
                          path_wd: str,
                          list_indices: List[str],
                          user_feat_path: str,
                          pix_type: str,
                          region_vec: Optional[str] = None,
                          user_feat_pattern: Optional[str] = None,
                          ds_sar_opt: Optional[bool] = False) -> None:
    """
    manage undecision comming from fusion of classifications
    Parameters
    ----------
    path_test: string
    path_fusion: string
    field_region: string
    path_to_img: string
    path_to_region: string
    region_vec: string
    output_path: string
    no_label_management: string
    path_wd: string
    list_indices: List[string],
    user_feat_path: string
    pix_type: string
    user_feat_pattern: string
    ds_sar_opt: bool
    Return
    ------
    None
    """

    stack_ind = fu.get_feat_stack_name(list_indices, user_feat_path,
                                       user_feat_pattern)

    suffix_pattern = ""
    if ds_sar_opt:
        suffix_pattern = "_DS"

    if region_vec:
        current_model = path_fusion.split("/")[-1].split("_")[3]
        config_model = os.path.join(output_path, "config_model",
                                    "configModel.cfg")
        n_fold = get_nb_split_shape(current_model, config_model)

    path_directory = path_test + "/classif"
    if path_wd is not None:
        working_dir = path_wd
        path_directory = path_wd
    else:
        working_dir = path_test + "/classif/MASK"

    current_tile = path_fusion.split("/")[-1].split("_")[0]

    shp_rname = path_to_region.split("/")[-1].replace(".shp", "")
    all_model = fu.FileSearch_AND(os.path.join(path_test, "model"), True,
                                  "model", ".txt")

    if region_vec is None:
        model_tile = gen_mask_region_by_tile(
            field_region, stack_ind, working_dir, current_tile, all_model,
            shp_rname, path_to_img, path_test,
            os.path.join(output_path, "config_model",
                         "configModel.cfg"), path_wd)
    elif region_vec and no_label_management == "maxConfidence":
        model_tile = path_fusion.split("/")[-1].split("_")[3]
    elif region_vec and no_label_management == "learningPriority":
        model_tile_tmp = path_fusion.split("/")[-1].split("_")[3]
        model_tile = []
        for i in range(n_fold):
            model_tile.append(f"{model_tile_tmp} f{i + 1}")

    if len(model_tile) == 0 or no_label_management == "maxConfidence":
        seed = os.path.split(path_fusion)[-1].split("_")[-1].split(".")[0]
        img_confidence = fu.FileSearch_AND(
            path_test + "/classif", True,
            "confidence_seed_" + str(seed) + suffix_pattern + ".tif",
            current_tile)

        img_classif = fu.FileSearch_AND(os.path.join(path_test, "classif"),
                                        True, "Classif_" + current_tile,
                                        f"seed_{seed}", suffix_pattern)
        img_data = os.path.join(
            path_directory, f"{current_tile}_FUSION_NODATA_seed{seed}.tif")
        if region_vec:
            img_confidence = fu.fileSearchRegEx(
                f"{path_test+os.sep}classif{os.sep}"
                f"{current_tile}_model_{model_tile}"
                f"f*_confidence_seed_{seed}{suffix_pattern}.tif")
            img_classif = fu.fileSearchRegEx(
                f"{path_test+os.sep}classif{os.sep}"
                f"Classif_{current_tile}_model_"
                f"{model_tile}f*_seed_"
                f"{seed}{suffix_pattern}.tif")
            img_data = (f"{path_directory+os.sep}Classif_"
                        f"{current_tile}_model_{model_tile}"
                        f"_seed_{seed}{suffix_pattern}.tif")

        img_confidence.sort()
        img_classif.sort()
        exp, il_str = build_confidence_exp(path_fusion, img_confidence,
                                           img_classif)
        cmd = (f"otbcli_BandMath -il {il_str} -out {img_data} {pix_type} "
               f"-exp '{exp}' ")
        run(cmd)
        if path_wd is not None:
            run(f"cp {img_data} {os.path.join(path_test, 'classif')}")

    elif len(model_tile) != 0 and no_label_management == "learningPriority":
        # Concaténation des classifications pour une tuile (qui a ou non
        # plusieurs régions) et Concaténation des masques de régions pour
        # une tuile (qui a ou non plusieurs régions)
        seed = os.path.split(path_fusion)[-1].split("_")[-1].split(".")[0]
        concat_out = (f"{os.path.join(path_test,  'classif')}"
                      f"{current_tile}_FUSION_concat_seed{seed}.tif")
        if region_vec:
            concat_out = (
                f"{os.path.join(path_test,  'classif')}"
                f"{current_tile}_FUSION_model_{model_tile[0].split('f')[0]}"
                f"concat_seed{seed}.tif")
        path_to_classif_concat = concat_classifs_one_tile(
            seed, current_tile, path_test, model_tile, concat_out, path_wd)

        pattern_mask = "*region_*_{current_tile}_NODATA.tif"
        classif_fusion_mask = fu.fileSearchRegEx(
            os.path.join(path_test, "classif", "MASK", pattern_mask))
        out_concat_mask = os.path.join(path_test, "classif",
                                       f"{current_tile}_MASK.tif")
        if region_vec:
            pattern_mask = ("*region_{model_tile[0].split('f')[0]}"
                            f"_{current_tile}.tif")
            classif_fusion_mask_tmp = fu.fileSearchRegEx(
                os.path.join(path_test, "classif", "MASK", pattern_mask))
            out_concat_mask = (f"{os.path.join(path_test, 'classif')}"
                               f"{current_tile}_MASK_model_"
                               f"{model_tile[0].split('f')[0]}.tif")
            classif_fusion_mask = []
            for i in range(n_fold):
                classif_fusion_mask.append(classif_fusion_mask_tmp[0])

        path_to_region_mask_concat = concat_region_one_tile(
            path_test, classif_fusion_mask, path_wd, out_concat_mask)

        # construction de la commande
        exp = ""
        im1 = path_fusion
        im2 = path_to_region_mask_concat
        im3 = path_to_classif_concat

        for i in range(len(classif_fusion_mask)):
            if i + 1 < len(classif_fusion_mask):
                exp = exp + "im2b" + str(i + 1) + ">=1?im3b" + str(i + 1) + ":"
            else:
                exp = exp + "im2b" + str(i + 1) + ">=1?im3b" + str(i +
                                                                   1) + ":0"
        exp = "im1b1!=0?im1b1:(" + exp + ")"

        img_data = (os.path.join(
            path_directory, f"{current_tile}_FUSION_"
            f"NODATA_seed{seed}.tif"))
        if region_vec:
            img_data = (f"{path_directory+os.sep}Classif_{current_tile}_model_"
                        f"{model_tile[0].split('f')[0]}_seed_{seed}.tif")

        cmd = (f'otbcli_BandMath -il {im1} {im2} {im3} -out + {img_data} '
               f'{pix_type} -exp "{exp}"')
        run(cmd)

        if path_wd is not None:
            run("cp {img_data} {path_test+os.sep}classif")


if __name__ == "__main__":

    PARSER = argparse.ArgumentParser(description="")
    PARSER.add_argument("-test.path",
                        help="Test's path",
                        dest="pathTest",
                        required=True)
    PARSER.add_argument(
        "-tile.fusion.path",
        help="path to the classification's images (with fusion)",
        dest="pathFusion",
        required=True)
    PARSER.add_argument("-region.field",
                        dest="fieldRegion",
                        help="region field into region shape",
                        required=True)
    PARSER.add_argument("-path.img",
                        dest="pathToImg",
                        help="path where all images are stored",
                        required=True)
    PARSER.add_argument("-path.region",
                        dest="pathToRegion",
                        help="path to the global region shape",
                        required=True)
    PARSER.add_argument("-N",
                        dest="N",
                        help="number of random sample(mandatory)",
                        type=int,
                        required=True)
    PARSER.add_argument("-output_path",
                        help="path to the output directory (mandatory)",
                        dest="output_path",
                        required=True)
    PARSER.add_argument("-no_label_meth",
                        dest="no_label_meth",
                        help="no label management rule",
                        choices=['maxConfidence', "learningPriority"],
                        required=True)
    PARSER.add_argument("--wd",
                        dest="pathWd",
                        help="path to the working directory",
                        default=None,
                        required=False)
    PARSER.add_argument("-list_feat",
                        nargs='+',
                        dest="list_features",
                        help="list containing features",
                        required=True)
    PARSER.add_argument("-user_feat_path",
                        dest="user_feat_path",
                        help="path to features provided by user",
                        required=True)
    PARSER.add_argument("-pixtype",
                        dest="pixtype",
                        help="pixel type",
                        choices=["uint8", "uint16", "float", "double"],
                        default="uint8",
                        required=False)
    PARSER.add_argument("-region_vec",
                        dest="region_vec",
                        help="a region shapefile (optional)",
                        required=False,
                        default=None)
    PARSER.add_argument("-patterns",
                        dest="patterns",
                        help="user feature pattern (optional)",
                        required=False,
                        default=None)
    PARSER.add_argument("-sar_fusion",
                        dest="sar_fusion",
                        help=("activate post classification fusion between "
                              "optical and SAR (optional)"),
                        required=False,
                        default=False)
    ARGS = PARSER.parse_args()

    undecision_management(ARGS.pathTest, ARGS.pathFusion, ARGS.fieldRegion,
                          ARGS.pathToImg, ARGS.pathToRegion, ARGS.output_path,
                          ARGS.no_label_meth, ARGS.pathWd, ARGS.list_feat,
                          ARGS.user_feat_path, ARGS.pixtype, ARGS.region_vec,
                          ARGS.patterns, ARGS.sar_fusion)
