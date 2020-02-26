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


def generate_fake_s2_data(root_directory, tile_name, dates):
    """
    Parameters
    ----------
    root_directory : string
        path to generate Sentinel-2 dates
    tile_name : string
        THEIA tile name (ex:T31TCJ)
    dates : list
        list of strings reprensentig dates format : YYYYMMDD
    """
    import numpy as np
    import random
    from Common.FileUtils import ensure_dir
    from Common.OtbAppBank import CreateConcatenateImagesApplication

    tile_dir = os.path.join(root_directory, tile_name)
    ensure_dir(tile_dir)

    band_of_interest = [
        "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"
    ]
    masks_of_interest = ["BINARY_MASK", "CLM_R1", "EDG_R1", "SAT_R1"]

    originX = 566377
    originY = 6284029
    array_name = "iota2_binary"
    for date in dates:
        date_dir = os.path.join(tile_dir,
                                ("SENTINEL2B_{}-000000-"
                                 "000_L2A_{}_D_V1-7".format(date, tile_name)))
        mask_date_dir = os.path.join(date_dir, "MASKS")
        ensure_dir(date_dir)
        ensure_dir(mask_date_dir)
        all_bands = []
        for cpt, mask in enumerate(masks_of_interest):
            new_mask = os.path.join(
                mask_date_dir,
                ("SENTINEL2B_{}-000000-000_L2A"
                 "_{}_D_V1-7_FRE_{}.tif".format(date, tile_name, mask)))

            arrayToRaster(fun_array(array_name) * cpt % 2,
                          new_mask,
                          originX=originX,
                          originY=originY)
        for band in band_of_interest:
            new_band = os.path.join(
                date_dir,
                ("SENTINEL2B_{}-000000-000_L2A"
                 "_{}_D_V1-7_FRE_{}.tif".format(date, tile_name, band)))
            all_bands.append(new_band)
            array = fun_array(array_name)
            random_array = []
            for y in array:
                y_tmp = []
                for pix_val in y:
                    y_tmp.append(pix_val * random.random() * 1000)
                random_array.append(y_tmp)

            arrayToRaster(np.array(random_array),
                          new_band,
                          originX=originX,
                          originY=originY)
            stack_date = os.path.join(
                date_dir, ("SENTINEL2B_{}-000000-000_L2A_{}_D_V1-7"
                           "_FRE_STACK.tif".format(date, tile_name)))
            stack_app = CreateConcatenateImagesApplication({
                "il": all_bands,
                "out": stack_date
            })
            stack_app.ExecuteAndWriteOutput()


def fun_array(fun):
    """arrays use in unit tests
    """
    import numpy as np
    if fun == "iota2_binary":
        array = [[
            0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0
        ],
                 [
                     0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1,
                     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                     0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 1, 1, 0, 0
                 ],
                 [
                     0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1,
                     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                     0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 1, 1, 1, 0
                 ],
                 [
                     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1,
                     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                     0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0,
                     0, 0, 1, 1, 1, 1, 1, 1, 1, 0
                 ],
                 [
                     1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                     0, 0, 1, 1, 1, 1, 1, 1, 1, 0
                 ],
                 [
                     1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                     0, 0, 1, 1, 1, 1, 1, 1, 1, 0
                 ],
                 [
                     0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1,
                     1, 1, 1, 1, 1, 1, 1, 1, 0, 0
                 ],
                 [
                     0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                     0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 1, 0, 0, 0
                 ],
                 [
                     0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0,
                     1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1,
                     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 0, 0, 0, 0, 0
                 ],
                 [
                     0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0,
                     1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1,
                     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 0, 0, 0, 0, 0, 0, 0, 0
                 ],
                 [
                     0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0,
                     1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1,
                     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0,
                     0, 0, 0, 0, 0, 0, 0, 0, 0, 0
                 ],
                 [
                     0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0,
                     1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1,
                     0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0,
                     0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0,
                     0, 0, 0, 0, 0, 0, 0, 0, 0, 0
                 ],
                 [
                     1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0,
                     0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0,
                     0, 0, 0, 0, 1, 1, 1, 1, 1, 1
                 ],
                 [
                     1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 1, 1, 1, 1
                 ],
                 [
                     1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 1, 1, 1, 1
                 ],
                 [
                     1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 1, 1, 1, 1
                 ]]
    array = np.array(array)
    return array


