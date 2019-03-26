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
from osgeo import osr
from config import Config
from Common import OtbAppBank
from Common import FileUtils as fu
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

    region, tiles, seed = region_tiles_seed

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

    for tile in tiles :
        if segmentationVector is None:
            tileVector = os.path.join(cfg.getParam('chain', 'outputPath'), "shapeRegion", "{}_region_{}_{}.shp".format(region_pattern, region, tile))
            tiledRasterSegmentation = os.path.join(cfg.getParam('chain', 'outputPath'), "segmentation", '{}_{}_seg.tif'.format(tile, region))
            extractRoiApp = OtbAppBank.CreateExtractROIApplication({"in": segmentationRaster,
                                                                   "mode": "fit",
                                                                   "mode.fit.vect": tileVector,
                                                                   "out": tiledRasterSegmentation})
            extractRoiApp.ExecuteAndWriteOutput()

            tiledVectorSegmentation = os.path.join(cfg.getParam('chain', 'outputPath'), "segmentation", '{}_{}_seg.shp'.format(tile, region))
            cmd = "gdal_polygonize.py -f \"ESRI Shapefile\" %s %s" % (tiledRasterSegmentation, tiledVectorSegmentation)
            os.system(cmd)

        else :
            tileVector = os.path.join(cfg.getParam('chain', 'outputPath'), "shapeRegion", "{}_region_{}_{}.shp".format(region_pattern, region, tile))
            outFolder = os.path.join(cfg.getParam('chain', 'outputPath'), "segmentation")
            tiledVectorSegmentation = os.path.join(cfg.getParam('chain', 'outputPath'), "segmentation", '{}_{}_seg.shp'.format(tile, region))
            intersect.intersectSqlites(segmentationVector, tileVector, outFolder, tiledVectorSegmentation, epsg, "union", [], vectformat='SQLite')

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
        segmentationVector = os.path.join(outFolder, '{}_{}_seg.shp'.format(tile, region))
        tileSamplesVector = os.path.join(outFolder, "{}_samples_region_{}_seed_{}.shp".format(tile, region, seed))
        tiles_samples.append(tileSamplesVector)
        if os.path.exists(tileSamplesVector) :
            fu.removeShape(os.path.splitext(tileSamplesVector)[0],['.prj','.shp','.dbf','.shx'])
        intersect_shp(samplesVector, segmentationVector, outFolder, tileSamplesVector)
        # intersect.intersectSqlites(samplesVector, segmentationVector, outFolder, tileSamplesVector, epsg, "intersection", attributes, vectformat='ESRI Shapefile')

    samplesVector = "samples_region_{}_seed_{}".format(region, seed)
    fu.mergeVectors(samplesVector,outFolder,tiles_samples)
    samplesVector = os.path.join(outFolder,samplesVector+'.shp')
    addFieldID(samplesVector)
    for tile in tiles:
        tileVector = os.path.join(cfg.getParam('chain', 'outputPath'), "shapeRegion", "{}_region_{}_{}.shp".format(region_pattern, region, tile))
        tileSamplesVector = "{}_samples_region_{}_seed_{}.shp".format(tile, region, seed)
        if os.path.exists(os.path.join(outFolder,tileSamplesVector)) :
            fu.removeShape(os.path.splitext(os.path.join(outFolder,tileSamplesVector))[0],['.prj','.shp','.dbf','.shx'])
        intersect_shp(samplesVector, tileVector, outFolder, tileSamplesVector)
        # intersect.intersectSqlites(samplesVector+'.shp', tileVector, outFolder, tileSamplesVector, epsg, "intersection", attributes, vectformat='ESRI Shapefile')