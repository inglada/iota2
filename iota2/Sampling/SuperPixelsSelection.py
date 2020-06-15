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

    sample_selection_directory = os.path.join(execution_dir,
                                              "samplesSelection")
    sample_sel_content = list(
        set(
            FileSearch_AND(sample_selection_directory, False,
                           "_samples_region_", "selection.sqlite")))
    selection_models = [(c_file.split("_")[model_position],
                         int(c_file.split("_")[seed_position]),
                         c_file.split("_")[tile_position], c_file)
                        for c_file in sample_sel_content]
    selected_ref = sorted(selection_models, key=operator.itemgetter(0, 1, 2))

    parameters = []
    for model, seed, tile_name, ref in selected_ref:
        SLIC_path = FileSearch_AND(
            os.path.join(execution_dir, "features", tile_name, "tmp"), True,
            "SLIC", ".tif")[0]
        ref_path = os.path.join(sample_selection_directory,
                                "{}.sqlite".format(ref))
        parameters.append({"selection_samples": ref_path, "SLIC": SLIC_path})

    return parameters


def choosable_annual_pixels(classification_raster: str, validity_raster: str,
                            region_mask: str, validity_threshold: str):
    """mask pixels in order to choose ones according to clouds, region...

    Parameters
    ----------
    classification_raster : string
        path to classification raster
    validity_raster : string
        path to vilidity raster
    region_mask : string
        path to region mask raster
    validity_threshold : int
        cloud threashold to pick up samples

    Return
    ------
    tuple (mask, (Ox, Oy, spx, spy))
        mask : numpy.array
            numpy array where non 0 are choosable pixels
        Ox : float
            x origin
        Oy : float
            y origin
        spx : float
            x spacing
        spy : float
            y spacing
    """
    from Common.OtbAppBank import CreateClassificationMapRegularization
    from Common.OtbAppBank import CreateBandMathApplication
    from Common.OtbAppBank import CreateSuperimposeApplication

    roi_classif, _ = CreateSuperimposeApplication({
        "inr": region_mask,
        "inm": classification_raster,
        "interpolator": "nn"
    })
    roi_classif.Execute()
    roi_validity, _ = CreateSuperimposeApplication({
        "inr": region_mask,
        "inm": validity_raster,
        "interpolator": "nn"
    })
    roi_validity.Execute()
    #~ classif_reg = CreateClassificationMapRegularization({"io.in": roi_classif,
    #~ "ip.undecidedlabel": 0})
    #~ classif_reg.Execute()
    mask_dummy = CreateBandMathApplication({
        "il": [region_mask],
        "exp": "im1b1"
    })
    mask_dummy.Execute()
    #~ valid = CreateBandMathApplication({"il": [roi_validity, classif_reg],
    valid = CreateBandMathApplication({
        "il": [roi_validity, roi_classif],
        "exp":
        "im1b1>{}?im2b1:0".format(validity_threshold)
    })
    valid.Execute()
    choosable = CreateBandMathApplication({
        "il": [valid, mask_dummy],
        "exp": "im1b1*(im2b1>=1?1:0)"
    })
    choosable.Execute()
    oy, ox = choosable.GetImageOrigin("out")
    spx, spy = choosable.GetImageSpacing("out")
    return choosable.GetImageAsNumpyArray("out"), (ox, oy, spx, spy)


def move_annual_samples_from_array(samples_position, target_label, dataField,
                                   samples_number, array, ox, oy, spx, spy,
                                   tile_origin_field_value, seed_field_value,
                                   region_field_value):
    """
    """
    import numpy as np
    import random
    from osgeo import ogr

    x_coords, y_coords = np.where(array == target_label)
    #~ y_coords, x_coords = np.where(array==target_label)
    samples_number = samples_number if len(y_coords) > samples_number else len(
        y_coords)

    geo_coordinates = []
    for y_coord, x_coord in zip(y_coords, x_coords):
        x_geo = (ox + spx) - spx * (x_coord + 1)
        y_geo = (oy + spy) - spy * (y_coord + 1)

        geo_coordinates.append((x_geo, y_geo))

    random_coords = random.sample(geo_coordinates, samples_number)

    #seek and destroy samples
    driver = ogr.GetDriverByName("SQLite")
    dataSource = driver.Open(samples_position, 1)
    layer = dataSource.GetLayer()
    for feature in layer:
        if feature.GetField(dataField) == target_label:
            layer.DeleteFeature(feature.GetFID())
    # add new samples according to random_coords
    for x_geo, y_geo in random_coords:
        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetField(dataField, int(target_label))
        feature.SetField(tile_origin_field_value[0],
                         tile_origin_field_value[1])
        feature.SetField(seed_field_value[0], seed_field_value[1])
        feature.SetField(region_field_value[0], region_field_value[1])

        point = ogr.CreateGeometryFromWkt("POINT({} {})".format(y_geo, x_geo))
        #~ point = ogr.CreateGeometryFromWkt("POINT({} {})".format(y_geo, x_geo))
        feature.SetGeometry(point)
        layer.CreateFeature(feature)
        feature = None
    dataSource = None