def arrayToRaster(inArray,
                  outRaster_path,
                  output_format="int",
                  output_driver="GTiff",
                  pixSize=30,
                  originX=777225.58,
                  originY=6825084.53,
                  epsg_code=2154):
    """usage : from an array of a list of array, create a raster

    Parameters
    ----------
    inArray : list
        list of numpy.array sorted by bands (fisrt array = band 1,
                                             N array = band N)
    outRaster_path : string
        output path
    output_format : string
        'int' or 'float'
    """
    import gdal
    import osr
    if not isinstance(inArray, list):
        inArray = [inArray]
    NB_BANDS = len(inArray)
    rows = inArray[0].shape[0]
    cols = inArray[0].shape[1]

    driver = gdal.GetDriverByName(output_driver)
    if output_format == 'int':
        outRaster = driver.Create(outRaster_path, cols, rows, len(inArray),
                                  gdal.GDT_UInt16)
    elif output_format == 'float':
        outRaster = driver.Create(outRaster_path, cols, rows, len(inArray),
                                  gdal.GDT_Float32)
    if not outRaster:
        raise Exception("can not create : " + outRaster)
    outRaster.SetGeoTransform((originX, pixSize, 0, originY, 0, -pixSize))

    for i in range(NB_BANDS):
        outband = outRaster.GetRasterBand(i + 1)
        outband.WriteArray(inArray[i])

    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromEPSG(epsg_code)
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()


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
        fields = fu.getAllFieldsInShape(vector, drivername)
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


def generate_data_tree(directory, mtd_s2st_date, s2st_ext="jp2"):
    """generate a fake Sen2Cor data
    TODO : replace this function by downloading a Sen2Cor data from PEPS.

    Return
    ------
    products : list
        list of data ready to be generated
    """
    # from xml.dom.minidom import parse
    import xml.dom.minidom
    from iota2.Common.FileUtils import ensure_dir

    ensure_dir(directory)

    dom_tree = xml.dom.minidom.parse(mtd_s2st_date)
    collection = dom_tree.documentElement
    general_info_node = collection.getElementsByTagName("n1:General_Info")
    date_dir = general_info_node[0].getElementsByTagName(
        'PRODUCT_URI')[0].childNodes[0].data

    products = []
    for product_organisation_nodes in general_info_node[
            0].getElementsByTagName('Product_Organisation'):
        img_list_nodes = product_organisation_nodes.getElementsByTagName(
            "IMAGE_FILE")
        for img_list in img_list_nodes:
            new_prod = os.path.join(
                directory, date_dir,
                "{}.{}".format(img_list.childNodes[0].data, s2st_ext))
            new_prod_dir, _ = os.path.split(new_prod)
            ensure_dir(new_prod_dir)
            products.append(new_prod)
    return products


def generate_fake_s2_s2c_data(output_directory, mtd_files):
    """
    generate fake s2_s2c data
    """
    import numpy as np
    fake_raster = [np.array([[10, 55, 61], [100, 56, 42], [1, 42, 29]])]
    fake_scene_classification = [np.array([[2, 0, 4], [0, 4, 2], [1, 1, 10]])]
    for mtd in mtd_files:
        prod_list = generate_data_tree(
            os.path.join(output_directory, "T31TCJ"), mtd)
        for prod in prod_list:
            if '10m.jp2' in prod:
                pix_size = 10
            if '20m.jp2' in prod:
                pix_size = 20
            if '60m.jp2' in prod:
                pix_size = 60
            if "_SCL_" in prod:
                array_raster = fake_scene_classification
            else:
                array_raster = fake_raster
            # output_driver has to be 'GTiff' even if S2ST are jp2
            arrayToRaster(array_raster,
                          prod,
                          output_driver="GTiff",
                          output_format="int",
                          pixSize=pix_size,
                          originX=300000,
                          originY=4900020,
                          epsg_code=32631)


