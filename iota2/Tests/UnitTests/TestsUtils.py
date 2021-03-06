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
from typing import List, Optional
from iota2.Tests.UnitTests.tests_utils.tests_utils_rasters import array_to_raster
from iota2.Tests.UnitTests.tests_utils.tests_utils_rasters import fun_array


def add_empty_geom(db_path, driver_name: Optional[str] = "ESRI Shapefile"):
    """add inplace an empty geometry
    """
    raise Exception("add_empty_geom does not work")

    import osgeo.ogr as ogr

    driver = ogr.GetDriverByName(driver_name)
    data_src = driver.Open(db_path, 1)
    layer_src = data_src.GetLayer()

    field_name = layer_src.GetLayerDefn().GetFieldDefn(0).GetName()
    field_type = layer_src.GetLayerDefn().GetFieldDefn(0).GetTypeName()

    new_feature = ogr.Feature(layer_src.GetLayerDefn())
    empty_geom = ogr.Geometry(type=ogr.wkbPolygon)
    print(empty_geom.IsEmpty())

    if "Interger" in field_type:
        new_feature.SetField(field_name, 1)
    else:
        new_feature.SetField(field_name, "1")
    new_feature.SetGeometry(empty_geom)
    layer_src.CreateFeature(new_feature)
    layer_src.SyncToDisk()
    new_feature = layer_src = data_src = None


def compare_vector_raster(in_vec: str, vec_field: str, field_values: List[int],
                          in_img: str) -> List[int]:
    """return img values at vector positions where field is equal to a given values
    """
    import numpy as np
    from Common.OtbAppBank import CreateRasterizationApplication

    rasterization = CreateRasterizationApplication({
        "in":
        in_vec,
        "im":
        in_img,
        "mode":
        "attribute",
        "mode.attribute.field":
        vec_field
    })
    rasterization.Execute()

    vec_array = rasterization.GetImageAsNumpyArray("out")
    y_coords, x_coords = np.where(np.isin(vec_array, field_values))
    classif_array = rasterToArray(in_img)
    values = []
    for y_coord, x_coord in zip(y_coords, x_coords):
        values.append(classif_array[y_coord][x_coord])
    return values


def test_raster_unique_value(raster_path, value, band_num=-1):
    """test if a raster contains an unique value

    Parameters
    ----------
    raster_path : string
        raster path
    value : int
        value to check
    band_num : int
        raster band to verify, from 1 to N (default=-1, mean all bands)

    Return
    ------
    bool
        True if the raster contains an unique value, else False
    """
    import numpy as np
    np_array = rasterToArray(raster_path)
    if band_num != -1:
        # bands start at index 0
        band_num -= 1
        np_array = np_array[band_num]
    unique, counts = np.unique(np_array, return_counts=True)

    return (len(unique == 1) and value == unique[0])


def random_ground_truth_generator(output_shape,
                                  data_field,
                                  number_of_class,
                                  region_field=None,
                                  min_cl_samples=10,
                                  max_cl_samples=100,
                                  epsg_code=2154,
                                  set_geom=True):
    """generate a shape file with random integer values in appropriate field

    Parameters
    ----------
    output_shape : string
        output shapeFile
    data_field : string
        data field
    number_of_class : int
        number of class
    region_field : string
        region field
    min_cl_samples : int
        minimum samples per class
    max_cl_samples : int
        maximum samples per class
    epsg_code : int
        epsg code
    set_geom : bool
        set a fake geometry
    """
    message = "max_cl_samples must be superior to min_cl_samples"
    assert max_cl_samples > min_cl_samples, message

    import random
    import osgeo.ogr as ogr
    import osgeo.osr as osr

    label_number = []
    for class_label in range(number_of_class):
        label_number.append(
            (class_label + 1, random.randrange(min_cl_samples,
                                               max_cl_samples)))

    driver = ogr.GetDriverByName("ESRI Shapefile")
    if os.path.exists(output_shape):
        driver.DeleteDataSource(output_shape)

    data_source = driver.CreateDataSource(output_shape)

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg_code)

    layer_name, _ = os.path.splitext(os.path.basename(output_shape))
    layer = data_source.CreateLayer(layer_name, srs, geom_type=ogr.wkbPolygon)
    data_field_name = ogr.FieldDefn(data_field, ogr.OFTInteger)
    data_field_name.SetWidth(10)
    layer.CreateField(data_field_name)
    if region_field:
        region_field_name = ogr.FieldDefn(region_field, ogr.OFTString)
        region_field_name.SetWidth(10)
        layer.CreateField(region_field_name)

    for class_label, features_num in label_number:
        for feat_cpt in range(features_num):
            feature = ogr.Feature(layer.GetLayerDefn())
            feature.SetField(data_field, class_label)
            if region_field:
                feature.SetField(region_field, "1")
            wkt = "POLYGON ((1 2, 2 2, 2 1, 1 1, 1 2))"
            point = ogr.CreateGeometryFromWkt(wkt)
            if set_geom:
                feature.SetGeometry(point)
            layer.CreateFeature(feature)
            feature = None
    data_source = None


