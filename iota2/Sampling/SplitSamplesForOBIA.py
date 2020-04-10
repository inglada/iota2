#!/usr/bin/python
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
import glob
from typing import Optional, List
from osgeo import gdal
from osgeo import ogr
from iota2.Common import FileUtils as fu
from iota2.Common.Tools import GridFit
from iota2.VectorTools.vector_functions import intersect_shp

logger = logging.getLogger(__name__)


def split_segmentation_by_tiles(iota2_directory: str,
                                tiles: List[str],
                                segmentation: str,
                                epsg: int,
                                working_dir: str,
                                region_path: Optional[str] = None,
                                size: Optional[int] = 1000):
    """ Split segmentation layer into tiled segmentation

    Parameters
    ----------
    cfg : serviceConfig obj
        configuration object for parameters
    tile : string
        tile id
    workingDirectory : string
        path to the working directory

    Note
    ------
    """

    # from iota2.Common import ServiceConfigFile as SCF

    # epsg = int((cfg.getParam('GlobChain', 'proj')).split(":")[-1])
    segmentation_raster = None
    segmentation_vector = None

    # region_path = cfg.getParam('chain', 'regionPath')
    if region_path is None:
        region_path = os.path.join(iota2_directory, "MyRegion.shp")
    region_pattern = os.path.basename(region_path).split(".")[0]

    # Determine if segmentation is a raster or a vector layer
    try:
        segmentation_raster = gdal.Open(segmentation)
        if segmentation_raster is not None:
            segmentation_raster = segmentation
            logger.info(f"{segmentation_raster} loaded as raster "
                        "segmentation reference")
    except:
        logger.info("{segmentation_raster} is not a raster input...")
    if segmentation_raster is None:
        segmentation_vector = ogr.Open(segmentation)
        if segmentation_vector is not None:
            segmentation_vector = segmentation
            logger.info(f"{segmentation_vector} loaded as vector "
                        "segmentation reference")

    # If raster, then vectorize
    if segmentation_vector is None:
        segmentation_vector = os.path.splitext(segmentation)[0] + '.gml'
        if os.path.exists(segmentation_vector) is not True:
            cmd = "gdal_polygonize.py -f GML %s %s" % (segmentation_raster,
                                                       segmentation_vector)
            os.system(cmd)

    env_dir = os.path.join(iota2_directory, 'envelope')
    seg_dir = os.path.join(iota2_directory, 'segmentation')
    wdir = seg_dir
    # if working_dir:
    #     wdir = working_dir
    # Split segmentation by tiles

    GridFit.generateSegVectorTiles(segmentation_vector,
                                   tiles,
                                   env_dir,
                                   wdir,
                                   epsg=epsg)
    seg_ds = gdal.Open(segmentation_raster)
    geot = seg_ds.GetGeoTransform()
    # spx, spy = str(geoT[1]), str(geoT[5])
    resol = min(abs(geot[1]), abs(geot[5]))
    seg_ds = None
    gsize = round(size * resol)
    for tile in tiles:
        tile_shp = os.path.join(wdir, f'{tile}_seg.shp')
        tile_region_shps = fu.FileSearch_AND(
            os.path.join(iota2_directory, "shapeRegion"), True,
            f"{region_pattern}_region_", f"_{tile}.shp")

        if len(tile_region_shps) > 1:
            # Split tiles with regions
            out_tile_region_shps = GridFit.generateSegVectorTilesRegion(
                tile_shp, tile, tile_region_shps, wdir, epsg=epsg)
            # Generate subtiles (quicker for zonal statistics processing)
            for out_tile_region_shp in out_tile_region_shps:
                grid_list = GridFit.generateGridBasedSubsets(os.path.join(
                    wdir, out_tile_region_shp),
                                                             tile,
                                                             [gsize, gsize],
                                                             epsg=epsg)
        else:
            region = tile_region_shps[0].split('_')[-2]
            outpath = os.path.join(wdir, f"{tile}_region_{region}_seg")
            tiled_vector_segmentation = f'{tile}_region_{region}_seg.shp'
            fu.cpShapeFile(
                os.path.splitext(tile_shp)[0], outpath,
                ['.shp', '.shx', '.dbf', '.prj'])
            # Generate subtiles (quicker for zonal statistics processing)
            grid_list = GridFit.generateGridBasedSubsets(os.path.join(
                wdir, tiled_vector_segmentation),
                                                         tile, [gsize, gsize],
                                                         epsg=epsg)

    return