def generate_fake_l8_data(root_directory, tile_name, dates):
    """
    Parameters
    ----------
    root_directory : string
        path to generate Sentinel-2 dates
    tile_name : string
        THEIA tile name (ex:T31TCJ)
    dates : list
        list of strings reprensentig dates format : YYYYMMDD
    """
    import numpy as np
    import random
    from iota2.Common.FileUtils import ensure_dir
    from iota2.Common.OtbAppBank import CreateConcatenateImagesApplication

    tile_dir = os.path.join(root_directory, tile_name)
    ensure_dir(tile_dir)

    band_of_interest = ["B1", "B2", "B3", "B4", "B5", "B6", "B7"]
    masks_of_interest = ["BINARY_MASK", "CLM_XS", "EDG_XS", "SAT_XS"]

    origin_x = 566377
    origin_y = 6284029
    array_name = "iota2_binary"
    for date in dates:
        date_dir = os.path.join(tile_dir,
                                ("LANDSAT8-OLITIRS-XS_{}-000000-"
                                 "000_L2A_{}_D_V1-7".format(date, tile_name)))
        mask_date_dir = os.path.join(date_dir, "MASKS")
        ensure_dir(date_dir)
        ensure_dir(mask_date_dir)
        all_bands = []
        for cpt, mask in enumerate(masks_of_interest):
            new_mask = os.path.join(
                mask_date_dir,
                ("LANDSAT8-OLITIRS-XS_{}-000000-000_L2A"
                 "_{}_D_V1-7_FRE_{}.tif".format(date, tile_name, mask)))

            arrayToRaster(fun_array(array_name) * cpt % 2,
                          new_mask,
                          pixSize=30,
                          originX=origin_x,
                          originY=origin_y)
        for band in band_of_interest:
            new_band = os.path.join(
                date_dir,
                ("LANDSAT8-OLITIRS-XS_{}-000000-000_L2A"
                 "_{}_D_V1-7_FRE_{}.tif".format(date, tile_name, band)))
            all_bands.append(new_band)
            array = fun_array(array_name)
            random_array = []
            for val in array:
                val_tmp = []
                for pix_val in val:
                    val_tmp.append(pix_val * random.random() * 1000)
                random_array.append(val_tmp)

            arrayToRaster(np.array(random_array),
                          new_band,
                          pixSize=30,
                          originX=origin_x,
                          originY=origin_y)
            stack_date = os.path.join(
                date_dir, ("LANDSAT8-OLITIRS-XS_{}-000000-000_L2A_{}_D_V1-7"
                           "_FRE_STACK.tif".format(date, tile_name)))
            stack_app = CreateConcatenateImagesApplication({
                "il": all_bands,
                "out": stack_date
            })
            stack_app.ExecuteAndWriteOutput()


def generate_fake_user_features_data(root_directory: str, tile_name: str,
                                     patterns: List[str]):
    """
    Parameters
    ----------
    root_directory : string
        path to generate Sentinel-2 dates
    tile_name : string
        THEIA tile name (ex:T31TCJ)
    dates : list
        List of raster's name
    """
    import numpy as np
    import random

    from iota2.Common.FileUtils import ensure_dir

    tile_dir = os.path.join(root_directory, tile_name)
    ensure_dir(tile_dir)

    origin_x = 566377
    origin_y = 6284029
    array_name = "iota2_binary"

    array = fun_array(array_name)
    for pattern in patterns:
        user_features_path = os.path.join(tile_dir, f"{pattern}.tif")
        random_array = []
        for val in array:
            val_tmp = []
            for pix_val in val:
                val_tmp.append(pix_val * random.random() * 1000)
            random_array.append(val_tmp)
        arrayToRaster(np.array(random_array),
                      user_features_path,
                      originX=origin_x,
                      originY=origin_y)


