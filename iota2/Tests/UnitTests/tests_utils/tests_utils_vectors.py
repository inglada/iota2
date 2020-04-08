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
This module offers some tools for writing tests
"""
from typing import Optional, List, Tuple


def shape_reference_vector(ref_vector: str, output_name: str) -> str:
    """
    modify reference vector (add field, rename...)
    Parameters
    ----------
    ref_vector : string
    output_name : string
    Return
    ------
    string
    """
    import os
    from iota2.Common.Utils import run
    from iota2.Common import FileUtils as fut
    from iota2.VectorTools.AddField import addField
    path, _ = os.path.split(ref_vector)

    tmp = os.path.join(path, output_name + "_TMP")
    fut.cpShapeFile(ref_vector.replace(".shp", ""), tmp,
                    [".prj", ".shp", ".dbf", ".shx"])
    addField(tmp + ".shp", "region", "1", str)
    addField(tmp + ".shp", "seed_0", "learn", str)
    cmd = (f"ogr2ogr -dialect 'SQLite' -sql 'select GEOMETRY,seed_0, "
           f"region, CODE as code from {output_name}_TMP' "
           f"{path}/{output_name}.shp {tmp}.shp")
    run(cmd)

    os.remove(tmp + ".shp")
    os.remove(tmp + ".shx")
    os.remove(tmp + ".prj")
    os.remove(tmp + ".dbf")
    return path + "/" + output_name + ".shp"


def prepare_test_selection(vector: str, raster_ref: str, output_selection: str,
                           working_directory: str, data_field: str) -> None:
    """
    Prepare vector selection files
    Parameters
    ----------
    vector: string
    raster_ref: string
    output_selection: string
    working_directory: string
    data_field: string
    Return
    ------
    None
    """
    import os
    from iota2.Common import OtbAppBank as otb
    stats_path = os.path.join(working_directory, "stats.xml")
    if os.path.exists(stats_path):
        os.remove(stats_path)
    stats = otb.CreatePolygonClassStatisticsApplication({
        "in": raster_ref,
        "vec": vector,
        "field": data_field,
        "out": stats_path
    })
    stats.ExecuteAndWriteOutput()
    sample_sel = otb.CreateSampleSelectionApplication({
        "in": raster_ref,
        "vec": vector,
        "out": output_selection,
        "instats": stats_path,
        "sampler": "random",
        "strategy": "all",
        "field": data_field
    })
    if os.path.exists(output_selection):
        os.remove(output_selection)
    sample_sel.ExecuteAndWriteOutput()
    os.remove(stats_path)


def delete_useless_fields(test_vector: str,
                          field_to_rm: Optional[str] = "region") -> None:
    """
    Parameters
    ----------
    test_vector: string
    field_to_rm: string
    Return
    ------
    None
    """
    from iota2.Common import FileUtils as fut
    from iota2.VectorTools.DeleteField import deleteField
    # const

    fields = fut.get_all_fields_in_shape(test_vector, driver='SQLite')

    rm_field = [field for field in fields if field_to_rm in field]

    for field_to_remove in rm_field:
        deleteField(test_vector, field_to_remove)


def compare_sqlite(vect_1: str,
                   vect_2: str,
                   cmp_mode: Optional[str] = 'table',
                   ignored_fields: Optional[List[str]] = None):
    """
    compare SQLite, table mode is faster but does not work with
    connected OTB applications.

    return true if vectors are the same
    """

    from collections import OrderedDict
    from iota2.Common import FileUtils as fut
    if ignored_fields is None:
        ignored_fields = []

    def get_field_value(feat, fields):
        """
        usage : get all fields's values in input feature

        IN
        feat [gdal feature]
        fields [list of string] : all fields to inspect

        OUT
        [dict] : values by fields
        """
        return OrderedDict([(currentField, feat.GetField(currentField))
                            for currentField in fields])

    def priority(item):
        """
        priority key
        """
        return (item[0], item[1])

    def get_values_sorted_by_coordinates(vector: str
                                         ) -> List[Tuple[float, float]]:
        """
        usage return values sorted by coordinates (x,y)

        IN
        vector [string] path to a vector of points

        OUT
        values [list of tuple] : [(x,y,[val1,val2]),()...]
        """
        import ogr
        values = []
        driver = ogr.GetDriverByName("SQLite")
        dataset = driver.Open(vector, 0)
        lyr = dataset.GetLayer()
        fields = fut.get_all_fields_in_shape(vector, 'SQLite')
        for feature in lyr:
            x_coord = feature.GetGeometryRef().GetX()
            y_coord = feature.GetGeometryRef().GetY()
            fields_val = get_field_value(feature, fields)
            values.append((x_coord, y_coord, fields_val))

        values = sorted(values, key=priority)
        return values

    fields_1 = fut.get_all_fields_in_shape(vect_1, 'SQLite')
    fields_2 = fut.get_all_fields_in_shape(vect_2, 'SQLite')

    if len(fields_1) != len(fields_2):
        return False

    if cmp_mode == 'table':
        import sqlite3 as lite
        import pandas as pad
        connection_1 = lite.connect(vect_1)
        df_1 = pad.read_sql_query("SELECT * FROM output", connection_1)

        connection_2 = lite.connect(vect_2)
        df_2 = pad.read_sql_query("SELECT * FROM output", connection_2)

        try:
            table = (df_1 != df_2).any(1)
            out = True
            if True in table.tolist():
                out = False
            return out
        except ValueError:
            return False

    elif cmp_mode == 'coordinates':
        values_1 = get_values_sorted_by_coordinates(vect_1)
        values_2 = get_values_sorted_by_coordinates(vect_2)
        same_feat = []
        for val_1, val_2 in zip(values_1, values_2):
            for (key_1, v_1), (key_2, v_2) in zip(list(val_1[2].items()),
                                                  list(val_2[2].items())):
                if key_1 not in ignored_fields and key_2 in ignored_fields:
                    # same_feat.append(cmp(v_1, v_2) == 0)
                    same_feat.append(v_1 == v_2)
        if False in same_feat:
            return False
        return True
    else:
        raise Exception("CmpMode parameter must be 'table' or 'coordinates'")
