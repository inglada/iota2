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

import os
import re
from osgeo import gdal, ogr, osr
from iota2.Common import FileUtils as fu
from iota2.Common.Utils import run


# def launchClassification(model, path_cfg, output_path: str,
def write_classification_command(model, path_cfg, output_path: str,
                                 classifier_name: str,
                                 classification_mode: str,
                                 nomenclature_path: str, stat, pathToRT,
                                 pathToImg, pathToRegion, fieldRegion,
                                 pathToCmdClassif, pathOut, RAM, pathWd):
    """
    Parameters
    ----------
    output_path : str
        iota2 output directory

    """
    scriptPath = os.path.join(fu.get_iota2_project_dir(), "iota2")
    pixType = fu.getOutputPixType(nomenclature_path)
    AllCmd = []

    maskFiles = pathOut + "/MASK"
    if not os.path.exists(maskFiles):
        run("mkdir " + maskFiles)

    if pathToRegion is None:
        pathToRegion = os.path.join(output_path, "MyRegion.shp")

    shpRName = pathToRegion.split("/")[-1].replace(".shp", "")

    AllModel_tmp = fu.FileSearch_AND(model, True, "model", ".txt")
    AllModel = fu.fileSearchRegEx(model + "/*model*.txt")

    for currentFile in AllModel_tmp:
        if currentFile not in AllModel:
            os.remove(currentFile)

    for path in AllModel:
        model = path.split("/")[-1].split("_")[1]
        tiles = fu.getListTileFromModel(
            model, output_path + "/config_model/configModel.cfg")
        model_Mask = model
        if re.search("model_.*f.*_", path.split("/")[-1]):
            model_Mask = path.split("/")[-1].split("_")[1].split("f")[0]
        seed = path.split("/")[-1].split("_")[-1].replace(".txt", "")
        suffix = ""
        if "SAR.txt" in os.path.basename(path):
            seed = path.split("/")[-1].split("_")[-2]
            suffix = "_SAR"
        tilesToEvaluate = tiles

        # construction du string de sortie
        for tile in tilesToEvaluate:
            pathToFeat = fu.FileSearch_AND(pathToImg + "/" + tile + "/tmp/",
                                           True, "MaskCommunSL", ".tif")[0]
            maskSHP = pathToRT + "/" + shpRName + "_region_" + model_Mask + "_" + tile + ".shp"
            maskTif = shpRName + "_region_" + model_Mask + "_" + tile + ".tif"
            CmdConfidenceMap = ""
            confidenceMap_name = "{}_model_{}_confidence_seed_{}{}.tif".format(
                tile, model, seed, suffix)
            CmdConfidenceMap = " -confmap " + os.path.join(
                pathOut, confidenceMap_name)

            if not os.path.exists(maskFiles + "/" + maskTif):
                pathToMaskCommun = pathToImg + "/" + tile + "/tmp/" + "MaskCommunSL" + ".shp"
                #cas cluster
                if pathWd != None:
                    maskFiles = pathWd
                nameOut = fu.ClipVectorData(maskSHP, pathToMaskCommun,
                                            maskFiles,
                                            maskTif.replace(".tif", ""))
                cmdRaster = "otbcli_Rasterization -in "+nameOut+" -mode attribute -mode.attribute.field "+\
                        fieldRegion+" -im "+pathToFeat+" -out "+maskFiles+"/"+maskTif
                if "fusion" in classification_mode:
                    cmdRaster = "otbcli_Rasterization -in "+nameOut+" -mode binary -mode.binary.foreground 1 -im "+\
                                pathToFeat+" -out "+maskFiles+"/"+maskTif
                run(cmdRaster)
                if pathWd != None:
                    run("cp " + pathWd + "/" + maskTif + " " + pathOut +
                        "/MASK")
                    os.remove(pathWd + "/" + maskTif)

            out = pathOut + "/Classif_" + tile + "_model_" + model + "_seed_" + seed + suffix + ".tif"

            #hpc case
            if pathWd != None:
                out = "$TMPDIR/Classif_" + tile + "_model_" + model + "_seed_" + seed + suffix + ".tif"
                CmdConfidenceMap = " -confmap $TMPDIR/" + confidenceMap_name

            appli = "python " + scriptPath + "/Classification/ImageClassifier.py -conf " + path_cfg + " "
            pixType_cmd = " -pixType " + pixType
            if pathWd != None:
                pixType_cmd = pixType_cmd + " --wd $TMPDIR "
            cmd = appli + " -in " + pathToFeat + " -model " + path + " -mask " + pathOut + "/MASK/" + maskTif + " -out " + out + " " + pixType_cmd + " -ram " + str(
                RAM) + " " + CmdConfidenceMap

            # add stats if svm
            if "svm" in classifier_name.lower():
                model_statistics = os.path.join(
                    stat, "Model_{}_seed_{}.xml".format(model, seed))
                cmd = "{} -imstat {}".format(cmd, model_statistics)
            AllCmd.append(cmd)
    fu.writeCmds(pathToCmdClassif + "/class.txt", AllCmd)
    return AllCmd
