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
import os
import osr
import gdal
import numpy as np
import random
from typing import List, Optional
from iota2.Common.FileUtils import ensure_dir
from iota2.Common.OtbAppBank import CreateConcatenateImagesApplication


def array_to_raster(input_array: np.ndarray,
                    output_raster_path: str,
                    output_format: Optional[str] = "int",
                    output_driver: Optional[str] = "GTiff",
                    pixel_size: Optional[float] = 30.0,
                    origin_x: Optional[float] = 777225.58,
                    origin_y: Optional[float] = 6825084.53,
                    epsg_code: Optional[int] = 2154):
    """usage : from an array of a list of array, create a raster

    Parameters
    ----------
    input_array : list
        list of numpy.array sorted by bands (fisrt array = band 1,
                                             N array = band N)
    output_raster_path : str
        output path
    output_format : str
        'int' or 'float'
    output_driver: str
        gdal outut format
    pixel_size: float
        pixel resolution
    origin_x: float
        x origin raster coordinate
    origin_y: float
        y origin raster coordinate
    epsg_code: int
        epsg code
    """

    if not isinstance(input_array, list):
        input_array = [input_array]
    nb_bands = len(input_array)
    rows = input_array[0].shape[0]
    cols = input_array[0].shape[1]

    driver = gdal.GetDriverByName(output_driver)
    if output_format == 'int':
        output_raster = driver.Create(output_raster_path, cols, rows,
                                      len(input_array), gdal.GDT_UInt16)
    elif output_format == 'float':
        output_raster = driver.Create(output_raster_path, cols, rows,
                                      len(input_array), gdal.GDT_Float32)
    if not output_raster:
        raise Exception("can not create : " + output_raster)
    output_raster.SetGeoTransform(
        (origin_x, pixel_size, 0, origin_y, 0, -pixel_size))

    for i in range(nb_bands):
        outband = output_raster.GetRasterBand(i + 1)
        outband.WriteArray(input_array[i])

    output_raster_srs = osr.SpatialReference()
    output_raster_srs.ImportFromEPSG(epsg_code)
    output_raster.SetProjection(output_raster_srs.ExportToWkt())
    outband.FlushCache()


def fun_array(fun: str):
    """arrays use in unit tests
    """
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


def generate_fake_s2_data(root_directory: str,
                          tile_name: str,
                          dates: List[str],
                          res: Optional[float] = 30.0):
    """
    Parameters
    ----------
    root_directory : str
        path to generate Sentinel-2 dates
    tile_name : string
        THEIA tile name (ex:T31TCJ)
    dates : list
        list of strings reprensentig dates format : YYYYMMDD
    """

    tile_dir = os.path.join(root_directory, tile_name)
    ensure_dir(tile_dir)

    band_of_interest = [
        "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"
    ]
    masks_of_interest = ["BINARY_MASK", "CLM_R1", "EDG_R1", "SAT_R1"]

    origin_x = 566377
    origin_y = 6284029
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

            array_to_raster(fun_array(array_name) * cpt % 2,
                            new_mask,
                            pixel_size=res,
                            origin_x=origin_x,
                            origin_y=origin_y)
        for band in band_of_interest:
            new_band = os.path.join(
                date_dir,
                ("SENTINEL2B_{}-000000-000_L2A"
                 "_{}_D_V1-7_FRE_{}.tif".format(date, tile_name, band)))
            all_bands.append(new_band)
            array = fun_array(array_name)
            random_array = []
            for y_coordinate in array:
                y_tmp = []
                for pix_val in y_coordinate:
                    y_tmp.append(pix_val * random.random() * 1000)
                random_array.append(y_tmp)

            array_to_raster(np.array(random_array),
                            new_band,
                            pixel_size=res,
                            origin_x=origin_x,
                            origin_y=origin_y)
            stack_date = os.path.join(
                date_dir, ("SENTINEL2B_{}-000000-000_L2A_{}_D_V1-7"
                           "_FRE_STACK.tif".format(date, tile_name)))
            stack_app = CreateConcatenateImagesApplication({
                "il": all_bands,
                "out": stack_date
            })
            stack_app.ExecuteAndWriteOutput()
