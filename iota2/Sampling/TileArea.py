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
import logging
import os
from osgeo import gdal, ogr, osr
from iota2.Common import FileUtils as fu
from iota2.Common.Utils import run

LOGGER = logging.getLogger(__name__)


def AddFieldModel(shpIn, modNum, fieldOut, logger=LOGGER):
    """
        add a field to a shapeFile and for every feature, add an ID
        IN :
            - shpIn : a shapeFile
            - modNum : the number to associate to features
            - fieldOut : the new field name
        OUT :
            - an update of the shape file in
    """
    source = ogr.Open(shpIn, 1)
    layer = source.GetLayer()
    new_field = ogr.FieldDefn(fieldOut, ogr.OFTInteger)
    layer.CreateField(new_field)

    for feat in layer:
        if feat.GetGeometryRef():
            layer.SetFeature(feat)
            feat.SetField(fieldOut, modNum)
            layer.SetFeature(feat)
        else:
            logger.debug(f"feature {feat.GetFID()} has not geometry")


def CreateModelShapeFromTiles(tilesModel, pathTiles, pathOut, OutSHPname,
                              fieldOut, pathWd):
    """
    create one shapeFile where all features belong to a model number according to the model description

    IN :
        - tilesModel : a list of list which describe which tile belong to which model
            ex : for 3 models
                tile model 1 : D0H0,D0H1
                tile model 2 : D0H2,D0H3
                tile model 3 : D0H4,D0H5,D0H6

                tilesModel = [["D0H0","D0H1"],["D0H2","D0H3"],["D0H4","D0H5","D0H6"]]
        - pathTiles : path to the tile's envelope with priority consideration
            ex : /xx/x/xxx/x
            /!\ the folder which contain the envelopes must contain only the envelopes   <========
        - pathOut : path to store the resulting shapeFile
            ex : x/x/x/xxx
        - OutSHPname : the name of the resulting shapeFile
            ex : "model"
        - fieldOut : the name of the field which will contain the model number
            ex : "Mod"
        - pathWd : path to working directory (not mandatory, due to cluster's architecture default = None)

    OUT :
        a shapeFile which contains for all feature the model number which it belong to
    """
    if pathWd is None:
        pathToTMP = pathOut + "/AllTMP"
    else:
        # HPC case
        pathToTMP = pathWd
    if not os.path.exists(pathToTMP):
        run("mkdir " + pathToTMP)

    to_remove = []
    for i in range(len(tilesModel)):
        for j in range(len(tilesModel[i])):
            to_remove.append(
                fu.renameShapefile(pathTiles, tilesModel[i][j], "", "",
                                   pathToTMP))

    AllTilePath = []
    AllTilePath_ER = []

    for i in range(len(tilesModel)):
        for j in range(len(tilesModel[i])):
            try:
                ind = AllTilePath.index(pathTiles + "/" + tilesModel[i][j] +
                                        ".shp")
            except ValueError:
                AllTilePath.append(pathToTMP + "/" + tilesModel[i][j] + ".shp")
                AllTilePath_ER.append(pathToTMP + "/" + tilesModel[i][j] +
                                      "_ERODE.shp")

    for i in range(len(tilesModel)):
        for j in range(len(tilesModel[i])):
            currentTile = pathToTMP + "/" + tilesModel[i][j] + ".shp"
            AddFieldModel(currentTile, i + 1, fieldOut)

    for path in AllTilePath:
        fu.erodeShapeFile(path, path.replace(".shp", "_ERODE.shp"), 0.1)

    fu.mergeVectors(OutSHPname, pathOut, AllTilePath_ER)
    if not pathWd:
        run("rm -r " + pathToTMP)
    else:
        for rm in to_remove:
            fu.removeShape(rm.replace(".shp", ""),
                           [".prj", ".shp", ".dbf", ".shx"])


def generate_region_shape(envelope_directory: str, output_region_file: str,
                          out_field_name: str, i2_output_path: str,
                          working_directory: str) -> None:
    """generate regions shape

    envelope_directory: str
        directory containing all iota2 tile's envelope
    output_region_file: str
        output file
    out_field_name: str
        output field containing region
    i2_output_path: str
        iota2 output path
    working_directory: str
        path to a working directory
    """

    region = []
    all_tiles = fu.FileSearch_AND(envelope_directory, False, ".shp")
    region.append(all_tiles)

    if not output_region_file:
        output_region_file = os.path.join(i2_output_path, "MyRegion.shp")

    p_f = output_region_file.replace(" ", "").split("/")
    out_name = p_f[-1].split(".")[0]

    path_mod = ""
    for i in range(1, len(p_f) - 1):
        path_mod = path_mod + "/" + p_f[i]

    CreateModelShapeFromTiles(region, envelope_directory, path_mod, out_name,
                              out_field_name, working_directory)


if __name__ == "__main__":

    PARSER = argparse.ArgumentParser(
        description=("This function allow you to create "
                     "a shape by tile for a given area and a given region"))
    PARSER.add_argument("-envelope_directory",
                        dest="envelope_directory",
                        help="directory containing all iota2 tile's envelope",
                        required=True)
    PARSER.add_argument("-output_region_file",
                        dest="output_region_file",
                        help="output file (shapeFile format)",
                        required=True)
    PARSER.add_argument("-out_field_name",
                        dest="out_field_name",
                        help="output field containing region",
                        required=True)
    PARSER.add_argument("-i2_output_path",
                        dest="i2_output_path",
                        help="iota2 output directory",
                        required=True)
    PARSER.add_argument("-working_directory",
                        dest="working_directory",
                        help="path to a working directory",
                        required=True)

    ARGS = PARSER.parse_args()

    generate_region_shape(ARGS.envelope_directory, ARGS.output_region_file,
                          ARGS.out_field_name, ARGS.i2_output_path,
                          ARGS.working_directory)
