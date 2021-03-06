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
Bibliothèque pour des traitements sur fichier vector
Dépendances : rtree
Rq: field name should contain 10 characters maximum, otherwise field name
    is cutting
"""

import os
import sys
import argparse
import osr
from osgeo import ogr
from typing import List, Optional
import vector_functions as vf


# --------------------------------------------------------------
def init_fields(in_lyr1: str,
                in_lyr2: str,
                out_lyr: str,
                keepfields: Optional[str] = "") -> List[str]:
    """
    Parameters
    ----------
    in_lyr1: string
    in_lyr2: string
    out_lyr: string
    keepfields: string
    Return
    ------
    """
    field_name_list = []
    for idxlyr, lyr in enumerate((in_lyr1, in_lyr2)):
        in_layer_defn = lyr.GetLayerDefn()
        for i in range(in_layer_defn.GetFieldCount()):
            field = in_layer_defn.GetFieldDefn(i).GetName()
            field_name_list.append((idxlyr, i, field))

    if keepfields is not None:
        listtokeep = [x for x in field_name_list if x[2] in keepfields]
    else:
        listtokeep = field_name_list

    try:
        if len(listtokeep) == 0:
            raise ValueError(
                "No field to keep. Vector file without field not possible")
    except ValueError as exc:
        sys.exit(str(exc))

    for lyr in (in_lyr1, in_lyr2):
        in_lyr_defn = lyr.GetLayerDefn()
        for iden in range(in_lyr_defn.GetFieldCount()):
            # Get the Field Definition
            field = in_lyr_defn.GetFieldDefn(iden)
            fname = field.GetName()
            ftype = field.GetTypeName()
            fwidth = field.GetWidth()
            # Copy field definitions from source
            if fname in [x[2] for x in listtokeep]:
                if ftype == 'String':
                    fielddefn = ogr.FieldDefn(fname, ogr.OFTString)
                    fielddefn.SetWidth(fwidth)
                else:
                    fielddefn = ogr.FieldDefn(fname, ogr.OFTInteger)
                out_lyr.CreateField(fielddefn)

    return listtokeep


# --------------------------------------------------------------
def addMultiPolygon(simplePolygon, valuesfields, out_lyr):
    """
    Link with multipart2singlepart (above)
    """
    featureDefn = out_lyr.GetLayerDefn()
    polygon = ogr.CreateGeometryFromWkb(simplePolygon)
    out_feat = ogr.Feature(featureDefn)
    out_feat.SetGeometry(polygon)

    # Loop over each field from the source, and copy onto the new feature
    for idx in range(len(valuesfields)):
        out_feat.SetField(idx, valuesfields[idx][2])
    out_lyr.CreateFeature(out_feat)


# --------------------------------------------------------------
def getFieldValues(lyr, feature):

    fieldList = vf.getFields(lyr)

    listFieldValues = []
    for idfield in range(feature.GetFieldCount()):
        listFieldValues.append(
            (idfield, fieldList[idfield], feature.GetField(idfield)))

    return listFieldValues


# --------------------------------------------------------------
def diffBetweenLayers(layer1,
                      layer2,
                      layer_out,
                      operation,
                      listfieldstokeep=""):
    """
    Difference of layer1 with layer2, save is done in layer_out
    ARGs:
    INPUT:
    - layer1: layer 1 
    - layer2: layer 2
    - layer_out: output layer
    """
    layer1.ResetReading()
    layer2.ResetReading()
    feature1 = layer1.GetNextFeature()
    while feature1:
        valuesfields1 = getFieldValues(layer1, feature1)
        layer2.ResetReading()
        geom1 = feature1.GetGeometryRef()
        if geom1 == None:
            continue
        feature2 = layer2.GetNextFeature()
        newgeom = geom1
        while feature2:
            geom2 = feature2.GetGeometryRef()
            if geom2 == None:
                continue
            if newgeom == None:
                continue

            if geom1.Intersects(geom2) == 1:
                if operation == "intersection":
                    newgeom = newgeom.Intersection(geom2)
                elif operation == "difference":
                    newgeom = newgeom.Difference(geom2)
                elif operation == "union":
                    newgeom = newgeom.Union(geom2)

            valuesfields2 = getFieldValues(layer2, feature2)
            feature2.Destroy()
            feature2 = layer2.GetNextFeature()

        valuesfields = [(x, y, z) for x, y, z in valuesfields1 if y in [tok[2] for tok in listfieldstokeep]] + \
                       [(x, y, z) for x, y, z in valuesfields2 if y in [tok[2] for tok in listfieldstokeep]]

        if newgeom.GetGeometryName() == 'MULTIPOLYGON':
            for geom_part in newgeom:
                addMultiPolygon(geom_part.ExportToWkb(), valuesfields,
                                layer_out)
        else:
            addMultiPolygon(newgeom.ExportToWkb(), valuesfields, layer_out)

        feature1.Destroy()
        feature1 = layer1.GetNextFeature()


# --------------------------------------------------------------


def diffBetweenLayersSpeedUp(layer2,
                             layer1,
                             layer_out,
                             operation,
                             listfieldstokeep="",
                             field_name=""):
    """
    Difference of layer1 with layer2, save is done in layer_out
    ARGs:
    INPUT:
    - layer1: layer 1 
    - layer2: layer 2
    - layer_out: output layer
    (Inspire from http://snorf.net/blog/2014/05/12/using-rtree-spatial-indexing-with-ogr/)
    """
    # RTree Spatial Indexing with OGR
    # -- Index creation
    try:
        import rtree
    except ImportError as e:
        raise ImportError(
            str(e) +
            "\n\n Please install rtree module if it isn't installed yet")

    print("Index creation...")
    index = rtree.index.Index(interleaved=False)

    for fid1 in range(0, layer1.GetFeatureCount()):
        feat1 = layer1.GetFeature(fid1)
        geom1 = feat1.GetGeometryRef()
        if geom1 == None:
            continue
        xmin, xmax, ymin, ymax = geom1.GetEnvelope()
        index.insert(fid1, (xmin, xmax, ymin, ymax))
        feat1.Destroy()
    # -- Search for all features in layer1 that intersect each feature in layer2
    print("Research...")
    for fid2 in range(0, layer2.GetFeatureCount()):

        feat2 = layer2.GetFeature(fid2)
        valuesfields2 = getFieldValues(layer2, feat2)
        geom2 = feat2.GetGeometryRef()
        if geom2 == None:
            continue
        newgeom = geom2
        xmin, xmax, ymin, ymax = geom2.GetEnvelope()
        for fid1 in list(index.intersection((xmin, xmax, ymin, ymax))):
            # if fid1 != fid2: ???
            feat1 = layer1.GetFeature(fid1)
            valuesfields1 = getFieldValues(layer1, feat1)
            geom1 = feat1.GetGeometryRef()
            if geom1 == None:
                continue
            if field_name is not None and field_name != "":
                if (geom2.Intersects(geom1)) and (feat1.GetField(field_name) !=
                                                  feat2.GetField(field_name)):
                    if newgeom == None:
                        continue
                    if operation == "intersection":
                        newgeom = newgeom.Intersection(geom1)
                    elif operation == "difference":
                        newgeom = newgeom.Difference(geom1)
                    elif operation == "union":
                        newgeom = newgeom.Union(geom1)
            else:
                if (geom2.Intersects(geom1)):
                    if newgeom == None:
                        continue
                    if operation == "intersection":
                        newgeom = newgeom.Intersection(geom1)
                    elif operation == "difference":
                        newgeom = newgeom.Difference(geom1)
                    elif operation == "union":
                        newgeom = newgeom.Union(geom1)

            feat1.Destroy()

        valuesfields = [(x, y, z) for x, y, z in valuesfields1 if y in [tok[2] for tok in listfieldstokeep]] + \
                       [(x, y, z) for x, y, z in valuesfields2 if y in [tok[2] for tok in listfieldstokeep]]

        if newgeom == None:
            continue
        if newgeom.GetGeometryName() == 'MULTIPOLYGON':
            for geom_part in newgeom:
                addMultiPolygon(geom_part.ExportToWkb(), valuesfields,
                                layer_out)
        else:
            addMultiPolygon(newgeom.ExportToWkb(), valuesfields, layer_out)

        feat2.Destroy()


# --------------------------------------------------------------
def shapeDifference(shp_in1,
                    shp_in2,
                    shp_out,
                    speed,
                    outformat,
                    epsg,
                    operation,
                    keepfields="",
                    field=""):
    """
    Merge by taking account field_name attribute
    ARGs:
    INPUT:
    - shp_in1: input filename 1
    - shp_in2: input filename 2
    - shp_out: name of output file
    Use of R Tree Spatial Index (faster)
    """
    try:
        driver = ogr.GetDriverByName(outformat)
    except Exception as e:
        raise Exception(
            str(e) + "\n\n Output format '%s' not exists" % (outformat))

    shp1 = driver.Open(shp_in1, 0)
    shp2 = driver.Open(shp_in2, 0)

    if shp1 is None:
        print("Could not open file ", shp_in1)
        sys.exit(1)

    if shp2 is None:
        print("Could not open file ", shp_in2)
        sys.exit(1)

    layer1 = shp1.GetLayer()
    layer2 = shp2.GetLayer()

    # -- Create output file
    if os.path.exists(shp_out):
        os.remove(shp_out)
    try:
        output = driver.CreateDataSource(shp_out)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(epsg)
    except:
        print('Could not create output datasource ', shp_out)
        sys.exit(1)

    newLayerName = os.path.splitext(os.path.basename(shp_out))[0]
    newLayer = output.CreateLayer('%s' % (newLayerName),
                                  geom_type=ogr.wkbPolygon,
                                  srs=layer1.GetSpatialRef())

    if newLayer is None:
        print("Could not create output layer")
        sys.exit(1)

    newLayerDef = newLayer.GetLayerDefn()

    listfieldstokeep = init_fields(layer1, layer2, newLayer, keepfields)

    # -- Processing
    if not speed:
        diffBetweenLayers(layer1, layer2, newLayer, operation,
                          listfieldstokeep, field)
    else:
        diffBetweenLayersSpeedUp(layer1, layer2, newLayer, operation,
                                 listfieldstokeep, field)

    shp1.Destroy()
    shp2.Destroy()


speed = False

if __name__ == "__main__":
    if len(sys.argv) == 1:
        PROG = os.path.basename(sys.argv[0])
        print('      ' + sys.argv[0] + ' [options]')
        print("     Help : ", PROG, " --help")
        print("        or : ", PROG, " -h")
        sys.exit(-1)
    else:
        USAGE = "usage: %prog [options] "
        PARSER = argparse.ArgumentParser(
            description="Difference shapefile of"
            "first shapefile with second shapefile, save is done in "
            "an output shapefile")
        PARSER.add_argument("-s1",
                            dest="s1",
                            action="store",
                            help="First shapefile",
                            required=True)
        PARSER.add_argument("-s2",
                            dest="s2",
                            action="store",
                            help="Second shapefile",
                            required=True)
        PARSER.add_argument("-output",
                            dest="output",
                            action="store",
                            help="Output shapefile",
                            required=True)
        PARSER.add_argument("-speed",
                            action="store_true",
                            help="Use of R Tree Spatial Index (faster)",
                            default=False)
        PARSER.add_argument(
            "-format",
            dest="outformat",
            action="store",
            help="OGR format (ogrinfo --formats). Default : ESRI shapefile ",
            default="ESRI shapefile")
        PARSER.add_argument(
            "-epsg",
            dest="epsg",
            action="store",
            help="EPSG code for projection. Default : 2154 - Lambert 93 ",
            type=int,
            default=2154)
        PARSER.add_argument(
            "-operation",
            dest="operation",
            action="store",
            help=("spatial operation (intersection or difference or union). "
                  "Default : intersection"),
            default="intersection")
        PARSER.add_argument(
            "-keepfields",
            dest="keepfields",
            action="store",
            nargs="*",
            help=("list of fields to keep in resulted vector file. "
                  "Default : All fields"))
        PARSER.add_argument("-f",
                            dest="field",
                            action="store",
                            help="field to look for difference")

        ARGS = PARSER.parse_args()

        if not ARGS.speed:
            shapeDifference(ARGS.s1, ARGS.s2, ARGS.output, False,
                            ARGS.outformat, ARGS.epsg, ARGS.operation,
                            ARGS.keepfields, ARGS.field)
        else:
            try:
                import rtree
            except ImportError as exc:
                raise ImportError(
                    str(exc) +
                    "\n\n Please install rtree module if it isn't installed yet"
                )

            shapeDifference(ARGS.s1, ARGS.s2, ARGS.output, True,
                            ARGS.outformat, ARGS.epsg, ARGS.operation,
                            ARGS.keepfields, ARGS.field)
