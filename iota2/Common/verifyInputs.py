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
import sys
import logging
from typing import List, Optional, Union
from osgeo import ogr

from iota2.Common import ServiceError
from iota2.Common.Tools import checkDataBase
from iota2.Common.FileUtils import is_writable_directory
from iota2.Common.FileUtils import FileSearch_AND
from iota2.Common.FileUtils import getRasterProjectionEPSG
from iota2.Common.FileUtils import getRasterExtent
from iota2.Common.FileUtils import getFieldElement

LOGGER = logging.getLogger(__name__)


def extent_to_geom(min_x, max_x, min_y, max_y, src_epsg,
                   tgt_epsg) -> Union[None, ogr.Geometry]:
    """create an ogr geometry from an extent
    """
    from osgeo import osr
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(min_x, min_y)
    ring.AddPoint(min_x, max_y)
    ring.AddPoint(max_x, max_y)
    ring.AddPoint(max_x, min_y)
    ring.AddPoint(min_x, min_y)

    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)

    source = osr.SpatialReference()
    source.ImportFromEPSG(int(src_epsg))

    target = osr.SpatialReference()
    target.ImportFromEPSG(int(tgt_epsg))

    transform = osr.CoordinateTransformation(source, target)
    poly.Transform(transform)
    return poly


def get_tile_raster_footprint(tile_name: str, sensor_path: str,
                              proj_epsg_t: int) -> Union[None, ogr.Geometry]:
    """from a sensor path and a tile's name, get the tile's envelope
       as an ogr geometry
    """
    raster_ref = None
    geom_raster_envelope = None

    ref_path = os.path.join(sensor_path, tile_name)

    raster_ref_list = FileSearch_AND(ref_path, True, ".jp2") or FileSearch_AND(
        ref_path, True, ".tif") or FileSearch_AND(ref_path, True, ".tiff")
    for raster_ref in raster_ref_list:
        if "STACK.tif" not in raster_ref:
            break
    if raster_ref:
        proj_epsg_o = getRasterProjectionEPSG(raster_ref)
        min_x, max_x, min_y, max_y = getRasterExtent(raster_ref)
        geom_raster_envelope = extent_to_geom(min_x,
                                              max_x,
                                              min_y,
                                              max_y,
                                              src_epsg=proj_epsg_o,
                                              tgt_epsg=proj_epsg_t)
    return geom_raster_envelope


def exist_intersection(geom_raster_envelope,
                       ground_truth,
                       region_shape,
                       region_field,
                       region_value,
                       driver_name: Optional[str] = "ESRI Shapefile") -> bool:
    """find if every models could be learn (intersection between ground truth
       and region shape / tiles is not empty)
    """
    class found(Exception):
        """double break"""
        pass

    intersection_found = False
    if region_shape:
        try:
            driver_reg = ogr.GetDriverByName(driver_name)
            reg_src = driver_reg.Open(region_shape, 0)
            reg_layer = reg_src.GetLayer()
            reg_layer.SetAttributeFilter("{}='{}'".format(
                region_field, region_value))
            for feat_reg in reg_layer:
                geom_reg = feat_reg.GetGeometryRef()
                if geom_reg.Intersect(geom_raster_envelope):
                    geom_inter_tile_reg = geom_reg.Intersection(
                        geom_raster_envelope)
                    driver = ogr.GetDriverByName(driver_name)
                    gt_src = driver.Open(ground_truth, 0)
                    gt_layer = gt_src.GetLayer()
                    for feature in gt_layer:
                        geom = feature.GetGeometryRef()
                        if geom.Intersect(geom_inter_tile_reg):
                            raise found
        except found:
            intersection_found = True
    else:
        driver = ogr.GetDriverByName(driver_name)
        gt_src = driver.Open(ground_truth, 0)
        gt_layer = gt_src.GetLayer()
        for feature in gt_layer:
            geom = feature.GetGeometryRef()
            if geom.Intersect(geom_raster_envelope):
                intersection_found = True
                break
    return intersection_found


def check_sqlite_db(i2_output_path):
    """check if every sqlite database could be open
    """
    # explicit call to the undecorate function thanks to __wrapped__
    return [
        ServiceError.sqliteCorrupted(elem) for elem in
        FileSearch_AND.__wrapped__(i2_output_path, True, "sqlite-journal")
    ]


