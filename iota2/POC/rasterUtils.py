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

import logging
import rasterio
import numpy as np
from rasterio.merge import merge
from rasterio.io import MemoryFile
from rasterio.transform import Affine
from typing import List, Dict, Optional, Tuple, Union

from iota2.Common.FileUtils import memory_usage_psutil
# Only for typing
import otbApplication
from functools import partial

logger = logging.getLogger(__name__)


def apply_function(otb_pipeline: otbApplication,
                   labels: List[str],
                   working_dir: str,
                   function: partial,
                   output_path: Optional[str] = None,
                   mask: Optional[str] = None,
                   mask_value: Optional[int] = 0,
                   chunk_size_mode: Optional[str] = "user_fixed",
                   chunck_size_x: Optional[int] = 10,
                   chunck_size_y: Optional[int] = 10,
                   targeted_chunk: Optional[int] = None,
                   number_of_chunks: Optional[int] = None,
                   output_number_of_bands: Optional[int] = None,
                   ram: Optional[int] = 128,
                   logger=logger) -> Tuple[np.ndarray, List[str], Affine, int]:
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
    chunk_size_mode : str
        "user_fixed" / "auto" / "split_number"
    chunck_size_x: int
        chunck x size (optional)
    chunck_size_y: int
        chunck y size (optional)
    targeted_chunk : int
        process only the targeted chunk
    output_number_of_bands : int
        use only if targeted_chunk and mask are set
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
                                          number_of_chunks=number_of_chunks,
                                          ram_per_chunk=ram,
                                          working_dir=working_dir)
    if targeted_chunk is not None:
        roi_rasters = [roi_rasters[targeted_chunk]]

    mask_array = None
    if mask:
        mask_array = rasterToArray(mask)

    new_arrays = []
    chunks_mask = []
    for index, roi_raster in enumerate(roi_rasters):
        start_x = int(roi_raster.GetParameterString("startx"))
        size_x = int(roi_raster.GetParameterString("sizex"))
        start_y = int(roi_raster.GetParameterString("starty"))
        size_y = int(roi_raster.GetParameterString("sizey"))

        region_info = "processing region start_x : {} size_x : {} start_y : {} size_y : {}".format(start_x,
                                                                                                   size_x,
                                                                                                   start_y,
                                                                                                   size_y)
        logger.info(region_info)
        print(region_info)
        print("memory usage : {}".format(memory_usage_psutil()))
        (roi_array, proj_geotransform), mask = process_function(roi_raster,
                                                                function=function,
                                                                mask_arr=mask_array,
                                                                mask_value=mask_value,
                                                                mask_box=(start_x,
                                                                          size_x,
                                                                          start_y,
                                                                          size_y))
        new_arrays.append((roi_array, proj_geotransform))
        chunks_mask.append(mask)

    all_data_sets = get_rasterio_datasets(new_arrays,
                                          mask_value,
                                          force_output_shape=(size_y,
                                                              size_x,
                                                              output_number_of_bands))
    if len(all_data_sets) > 1:
        mosaic, out_trans = merge(all_data_sets)
    else:
        if isinstance(new_arrays[0][0], int):
            mosaic = np.repeat(mask[np.newaxis, :, :], output_number_of_bands, axis=0)
        else:
            mosaic = np.moveaxis(new_arrays[0][0], -1, 0)
        out_trans = all_data_sets[0].transform
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
    return mosaic, new_labels, out_trans, epsg_code, chunks_mask


def get_rasterio_datasets(array_proj: List[Tuple[Union[np.ndarray, int], Dict]],
                          mask_value: Optional[int] = 0,
                          force_output_shape: Optional[Tuple[int, int, int]] = (1, 1, 1),
                          force_output_type: Optional[str] = "int32") -> List[rasterio.io.DatasetReader]:
    """transform numpy arrays (containing projection data) to rasterio datasets
        it works only with 3D arrays
    """
    all_data_sets = []
    expected_arr_shapes = set([arr[0].shape for arr in array_proj if isinstance(arr[0], np.ndarray)])
    if not expected_arr_shapes:
        expected_arr_shapes = [force_output_shape]
    expected_arr_shape = list(expected_arr_shapes)[0]
    expected_arr_types = set([arr[0].dtype for arr in array_proj if isinstance(arr[0], np.ndarray)])
    if not expected_arr_types:
        expected_arr_types = [force_output_type]
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
    from sklearn.preprocessing import binarize

    roi_to_ignore = False
    roi_contains_mask_part = False
    if mask_arr is not None:
        start_x, size_x, start_y, size_y = mask_box
        mask_roi = mask_arr[start_y:start_y + size_y, start_x:start_x + size_x]
        mask_roi = binarize(mask_roi)
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
            mask_roi_bands = np.repeat(mask_roi[:, :, np.newaxis], output_arr.shape[-1], axis=2)
            output_arr = output_arr * mask_roi_bands
        output = (output_arr,
                  {"projection": projection, "geo_transform": geo_transform})
    else:
        output = (mask_value,
                  {"projection": projection, "geo_transform": geo_transform})
    otb_pipeline = None
    return output, mask_roi


