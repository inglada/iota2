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
import random
from typing import List, Optional
import osr
import gdal
import numpy as np
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


def generate_data_tree(directory, mtd_s2st_date, s2st_ext="jp2"):
    """generate a fake Sen2Cor data
    TODO : replace this function by downloading a Sen2Cor data from PEPS.

    Return
    ------
    products : list
        list of data ready to be generated
    """
    # from xml.dom.minidom import parse
    import xml.dom.minidom

    ensure_dir(directory)

    dom_tree = xml.dom.minidom.parse(mtd_s2st_date)
    collection = dom_tree.documentElement
    general_info_node = collection.getElementsByTagName("n1:General_Info")
    date_dir = general_info_node[0].getElementsByTagName(
        'PRODUCT_URI')[0].childNodes[0].data

    products = []
    for product_organisation_nodes in general_info_node[
            0].getElementsByTagName('Product_Organisation'):
        img_list_nodes = product_organisation_nodes.getElementsByTagName(
            "IMAGE_FILE")
        for img_list in img_list_nodes:
            new_prod = os.path.join(
                directory, date_dir,
                "{}.{}".format(img_list.childNodes[0].data, s2st_ext))
            new_prod_dir, _ = os.path.split(new_prod)
            ensure_dir(new_prod_dir)
            products.append(new_prod)
    return products


def generate_fake_s2_s2c_data(
        output_directory: str,
        tile_name: str,
        mtd_files: List[str],
        res: Optional[float] = 30.0,
        fake_raster: Optional[List[np.ndarray]] = [
            np.array([[10, 55, 61], [100, 56, 42], [1, 42, 29]])
        ],
        fake_scene_classification: Optional[List[np.ndarray]] = [
            np.array([[2, 0, 4], [0, 4, 2], [1, 1, 10]])
        ],
        origin_x: Optional[float] = 300000.0,
        origin_y: Optional[float] = 4900020.0,
        epsg_code: Optional[int] = 32631):
    """
    generate fake s2_s2c data
    """
    for mtd in mtd_files:
        prod_list = generate_data_tree(
            os.path.join(output_directory, tile_name), mtd)
        for prod in prod_list:
            if '10m.jp2' in prod:
                pix_size = 10
            if '20m.jp2' in prod:
                pix_size = 20
            if '60m.jp2' in prod:
                pix_size = 60
            if "_SCL_" in prod:
                array_raster = fake_scene_classification
            else:
                array_raster = fake_raster
            # output_driver has to be 'GTiff' even if S2ST are jp2
            array_to_raster(array_raster,
                            prod,
                            output_driver="GTiff",
                            output_format="int",
                            pixel_size=pix_size,
                            origin_x=origin_x,
                            origin_y=origin_y,
                            epsg_code=epsg_code)


def generate_fake_l8_data(root_directory: str,
                          tile_name: str,
                          dates: List[str],
                          res: Optional[float] = 30.0):
    """
    Parameters
    ----------
    root_directory : string
        path to generate Sentinel-2 dates
    tile_name : string
        THEIA tile name (ex:T31TCJ)
    dates : list
        list of strings reprensentig dates format : YYYYMMDD
    """

    tile_dir = os.path.join(root_directory, tile_name)
    ensure_dir(tile_dir)

    band_of_interest = ["B1", "B2", "B3", "B4", "B5", "B6", "B7"]
    masks_of_interest = ["BINARY_MASK", "CLM_XS", "EDG_XS", "SAT_XS"]

    origin_x = 566377
    origin_y = 6284029
    array_name = "iota2_binary"
    for date in dates:
        date_dir = os.path.join(tile_dir,
                                ("LANDSAT8-OLITIRS-XS_{}-000000-"
                                 "000_L2A_{}_D_V1-7".format(date, tile_name)))
        mask_date_dir = os.path.join(date_dir, "MASKS")
        ensure_dir(date_dir)
        ensure_dir(mask_date_dir)
        all_bands = []
        for cpt, mask in enumerate(masks_of_interest):
            new_mask = os.path.join(
                mask_date_dir,
                ("LANDSAT8-OLITIRS-XS_{}-000000-000_L2A"
                 "_{}_D_V1-7_FRE_{}.tif".format(date, tile_name, mask)))

            array_to_raster(fun_array(array_name) * cpt % 2,
                            new_mask,
                            pixel_size=res,
                            origin_x=origin_x,
                            origin_y=origin_y)
        for band in band_of_interest:
            new_band = os.path.join(
                date_dir,
                ("LANDSAT8-OLITIRS-XS_{}-000000-000_L2A"
                 "_{}_D_V1-7_FRE_{}.tif".format(date, tile_name, band)))
            all_bands.append(new_band)
            array = fun_array(array_name)
            random_array = []
            for val in array:
                val_tmp = []
                for pix_val in val:
                    val_tmp.append(pix_val * random.random() * 1000)
                random_array.append(val_tmp)

            array_to_raster(np.array(random_array),
                            new_band,
                            pixel_size=res,
                            origin_x=origin_x,
                            origin_y=origin_y)
            stack_date = os.path.join(
                date_dir, ("LANDSAT8-OLITIRS-XS_{}-000000-000_L2A_{}_D_V1-7"
                           "_FRE_STACK.tif".format(date, tile_name)))
            stack_app = CreateConcatenateImagesApplication({
                "il": all_bands,
                "out": stack_date
            })
            stack_app.ExecuteAndWriteOutput()


