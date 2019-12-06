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
import os

import rasterio
from rasterio.transform import Affine
from rasterio.io import MemoryFile
from rasterio.merge import merge
import numpy as np

from typing import List, Dict, Optional, Tuple, Union

# Only for typing
import otbApplication
from functools import partial


def apply_function(otb_pipeline: otbApplication,
                   labels: List[str],
                   working_dir: str,
                   function: partial,
                   output_path: Optional[str] = None,
                   mask: Optional[str] = None,
                   mask_value: Optional[int] = 0,
                   chunk_size_mode: Optional[str] = "auto",
                   chunck_size_x: Optional[int] = 10,
                   chunck_size_y: Optional[int] = 10,
                   ram: Optional[int] = 128) -> Tuple[np.ndarray, List[str], Affine, int]:
    """
    Parameters
    ----------
    otb_pipeline: otbApplication
        otb application ready to be Execute()
    labels: List[str]
        list of input bands names
    working_dir: str
        working directory path
    function: partial
        function to apply
    output_path: str
        output raster path (optional)
    mask: str
        input mask path (optional)
    mask_value: int
        input mask value to consider (optional)
    chunck_size_x: int
        chunck x size (optional)
    chunck_size_y: int
        chunck y size (optional)
    ram: int
        available ram

    Return
    ------
    tuple
        (np.array, new_labels, affine transform, epsg code)
    """
    from iota2.Tests.UnitTests.TestsUtils import rasterToArray

    mosaic = new_labels = None

    roi_rasters, epsg_code = split_raster(otb_pipeline=otb_pipeline,
                                          chunk_size_mode=chunk_size_mode,
                                          chunk_size=(chunck_size_x,
                                                      chunck_size_y),
                                          ram_per_chunk=ram,
                                          working_dir=working_dir)
    mask_array = None
    if mask:
        mask_array = rasterToArray(mask)

    new_arrays = []
    for index, roi_raster in enumerate(roi_rasters):
        start_x = int(roi_raster.GetParameterString("startx"))
        size_x = int(roi_raster.GetParameterString("sizex"))
        start_y = int(roi_raster.GetParameterString("starty"))
        size_y = int(roi_raster.GetParameterString("sizey"))

        roi_array, proj_geotransform = process_function(roi_raster,
                                                        function=function,
                                                        mask_arr=mask_array,
                                                        mask_value=mask_value,
                                                        mask_box=(start_x,
                                                                  size_x,
                                                                  start_y,
                                                                  size_y))
        new_arrays.append((roi_array, proj_geotransform))

    all_data_sets = get_rasterio_datasets(new_arrays, mask_value)
    mosaic, out_trans = merge(all_data_sets)
    if output_path:
        with rasterio.open(output_path,
                           "w",
                           driver='GTiff',
                           height=mosaic.shape[1],
                           width=mosaic.shape[2],
                           count=mosaic.shape[0],
                           crs="EPSG:{}".format(epsg_code),
                           transform=out_trans,
                           dtype=mosaic.dtype) as dest:
            dest.write(mosaic)

    # TODO : new_labels definition
    return mosaic, new_labels, out_trans, epsg_code


def get_rasterio_datasets(array_proj: List[Tuple[Union[np.ndarray, int], Dict]],
                          mask_value: Optional[int] = 0) -> List[rasterio.io.DatasetReader]:
    """transform numpy arrays (containing projection data) to rasterio datasets
        it works only with 3D arrays
    """
    all_data_sets = []
    expected_arr_shapes = set([arr[0].shape for arr in array_proj if isinstance(arr[0], np.ndarray)])
    expected_arr_shape = list(expected_arr_shapes)[0]
    expected_arr_types = set([arr[0].dtype for arr in array_proj if isinstance(arr[0], np.ndarray)])
    expected_arr_type = list(expected_arr_types)[0]

    for index, new_array in enumerate(array_proj):
        array = new_array[0]
        if isinstance(array, int):
            array = np.full(expected_arr_shape, mask_value, dtype=expected_arr_type)

        proj = new_array[-1]["projection"]
        geo_transform = new_array[-1]["geo_transform"]

        if index == 0:
            epsg_code = proj.GetAttrValue("AUTHORITY", 1)

        transform = Affine.from_gdal(*geo_transform)
        array_ordered = np.moveaxis(array, -1, 0)
        array_ordered_shape = array_ordered.shape

        if len(array_ordered_shape) != 3:
            raise ValueError("array's must be 3D")
        else:
            height = array_ordered_shape[1]
            width = array_ordered_shape[2]
            count = array_ordered_shape[0]
        with MemoryFile() as memfile:
            with memfile.open(driver='GTiff',
                              height=height,
                              width=width,
                              count=count,
                              dtype=array.dtype,
                              crs="EPSG:{}".format(epsg_code),
                              transform=transform) as dataset:
                dataset.write(array_ordered)
            all_data_sets.append(memfile.open())
    return all_data_sets