def get_chunks_boundaries(chunk_size: Tuple[int, int],
                          shape: Tuple[int, int],
                          chunk_size_mode: str,
                          number_of_chunks: int,
                          ram_estimation: int,
                          ram_per_chunk: int) -> List[Dict[str, int]]:
    """from numpy array shape, return chunks boundaries (Extract ROI coordinates)

    Parameters
    ----------
    chunk_size : tuple
        tuple(chunk_size_x, chunk_size_y)
    shape : tuple
        tuple(size_x, size_y)
    chunk_size_mode : str
        flag
    number_of_chunks : int
        use if chunk_size_mode is "split_number"
    ram_estimation : float
        ram estimation to compute the whole OTB process (in octets)
    ram_per_chunk : float
        ram per chunks in octets
    Return
    ------
    dict
        {"startx": int,
         "sizex" : int,
         "starty": int,
         "sizey" : int}
    """
    import math
    import numpy as np

    chunk_size_x, chunk_size_y = chunk_size[0], chunk_size[1]
    size_x, size_y = shape[0], shape[1]

    if chunk_size_mode == "auto":
        ram_estimation = ram_estimation * 1.5
        nb_chunks = math.ceil(ram_estimation / ram_per_chunk)
        chunk_size_x = size_x
        chunk_size_y = int(math.ceil(float(size_y) / float(nb_chunks)))
    elif chunk_size_mode == "split_number":
        chunk_size_x = size_x
        chunk_size_y = int(math.ceil(float(size_y) / float(number_of_chunks)))

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
                 number_of_chunks: int,
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

    ram_estimation = otb_pipeline.PropagateRequestedRegion(key="out",
                                                           region=otb_pipeline.GetImageRequestedRegion("out"))

    print("x_size : {} et y_size : {}".format(x_size, y_size))

    roi = CreateExtractROIApplication({"in": otb_pipeline,
                                       "cl": ["Channel1"],
                                       "ram": "60000",
                                       "out": "/work/OT/theia/oso/arthur/TMP/test_ROI.tif"})
    boundaries = get_chunks_boundaries(chunk_size,
                                       shape=(x_size, y_size),
                                       chunk_size_mode=chunk_size_mode,
                                       number_of_chunks=number_of_chunks,
                                       ram_estimation=float(ram_estimation),
                                       ram_per_chunk=float(ram_per_chunk) * 1024 ** 2)
    independant_raster = []

    for index, boundary in enumerate(boundaries):
        output_roi = ""
        if working_dir:
            output_roi = os.path.join(working_dir, "ROI_{}.tif".format(index))
        roi = CreateExtractROIApplication({"in": otb_pipeline,
                                           "startx": boundary["startx"],
                                           "sizex": boundary["sizex"],
                                           "starty": boundary["starty"],
                                           "sizey": boundary["sizey"],
                                           "out": output_roi})
        independant_raster.append(roi)
    return independant_raster, projection.GetAttrValue("AUTHORITY", 1)


def merge_rasters(rasters: List[str],
                  output_path: str,
                  epsg_code: int,
                  working_dir: Optional[str] = None) -> Tuple[np.ndarray, Affine]:
    """merge geo-referenced rasters thanks to rasterio.merge

    Parameters
    ----------
    rasters : list
        list of raster's path
    output_path : str
        output path
    epsg_code : int
        output epsg code projection
    working_dir : str
        working directory

    Return
    ------
    tuple
        merged array, rasterio output transform
    """
    from iota2.Common.FileUtils import assembleTile_Merge
    assembleTile_Merge(rasters, 10, output_path, ot="Int16", co=None)
    # ~ rasters_datasets = [rasterio.open(raster) for raster in rasters]
    # ~ out_arr, out_trans = merge(rasters_datasets)
    # ~ if output_path:
        # ~ with rasterio.open(output_path,
                           # ~ "w",
                           # ~ driver='GTiff',
                           # ~ height=out_arr.shape[1],
                           # ~ width=out_arr.shape[2],
                           # ~ count=out_arr.shape[0],
                           # ~ crs="EPSG:{}".format(epsg_code),
                           # ~ transform=out_trans,
                           # ~ dtype=out_arr.dtype) as dest:
            # ~ dest.write(out_arr)
    # ~ return out_arr, out_trans