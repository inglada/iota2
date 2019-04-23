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
import argparse
import ast
import os
import sys
import shutil
import logging
import glob
from datetime import date
from osgeo import gdal
from osgeo import ogr
from osgeo import osr
from config import Config
from Common import OtbAppBank
from Common import FileUtils as fu
from Common.Tools import GridFit
from VectorTools import spatialOperations as intersect
from VectorTools.vector_functions import intersect_shp

logger = logging.getLogger(__name__)

def split_segmentation_by_tiles(cfg, region_tiles_seed, wd):
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

    from Common import ServiceConfigFile as SCF

    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)

    epsg = int((cfg.getParam('GlobChain', 'proj')).split(":")[-1])
    segmentation = cfg.getParam('chain','OBIA_segmentation_path')
    segmentationRaster = None
    segmentationVector = None

    region_path = cfg.getParam('chain','regionPath')
    if not region_path :
        region_path = os.path.join(cfg.getParam('chain', 'outputPath'), "MyRegion.shp")
    region_pattern = os.path.basename(region_path).split(".")[0]

    try :
        segmentationRaster = gdal.Open(segmentation)
        if segmentationRaster is not None :
            segmentationRaster = segmentation
            logger.info("%s loaded as raster segmentation reference")
    except :
        logger.info("%s is not a raster input...")
    if segmentationRaster is None:
        segmentationVector = ogr.Open(segmentation)
        if segmentationVector is not None :
            segmentationVector = segmentation
            logger.info("%s loaded as vector segmentation reference")

    if segmentationVector is None :
        segmentationVector = os.path.splitext(segmentation)[0]+'.gml'
        if os.path.exists(segmentationVector) is not True :
            cmd = "gdal_polygonize.py -f GML %s %s" % (segmentationRaster, segmentationVector)
            os.system(cmd)

    tiles = cfg.getParam('chain','listTile').split(' ')
    output_dir = os.path.join(cfg.getParam('chain', 'outputPath'))
    env_dir = os.path.join(output_dir,'envelope')
    seg_dir = os.path.join(output_dir,'segmentation')
    GridFit.generateSegVectorTiles(segmentationVector, tiles, env_dir, seg_dir)
    field_Region = cfg.getParam('chain', 'regionField')
    seg_ds = gdal.Open(segmentationRaster)
    geoT = seg_ds.GetGeoTransform()
    spx, spy = str(geoT[1]), str(geoT[5])
    resol = min(abs(geoT[1]), abs(geoT[5]))
    seg_ds = None
    gsize = round(1000 * resol)
    for tile in tiles :
        tileShp = os.path.join(seg_dir,'{}_seg.shp'.format(tile))
        tileRegionShps = glob.glob(os.path.join(cfg.getParam('chain', 'outputPath'), "shapeRegion", "{}_region_*_{}.shp".format(region_pattern, tile)))
        if len(tileRegionShps) > 1 :
            for tileRegionShp in tileRegionShps :
                region = tileRegionShp.split('_')[-2]
                tiledVectorSegmentation = '{}_region_{}_seg.shp'.format(tile, region)
                intersect_shp(tileShp, tileRegionShp, seg_dir, tiledVectorSegmentation, where = "{}={}".format(field_Region, region))
                grid_list = GridFit.generateGridBasedSubsets(os.path.join(seg_dir, tiledVectorSegmentation), tile, [gsize, gsize], epsg)
        else :
            region = tileRegionShps[0].split('_')[-2]
            outpath = os.path.join(seg_dir,"{}_region_{}_seg".format(tile,region))
            tiledVectorSegmentation = '{}_region_{}_seg.shp'.format(tile, region)
            fu.cpShapeFile(os.path.splitext(tileShp)[0], outpath, ['.shp','.shx','.dbf','.prj'])
            grid_list = GridFit.generateGridBasedSubsets(os.path.join(seg_dir, tiledVectorSegmentation), tile, [gsize, gsize], epsg)

    return

def format_sample_to_segmentation(cfg, region_tiles_seed, wd):
    """ Split train samples with segmentation

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
    from Common import ServiceConfigFile as SCF
    from VectorTools.AddFieldID import addFieldID

    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)

    region, tiles, seed = region_tiles_seed
    region_path = cfg.getParam('chain','regionPath')
    if not region_path :
        region_path = os.path.join(cfg.getParam('chain', 'outputPath'), "MyRegion.shp")
    region_pattern = os.path.basename(region_path).split(".")[0]

    samplesVector = os.path.join(cfg.getParam('chain', 'outputPath'), 'samplesSelection', "samples_region_{}_seed_{}.shp".format(region, seed))
    dataField = (cfg.getParam('chain', 'dataField')).lower()
    regionField = (cfg.getParam('chain', 'regionField')).lower()

    outFolder = os.path.join(cfg.getParam('chain', 'outputPath'), "segmentation")
    epsg = int((cfg.getParam('GlobChain', 'proj')).split(":")[-1])

    tiles_samples = []
    for tile in tiles :
        segmentationVector = os.path.join(outFolder, '{}_region_{}_seg.shp'.format(tile, region))
        tileSamplesVector = os.path.join(outFolder, "{}_learn_samples_region_{}_seed_{}.shp".format(tile, region, seed))
        tiles_samples.append(tileSamplesVector)
        if os.path.exists(tileSamplesVector) :
            fu.removeShape(os.path.splitext(tileSamplesVector)[0],['.prj','.shp','.dbf','.shx'])
        intersect_shp(samplesVector, segmentationVector, outFolder, tileSamplesVector)
        # intersect.intersectSqlites(samplesVector, segmentationVector, outFolder, tileSamplesVector, epsg, "intersection", attributes, vectformat='ESRI Shapefile')

    samplesVector = "learn_samples_region_{}_seed_{}".format(region, seed)
    fu.mergeVectors(samplesVector,outFolder,tiles_samples)
    samplesVector = os.path.join(outFolder,samplesVector+'.shp')
    addFieldID(samplesVector)
    for tile in tiles:
        tileVector = os.path.join(cfg.getParam('chain', 'outputPath'), "shapeRegion", "{}_region_{}_{}.shp".format(region_pattern, region, tile))
        tileSamplesVector = "{}_learn_samples_region_{}_seed_{}.shp".format(tile, region, seed)
        if os.path.exists(os.path.join(outFolder,tileSamplesVector)) :
            fu.removeShape(os.path.splitext(os.path.join(outFolder,tileSamplesVector))[0],['.prj','.shp','.dbf','.shx'])
        intersect_shp(samplesVector, tileVector, outFolder, tileSamplesVector)
        # intersect.intersectSqlites(samplesVector+'.shp', tileVector, outFolder, tileSamplesVector, epsg, "intersection", attributes, vectformat='ESRI Shapefile')