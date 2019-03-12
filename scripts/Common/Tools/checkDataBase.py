#!/usr/bin/python
#-*- coding: utf-8 -*-

# =========================================================================
#   Program:   vector tools
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


def str2bool(v):
    """
    usage : use in argParse as function to parse options

    IN:
    v [string]
    out [bool]
    """
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def vector_name_check(input_vector):
    """
    check if first character is a letter
    """
    import os
    import string
    avail_characters = string.ascii_letters
    first_character = os.path.basename(input_vector)[0]
    return True if first_character in avail_characters else False


def remove_invalid_features(shapefile):
    
    # remove invalid features
    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = driver.Open(shapefile, 1)
    if not dataSource:
        raise
    layer = dataSource.GetLayer()
    count=layer.GetFeatureCount()
    for feature in range(count):
        feat = layer[feature]
        geom = feat.GetGeometryRef()
        if not geom:
            layer.DeleteFeature(feature)
    layer.ResetReading()


def do_check(input_vector, output_vector, data_field, epsg, pix_area,
             pix_area_threshold, do_corrections):
    """
    """
    import os
    from VectorTools import checkGeometryAreaThreshField
    from VectorTools.vector_functions import getFields
    from VectorTools.vector_functions import getFieldType
    from VectorTools.vector_functions import checkEmptyGeom

    input_vector_fields = getFields(input_vector)

    errors = []
    # check vector's name
    name_check = vector_name_check(input_vector)
    if name_check is False:
        error_msg = "file's name not correct"
        errors.append(error_msg)

    # check field
    if not data_field in input_vector_fields:
        error_msg = "field '{}' not found".format(data_field)
        errors.append(error_msg)

    # check field's type
    label_field_type = getFieldType(input_vector, data_field)
    if not label_field_type is int:
        error_msg = "field '{}' is not containing intergers".format(data_field)
        errors.append(error_msg)

    # geometries checks 
    shape_no_empty_name = "no_empty.shp"
    shape_no_empty_dir = os.path.split(input_vector)[0]
    shape_no_empty = os.path.join(shape_no_empty_dir, shape_no_empty_name)
    _, empty_geom_number = checkEmptyGeom(input_vector, do_corrections, shape_no_empty)
    if empty_geom_number != 0:
        error_msg = "'{}' contains empty geometries".format(input_vector)
        if do_corrections:
            error_msg = "{} and they were removed".format(error_msg)
        errors.append(error_msg)

    # suppression des doubles géométries
    #~ DeleteDuplicateGeometriesSqlite.deleteDuplicateGeometriesSqlite(outShapefileGeom)
    #~ DeleteDuplicateGeometriesSqlite.deleteDuplicateGeometriesSqlite(inputShapeFile, outShapefileGeom, do_corrections)
    
    # Suppression des multipolygons
    #~ MultiPolyToPoly.multipoly2poly(outShapefileGeom, shapefileNoDupspoly)
    #~ MultiPolyToPoly.multipoly2poly(inputshape, outputShape, do_corrections)

    # recalcul des superficies, on est obligé d'ajouter une nouvelle colonne ?
    #~ AddFieldArea.addFieldArea(shapefileNoDupspoly, pixelArea)

    # Filter by Area
    #~ SelectBySize.selectBySize(shapefileNoDupspoly, 'Area', pix_thresh, outshape)
    #~ SelectBySize.selectBySize(shapefileNoDupspoly, pix_thresh, outshape, do_corrections)

    # Check valid geometry
    #~ vf.checkValidGeom(outshape)
    #~ vf.checkValidGeom(inputShape, outshape)

    # remove features with empty geometries
    #~ remove_invalid_features(shapefile)
    #~ remove_invalid_features(shapefile, outputshape, do_corrections)
    return errors

if __name__ == "__main__":
    description=("This function allow user if the inpute dataBase can be used by IOTA²'s\n"
                 "\t- remove empty geometries\n"
                 "\t- remove duplicate geometries\n"
                 "\t- split multi-polygons to polygons\n"
                 "\t- polygons could be filtered by Area\n"
                 "\t- check projection\n"
                 "\t- check if the label field is integer type")
    parser = argparse.ArgumentParser(description)
    parser.add_argument("-in.vector",
                        help="absolute path to the vector (mandatory)",
                        dest="input_vector", required=True)
    parser.add_argument("-out.vector",
                        help="output vector",
                        dest="output_vector", required=False,
                        default=None)
    parser.add_argument("-dataField",
                        help="field containing labels (mandatory)",
                        dest="data_field", required=True)
    parser.add_argument("-epsg",
                        help="EPSG's code (mandatory)",
                        dest="epsg", required=True,
                        type=int)
    parser.add_argument("-pixArea",
                        help="pixel's area (mandatory)",
                        dest="pix_area", required=True,
                        type=float)
    parser.add_argument("-pixAreaThreshold",
                        help="pixel's area threshold",
                        dest="pix_area_threshold", required=False,
                        default=0.0, type=float)
    parser.add_argument("-doCorrections",
                        help="enable corrections (default = False)",
                        dest="do_corrections", required=False,
                        default=False, type=str2bool)
    args = parser.parse_args()

    do_check(args.input_vector, args.output_vector, args.data_field,
             args.epsg, args.pix_area, args.pix_area_threshold,
             args.do_corrections)