def compute_brightness_from_vector(input_vector):
    """compute brightness from a vector of values

    Parameters
    ----------
    input_vector : list
        input vector
    Return
    ------
    brightness : float
        output brightness
    """
    import math
    brightness = None
    brightness = math.sqrt(sum([val**2 for val in input_vector]))
    return brightness


def rasterToArray(InRaster):
    """
    convert a raster to an array
    """
    import gdal
    arrayOut = None
    ds = gdal.Open(InRaster)
    arrayOut = ds.ReadAsArray()
    return arrayOut


def compareVectorFile(vect_1,
                      vect_2,
                      mode='table',
                      typegeom='point',
                      drivername="SQLite"):
    """used to compare two SQLite vector files

    mode=='table' is faster but does not work with connected OTB applications.

    Parameters
    ----------
    vect_1 : string
        path to a vector file
    vect_2 : string
        path to a vector file
    mode : string
        'table' or 'coordinates'
        -> table : compare sqlite tables
        -> 'coordinates' : compare features geo-referenced at the same
                           coordinates
    typegeom : string
        'point' or 'polygon'
    drivername : string
        ogr driver's name

    Return
    ------
    bool
        True if vectors are the same
    """
    import ogr
    from itertools import zip_longest
    from Common import FileUtils as fu
    import sqlite3 as lite
    import pandas as pad

    def getFieldValue(feat, fields):
        return dict([(currentField, feat.GetField(currentField))
                     for currentField in fields])

    def priority(item):
        return (item[0], item[1])

    def getValuesSortedByCoordinates(vector):
        values = []
        driver = ogr.GetDriverByName(drivername)
        ds = driver.Open(vector, 0)
        lyr = ds.GetLayer()
        fields = fu.get_all_fields_in_shape(vector, drivername)
        for feature in lyr:
            if typegeom == "point":
                x = feature.GetGeometryRef().GetX(),
                y = feature.GetGeometryRef().GetY()
            elif typegeom == "polygon":
                x = feature.GetGeometryRef().Centroid().GetX()
                y = feature.GetGeometryRef().Centroid().GetY()
            fields_val = getFieldValue(feature, fields)
            values.append((x, y, fields_val))

        values = sorted(values, key=priority)
        return values

    fields_1 = fu.get_all_fields_in_shape(vect_1, drivername)
    fields_2 = fu.get_all_fields_in_shape(vect_2, drivername)

    for field_1, field_2 in zip_longest(fields_1, fields_2, fillvalue=None):
        if not field_1 == field_2:
            return False

    if mode == 'table':
        connection_1 = lite.connect(vect_1)
        df_1 = pad.read_sql_query("SELECT * FROM output", connection_1)

        connection_2 = lite.connect(vect_2)
        df_2 = pad.read_sql_query("SELECT * FROM output", connection_2)

        try:
            table = (df_1 != df_2).any(1)
            if True in table.tolist():
                return False
            else:
                return True
        except ValueError:
            return False

    elif mode == 'coordinates':
        values_1 = getValuesSortedByCoordinates(vect_1)
        values_2 = getValuesSortedByCoordinates(vect_2)
        sameFeat = [val_1 == val_2 for val_1, val_2 in zip(values_1, values_2)]
        if False in sameFeat:
            return False
        return True
    else:
        raise Exception("mode parameter must be 'table' or 'coordinates'")


def rename_table(vect_file, old_table_name, new_table_name="output"):
    """
    use in test_split_selection Test
    """
    import sqlite3 as lite

    sql_clause = "ALTER TABLE {} RENAME TO {}".format(old_table_name,
                                                      new_table_name)

    conn = lite.connect(vect_file)
    cursor = conn.cursor()
    cursor.execute(sql_clause)
    conn.commit()


def cmp_xml_stat_files(xml_1, xml_2):
    """compare statistics xml files

    samplesPerClass and samplesPerVector tags from input files are
    compared without considering line's order

    Parameters
    ----------
    xml_1 : string
        statistics file from otbcli_PolygonClassStatistics
    xml_2 : string
        statistics file from otbcli_PolygonClassStatistics

    Return
    ------
    bool
        True if content are equivalent
    """
    import xml.etree.ElementTree as ET

    xml_1_stats = {}
    tree_1 = ET.parse(xml_1)
    root_1 = tree_1.getroot()

    xml_2_stats = {}
    tree_2 = ET.parse(xml_2)
    root_2 = tree_2.getroot()

    xml_1_stats["samplesPerClass"] = set([(samplesPerClass.attrib["key"],
                                           samplesPerClass.attrib["value"])
                                          for samplesPerClass in root_1[0]])
    xml_1_stats["samplesPerVector"] = set([(samplesPerClass.attrib["key"],
                                            samplesPerClass.attrib["value"])
                                           for samplesPerClass in root_1[1]])

    xml_2_stats["samplesPerClass"] = set([(samplesPerClass.attrib["key"],
                                           samplesPerClass.attrib["value"])
                                          for samplesPerClass in root_2[0]])
    xml_2_stats["samplesPerVector"] = set([(samplesPerClass.attrib["key"],
                                            samplesPerClass.attrib["value"])
                                           for samplesPerClass in root_2[1]])

    return xml_1_stats == xml_2_stats
