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
from iota2.Learning import GetModel as GM
from iota2.Common import FileUtils as fu
from typing import Optional, List


# def generateStatModel(path_shapes: str,
def generate_stat_model(path_shapes: str,
                        path_to_tiles: str,
                        path_to_stats: str,
                        path_to_cmd_stats: str,
                        output_path: str,
                        classifier: str,
                        list_indices: List[str],
                        user_feat_path: str,
                        user_feat_pattern: Optional[str] = None) -> str:
    """
    Parameters
    ----------
    path_shapes: string
    path_to_tiles: string
    path_to_stats: string
    path_to_cmd_stats: string
    output_path: string
    classifier: string
    list_indices: string
    user_feat_path: string
    user_feat_pattern: string
    Return
    ------
    string: the otb command for compute statistics
    """
    all_cmd = []

    all_shape = fu.fileSearchRegEx(output_path + "/dataAppVal/*.shp")
    for current_shape in all_shape:
        # name = currentShape.split("/")[-1]
        path, name = os.path.split(current_shape)
        if len(name.split("_")[2].split("f")) > 1:
            fold = name.split("_")[2].split("f")[-1]
            # path = currentShape.split("/")[0]
            name_to_rm = name.replace("f" + fold, "").replace(".shp", "")
            print(f"remove : {os.path.join(path,name_to_rm+'.shp')}")
            if os.path.exists(os.path.join(path, name_to_rm + ".shp")):
                fu.removeShape(os.path.join(path, name_to_rm),
                               [".prj", ".shp", ".dbf", ".shx"])

    mod_tiles = GM.getModel(path_shapes)
    stack_ind = fu.get_feat_stack_name(list_indices, user_feat_path,
                                       user_feat_pattern)

    for mod, tiles in mod_tiles:
        allpath = ""
        for tile in tiles:
            path_to_feat = os.path.join(path_to_tiles, tile, "Final",
                                        stack_ind)
            allpath = allpath + " " + path_to_feat + " "
        if classifier == "svm":
            cmd = (f"otbcli_ComputeImagesStatistics -il {allpath} -out "
                   f"{path_to_stats}/Model_{mod}.xml")
        else:
            cmd = "echo 'radom forest does not need stats'"
        all_cmd.append(cmd)

    fu.writeCmds(path_to_cmd_stats + "/stats.txt", all_cmd)
    return all_cmd


if __name__ == "__main__":

    PARSER = argparse.ArgumentParser(
        description=
        "This function compute the statistics for a model compose by N tiles")
    PARSER.add_argument(
        "-shapesIn",
        help=
        "path to the folder which ONLY contains shapes for the classification (learning and validation) (mandatory)",
        dest="pathShapes",
        required=True)
    PARSER.add_argument("-tiles.path",
                        dest="pathToTiles",
                        help="path where tiles are stored (mandatory)",
                        required=True)
    PARSER.add_argument(
        "-Stats.out",
        dest="pathToStats",
        help="path where all statistics will be stored (mandatory)",
        required=True)
    PARSER.add_argument(
        "-Stat.out.cmd",
        dest="pathToCmdStats",
        help=
        "path where all statistics cmd will be stored in a text file(mandatory)",
        required=True)
    PARSER.add_argument(
        "-conf",
        help=
        "path to the configuration file which describe the learning method (mandatory)",
        dest="pathConf",
        required=True)
    ARGS = PARSER.parse_args()

    # load configuration file
    from iota2.Common.ServiceConfigFile import ServiceConfigFile as SCF
    CFG = SCF.serviceConfigFile(ARGS.pathConf)
    USER_FEAT_PATTERN = CFG.getParam("userFeat", "patterns")
    if "none" in USER_FEAT_PATTERN.lower():
        USER_FEAT_PATTERN = None
    generate_stat_model(ARGS.pathShapes, ARGS.pathToTiles,
                        ARGS.pathToStats, ARGS.pathToCmdStats,
                        CFG.getParam("chain", "outputPath"),
                        CFG.getParam('argTrain', 'classifier'),
                        CFG.getParam("GlobChain", "features"),
                        CFG.getParam("chain",
                                     "userFeatPath"), USER_FEAT_PATTERN)
