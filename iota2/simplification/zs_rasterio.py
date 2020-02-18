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

        feature = next(filtered)
        geometry = feature["geometry"]

    with rasterio.open(raster) as rast:
        out_image, out_transform = mask(rast, [geometry], crop=True)
        print(out_image)


maskraster(
    "/work/OT/theia/oso/production/cnes/production_2018/FRANCE_2018/final/Classif_Seed_0.tif",
    "/work/OT/theia/oso/vincent/IOTA2_TEST_S2/IOTA2_Outputs/Results/final/simplification/vectors/dept_31555.shp",
    "42")
