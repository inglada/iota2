#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import os
import argparse
from osgeo import ogr, gdal
import sys
from iota2.VectorTools import vector_functions as vf

gdal.UseExceptions()


def addPolygon(feat, simplePolygon, in_lyr, out_lyr, field_name_list):
    featureDefn = in_lyr.GetLayerDefn()
    polygon = ogr.CreateGeometryFromWkb(simplePolygon)
    out_feat = ogr.Feature(featureDefn)
    for field in field_name_list:
        inValue = feat.GetField(field)
        out_feat.SetField(field, inValue)

    out_feat.SetGeometry(polygon)
    out_lyr.CreateFeature(out_feat)
    out_lyr.SetFeature(out_feat)


def manageMultiPoly2Poly(in_lyr, out_lyr, field_name_list, do_correction=True):
    multi_cpt = 0
    for in_feat in in_lyr:
        geom = in_feat.GetGeometryRef()
        if geom is not None:
            if geom.GetGeometryName() == 'MULTIPOLYGON':
                multi_cpt += 1
                if do_correction:
                    for geom_part in geom:
                        addPolygon(in_feat, geom_part.ExportToWkb(), in_lyr,
                                   out_lyr, field_name_list)
            else:
                if do_correction:
                    addPolygon(in_feat, geom.ExportToWkb(), in_lyr, out_lyr,
                               field_name_list)
    return multi_cpt


def multipoly2poly(inshape,
                   outshape,
                   do_correction=True,
                   outformat="ESRI shapefile"):
    """Check if a geometry is a MULTIPOLYGON, if it is it will not be split in POLYGON

    Parameters
    ----------
    inshape : string
        input shapeFile
    outshape : string
        output shapeFile
    do_correction : bool
        flag to remove MULTIPOLYGONs
    Return
    ------
    int
        number of MULTIPOLYGON found
    """
    # Get field list
    field_name_list = vf.getFields(inshape)

    # Open input and output shapefile
    driver = ogr.GetDriverByName(outformat)
    in_ds = driver.Open(inshape, 0)
    in_lyr = in_ds.GetLayer()
    inLayerDefn = in_lyr.GetLayerDefn()
    srsObj = in_lyr.GetSpatialRef()
    if os.path.exists(outshape):
        driver.DeleteDataSource(outshape)
    out_lyr = None
    if do_correction:
        out_ds = driver.CreateDataSource(outshape)
        out_lyr = out_ds.CreateLayer('poly', srsObj, geom_type=ogr.wkbPolygon)
        for i in range(len(field_name_list)):
            fieldDefn = inLayerDefn.GetFieldDefn(i)
            fieldName = fieldDefn.GetName()
            if fieldName not in field_name_list:
                continue
            out_lyr.CreateField(fieldDefn)

    return manageMultiPoly2Poly(in_lyr, out_lyr, field_name_list,
                                     do_correction)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        prog = os.path.basename(sys.argv[0])
        print('      ' + sys.argv[0] + ' [options]')
        print("     Help : ", prog, " --help")
        print("        or : ", prog, " -h")
        sys.exit(-1)
    else:
        usage = "usage: %prog [options] "
        parser = argparse.ArgumentParser(description = "Transform multipolygons shapefile" \
        "in single polygons shapefile")
        parser.add_argument("-s", dest="inshapefile", action="store", \
                            help="Input shapefile", required = True)
        parser.add_argument("-o", dest="outshapefile", action="store", \
                            help="Output shapefile without multipolygons", required = True)
        args = parser.parse_args()
        multipoly2poly(args.inshapefile, args.outshapefile)
