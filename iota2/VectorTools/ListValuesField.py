#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sys
import os
from osgeo import ogr
from iota2.VectorTools import vector_functions as vf
"""
For a attribute field list the values
"""


def ListValues(shp):
    fields = vf.getFields(shp)
    print("The name of the fields are: " + ' - '.join(fields))
    field = input("Field to list values: ")
    if field not in fields:
        print('This field does not exist. Verify!')
        sys.exit(1)
    ds = vf.openToRead(shp)
    layer = ds.GetLayer()
    values = []
    for feat in layer:
        if feat.GetField(field) not in values:
            values.append(feat.GetField(field))
    return values


if __name__ == '__main__':
    usage = 'usage: <shapefile>'
    if len(sys.argv) != 2:
        print(usage)
        sys.exit(1)
    else:
        print(ListValues(sys.argv[1]))
