#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
from osgeo import ogr
from iota2.VectorTools import vector_functions as vf


def selectBySize(filein, col, nbpix, fileout):

    source = ogr.Open(filein, 0)

    baseext = os.path.splitext(fileout)[1]
    if baseext == ".shp":
        outformat = "ESRI Shapefile"
    elif baseext == ".sqlite":
        outformat = "SQlite"
    else:
        print("Output format not managed")
        sys.exit()

    layer = source.GetLayer()
    request = col + " >= " + str(nbpix)
    layer.SetAttributeFilter(request)
    vf.CreateNewLayer(layer, fileout, outformat)
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 1:
        prog = os.path.basename(sys.argv[0])
        print('      ' + sys.argv[0] + ' [options]')
        print("     Help : ", prog, " --help")
        print("        or : ", prog, " -h")
        sys.exit(-1)
    else:
        usage = "usage: %prog [options] "
        parser = argparse.ArgumentParser(
            description="Select features of an input shapefile"
            "based on area threshold (same unit of the area field)")
        parser.add_argument("-s",
                            dest="inshapefile",
                            action="store",
                            help="Input shapefile",
                            required=True)
        parser.add_argument("-f",
                            dest="field",
                            action="store",
                            help="Area field",
                            required=True)
        parser.add_argument("-size",
                            dest="nbpix",
                            action="store",
                            help="Area threshold",
                            required=True)
        parser.add_argument("-o",
                            dest="outshapefile",
                            action="store",
                            help="Output shapefile",
                            required=True)
        args = parser.parse_args()
        selectBySize(args.inshapefile, args.field, args.nbpix,
                     args.outshapefile)
