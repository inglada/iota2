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
""""""
import os

import logging
from typing import List, Dict, Optional, Tuple, Union
from functools import partial
import numpy as np
import rasterio
from rasterio.merge import merge
from rasterio.io import MemoryFile
from rasterio.transform import Affine
from iota2.Common.FileUtils import memory_usage_psutil
from iota2.Common.Utils import run
# Only for typing
import otbApplication

LOGGER = logging.getLogger(__name__)


def compress_raster(raster_in: str,
                    raster_out: str,
                    compress_mode: Optional[str] = "LZW") -> bool:
    """ compress a raster thanks to gdal_translate
    """
    success = True
    command = f"gdal_translate -co 'COMPRESS={compress_mode}' {raster_in} {raster_out}"
    try:
        run(command)
    except Exception:
        success = False
    return success


def insert_external_function_to_pipeline(
        otb_pipeline: otbApplication,
        labels: List[str],
        working_dir: str,
        function: partial,
        output_path: Optional[str] = None,
        mask: Optional[str] = None,
        mask_value: Optional[int] = 0,
        chunk_size_mode: Optional[str] = "user_fixed",
        chunk_size_x: Optional[int] = 10,
        chunk_size_y: Optional[int] = 10,
        targeted_chunk: Optional[int] = None,
        number_of_chunks: Optional[int] = None,
        output_number_of_bands: Optional[int] = None,
        ram: Optional[int] = 128,
        logger=LOGGER,
) -> Tuple[np.ndarray, List[str], Affine, int]:
    """Apply a python function to an otb pipeline

    If a mask is provided (values not to be taken into account are 'mask_value'),
    then the resulting output could be define as the following :
    output = output * mask

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
    chunk_size_x: int
        chunk x size (optional)
    chunk_size_y: int
        chunk y size (optional)
    targeted_chunk : int
        process only the targeted chunk
    output_number_of_bands : int
        used only if targeted_chunk and mask are set
    ram: int
        available ram

    Return
    ------
    tuple
        (np.array, new_labels, affine transform, epsg code)
    """
    from iota2.Tests.UnitTests.TestsUtils import rasterToArray

    mosaic = new_labels = None

    roi_rasters, epsg_code = split_raster(
        otb_pipeline=otb_pipeline,
        chunk_size_mode=chunk_size_mode,
        chunk_size=(chunk_size_x, chunk_size_y),
        number_of_chunks=number_of_chunks,
        ram_per_chunk=ram,
        working_dir=working_dir,
    )
    if targeted_chunk is not None:
        roi_rasters = [roi_rasters[targeted_chunk]]

    mask_array = None
    if mask:
        mask_array = rasterToArray(mask)

    new_arrays = []
    chunks_mask = []
    for roi_raster in roi_rasters:
        start_x = int(roi_raster.GetParameterString("startx"))
        size_x = int(roi_raster.GetParameterString("sizex"))
        start_y = int(roi_raster.GetParameterString("starty"))
        size_y = int(roi_raster.GetParameterString("sizey"))

        region_info = (f"processing region start_x : {start_x} size_x :"
                       f" {size_x} start_y : {start_y} size_y : {size_y}")
        logger.info(region_info)
        print(region_info)
        print("memory usage : {}".format(memory_usage_psutil()))
        (roi_array,
         proj_geotransform), mask, new_labels, otbimage = process_function(
             roi_raster,
             function=function,
             mask_arr=mask_array,
             mask_value=mask_value,
             stream_bbox=(start_x, size_x, start_y, size_y),
         )
        new_arrays.append((roi_array, proj_geotransform))
        chunks_mask.append(mask)

    all_data_sets = get_rasterio_datasets(
        new_arrays,
        mask_value,
        force_output_shape=(size_y, size_x, output_number_of_bands),
    )
    if len(all_data_sets) > 1:
        mosaic, out_trans = merge(all_data_sets)
    else:
        if isinstance(new_arrays[0][0], int):
            mosaic = np.repeat(mask[np.newaxis, :, :],
                               output_number_of_bands,
                               axis=0)
        else:
            mosaic = np.moveaxis(new_arrays[0][0], -1, 0)
        out_trans = all_data_sets[0].transform
    if output_path:
        with rasterio.open(
                output_path,
                "w",
                driver="GTiff",
                height=mosaic.shape[1],
                width=mosaic.shape[2],
                count=mosaic.shape[0],
                crs="EPSG:{}".format(epsg_code),
                transform=out_trans,
                dtype=mosaic.dtype,
        ) as dest:
            dest.write(mosaic)
    # the returned otbimage is a dictionary
    # we don't need a list as only the object (swig) is relevant the
    # final dictionary is overwritted by insert_external_function_to_pipeline
    return mosaic, new_labels, out_trans, epsg_code, chunks_mask, otbimage


