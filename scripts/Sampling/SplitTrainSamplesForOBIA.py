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

logger = logging.getLogger(__name__)

def split_segmentation_by_tiles(cfg, tile, wd):
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

    logger.info("Clip segmentation for %s tile and vectorize" % tile)
    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)

    epsg = int((cfg.getParam('GlobChain', 'proj')).split(":")[-1])
    segmentation = cfg.getParam('chain','OBIA_segmentation_path')
    segmentationRaster = None
    segmentationVector = None
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

    if segmentationVector is None:
        tileVector = os.path.join(cfg.getParam('chain', 'outputPath'), "envelope", tile + '.shp')
        tiledRasterSegmentation = os.path.join(cfg.getParam('chain', 'outputPath'), "segmentation", tile + '_seg.tif')
        extractRoiApp = OtbAppBank.CreateExtractROIApplication({"in": segmentationRaster,
                                                               "mode": "fit",
                                                               "mode.fit.vect": tileVector,
                                                               "out": tiledRasterSegmentation})
        extractRoiApp.ExecuteAndWriteOutput()

        tiledVectorSegmentation = os.path.join(cfg.getParam('chain', 'outputPath'), "segmentation", tile + '_seg.shp')
        cmd = "gdal_polygonize.py -f \"ESRI Shapefile\" %s %s" % (tiledRasterSegmentation, tiledVectorSegmentation)
        os.system(cmd)

    else :
        tileVector = os.path.join(cfg.getParam('chain', 'outputPath'), "envelope", tile + '.shp')
        outFolder = os.path.join(cfg.getParam('chain', 'outputPath'), "segmentation")
        tiledVectorSegmentation = os.path.join(outFolder, tile + '_seg.shp')
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

    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)

    region, tiles, seed = region_tiles_seed
    samplesVector = os.path.join(cfg.getParam('chain', 'outputPath'), 'samplesSelection', "samples_region_{}_seed_{}.shp".format(region, seed))
    dataField = (cfg.getParam('chain', 'dataField')).lower()
    regionField = (cfg.getParam('chain', 'regionField')).lower()
    attributes = [dataField, regionField, "originfid", "seed_"+str(seed)]
    outFolder = os.path.join(cfg.getParam('chain', 'outputPath'), "segmentation")
    epsg = int((cfg.getParam('GlobChain', 'proj')).split(":")[-1])
    tiles_samples = []
    for tile in tiles :
        segmentationVector = os.path.join(outFolder, tile + "_seg.shp")
        tileSamplesVector = os.path.join(outFolder, "{}_samples_region_{}_seed_{}.shp".format(tile,region, seed))
        tiles_samples.append(tileSamplesVector)
        intersect.intersectSqlites(samplesVector, segmentationVector, outFolder, tileSamplesVector, epsg, "intersection", attributes, vectformat='SQLite')

    tileSamplesVector = "samples_region_{}_seed_{}".format(region, seed)
    fu.mergeVectors(tileSamplesVector,outFolder,tiles_samples)