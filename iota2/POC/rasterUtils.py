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

from typing import List, Dict, Optional, Tuple

# Only for typing
import otbApplication
from functools import partial


def apply_function(otb_pipeline: otbApplication,
                   labels: List[str],
                   working_dir: str,
                   function: partial,
                   output_path: Optional[str] = None,
                   chunck_size_x: Optional[int] = 10,
                   chunck_size_y: Optional[int] = 10,
                   ram: Optional[int] = 128) -> Tuple[np.ndarray, List[str]]:
    """
    Parameters
    ----------
    otb_pipeline: otbApplication
    labels: List[str]
    working_dir: str
    function: partial
    output_path: str
    chunck_size_x: int
    chunck_size_y: int
    ram: int

    Return
    ------
    tuple
        (np.array, new_labels)
    """
    mosaic = new_labels = None

    roi_rasters, epsg_code = split_raster(otb_pipeline=otb_pipeline,
                                          chunk_size=(chunck_size_x,
                                                      chunck_size_y),
                                          ram_per_chunk=ram,
                                          working_dir=working_dir)
    new_arrays = []
    for index, roi_raster in enumerate(roi_rasters):
        roi_array, proj_geotransform = process_function(roi_raster,
                                                        function=function)
        new_arrays.append((roi_array, proj_geotransform))

    all_data_sets = get_rasterio_datasets(new_arrays)
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
    return mosaic, new_labels


def get_rasterio_datasets(array_proj: List[Tuple[np.ndarray, Dict]]) -> \
                          List[rasterio.io.DatasetReader]:
    """transform numpy arrays (containing projection data) to rasterio datasets
        it works only with 2D and 3D arrays
    """
    all_data_sets = []
    for index, new_array in enumerate(array_proj):

        array = new_array[0]
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
                     function: partial) -> Tuple[np.ndarray, Dict]:
    """apply python function to the output of an otbApplication

    Parameters
    ----------
    otb_pipeline : otbApplication
        otb application ready to be Execute()
    function : itertools.partial
        function manipulating numpy array

    Return
    ------
    tuple
        (np.ndarray, dict)
    """
    import osr
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

    return (function(array),
            {"projection": projection, "geo_transform": geo_transform})


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

    # TODO : ram_estimation could be useful if chunck_size == "auto"
    # ~ ram_estimation = otb_pipeline.PropagateRequestedRegion(key="out",
    # ~ region=otb_pipeline.GetImageRequestedRegion("out"))

    independent_raster = []
    boundaries = get_chunks_boundaries(chunk_size, shape=(x_size, y_size))
    for index, boundary in enumerate(boundaries):
        roi = CreateExtractROIApplication({"in": otb_pipeline,
                                           "startx": boundary["startx"],
                                           "sizex": boundary["sizex"],
                                           "starty": boundary["starty"],
                                           "sizey": boundary["sizey"],
                                           "out": os.path.join(working_dir,
                                                               "ROI_{}.tif".
                                                               format(index))})
        independent_raster.append(roi)
    return independent_raster, projection.GetAttrValue("AUTHORITY", 1)
