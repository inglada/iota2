#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
from osgeo import ogr


def simplify(infile, outfile, tolerance):
    try:
        dataset = ogr.Open(infile)
        drv = dataset.GetDriver()
        if os.path.exists(outfile):
            drv.DeleteDataSource(outfile)
        drv.CopyDataSource(dataset, outfile)
        dataset.Destroy()

        dataset = ogr.Open(outfile, 1)
        lyr = dataset.GetLayer(0)
        cpt = 0
        for i in range(0, lyr.GetFeatureCount()):
            feat = lyr.DeleteFeature(i)
            geom = feat.GetGeometryRef()
            if geom.Simplify(
                    float(tolerance)).GetEnvelope() != (0.0, 0.0, 0.0, 0.0):
                feat.SetGeometry(geom.Simplify(float(tolerance)))
                lyr.CreateFeature(feat)
            else:
                cpt += 1
        dataset.Destroy()
        print(f"Simplification process created {cpt} empty geometry. "
              "All these geometries have been deleted")
    except:
        return False
    return True


if __name__ == '__main__':
    usage = "usage: simplify <infile> <outfile> <tolerance>"
    if len(sys.argv) == 4:
        if simplify(sys.argv[1], sys.argv[2], sys.argv[3]):
            print("Simplify succeeded !")
            sys.exit(0)
        else:
            print("Simplify failed")
            sys.exit(1)
    else:
        print(usage)
        sys.exit(1)