def check_data_intersection(ground_truth: str, region_shape: Union[str, None],
                            region_field: str, proj_epsg_t: int,
                            sensor_path: str,
                            tiles: List[str]) -> List[type(ServiceError)]:
    """ check if there is an intersection between the ground truth, the regions
        and tiles

    Parameters
    ----------
    ground_truth : str
        ground truth path
    region_shape : str
        region shapeFile path
    region_field : str
        region field in region shapeFile
    proj_epsg_t : int
        target projection
    sensor_path : str
        path to a directory containg sensors data split
        by tiles
    tiles : list
        list of tiles

    Sentinel-1 data are not checked (not tilled)
    """

    errors = []
    found_intersection_in_tile = []

    region_list = ["1"]
    if region_shape is not None:
        region_list = getFieldElement(region_shape,
                                      field=region_field,
                                      mode="unique",
                                      elemType="str")
    # init each region intersection to False
    dico_region_intersection = {}
    for region_name in region_list:
        dico_region_intersection[region_name] = False

    for tile in tiles:
        geom_raster_envelope = get_tile_raster_footprint(
            tile, sensor_path, proj_epsg_t)
        if geom_raster_envelope is not None:
            # only one intersection per model is needed
            for region in region_list:
                if dico_region_intersection[region] is False:
                    is_intersections = exist_intersection(
                        geom_raster_envelope, ground_truth, region_shape,
                        region_field, region)
                    dico_region_intersection[region] = is_intersections
                    found_intersection_in_tile.append(is_intersections)
            found_intersection_in_tile = [
                inter for _, inter in dico_region_intersection.items()
            ]
        else:
            LOGGER.warning("Cannot check intersections")
    if found_intersection_in_tile and False in found_intersection_in_tile:
        errors.append(ServiceError.intersectionError())
    return errors


def check_iota2_inputs(i2_output_path: str, ground_truth: str,
                       region_shape: str, data_field: str, region_field: str,
                       epsg: int, sensor_path: str,
                       tiles: List[str]) -> List[type(ServiceError)]:
    """check inputs in order to achieve a iota2 run

    Parameters
    ----------
    i2_output_path : str
        iota2 output path
    ground_truth : str
        ground truth path
    region_shape : str
        region shapeFile path
    data_field : str
        data field in ground truth database
    region_field : str
        region field in region shapeFile
    epsg : int
        target projection
    sensor_path : str
        path to a directory containg sensors data split
        by tiles
    tiles : list
        list of tiles
    Return
    ------
    list
        list of errors
    this function check :
        - the ground truth
        - the region shape (if exists)
        - if an intersection exists between data
        - reachable paths
        - check corrupted data
    TODO :
        - check if all expected sensors data exists, new sensors methods ?
    """
    # check input vectors
    gt_errors = checkDataBase.check_ground_truth(ground_truth,
                                                 "",
                                                 data_field,
                                                 epsg,
                                                 do_corrections=False,
                                                 display=False)
    regions_errors = []
    if region_shape is not None:
        regions_errors = checkDataBase.check_region_shape(region_shape,
                                                          "",
                                                          region_field,
                                                          epsg,
                                                          do_corrections=False,
                                                          display=False)
    # check if outputPath can be reach
    error_output_i2_dir = is_writable_directory(i2_output_path)
    path_errors = []
    if not error_output_i2_dir:
        path_errors.append(ServiceError.directoryError(i2_output_path))

    # check if every sqlite database could be read
    sql_db_errors = check_sqlite_db(i2_output_path)

    # check if the intersection of the ground truth, the region shape, tiles is not empty
    errors_instersection = check_data_intersection(ground_truth, region_shape,
                                                   region_field, epsg,
                                                   sensor_path, tiles)

    errors = gt_errors + regions_errors + path_errors + errors_instersection + sql_db_errors
    if errors:
        sys.tracebacklimit = 0
        errors_sum = "\n".join(
            ["ERROR : {}".format(error.msg) for error in errors])
        LOGGER.error(errors_sum)
        raise Exception(errors_sum)