def generate_fake_s2_l3a_data(root_directory, tile_name, dates):
    """
    Parameters
    ----------
    root_directory : string
        path to generate Sentinel-2 l3a dates
    tile_name : string
        THEIA tile name (ex:T31TCJ)
    dates : list
        list of strings reprensentig dates format : YYYYMMDD
    """
    import numpy as np
    import random
    from iota2.Common.FileUtils import ensure_dir
    from iota2.Common.OtbAppBank import CreateConcatenateImagesApplication

    tile_dir = os.path.join(root_directory, tile_name)
    ensure_dir(tile_dir)

    band_of_interest = [
        "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"
    ]
    masks_of_interest = ["BINARY_MASK", "FLG_R1"]

    origin_x = 566377
    origin_y = 6284029
    array_name = "iota2_binary"
    for date in dates:
        date_dir = os.path.join(tile_dir,
                                ("SENTINEL2X_{}-000000-"
                                 "000_L3A_{}_D_V1-7".format(date, tile_name)))
        mask_date_dir = os.path.join(date_dir, "MASKS")
        ensure_dir(date_dir)
        ensure_dir(mask_date_dir)
        all_bands = []
        for cpt, mask in enumerate(masks_of_interest):
            new_mask = os.path.join(
                mask_date_dir,
                ("SENTINEL2X_{}-000000-000_L3A"
                 "_{}_D_V1-7_{}.tif".format(date, tile_name, mask)))

            arrayToRaster(fun_array(array_name) * cpt % 2,
                          new_mask,
                          pixSize=10,
                          originX=origin_x,
                          originY=origin_y)
        for band in band_of_interest:
            new_band = os.path.join(
                date_dir,
                ("SENTINEL2X_{}-000000-000_L3A"
                 "_{}_D_V1-7_FRC_{}.tif".format(date, tile_name, band)))
            all_bands.append(new_band)
            array = fun_array(array_name)
            random_array = []
            for val in array:
                val_tmp = []
                for pix_val in val:
                    val_tmp.append(pix_val * random.random() * 1000)
                random_array.append(val_tmp)

            arrayToRaster(np.array(random_array),
                          new_band,
                          pixSize=10,
                          originX=origin_x,
                          originY=origin_y)
            stack_date = os.path.join(
                date_dir, ("SENTINEL2X_{}-000000-000_L3A_{}_D_V1-7"
                           "_FRC_STACK.tif".format(date, tile_name)))
            stack_app = CreateConcatenateImagesApplication({
                "il": all_bands,
                "out": stack_date
            })
            stack_app.ExecuteAndWriteOutput()


def generate_fake_l5_old_data(root_directory, tile_name, dates):
    """
    Parameters
    ----------
    root_directory : string
        path to generate Sentinel-2 dates
    tile_name : string
        THEIA tile name (ex:T31TCJ)
    dates : list
        list of strings reprensentig dates format : YYYYMMDD
    """
    import numpy as np
    import random
    from iota2.Common.FileUtils import ensure_dir
    from iota2.Common.OtbAppBank import CreateConcatenateImagesApplication

    tile_dir = os.path.join(root_directory, tile_name)
    ensure_dir(tile_dir)

    band_of_interest = ["B1", "B2", "B3", "B4", "B5", "B6"]
    masks_of_interest = ["BINARY_MASK", "DIV", "NUA", "SAT"]

    origin_x = 566377
    origin_y = 6284029
    array_name = "iota2_binary"
    for date in dates:
        date_dir = os.path.join(tile_dir,
                                (f"LANDSAT5_TM_XS_{date}_N2A_{tile_name}"))
        mask_date_dir = os.path.join(date_dir, "MASK")
        ensure_dir(date_dir)
        ensure_dir(mask_date_dir)
        all_bands = []
        for cpt, mask in enumerate(masks_of_interest):
            new_mask = os.path.join(mask_date_dir,
                                    (f"LANDSAT5_TM_XS_{date}_N2A"
                                     f"_{tile_name}_{mask}.TIF"))

            arrayToRaster(fun_array(array_name) * cpt % 2,
                          new_mask,
                          pixSize=30,
                          originX=origin_x,
                          originY=origin_y)
        for band in band_of_interest:
            new_band = os.path.join(date_dir, (f"LANDSAT5_TM_XS_{date}_N2A"
                                               f"_{tile_name}_{band}.TIF"))
            all_bands.append(new_band)
            array = fun_array(array_name)
            random_array = []
            for val in array:
                val_tmp = []
                for pix_val in val:
                    val_tmp.append(pix_val * random.random() * 1000)
                random_array.append(val_tmp)

            arrayToRaster(np.array(random_array),
                          new_band,
                          pixSize=30,
                          originX=origin_x,
                          originY=origin_y)
            stack_date = os.path.join(date_dir, (f"LANDSAT5_TM_XS_{date}_"
                                                 "N2A_ORTHO_SURF_CORR"
                                                 f"_PENTE_{tile_name}.TIF"))
            stack_app = CreateConcatenateImagesApplication({
                "il": all_bands,
                "out": stack_date
            })
            stack_app.ExecuteAndWriteOutput()