def generate_fake_user_features_data(root_directory: str, tile_name: str,
                                     patterns: List[str]):
    """
    Parameters
    ----------
    root_directory : string
        path to generate Sentinel-2 dates
    tile_name : string
        THEIA tile name (ex:T31TCJ)
    dates : list
        List of raster's name
    """

    tile_dir = os.path.join(root_directory, tile_name)
    ensure_dir(tile_dir)

    origin_x = 566377
    origin_y = 6284029
    array_name = "iota2_binary"

    array = fun_array(array_name)
    for pattern in patterns:
        user_features_path = os.path.join(tile_dir, f"{pattern}.tif")
        random_array = []
        for val in array:
            val_tmp = []
            for pix_val in val:
                val_tmp.append(pix_val * random.random() * 1000)
            random_array.append(val_tmp)
        array_to_raster(np.array(random_array),
                        user_features_path,
                        origin_x=origin_x,
                        origin_y=origin_y)


def generate_fake_s2_l3a_data(root_directory: str,
                              tile_name: str,
                              dates: List[str],
                              res: Optional[float] = 30.0):
    """
    Parameters
    ----------
    root_directory : string
        path to generate Sentinel-2 l3a dates
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
    masks_of_interest = ["BINARY_MASK", "FLG_R1"]

    origin_x = 566377
    origin_y = 6284029
    array_name = "iota2_binary"
    for date in dates:
        date_dir = os.path.join(tile_dir,
                                ("SENTINEL2X_{}-000000-"
                                 "000_L3A_{}_D_V1-7".format(date, tile_name)))
        mask_date_dir = os.path.join(date_dir, "MASKS")
        ensure_dir(date_dir)
        ensure_dir(mask_date_dir)
        all_bands = []
        for cpt, mask in enumerate(masks_of_interest):
            new_mask = os.path.join(
                mask_date_dir,
                ("SENTINEL2X_{}-000000-000_L3A"
                 "_{}_D_V1-7_{}.tif".format(date, tile_name, mask)))

            array_to_raster(fun_array(array_name) * cpt % 2,
                            new_mask,
                            pixel_size=res,
                            origin_x=origin_x,
                            origin_y=origin_y)
        for band in band_of_interest:
            new_band = os.path.join(
                date_dir,
                ("SENTINEL2X_{}-000000-000_L3A"
                 "_{}_D_V1-7_FRC_{}.tif".format(date, tile_name, band)))
            all_bands.append(new_band)
            array = fun_array(array_name)
            random_array = []
            for val in array:
                val_tmp = []
                for pix_val in val:
                    val_tmp.append(pix_val * random.random() * 1000)
                random_array.append(val_tmp)

            array_to_raster(np.array(random_array),
                            new_band,
                            pixel_size=res,
                            origin_x=origin_x,
                            origin_y=origin_y)
            stack_date = os.path.join(
                date_dir, ("SENTINEL2X_{}-000000-000_L3A_{}_D_V1-7"
                           "_FRC_STACK.tif".format(date, tile_name)))
            stack_app = CreateConcatenateImagesApplication({
                "il": all_bands,
                "out": stack_date
            })
            stack_app.ExecuteAndWriteOutput()


def generate_fake_l5_old_data(root_directory: str,
                              tile_name: str,
                              dates: List[str],
                              res: Optional[float] = 30.0):
    """
    Parameters
    ----------
    root_directory : string
        path to generate Sentinel-2 dates
    tile_name : string
        THEIA tile name (ex:T31TCJ)
    dates : list
        list of strings reprensentig dates format : YYYYMMDD
    """

    tile_dir = os.path.join(root_directory, tile_name)
    ensure_dir(tile_dir)

    band_of_interest = ["B1", "B2", "B3", "B4", "B5", "B6"]
    masks_of_interest = ["DIV", "BINARY_MASK", "NUA", "SAT"]

    origin_x = 566377
    origin_y = 6284029
    array_name = "iota2_binary"
    for date in dates:
        date_dir = os.path.join(tile_dir,
                                (f"LANDSAT5_TM_XS_{date}_N2A_{tile_name}"))
        mask_date_dir = os.path.join(date_dir, "MASK")
        ensure_dir(date_dir)
        ensure_dir(mask_date_dir)
        all_bands = []
        for cpt, mask in enumerate(masks_of_interest):
            new_mask = os.path.join(mask_date_dir,
                                    (f"LANDSAT5_TM_XS_{date}_N2A"
                                     f"_{tile_name}_{mask}.TIF"))

            array_to_raster(fun_array(array_name) * cpt % 2,
                            new_mask,
                            pixel_size=res,
                            origin_x=origin_x,
                            origin_y=origin_y)
        for band in band_of_interest:
            new_band = os.path.join(date_dir, (f"LANDSAT5_TM_XS_{date}_N2A"
                                               f"_{tile_name}_{band}.TIF"))
            all_bands.append(new_band)
            array = fun_array(array_name)
            random_array = []
            for val in array:
                val_tmp = []
                for pix_val in val:
                    val_tmp.append(pix_val * random.random() * 1000)
                random_array.append(val_tmp)

            array_to_raster(np.array(random_array),
                            new_band,
                            pixel_size=res,
                            origin_x=origin_x,
                            origin_y=origin_y)
            stack_date = os.path.join(date_dir, (f"LANDSAT5_TM_XS_{date}_"
                                                 "N2A_ORTHO_SURF_CORR"
                                                 f"_PENTE_{tile_name}.TIF"))
            stack_app = CreateConcatenateImagesApplication({
                "il": all_bands,
                "out": stack_date
            })
            stack_app.ExecuteAndWriteOutput()


def generate_fake_l8_old_data(root_directory: str,
                              tile_name: str,
                              dates: List[str],
                              res: Optional[float] = 30.0):
    """
    Parameters
    ----------
    root_directory : string
        path to generate Sentinel-2 dates
    tile_name : string
        THEIA tile name (ex:T31TCJ)
    dates : list
        list of strings reprensentig dates format : YYYYMMDD
    """

    tile_dir = os.path.join(root_directory, tile_name)
    ensure_dir(tile_dir)

    band_of_interest = ["B1", "B2", "B3", "B4", "B5", "B6", "B7"]
    masks_of_interest = ["DIV", "BINARY_MASK", "NUA", "SAT"]

    origin_x = 566377
    origin_y = 6284029
    array_name = "iota2_binary"
    for date in dates:
        date_dir = os.path.join(
            tile_dir, (f"LANDSAT8_OLITIRS_XS_{date}_N2A_{tile_name}"))
        mask_date_dir = os.path.join(date_dir, "MASK")
        ensure_dir(date_dir)
        ensure_dir(mask_date_dir)
        all_bands = []
        for cpt, mask in enumerate(masks_of_interest):
            new_mask = os.path.join(mask_date_dir,
                                    (f"LANDSAT8_OLITIRS_XS_{date}_N2A"
                                     f"_{tile_name}_{mask}.TIF"))

            array_to_raster(fun_array(array_name) * cpt % 2,
                            new_mask,
                            pixel_size=res,
                            origin_x=origin_x,
                            origin_y=origin_y)
        for band in band_of_interest:
            new_band = os.path.join(date_dir,
                                    (f"LANDSAT8_OLITIRS_XS_{date}_N2A"
                                     f"_{tile_name}_{band}.TIF"))
            all_bands.append(new_band)
            array = fun_array(array_name)
            random_array = []
            for val in array:
                val_tmp = []
                for pix_val in val:
                    val_tmp.append(pix_val * random.random() * 1000)
                random_array.append(val_tmp)

            array_to_raster(np.array(random_array),
                            new_band,
                            pixel_size=res,
                            origin_x=origin_x,
                            origin_y=origin_y)
            stack_date = os.path.join(date_dir, (f"LANDSAT8_OLITIRS_XS_{date}_"
                                                 "N2A_ORTHO_SURF_CORR"
                                                 f"_PENTE_{tile_name}.TIF"))
            stack_app = CreateConcatenateImagesApplication({
                "il": all_bands,
                "out": stack_date
            })
            stack_app.ExecuteAndWriteOutput()


def prepare_annual_features(working_directory,
                            reference_directory,
                            pattern,
                            rename=None):
    """
    double all rasters's pixels
    rename must be a tuple
    """
    import iota2.Common.FileUtils as fut
    import shutil
    for dirname, dirnames, filenames in os.walk(reference_directory):
        # print path to all subdirectories first.
        for subdirname in dirnames:
            os.mkdir(
                os.path.join(dirname, subdirname).replace(
                    reference_directory,
                    working_directory).replace(rename[0], rename[1]))

        # print path to all filenames.
        for filename in filenames:
            shutil.copy(
                os.path.join(dirname, filename),
                os.path.join(dirname, filename).replace(
                    reference_directory,
                    working_directory).replace(rename[0], rename[1]))

    rasters_path = fut.FileSearch_AND(working_directory, True, pattern)
    for raster in rasters_path:
        cmd = ('otbcli_BandMathX -il ' + raster + ' -out ' + raster +
               ' -exp "im1+im1"')
        print(cmd)
        os.system(cmd)

    if rename:
        all_content = []
        for dirname, dirnames, filenames in os.walk(working_directory):
            # print path to all subdirectories first.
            for subdirname in dirnames:
                all_content.append(os.path.join(dirname, subdirname))

            # print path to all filenames.
            for filename in filenames:
                all_content.append(os.path.join(dirname, filename))