def format_sample_to_segmentation(iota2_directory: str,
                                  region_tiles_seed,
                                  working_dir,
                                  region_path: Optional[str] = None):
    """ Split train samples with one region of the segmentation,
    through each tile of the region and for the wanted run

    Parameters
    ----------
    cfg : serviceConfig obj
        configuration object for parameters
    tile : string
        tile id
    workingDirectory : string
        path to the working directory

    Note
    ------
    """
    from iota2.VectorTools.AddFieldID import addFieldID
    from iota2.VectorTools.vector_functions import checkValidGeom
    region, tiles, seed = region_tiles_seed

    if region_path is None:
        region_path = os.path.join(iota2_directory, "MyRegion.shp")
    region_pattern = os.path.basename(region_path).split(".")[0]

    samples_vector = os.path.join(iota2_directory, 'samplesSelection',
                                  f"samples_region_{region}_seed_{seed}.shp")
    # dataField = (cfg.getParam('chain', 'dataField')).lower()
    # regionField = (cfg.getParam('chain', 'regionField')).lower()

    out_folder = os.path.join(iota2_directory, "segmentation")
    # if working_dir is not None:
    #    out_folder = working_dir
    # epsg = int((cfg.getParam('GlobChain', 'proj')).split(":")[-1])
    print('before first intersect')
    tiles_samples = []
    # intersects each segmented tile with train samples
    for tile in tiles:
        segmentation_vector = os.path.join(
            out_folder, '{}_region_{}_seg.shp'.format(tile, region))
        # Ensure that all geometries are correct
        checkValidGeom(segmentation_vector)
        tile_samples_vector = os.path.join(
            out_folder, "{}_learn_samples_region_{}_seed_{}.shp".format(
                tile, region, seed))
        tiles_samples.append(tile_samples_vector)
        if os.path.exists(tile_samples_vector):
            fu.removeShape(
                os.path.splitext(tile_samples_vector)[0],
                ['.prj', '.shp', '.dbf', '.shx'])
        intersect_shp(samples_vector, segmentation_vector, out_folder,
                      tile_samples_vector)
        # intersect.intersectSqlites(samples_vector, segmentation_vector,
        # out_folder, tile_samples_vector, epsg, "intersection", attributes,
        # vectformat='ESRI Shapefile')
    print("end first intersect")
    # merge each tiled train samples to assign an unique ID
    samples_vector = "learn_samples_region_{}_seed_{}".format(region, seed)
    fu.mergeVectors(samples_vector, out_folder, tiles_samples)
    samples_vector = os.path.join(out_folder, samples_vector + '.shp')
    # add a unique id for each segment (needed to zonal statistic step)
    addFieldID(samples_vector)
    # split again the new layer in tiles
    for tile in tiles:
        tile_vector = os.path.join(
            iota2_directory, "shapeRegion",
            "{}_region_{}_{}.shp".format(region_pattern, region, tile))
        tile_samples_vector = "{}_learn_samples_region_{}_seed_{}.shp".format(
            tile, region, seed)
        if os.path.exists(os.path.join(out_folder, tile_samples_vector)):
            fu.removeShape(
                os.path.splitext(os.path.join(out_folder,
                                              tile_samples_vector))[0],
                ['.prj', '.shp', '.dbf', '.shx'])
        print(samples_vector, tile_vector, out_folder, tile_samples_vector)

        intersect_shp(samples_vector, tile_vector, out_folder,
                      tile_samples_vector)
        # intersect.intersectSqlites(samples_vector+'.shp', tileVector,
        # out_folder, tile_samples_vector, epsg, "intersection", attributes,
        # vectformat='ESRI Shapefile')
