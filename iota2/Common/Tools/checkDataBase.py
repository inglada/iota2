#!/usr/bin/env python3
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
import os
import sys

import argparse
from typing import List, Optional


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


def get_geometries_by_area(input_vector: str,
                           area: float,
                           driver_name: Optional[str] = "ESRI Shapefile"
                           ) -> List:
    """get geometries smaller than the area

    sub geometries of a MULTIPOLYGONS are checked and returned either
    """
    from osgeo import ogr
    driver = ogr.GetDriverByName(driver_name)
    data_src = driver.Open(input_vector, 0)
    layer_src = data_src.GetLayer()
    output_geoms = []
    for feature in layer_src:
        geom = feature.GetGeometryRef()
        for geom_part in geom:
            geom_area = geom_part.GetArea()
            if geom_area < area:
                output_geoms.append((geom_part.Clone(), geom_area))
    return output_geoms


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
    from osgeo import ogr
    # remove invalid features
    none_geom = 0
    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = driver.Open(shapefile, 1)
    if not dataSource:
        raise
    layer = dataSource.GetLayer()
    count = layer.GetFeatureCount()
    for feature in range(count):
        feat = layer[feature]
        geom = feat.GetGeometryRef()
        if not geom:
            none_geom += 1
            layer.DeleteFeature(feature)
    layer.ResetReading()
    return none_geom


def check_region_shape(input_vector,
                       output_vector,
                       field,
                       epsg,
                       do_corrections,
                       display=False):
    """
    """
    from iota2.Common import ServiceError
    from iota2.Common.FileUtils import cpShapeFile
    from iota2.VectorTools.vector_functions import getFields
    from iota2.VectorTools.vector_functions import getFieldType
    from iota2.VectorTools.vector_functions import get_vector_proj
    from iota2.VectorTools.vector_functions import checkEmptyGeom
    from iota2.VectorTools.vector_functions import checkValidGeom
    from iota2.VectorTools.DeleteDuplicateGeometriesSqlite import deleteDuplicateGeometriesSqlite

    area_threshold = 0.1
    input_vector_fields = getFields(input_vector)
    errors = []

    # check vector's projection
    vector_projection = get_vector_proj(input_vector)
    if not int(epsg) == int(vector_projection):
        error_msg = "{} projection ({}) incorrect".format(
            input_vector, vector_projection)
        errors.append(ServiceError.invalidProjection(error_msg))

    # check vector's name
    name_check = vector_name_check(input_vector)
    if name_check is False:
        error_msg = "{} file's name not correct, it must start with an ascii letter".format(
            input_vector)
        errors.append(ServiceError.namingConvention(error_msg))

    # check field
    if not field in input_vector_fields:
        errors.append(ServiceError.missingField(input_vector, field))

    # check field's type
    label_field_type = getFieldType(input_vector, field)
    if not label_field_type is str:
        errors.append(ServiceError.fieldType(input_vector, field, str))

    # geometries checks
    shape_no_empty_name = "no_empty.shp"
    shape_no_empty_dir = os.path.split(input_vector)[0]
    shape_no_empty = os.path.join(shape_no_empty_dir, shape_no_empty_name)
    shape_no_empty, empty_geom_number = checkEmptyGeom(
        input_vector,
        do_corrections=do_corrections,
        output_file=shape_no_empty)
    if empty_geom_number != 0:
        error_msg = "'{}' contains {} empty geometries".format(
            input_vector, empty_geom_number)
        errors.append(ServiceError.emptyGeometry(error_msg))

    # remove duplicates features
    shape_no_duplicates_name = "no_duplicates.shp"
    shape_no_duplicates_dir = os.path.split(input_vector)[0]
    shape_no_duplicates = os.path.join(shape_no_duplicates_dir,
                                       shape_no_duplicates_name)

    shape_no_duplicates, duplicated_features = deleteDuplicateGeometriesSqlite(
        shape_no_empty, do_corrections, shape_no_duplicates, quiet_mode=True)
    if duplicated_features != 0:
        error_msg = "'{}' contains {} duplicated features".format(
            input_vector, duplicated_features)
        errors.append(ServiceError.duplicatedFeatures(error_msg))

    # Check valid geometry
    shape_valid_geom_name = "valid_geom.shp"
    shape_valid_geom_dir = os.path.split(input_vector)[0]
    shape_valid_geom = os.path.join(shape_valid_geom_dir,
                                    shape_valid_geom_name)
    shape_valid_geom = output_vector if output_vector else shape_valid_geom

    input_valid_geom_shape = shape_no_multi if do_corrections else shape_no_duplicates
    cpShapeFile(input_valid_geom_shape.replace(".shp", ""),
                shape_valid_geom.replace(".shp", ""),
                extensions=[".prj", ".shp", ".dbf", ".shx"])

    shape_valid_geom, invalid_geom, invalid_geom_corrected = checkValidGeom(
        shape_valid_geom, display=False)
    # remove features with None geometries
    none_geoms = remove_invalid_features(shape_valid_geom)
    invalid_geom += none_geoms

    if invalid_geom != 0:
        error_msg = "'{}' contains {} invalid geometries".format(
            input_vector, invalid_geom)
        errors.append(ServiceError.invalidGeometry(error_msg))

    nb_too_small_geoms = len(
        get_geometries_by_area(input_vector,
                               area=area_threshold,
                               driver_name="ESRI Shapefile"))
    if nb_too_small_geoms != 0:
        errors.append(
            ServiceError.tooSmallRegion(input_vector, area_threshold,
                                        nb_too_small_geoms))
    return errors