def process_function(otb_pipeline: otbApplication,
                     function: partial,
                     mask_arr: Optional[np.ndarray] = None,
                     mask_value: Optional[int] = 0,
                     mask_box: Optional[Tuple[int, int, int, int]] = None) -> Tuple[np.ndarray, Dict]:
    """apply python function to the output of an otbApplication

    Parameters
    ----------
    otb_pipeline : otbApplication
        otb application ready to be Execute()
    function : itertools.partial
        function manipulating numpy array
    mask_arr: np.ndarray
        mask raster array
    mask_value: int
        every pixels under 'mask_value' will be ignored
    mask_box : tuple
        mask bbox
    Return
    ------
    tuple
        (np.ndarray, dict)
    """
    import osr

    roi_to_ignore = False
    roi_contains_mask_part = False
    if mask_arr is not None:
        start_x, size_x, start_y, size_y = mask_box
        mask_roi = mask_arr[start_y:start_y + size_y, start_x:start_x + size_x]
        unique_mask_values = np.unique(mask_roi)
        if len(unique_mask_values) == 1 and unique_mask_values[0] == mask_value:
            roi_to_ignore = True
        elif len(unique_mask_values) > 1 and mask_value in unique_mask_values:
            roi_contains_mask_part = True

    otb_pipeline.Execute()
    array = otb_pipeline.GetVectorImageAsNumpyArray("out")

    proj = otb_pipeline.GetImageProjection("out")
    projection = osr.SpatialReference()
    projection.ImportFromWkt(proj)
    origin_x, origin_y = otb_pipeline.GetImageOrigin("out")
    xres, yres = otb_pipeline.GetImageSpacing("out")

    # gdal offset
    geo_transform = [origin_x - xres / 2.0,
                     xres,
                     0,
                     origin_y - yres / 2.0,
                     0,
                     yres]

    if roi_to_ignore is False:
        output_arr = function(array)
        if roi_contains_mask_part:
            mask_roi = np.repeat(mask_roi[:, :, np.newaxis], output_arr.shape[-1], axis=2)
            output_arr = output_arr * mask_roi
        output = (output_arr,
                  {"projection": projection, "geo_transform": geo_transform})
    else:
        output = (mask_value,
                  {"projection": projection, "geo_transform": geo_transform})
    return output


def get_chunks_boundaries(chunk_size: Tuple[int, int],
                          shape: Tuple[int, int]) -> List[Dict[str, int]]:
    """from numpy array shape, return chunks boundaries (Extract ROI coordinates)

    Parameters
    ----------
    chunk_size : tuple
        tuple(chunk_size_x, chunk_size_y)
    shape : tuple
        tuple(size_x, size_y)

    Return
    ------
    dict
        {"startx": int,
         "sizex" : int,
         "starty": int,
         "sizey" : int}
    """
    import numpy as np
    chunk_size_x, chunk_size_y = chunk_size[0], chunk_size[1]
    size_x, size_y = shape[0], shape[1]
    boundaries = []
    for y in np.arange(0, size_y, chunk_size_y):
        start_y = y
        for x in np.arange(0, size_x, chunk_size_x):
            start_x = x
            boundaries.append({"startx": start_x,
                               "sizex": chunk_size_x,
                               "starty": start_y,
                               "sizey": chunk_size_y})
    return boundaries


OTB_CHUNK = Tuple[type(otbApplication), int]


def split_raster(otb_pipeline: otbApplication,
                 chunk_size_mode: str,
                 chunk_size: Tuple[int, int],
                 ram_per_chunk: int,
                 working_dir: str) -> List[OTB_CHUNK]:
    """extract regions of interest over the otbApplication

    Parameters
    ----------
    otb_pipeline : otbApplication
        otb application
    chunk_size : tuple
        tuple(chunk_size_x, chunk_size_y)
    ram_per_chunk : int
        otb's pipeline size (Mo)
    working_dir : str
        working directory
    """
    import osr
    from iota2.Common.OtbAppBank import CreateExtractROIApplication

    otb_pipeline.Execute()

    proj = otb_pipeline.GetImageProjection("out")
    projection = osr.SpatialReference()
    projection.ImportFromWkt(proj)
    origin_x, origin_y = otb_pipeline.GetImageOrigin("out")
    xres, yres = otb_pipeline.GetImageSpacing("out")
    x_size, y_size = otb_pipeline.GetImageSize("out")

    if chunk_size_mode == "auto":
        # ~ TODO : -> otb_pipeline.GetImageRequestedRegion("out")[size] is (x, y) or (y, x) ?
        chunk_size = tuple(otb_pipeline.GetImageRequestedRegion("out")["size"])

    independant_raster = []
    boundaries = get_chunks_boundaries(chunk_size, shape=(x_size, y_size))
    for index, boundary in enumerate(boundaries):
        roi = CreateExtractROIApplication({"in": otb_pipeline,
                                           "startx": boundary["startx"],
                                           "sizex": boundary["sizex"],
                                           "starty": boundary["starty"],
                                           "sizey": boundary["sizey"],
                                           "out": os.path.join(working_dir,
                                                               "ROI_{}.tif".format(index))})
        independant_raster.append(roi)
    return independant_raster, projection.GetAttrValue("AUTHORITY", 1)
