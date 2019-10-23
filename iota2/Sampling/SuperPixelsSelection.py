# !/usr/bin/env python3
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
import numpy as np
import logging
from typing import List, Dict, Tuple, Optional, Generator, TypeVar

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())

Param = Dict[str, str]
y_coords = List[float]
x_coords = List[float]
values = List[float]

def input_parameters(execution_dir: str) -> List[Param]:
    """function dedicated to feed merge_ref_super_pix

    Parameters
    ----------
    execution_dir : str
        path to iota² running directory
    """
    import operator
    from Common.FileUtils import FileSearch_AND
    from Common.FileUtils import sortByFirstElem

    tile_position = 0
    model_position = 3
    seed_position = 5

    sample_selection_directory = os.path.join(execution_dir, "samplesSelection")
    sample_sel_content = list(set(FileSearch_AND(sample_selection_directory, False, "_samples_region_", "selection.sqlite")))
    selection_models = [(c_file.split("_")[model_position],
                         int(c_file.split("_")[seed_position]),
                         c_file.split("_")[tile_position],
                         c_file) for c_file in sample_sel_content]
    selected_ref = sorted(selection_models, key=operator.itemgetter(0, 1, 2))

    parameters = []
    for model, seed, tile_name, ref in selected_ref:
        SLIC_path = FileSearch_AND(os.path.join(execution_dir,
                                                "features", tile_name, "tmp"),
                                                 True, "SLIC", ".tif")[0]
        ref_path = os.path.join(sample_selection_directory, "{}.sqlite".format(ref))
        parameters.append({"selection_samples": ref_path,
                           "SLIC": SLIC_path})

    return parameters


def SP_geo_coordinates_with_value(coordinates: Tuple[y_coords, x_coords],
                                  SP_array: np.ndarray,
                                  x_origin: float, y_origin: float,
                                  x_size: float, y_size: float) -> Generator[float, float, float]:
    """generator
    convert tabular coordinates to geographical

    Parameters
    ----------
    coordinates: tuple
        tuple of coordinates (lists) to convert
    SP_array: np.array
        numpy array to extract value
    x_origin: float
        x origin
    y_origin: float
        y origin
    x_size: float
        x size
    y_size: float
        y size

    Return
    ------
    tuple(y_geo_coordinates, x_geo_coordinates, array_value)
    """
    offset_y = y_size / 2.0
    offset_x = x_size / 2.0

    for y_coord, x_coord in zip(coordinates[0], coordinates[1]):
        y_geo = y_origin + offset_y + y_size * y_coord
        x_geo = x_origin + offset_x + x_size * x_coord
        value = SP_array[y_coord][x_coord]
        yield (y_geo, x_geo, value)


def super_pixels_coordinates(input_vector: str,
                             segmented_raster: str,
                             workingDirectory: Optional[str] = None,
                             logger: Optional[logging.Logger] = LOGGER) -> Generator[float, float, float]:
    """return superpixels coordinates which intersect input vector data-set

    Parameters
    ----------
    input_vector : str
        data-set path
    segmented_raster : str
        raster path
    workingDirectory : str
        working directory path
        
    Return
    ------
    tuple
        tuple containing two list, y coordinates and x coordinates
    """
    import numpy as np
    from collections import Counter
    import ogr
    import gdal
    import shutil
    import osgeo.osr as osr
    from Common.OtbAppBank import CreateRasterizationApplication
    from Common.FileUtils import readRaster
    from Common.FileUtils import getRasterResolution
    from Common.Utils import run
    logger.info("getting superpixels positions from intersection of {} and {}".format(segmented_raster, input_vector))
    
    if workingDirectory is None:
        tmp_dir = os.path.split(input_vector)[0]
    else:
        tmp_dir = workingDirectory

    input_vector_name = "{}.tif".format(os.path.split(os.path.splitext(input_vector)[0])[-1])
    vector_raster_path = os.path.join(tmp_dir, input_vector_name)

    ref_raster = CreateRasterizationApplication({"in": input_vector,
                                                 "out": vector_raster_path,
                                                 "im": segmented_raster,
                                                 "mode.binary.foreground": "1",
                                                 "background": "0"})
    ref_raster.Execute()

    seg_ds = gdal.Open(segmented_raster, 0)
    slic_array = seg_ds.GetRasterBand(1).ReadAsArray()

    mask_array = np.int32(ref_raster.GetImageAsNumpyArray("out"))

    intersection_array = np.multiply(mask_array, slic_array)
    super_pix_id = np.unique(intersection_array)
    # remove label 0
    if 0 in super_pix_id:
        super_pix_id = super_pix_id[super_pix_id != 0]

    y_coordinates, x_coordinates = np.where(np.isin(slic_array, super_pix_id))

    _, _, projection, transform = readRaster(segmented_raster)
    x_min, spacing_x, _, y_max, _, spacing_y = transform
    
    coords = SP_geo_coordinates_with_value(coordinates=(y_coordinates, x_coordinates),
                                           SP_array=slic_array,
                                           x_origin=x_min, y_origin=y_max,
                                           x_size=spacing_x, y_size=spacing_y)
    return coords

