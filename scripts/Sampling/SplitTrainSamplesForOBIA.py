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
    segmentationRaster = cfg.getParam('objectbase','segmentation_raster')
    if segmentationRaster == "None":
        segmentationRaster = os.path.join(cfg.getParam('chain', 'outputPath'), "segmentation",'seg_input.tif')

    segmentationVector = cfg.getParam('objectbase','segmentation_vector')
    if segmentationVector == "None":
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

def format_sample_to_segmentation(cfg, tile, wd):
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

    logger.info("Split %s train sample with segmentation" % tile)
    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)

    segmentationVector = cfg.getParam('objectbase','segmentation_vector')
    if segmentationVector == "None":
        segmentationVector = os.path.join(cfg.getParam('chain', 'outputPath'), "segmentation",tile + "_seg.shp")

    samplesVector = os.path.join(cfg.getParam('chain', 'outputPath'),'formattingVectors',tile + '.shp')

    outFolder = os.path.join(cfg.getParam('chain', 'outputPath'), "segmentation")
    trainSampleSeg = os.path.join(outFolder, tile + '_train_Seg.shp')
    epsg = int((cfg.getParam('GlobChain', 'proj')).split(":")[-1])

    dataField = (cfg.getParam('chain', 'dataField')).lower()
    regionField = (cfg.getParam('chain', 'regionField')).lower()
    seeds = cfg.getParam('chain', 'runs')
    seedslist = []
    for seed in range(seeds):
    	seedslist.append("seed_"+str(seed))

    attributes = [dataField, regionField, "originfid"] + seedslist + ["tile_o"]
    intersect.intersectSqlites(samplesVector, segmentationVector, outFolder, trainSampleSeg, epsg, "intersection", attributes, vectformat='SQLite')