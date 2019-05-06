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

def arrayToRaster(inArray, outRaster, output_format="int"):
    """
    usage : from an array, create a raster with (originX,originY) origin
    IN
    inArray [numpy.array] : input array
    outRaster [string] : output raster
    """
    import gdal
    import osr

    rows = inArray.shape[0]
    cols = inArray.shape[1]
    originX = 777225.58
    originY = 6825084.53
    pixSize = 30
    driver = gdal.GetDriverByName('GTiff')
    if output_format=='int':
        outRaster = driver.Create(outRaster, cols, rows, 1, gdal.GDT_UInt16)
    elif output_format=='float':
        outRaster = driver.Create(outRaster, cols, rows, 1, gdal.GDT_Float32)
    if not outRaster:
        raise Exception("can not create : "+outRaster)
    outRaster.SetGeoTransform((originX, pixSize, 0, originY, 0, pixSize))
    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(inArray)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromEPSG(2154)
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

def compareVectorFile(vect_1, vect_2, mode='table', typegeom='point', drivername="SQLite"):
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
        -> 'coordinates' : compare features geo-referenced at the same coordinates
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

    def getFieldValue(feat,fields):
            return dict([(currentField,feat.GetField(currentField)) for currentField in fields])
    def priority(item):
            return (item[0],item[1])
    def getValuesSortedByCoordinates(vector):
            values = []
            driver = ogr.GetDriverByName(drivername)
            ds = driver.Open(vector,0)
            lyr = ds.GetLayer()
            fields = fu.getAllFieldsInShape(vector, drivername)
            for feature in lyr:
                if typegeom == "point":
                    x,y= feature.GetGeometryRef().GetX(),feature.GetGeometryRef().GetY()
                elif typegeom == "polygon":
                    x,y= feature.GetGeometryRef().Centroid().GetX(),feature.GetGeometryRef().Centroid().GetY()
                fields_val = getFieldValue(feature,fields)
                values.append((x,y,fields_val))

            values = sorted(values,key=priority)
            return values

    fields_1 = fu.getAllFieldsInShape(vect_1, drivername)
    fields_2 = fu.getAllFieldsInShape(vect_2, drivername)

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
                    if True in table.tolist():return False
                    else:return True
            except ValueError:
                    return False

    elif mode == 'coordinates':
            values_1 = getValuesSortedByCoordinates(vect_1)
            values_2 = getValuesSortedByCoordinates(vect_2)
            sameFeat = [val_1==val_2 for val_1,val_2 in zip(values_1,values_2)]
            if False in sameFeat:return False
            return True
    else:
            raise Exception("mode parameter must be 'table' or 'coordinates'")

def rename_table(vect_file, old_table_name, new_table_name="output"):
    """
    use in test_split_selection Test
    """
    import sqlite3 as lite

    sql_clause = "ALTER TABLE {} RENAME TO {}".format(old_table_name, new_table_name)

    conn = lite.connect(vect_file)
    cursor = conn.cursor()
    cursor.execute(sql_clause)
    conn.commit()

def cmp_xml_stat_files(xml_1, xml_2):
    """compare statistics xml files

    samplesPerClass and samplesPerVector tags from input files are compared without
    considering line's order

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

    xml_1_stats["samplesPerClass"] = set([(samplesPerClass.attrib["key"], samplesPerClass.attrib["value"]) for samplesPerClass in root_1[0]])
    xml_1_stats["samplesPerVector"] = set([(samplesPerClass.attrib["key"], samplesPerClass.attrib["value"]) for samplesPerClass in root_1[1]])

    xml_2_stats["samplesPerClass"] = set([(samplesPerClass.attrib["key"], samplesPerClass.attrib["value"]) for samplesPerClass in root_2[0]])
    xml_2_stats["samplesPerVector"] = set([(samplesPerClass.attrib["key"], samplesPerClass.attrib["value"]) for samplesPerClass in root_2[1]])

    return xml_1_stats == xml_2_stats