def move_annual_samples_position(samples_position, dataField, annual_labels,
                                 classification_raster, validity_raster,
                                 region_mask, validity_threshold,
                                 tile_origin_field_value, seed_field_value,
                                 region_field_value):
    """move samples position of labels of interest according to rasters
    
    Parameters
    ----------
    samples_position : string
        path to a vector file containing points, representing samples' positions
    dataField : string
        data field in vector
    annual_labels : list
        list of annual labels
    classification_raster : string
        path to classification raster
    validity_raster : string
        path to vilidity raster
    region_mask : string
        path to region mask raster
    validity_threshold : int
        cloud threshold to pick up samples
    """
    import collections
    from Common.FileUtils import getFieldElement

    annual_labels = map(int, annual_labels)
    class_repartition = getFieldElement(samples_position,
                                        driverName="SQLite",
                                        field=dataField,
                                        mode="all",
                                        elemType="int")
    class_repartition = collections.Counter(class_repartition)

    mask_array, (ox, oy, spx,
                 spy) = choosable_annual_pixels(classification_raster,
                                                validity_raster, region_mask,
                                                validity_threshold)
    for annual_label in annual_labels:
        if annual_label in class_repartition:
            samples_number = class_repartition[annual_label]
            move_annual_samples_from_array(samples_position, annual_label,
                                           dataField, samples_number,
                                           mask_array, ox, oy, spx, spy,
                                           tile_origin_field_value,
                                           seed_field_value,
                                           region_field_value)
        else:
            continue


def SP_geo_coordinates_with_value(coordinates: Tuple[y_coords, x_coords],
                                  SP_array: np.ndarray, x_origin: float,
                                  y_origin: float, x_size: float, y_size: float
                                  ) -> Generator[float, float, float]:
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
                             logger: Optional[logging.Logger] = LOGGER
                             ) -> Generator[float, float, float]:
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
    logger.info(
        "getting superpixels positions from intersection of {} and {}".format(
            segmented_raster, input_vector))

    if workingDirectory is None:
        tmp_dir = os.path.split(input_vector)[0]
    else:
        tmp_dir = workingDirectory

    input_vector_name = "{}.tif".format(
        os.path.split(os.path.splitext(input_vector)[0])[-1])
    vector_raster_path = os.path.join(tmp_dir, input_vector_name)

    ref_raster = CreateRasterizationApplication({
        "in": input_vector,
        "out": vector_raster_path,
        "im": segmented_raster,
        "mode.binary.foreground": "1",
        "background": "0"
    })
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

    return SP_geo_coordinates_with_value(coordinates=(y_coordinates,
                                                        x_coordinates),
                                           SP_array=slic_array,
                                           x_origin=x_min,
                                           y_origin=y_max,
                                           x_size=spacing_x,
                                           y_size=spacing_y)