def add_SP_to_ref(reference: str, SP_field: str, SP_belong_field: str,
                  region_field: str, coordinates: Generator[float, float, float],
                  logger: Optional[logging.Logger] = LOGGER) -> None:
    """adding superPixel position to reference samples
    
    reference : str
        reference vector data (containing points)
    SP_field : str
        field to descriminate superpixels labels
    SP_belong_field : str
        field to descriminate superpixels from reference labels
    region_field : str
        region field
    coordinates : tuple generator
        (y geo coordinates, x geo coordinates, superpixel value)
    logger : logging.Logger
        root logger
    """
    from osgeo import ogr
    from VectorTools.AddField import addField
    from Common.FileUtils import getAllFieldsInShape

    logger.info("adding superPixel position to {}".format(reference))
    learn_flag = "learn"
    seed_position = 5
    region_position = 3
    tile_position = 0

    DRIVER = "SQLite"
    if SP_field not in getAllFieldsInShape(reference, "SQLite"):
        addField(reference, SP_field, valueField=0, valueType="int64", driver_name=DRIVER)

    if SP_belong_field not in getAllFieldsInShape(reference, "SQLite"):
        addField(reference, SP_belong_field, valueField=0, valueType=int, driver_name=DRIVER)

    seed_number = os.path.basename(os.path.split(reference)[-1]).split("_")[seed_position]
    region_name = os.path.basename(os.path.split(reference)[-1]).split("_")[region_position]
    tile_origin = os.path.basename(os.path.split(reference)[-1]).split("_")[tile_position]

    driver = ogr.GetDriverByName(DRIVER)
    data_source = driver.Open(reference, 1)
    layer = data_source.GetLayer()

    feture_defn = layer.GetLayerDefn()
    for y_coord, x_coord, value in coordinates:
        new_feature = ogr.Feature(feture_defn)
        wkt = "POINT({} {})".format(x_coord, y_coord)
        point = ogr.CreateGeometryFromWkt(wkt)
        new_feature.SetGeometry(point)
        new_feature.SetField(SP_field, int(value))
        new_feature.SetField("seed_{}".format(seed_number), learn_flag)
        new_feature.SetField(region_field, region_name)
        new_feature.SetField("tile_o", tile_origin)
        new_feature.SetField(SP_belong_field, 1)
        layer.CreateFeature(new_feature)
    data_source = layer = None


def geo_to_tab(x_coord,
               y_coord,
               x_origin,
               y_origin,
               x_size,
               y_size):
    """
    """
    import math
    y_tab = (y_coord - y_origin) / y_size
    x_tab = (x_coord - x_origin) / x_size
    return math.floor(x_tab), math.floor(y_tab)

def add_SP_labels(reference: str, SLIC: str, SP_FIELD_NAME: str) -> None:
    """Add new column to a database and add raster's value in it

    Parameters
    ----------
    reference : str
        database path
    SLIC : str
        raster path
    SP_FIELD_NAME : str
        database field to add raster's value
    """
    import gdal
    from osgeo import ogr
    from VectorTools.AddField import addField
    from Common.FileUtils import getAllFieldsInShape
    from Common.FileUtils import readRaster

    DRIVER = "SQLite"
    if SP_FIELD_NAME not in getAllFieldsInShape(reference, "SQLite"):
        addField(reference, SP_FIELD_NAME, valueField=0, valueType="int64", driver_name=DRIVER)
    seg_ds = gdal.Open(SLIC, 0)
    slic_array = seg_ds.GetRasterBand(1).ReadAsArray()
    driver = ogr.GetDriverByName(DRIVER)

    data_source = driver.Open(reference, 1)
    layer = data_source.GetLayer()
    _, _, projection, transform = readRaster(SLIC)
    x_min, spacing_x, _, y_max, _, spacing_y = transform
    for feature in layer:
        geom = feature.GetGeometryRef()
        x_coord = geom.GetX()
        y_coord = geom.GetY()
        x_tab, y_tab = geo_to_tab(x_coord,
                                  y_coord,
                                  x_origin=x_min,
                                  y_origin=y_max,
                                  x_size=spacing_x,
                                  y_size=spacing_y)
        feature.SetField(SP_FIELD_NAME, int(slic_array[y_tab][x_tab]))
        layer.SetFeature(feature)
    data_source = layer = None

def merge_ref_super_pix(data: Param,
                        SP_FIELD_NAME: str,
                        SP_BELONG_FIELD_NAME: str,
                        REGION_FIELD_NAME: str,
                        workingDirectory: Optional[str] = None,
                        ram: Optional[int] = 128):
    """add superPixels points to reference data

    Parameters
    ----------
    data : dict
        {"selection_samples": "/path/to/pointsDataBase.sqlite",
         "SLIC": "/path/to/segmentedRaster.tif"}
    SP_FIELD_NAME : str
        field added in database representing segment labels
    SP_BELONG_FIELD_NAME : str
        field added in database discriminating original samples from new samples
    REGION_FIELD_NAME : str
        region field in database
    workingDirectory : str
        path to store temporary files
    ram : int
        available ram
    """
    import shutil
    reference = data["selection_samples"]
    SLIC = data["SLIC"]

    if workingDirectory:
        shutil.copy(reference, workingDirectory)
        _, reference_name = os.path.split(reference)[-1]
        reference = os.path.join(workingDirectory, reference_name)
        
    add_SP_labels(reference, SLIC, SP_FIELD_NAME)

    sp_coords_val = super_pixels_coordinates(reference, SLIC)

    add_SP_to_ref(reference,
                  SP_field=SP_FIELD_NAME,
                  SP_belong_field=SP_BELONG_FIELD_NAME,
                  region_field=REGION_FIELD_NAME,
                  coordinates=sp_coords_val)
    if workingDirectory:
        shutil.move(reference, data["selection_samples"])
    