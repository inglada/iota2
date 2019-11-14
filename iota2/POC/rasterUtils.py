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


def apply_function(OTB_pipeline, labels, working_dir, function, output_path, chunck_size_x=10, chunck_size_y=10, ram=128):
    """
    function : partial function
    """
    from iota2.Common.FileUtils import assembleTile_Merge
    new_array = new_labels = None

    ROI_rasters = split_raster(OTB_pipeline=OTB_pipeline,
                               chunk_size=(chunck_size_x, chunck_size_y),
                               ram_per_chunk=ram,
                               working_dir=working_dir) 
    new_arrays = []
    for index, ROI_raster in enumerate(ROI_rasters):
        ROI_array, proj_geotransform = process_function(ROI_raster, function=function)
        new_arrays.append((ROI_array, proj_geotransform))

        if index == 0:
            spacing_x, _ = ROI_raster.GetImageSpacing("out")
        
    # TODO : ROI_tmp_*.tif must not be written on disk ()
    tmp_rasters = []
    for index, new_array in enumerate(new_arrays):
        tmp_raster = os.path.join(working_dir, "ROI_tmp_{}.tif".format(index))
        write_array(array_proj=new_array, num=index, output_path=tmp_raster)
        tmp_rasters.append(tmp_raster)

    assembleTile_Merge(tmp_rasters, spacing_x, output_path)

    for tmp_raster in tmp_rasters:
        os.remove(tmp_raster)

    ds = gdal.Open(output_path)
    arrayOut = ds.ReadAsArray()
    ds = None

    # TODO : new_labels definition
    return new_array, new_labels


def write_array(array_proj, num, output_path, dtype=gdal.GDT_Float32):
    """
    """
    array = array_proj[0]
    proj = array_proj[-1]["projection"]
    geo_transform = array_proj[-1]["geo_transform"]
    
    y_size, x_size, z_size = array.shape
    
    driver = gdal.GetDriverByName("GTiff")
    
    ds = driver.Create(output_path, x_size, y_size, z_size, dtype)

    for i in range(z_size):
        outband = ds.GetRasterBand(i + 1)
        outband.WriteArray(array[:,:,i])

    ds.SetProjection(proj.ExportToWkt())
    ds.SetGeoTransform(geo_transform)
    ds.FlushCache()


def process_function(OTB_pipeline, function):
    """
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


def get_chunks_boundaries(chunk_size, shape):
    """
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


def split_raster(OTB_pipeline, chunk_size, ram_per_chunk, working_dir):
    """
    """
    from iota2.Common.OtbAppBank import CreateExtractROIApplication
    
    OTB_pipeline.Execute()
    
    y_size, x_size = OTB_pipeline.GetImageSize("out")# check if (y_size, x_size) or (x_size, y_size)

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
    return independant_raster