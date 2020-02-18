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

import os, sys, argparse
import shutil
import osgeo
import ogr
import gdal
import rasterio
import fiona
from rasterio.mask import mask


def maskraster(raster, shp, fid):
    with fiona.open(shp) as src:
        filtered = filter(lambda f: f['id'] == fid, src)

        for feature in filtered:
            shape = feature["geometry"]

    with rasterio.open(raster) as src:
        out_image, out_transform = mask(src, [shape], crop=True)
        print(out_image)


maskraster(
    "/work/OT/theia/oso/vincent/IOTA2_TEST_S2/IOTA2_Outputs/Results/final/Classif_Seed_0.tif",
    "/work/OT/theia/oso/vincent/IOTA2_TEST_S2/IOTA2_Outputs/Results/final/simplification/vectors/dept_31555.shp",
    "10")