def get_rasterio_datasets(
        array_proj: List[Tuple[Union[np.ndarray, int], Dict]],
        mask_value: Optional[int] = 0,
        force_output_shape: Optional[Tuple[int, int, int]] = (1, 1, 1),
        force_output_type: Optional[str] = "int32",
) -> List[rasterio.io.DatasetReader]:
    """transform numpy arrays (containing projection data) to rasterio datasets
        it works only with 3D arrays
    """
    all_data_sets = []
    expected_arr_shapes = set(
        [arr[0].shape for arr in array_proj if isinstance(arr[0], np.ndarray)])
    if not expected_arr_shapes:
        expected_arr_shapes = [force_output_shape]
    expected_arr_shape = list(expected_arr_shapes)[0]
    expected_arr_types = set(
        [arr[0].dtype for arr in array_proj if isinstance(arr[0], np.ndarray)])
    if not expected_arr_types:
        expected_arr_types = [force_output_type]
    expected_arr_type = list(expected_arr_types)[0]

    for index, new_array in enumerate(array_proj):
        array = new_array[0]
        if isinstance(array, int):
            array = np.full(expected_arr_shape,
                            mask_value,
                            dtype=expected_arr_type)

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
            with memfile.open(
                    driver="GTiff",
                    height=height,
                    width=width,
                    count=count,
                    dtype=array.dtype,
                    crs="EPSG:{}".format(epsg_code),
                    transform=transform,
            ) as dataset:
                dataset.write(array_ordered)
            all_data_sets.append(memfile.open())
    return all_data_sets