def check_ground_truth(input_vector,
                       output_vector,
                       data_field,
                       epsg,
                       do_corrections,
                       display=False):
    """
    """
    import os
    from iota2.Common.FileUtils import removeShape
    from iota2.Common.FileUtils import cpShapeFile
    from iota2.VectorTools import checkGeometryAreaThreshField
    from iota2.VectorTools.vector_functions import getFields
    from iota2.VectorTools.vector_functions import getFieldType
    from iota2.VectorTools.vector_functions import checkEmptyGeom
    from iota2.VectorTools.vector_functions import get_vector_proj
    from iota2.VectorTools.vector_functions import checkValidGeom
    from iota2.VectorTools.DeleteDuplicateGeometriesSqlite import deleteDuplicateGeometriesSqlite
    from iota2.VectorTools.MultiPolyToPoly import multipoly2poly
    from iota2.Common import ServiceError
    tmp_files = []
    input_vector_fields = getFields(input_vector)

    errors = []
    # check vector's projection
    vector_projection = get_vector_proj(input_vector)
    if not int(epsg) == int(vector_projection):
        error_msg = "{} projection ({}) incorrect".format(
            input_vector, vector_projection)
        errors.append(ServiceError.invalidProjection(error_msg))

    # check vector's name
    name_check = vector_name_check(input_vector)
    if name_check is False:
        error_msg = "file's name not correct, it must start with an ascii letter"
        errors.append(ServiceError.namingConvention(error_msg))

    # check field
    if not data_field in input_vector_fields:
        errors.append(ServiceError.missingField(input_vector, data_field))
    else:
        # check field's type
        label_field_type = getFieldType(input_vector, data_field)
        if not label_field_type is int:
            errors.append(ServiceError.fieldType(input_vector, data_field,
                                                 int))

    # geometries checks
    shape_no_empty_name = "no_empty.shp"
    shape_no_empty_dir = os.path.split(input_vector)[0]
    shape_no_empty = os.path.join(shape_no_empty_dir, shape_no_empty_name)
    shape_no_empty, empty_geom_number = checkEmptyGeom(
        input_vector,
        do_corrections=do_corrections,
        output_file=shape_no_empty)

    if empty_geom_number != 0:
        error_msg = "'{}' contains {} empty geometries".format(
            input_vector, empty_geom_number)
        if do_corrections:
            error_msg = "{} and they were removed".format(error_msg)
        errors.append(ServiceError.emptyGeometry(error_msg))
    tmp_files.append(shape_no_empty)

    # remove duplicates features
    shape_no_duplicates_name = "no_duplicates.shp"
    shape_no_duplicates_dir = os.path.split(input_vector)[0]
    shape_no_duplicates = os.path.join(shape_no_duplicates_dir,
                                       shape_no_duplicates_name)

    shape_no_duplicates, duplicated_features = deleteDuplicateGeometriesSqlite(
        shape_no_empty, do_corrections, shape_no_duplicates, quiet_mode=True)
    if duplicated_features != 0:
        error_msg = "'{}' contains {} duplicated features".format(
            input_vector, duplicated_features)
        if do_corrections:
            error_msg = "{} and they were removed".format(error_msg)
        errors.append(ServiceError.duplicatedFeatures(error_msg))
    tmp_files.append(shape_no_duplicates)

    # remove multipolygons
    shape_no_multi_name = "no_multi.shp"
    shape_no_multi_dir = os.path.split(input_vector)[0]
    shape_no_multi = os.path.join(shape_no_multi_dir, shape_no_multi_name)

    multipolygons_number = multipoly2poly(shape_no_duplicates, shape_no_multi,
                                          do_corrections)
    if multipolygons_number != 0:
        error_msg = "'{}' contains {} MULTIPOLYGON".format(
            input_vector, multipolygons_number)
        if do_corrections:
            error_msg = "{} and they were removed".format(error_msg)
        errors.append(ServiceError.containsMultipolygon(error_msg))
    tmp_files.append(shape_no_multi)

    # Check valid geometry
    shape_valid_geom_name = "valid_geom.shp"
    shape_valid_geom_dir = os.path.split(input_vector)[0]
    shape_valid_geom = os.path.join(shape_valid_geom_dir,
                                    shape_valid_geom_name)
    shape_valid_geom = output_vector if output_vector else shape_valid_geom

    input_valid_geom_shape = shape_no_multi if do_corrections else shape_no_duplicates
    cpShapeFile(input_valid_geom_shape.replace(".shp", ""),
                shape_valid_geom.replace(".shp", ""),
                extensions=[".prj", ".shp", ".dbf", ".shx"])

    shape_valid_geom, invalid_geom, invalid_geom_corrected = checkValidGeom(
        shape_valid_geom, display=False)
    # remove features with None geometries
    none_geoms = remove_invalid_features(shape_valid_geom)
    invalid_geom += none_geoms

    if invalid_geom != 0:
        error_msg = "'{}' contains {} invalid geometries".format(
            input_vector, invalid_geom)
        errors.append(ServiceError.invalidGeometry(error_msg))
    if output_vector is not None:
        tmp_files.append(shape_valid_geom)
    for tmp_file in tmp_files:
        if tmp_file is not input_vector and os.path.exists(tmp_file):
            removeShape(tmp_file.replace(".shp", ""),
                        [".prj", ".shp", ".dbf", ".shx"])
    if display:
        print("\n".join(errors))
    return errors