def add_SP_to_ref(reference: str,
                  SP_field: str,
                  SP_belong_field: str,
                  region_field: str,
                  coordinates: Generator[float, float, float],
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
    from Common.FileUtils import get_all_fields_in_shape

    logger.info("adding superPixel position to {}".format(reference))
    learn_flag = "learn"
    seed_position = 5
    region_position = 3
    tile_position = 0

    DRIVER = "SQLite"
    if SP_field not in get_all_fields_in_shape(reference, "SQLite"):
        addField(reference,
                 SP_field,
                 valueField=0,
                 valueType="int64",
                 driver_name=DRIVER)

    if SP_belong_field not in get_all_fields_in_shape(reference, "SQLite"):
        addField(reference,
                 SP_belong_field,
                 valueField=0,
                 valueType=int,
                 driver_name=DRIVER)

    seed_number = os.path.basename(
        os.path.split(reference)[-1]).split("_")[seed_position]
    region_name = os.path.basename(
        os.path.split(reference)[-1]).split("_")[region_position]
    tile_origin = os.path.basename(
        os.path.split(reference)[-1]).split("_")[tile_position]

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


def geo_to_tab(x_coord, y_coord, x_origin, y_origin, x_size, y_size):
    """
    """
    import math
    y_tab = (y_coord - y_origin) / y_size
    x_tab = (x_coord - x_origin) / x_size
    return math.floor(x_tab), math.floor(y_tab)


def add_SP_labels(reference: str, SLIC: str, DATAREF_FIELD_NAME: str,
                  SP_FIELD_NAME: str, ram: Optional[int]) -> None:
    """Add new column to a database and add raster's value in it

    Parameters
    ----------
    reference : str
        database path
    SLIC : str
        raster path
    DATAREF_FIELD_NAME : str
        database labels field name
    SP_FIELD_NAME : str
        database field to add raster's value
    ram : int
        available ram
    """
    from Common.OtbAppBank import CreateSampleExtractionApplication

    extraction = CreateSampleExtractionApplication({
        "in":
        SLIC,
        "vec":
        reference,
        "outfield":
        "list",
        "field":
        DATAREF_FIELD_NAME,
        "ram":
        ram,
        "outfield.list.names": [SP_FIELD_NAME]
    })
    extraction.ExecuteAndWriteOutput()


def merge_ref_super_pix(data: Param,
                        DATAREF_FIELD_NAME: str,
                        SP_FIELD_NAME: str,
                        SP_BELONG_FIELD_NAME: str,
                        REGION_FIELD_NAME: str,
                        sampling_labels_from_raster: Optional[dict] = {},
                        workingDirectory: Optional[str] = None,
                        ram: Optional[int] = 128):
    """add superPixels points to reference data

    Parameters
    ----------
    data : dict
        {"selection_samples": "/path/to/pointsDataBase.sqlite",
         "SLIC": "/path/to/segmentedRaster.tif"}
    DATAREF_FIELD_NAME : str
        database labels field name
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
    from Common.FileUtils import FileSearch_AND
    reference = data["selection_samples"]
    SLIC = data["SLIC"]

    if workingDirectory:
        shutil.copy(reference, workingDirectory)
        _, reference_name = os.path.split(reference)
        reference = os.path.join(workingDirectory, reference_name)

    if sampling_labels_from_raster:
        model_name = os.path.basename(reference).split("_")[3].split("f")[0]
        tile = os.path.basename(reference).split("_")[0]
        seed = os.path.basename(reference).split("_")[5]
        region_mask = FileSearch_AND(
            sampling_labels_from_raster["region_mask_directory"], True,
            "region_{}_{}.tif".format(model_name.split("f")[0], tile))[0]

        tile_origin_field_value = ("tile_o", tile)
        seed_field_value = ("seed_{}".format(seed), "learn")
        region_field_value = (REGION_FIELD_NAME, model_name)
        move_annual_samples_position(
            reference, DATAREF_FIELD_NAME,
            sampling_labels_from_raster["annual_labels"],
            sampling_labels_from_raster["classification_raster"],
            sampling_labels_from_raster["validity_raster"], region_mask,
            sampling_labels_from_raster["val_threshold"],
            tile_origin_field_value, seed_field_value, region_field_value)

    add_SP_labels(reference, SLIC, DATAREF_FIELD_NAME.lower(), SP_FIELD_NAME,
                  ram)

    sp_coords_val = super_pixels_coordinates(reference, SLIC)

    add_SP_to_ref(reference,
                  SP_field=SP_FIELD_NAME,
                  SP_belong_field=SP_BELONG_FIELD_NAME,
                  region_field=REGION_FIELD_NAME,
                  coordinates=sp_coords_val)
    if workingDirectory:
        shutil.move(reference, data["selection_samples"])