def generate_fake_l8_old_data(root_directory, tile_name, dates):
    """
    Parameters
    ----------
    root_directory : string
        path to generate Sentinel-2 dates
    tile_name : string
        THEIA tile name (ex:T31TCJ)
    dates : list
        list of strings reprensentig dates format : YYYYMMDD
    """
    import numpy as np
    import random
    from iota2.Common.FileUtils import ensure_dir
    from iota2.Common.OtbAppBank import CreateConcatenateImagesApplication

    tile_dir = os.path.join(root_directory, tile_name)
    ensure_dir(tile_dir)

    band_of_interest = ["B1", "B2", "B3", "B4", "B5", "B6", "B7"]
    masks_of_interest = ["BINARY_MASK", "DIV", "NUA", "SAT"]

    origin_x = 566377
    origin_y = 6284029
    array_name = "iota2_binary"
    for date in dates:
        date_dir = os.path.join(
            tile_dir, (f"LANDSAT8_OLITIRS_XS_{date}_N2A_{tile_name}"))
        mask_date_dir = os.path.join(date_dir, "MASK")
        ensure_dir(date_dir)
        ensure_dir(mask_date_dir)
        all_bands = []
        for cpt, mask in enumerate(masks_of_interest):
            new_mask = os.path.join(mask_date_dir,
                                    (f"LANDSAT8_OLITIRS_XS_{date}_N2A"
                                     f"_{tile_name}_{mask}.TIF"))

            arrayToRaster(fun_array(array_name) * cpt % 2,
                          new_mask,
                          pixSize=30,
                          originX=origin_x,
                          originY=origin_y)
        for band in band_of_interest:
            new_band = os.path.join(date_dir,
                                    (f"LANDSAT8_OLITIRS_XS_{date}_N2A"
                                     f"_{tile_name}_{band}.TIF"))
            all_bands.append(new_band)
            array = fun_array(array_name)
            random_array = []
            for val in array:
                val_tmp = []
                for pix_val in val:
                    val_tmp.append(pix_val * random.random() * 1000)
                random_array.append(val_tmp)

            arrayToRaster(np.array(random_array),
                          new_band,
                          pixSize=30,
                          originX=origin_x,
                          originY=origin_y)
            stack_date = os.path.join(date_dir, (f"LANDSAT8_OLITIRS_XS_{date}_"
                                                 "N2A_ORTHO_SURF_CORR"
                                                 f"_PENTE_{tile_name}.TIF"))
            stack_app = CreateConcatenateImagesApplication({
                "il": all_bands,
                "out": stack_date
            })
            stack_app.ExecuteAndWriteOutput()


def prepare_annual_features(workingDirectory,
                            referenceDirectory,
                            pattern,
                            rename=None):
    """
    double all rasters's pixels
    rename must be a tuple
    """
    import iota2.Common.FileUtils as fut
    import shutil
    for dirname, dirnames, filenames in os.walk(referenceDirectory):
        # print path to all subdirectories first.
        for subdirname in dirnames:
            os.mkdir(
                os.path.join(dirname, subdirname).replace(
                    referenceDirectory,
                    workingDirectory).replace(rename[0], rename[1]))

        # print path to all filenames.
        for filename in filenames:
            shutil.copy(
                os.path.join(dirname, filename),
                os.path.join(dirname, filename).replace(
                    referenceDirectory,
                    workingDirectory).replace(rename[0], rename[1]))

    rastersPath = fut.FileSearch_AND(workingDirectory, True, pattern)
    for raster in rastersPath:
        cmd = 'otbcli_BandMathX -il ' + raster + ' -out ' + raster + ' -exp "im1+im1"'
        print(cmd)
        os.system(cmd)

    if rename:
        all_content = []
        for dirname, dirnames, filenames in os.walk(workingDirectory):
            # print path to all subdirectories first.
            for subdirname in dirnames:
                all_content.append(os.path.join(dirname, subdirname))

            # print path to all filenames.
            for filename in filenames:
                all_content.append(os.path.join(dirname, filename))