if __name__ == "__main__":
    parent = os.path.abspath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
    iota2_scripts_dir = os.path.abspath(os.path.join(parent, os.pardir))

    if not iota2_scripts_dir in sys.path:
        sys.path.append(iota2_scripts_dir)

    description = (
        "This function allow user if the inpute dataBase can be used by IOTA²'s\n"
        "\t- remove empty geometries\n"
        "\t- remove duplicate geometries\n"
        "\t- split multi-polygons to polygons\n"
        "\t- check projection\n"
        "\t- check vector's name\n"
        "\t- check if the label field is integer type")
    parser = argparse.ArgumentParser(description)
    parser.add_argument("-in.vector",
                        help="absolute path to the vector (mandatory)",
                        dest="input_vector",
                        required=True)
    parser.add_argument("-out.vector",
                        help="output vector",
                        dest="output_vector",
                        required=False,
                        default=None)
    parser.add_argument("-dataField",
                        help="field containing labels (mandatory)",
                        dest="data_field",
                        required=True)
    parser.add_argument("-epsg",
                        help="EPSG's code (mandatory)",
                        dest="epsg",
                        required=True,
                        type=int)
    parser.add_argument("-doCorrections",
                        help="enable corrections (default = False)",
                        dest="do_corrections",
                        required=False,
                        default=False,
                        type=str2bool)
    args = parser.parse_args()

    do_check(args.input_vector, args.output_vector, args.data_field, args.epsg,
             args.do_corrections)
