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
import os
import gdal

import rasterio
from rasterio.transform import Affine
from rasterio.io import MemoryFile
from rasterio.merge import merge
import numpy as np

from typing import List, Dict, Union, Optional, Tuple

#Only for typing
import otbApplication
from functools import partial


def apply_function(OTB_pipeline: otbApplication,
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
    OTB_pipeline: otbApplication
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
    new_array = new_labels = None

    ROI_rasters, epsg_code = split_raster(OTB_pipeline=OTB_pipeline,
                                          chunk_size=(chunck_size_x, chunck_size_y),
                                          ram_per_chunk=ram,
                                          working_dir=working_dir) 
    new_arrays = []
    for index, ROI_raster in enumerate(ROI_rasters):
        ROI_array, proj_geotransform = process_function(ROI_raster, function=function)
        new_arrays.append((ROI_array, proj_geotransform))

    all_data_sets = get_rasterio_datasets(new_arrays)
    mosaic, out_trans = merge(all_data_sets)
    if output_path:
        with rasterio.open(output_path, "w", driver='GTiff',
                           height=mosaic.shape[1], width=mosaic.shape[2], count=mosaic.shape[0],crs="EPSG:{}".format(epsg_code),
                           transform=out_trans, dtype=mosaic.dtype) as dest:
            dest.write(mosaic)

    # TODO : new_labels definition
    return mosaic, new_labels


def get_rasterio_datasets(array_proj: List[Tuple[np.ndarray, Dict]]) -> List[rasterio.io.DatasetReader]:
    """transform numpy arrays (containing projection data) to rasterio datasets
    """
    all_data_sets = []
    for index, new_array in enumerate(array_proj):
        
        array = new_array[0]
        proj = new_array[-1]["projection"]
        geo_transform = new_array[-1]["geo_transform"]
        
        if index==0:
            epsg_code = proj.GetAttrValue("AUTHORITY", 1)

        transform = Affine.from_gdal(*geo_transform)
        array_ordered = np.moveaxis(array, -1, 0)
        with MemoryFile() as memfile:
            with memfile.open(driver='GTiff',
                               height=array_ordered.shape[1],
                               width=array_ordered.shape[2],
                               count=array_ordered.shape[0],
                               dtype=array.dtype,
                               crs="EPSG:{}".format(epsg_code),
                               transform=transform) as dataset:
                dataset.write(array_ordered)
            all_data_sets.append(memfile.open())
    return all_data_sets


def process_function(OTB_pipeline: otbApplication,
                     function: partial) -> Tuple[np.ndarray, Dict]:
    """apply python function to the output of an otbApplication

    Parameters
    ----------
    OTB_pipeline : otbApplication
        otb application ready to be Execute()
    function : itertools.partial
        function manipulating numpy array

    Return
    ------
    tuple
        (np.ndarray, dict)
    """
    import osr
    OTB_pipeline.Execute()

    array = OTB_pipeline.GetVectorImageAsNumpyArray("out")

    proj = OTB_pipeline.GetImageProjection("out")    
    projection = osr.SpatialReference()
    projection.ImportFromWkt(proj)
    origin_x, origin_y = OTB_pipeline.GetImageOrigin("out")
    xres, yres = OTB_pipeline.GetImageSpacing("out")

    # gdal offset
    geo_transform = [origin_x - xres / 2.0, xres, 0, origin_y - yres / 2.0, 0, yres]
    
    return function(array), {"projection": projection, "geo_transform": geo_transform}


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

otbChunks = List[otbApplication]

def split_raster(OTB_pipeline: otbApplication,
                 chunk_size: Tuple[int, int],
                 ram_per_chunk: int,
                 working_dir: str) -> otbChunks:
    """extract regions of interest over the otbApplication

    Parameters
    ----------
    OTB_pipeline : otbApplication
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
    
    OTB_pipeline.Execute()
    
    proj = OTB_pipeline.GetImageProjection("out")    
    projection = osr.SpatialReference()
    projection.ImportFromWkt(proj)
    origin_x, origin_y = OTB_pipeline.GetImageOrigin("out")
    xres, yres = OTB_pipeline.GetImageSpacing("out")
    # gdal offset
    geo_transform_origin = [origin_x - xres / 2.0, xres, 0, origin_y - yres / 2.0, 0, yres]
    
    x_size, y_size = OTB_pipeline.GetImageSize("out")

    # TODO : ram_estimation could be useful if chunck_size == "auto"
    ram_estimation = OTB_pipeline.PropagateRequestedRegion(key="out",
                                                           region=OTB_pipeline.GetImageRequestedRegion("out"))
    
    independant_raster = []
    boundaries = get_chunks_boundaries(chunk_size, shape=(x_size, y_size))
    for index, boundary in enumerate(boundaries):
        ROI = CreateExtractROIApplication({"in": OTB_pipeline,
                                           "startx": boundary["startx"],
                                           "sizex": boundary["sizex"],
                                           "starty": boundary["starty"],
                                           "sizey": boundary["sizey"],
                                           "out": os.path.join(working_dir, "ROI_{}.tif".format(index))})
        independant_raster.append(ROI)

    return independant_raster, projection.GetAttrValue("AUTHORITY", 1)