def process_function(
        otb_pipeline: otbApplication,
        function: partial,
        mask_arr: Optional[np.ndarray] = None,
        mask_value: Optional[int] = 0,
        stream_bbox: Optional[Tuple[int, int, int, int]] = None,
) -> Tuple[np.ndarray, Dict, List[str]]:
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
    stream_bbox : tuple
        stream bounding box
    Return
    ------
    tuple
        (np.ndarray, dict)
    """
    import osr
    from sklearn.preprocessing import binarize

    roi_to_ignore = False
    roi_contains_mask_part = False
    mask_roi = None
    if mask_arr is not None:
        start_x, size_x, start_y, size_y = stream_bbox
        mask_roi = mask_arr[start_y:start_y + size_y, start_x:start_x + size_x]
        mask_roi = binarize(mask_roi)
        unique_mask_values = np.unique(mask_roi)
        if len(unique_mask_values
               ) == 1 and unique_mask_values[0] == mask_value:
            roi_to_ignore = True
        elif len(unique_mask_values) > 1 and mask_value in unique_mask_values:
            roi_contains_mask_part = True
    otb_pipeline.Execute()
    # remove this call to GetVectorImageAsNumpyArray
    # allow a gain of few seconds requiered to initialise otbimage object
    # This step is very time consumming as the whole pipeline is computed here
    # array = otb_pipeline.GetVectorImageAsNumpyArray("out")
    otbimage = otb_pipeline.ExportImage("out")
    proj = otb_pipeline.GetImageProjection("out")
    projection = osr.SpatialReference()
    projection.ImportFromWkt(proj)
    origin_x, origin_y = otb_pipeline.GetImageOrigin("out")
    xres, yres = otb_pipeline.GetImageSpacing("out")
    # gdal offset
    geo_transform = [
        origin_x - xres / 2.0, xres, 0, origin_y - yres / 2.0, 0, yres
    ]
    new_labels = []
    if roi_to_ignore is False:

        output_arr, new_labels = function(otbimage["array"])

        if roi_contains_mask_part:
            output_arr = output_arr * mask_roi[:, :, np.newaxis]
        output = (
            output_arr,
            {
                "projection": projection,
                "geo_transform": geo_transform
            },
        )
    else:
        output = (
            mask_value,
            {
                "projection": projection,
                "geo_transform": geo_transform
            },
        )
    otb_pipeline = None

    return output, mask_roi, new_labels, otbimage


def get_chunks_boundaries(
        chunk_size: Tuple[int, int],
        shape: Tuple[int, int],
        chunk_size_mode: str,
        number_of_chunks: int,
        ram_estimation: int,
        ram_per_chunk: int,
) -> List[Dict[str, int]]:
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

    # if chunk_size_mode == "auto":
    #     ram_estimation = ram_estimation * 1.5
    #     nb_chunks = math.ceil(ram_estimation / ram_per_chunk)
    #     chunk_size_x = size_x
    #     chunk_size_y = int(math.ceil(float(size_y) / float(nb_chunks)))

    if chunk_size_mode == "user_fixed":
        boundaries = []
        for y in np.arange(0, size_y, chunk_size_y):
            start_y = y
            for x in np.arange(0, size_x, chunk_size_x):
                start_x = x
                boundaries.append({
                    "startx": start_x,
                    "sizex": chunk_size_x,
                    "starty": start_y,
                    "sizey": chunk_size_y,
                })

    elif chunk_size_mode == "split_number":

        if number_of_chunks > size_x + size_y:
            raise ValueError(
                f"Error: number of chunks ({number_of_chunks})"
                f"vastly exceeds the image size ({size_x * size_y} pixels)")
        if number_of_chunks > size_y:
            unused_chunks = number_of_chunks - size_y
            split_x = np.linspace(0, size_x, unused_chunks + 1)
            split_y = np.linspace(0, size_y, size_y + 1)
            print(split_y)
        else:
            split_x = np.linspace(0, size_x, 2)
            split_y = np.linspace(0, size_y, number_of_chunks + 1)

        boundaries = []

        split_y = [math.floor(x) for x in split_y]
        split_x = [math.floor(x) for x in split_x]

        for i, start_y in enumerate(split_y[:-1]):

            for j, start_x in enumerate(split_x[:-1]):
                boundaries.append({
                    "startx": start_x,
                    "sizex": split_x[j + 1] - start_x,
                    "starty": start_y,
                    "sizey": split_y[i + 1] - start_y
                })
    else:
        raise ValueError(
            f"Unknow split method {chunk_size_mode}, only split_number"
            " and user_fixed are handled")

    return boundaries


OTB_CHUNK = Tuple[type(otbApplication), int]


def split_raster(
        otb_pipeline: otbApplication,
        chunk_size_mode: str,
        chunk_size: Tuple[int, int],
        number_of_chunks: int,
        ram_per_chunk: int,
        working_dir: str,
) -> List[OTB_CHUNK]:
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

    ram_estimation = otb_pipeline.PropagateRequestedRegion(
        key="out", region=otb_pipeline.GetImageRequestedRegion("out"))

    print("x_size : {} et y_size : {}".format(x_size, y_size))

    roi = CreateExtractROIApplication({
        "in": otb_pipeline,
        "cl": ["Channel1"],
        "ram": "60000"
    })
    print("Compute bounds")
    boundaries = get_chunks_boundaries(
        chunk_size,
        shape=(x_size, y_size),
        chunk_size_mode=chunk_size_mode,
        number_of_chunks=number_of_chunks,
        ram_estimation=float(ram_estimation),
        ram_per_chunk=float(ram_per_chunk) * 1024**2,
    )
    independant_raster = []
    print("Create ROI app")
    for index, boundary in enumerate(boundaries):
        output_roi = ""
        if working_dir:
            output_roi = os.path.join(working_dir, "ROI_{}.tif".format(index))
        roi = CreateExtractROIApplication({
            "in": otb_pipeline,
            "startx": boundary["startx"],
            "sizex": boundary["sizex"],
            "starty": boundary["starty"],
            "sizey": boundary["sizey"],
            "out": output_roi,
        })
        independant_raster.append(roi)
    print("end split")
    return independant_raster, projection.GetAttrValue("AUTHORITY", 1)


def merge_rasters(
        rasters: List[str],
        output_path: str,
        epsg_code: int,
        working_dir: Optional[str] = None,
) -> Tuple[np.ndarray, Affine]:
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
    from iota2.Common.FileUtils import getRasterResolution
    res_x, res_y = getRasterResolution(rasters[0])
    assembleTile_Merge(rasters, (res_x, -res_y),
                       output_path,
                       ot="Int16",
                       co=None)
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
