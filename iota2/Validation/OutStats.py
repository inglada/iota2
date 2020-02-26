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
"""
compute statistics (histograms of training/validation samples
well/bad classified) by tiles
"""

import argparse
import os
import sys
from osgeo import gdal
from osgeo.gdalconst import *
from osgeo import ogr
import numpy as np


def raster2array(rasterfn):
    """get raster as a numpy array"""
    raster = gdal.Open(rasterfn)
    band = raster.GetRasterBand(1)
    return band.ReadAsArray()


def get_diff_histo(conf_min, conf_max, conf_step, confidence, difference):
    """compute histrograms"""
    diff = [[], [], [], [], [], [], []]
    for current_conf in np.arange(conf_min, conf_max + 1, conf_step):
        y, x = np.where(confidence == current_conf)
        if len(y) >= 1:
            coord = [(current_x, current_y)
                     for current_x, current_y in zip(x, y)]
            for current_x, current_y in coord:
                diff[difference[current_y][current_x]].append(current_conf)
    return diff


def gen_stats_diff(path_to_config_stats, stats_name, histrogram, bins):
    """write histrogram"""
    stats = open(path_to_config_stats, "a")
    stats.write(stats_name + ":\n{\n\thistogram:'" + histrogram +
                "'\n\tbins:'" + bins + "'\n}\n\n")
    stats.close()


def histo(array, bins):
    """compute histogram"""
    hist = []
    for current_bin in bins:
        indexes = np.where(array == current_bin)
        hist.append(len(indexes[0]))
    return hist, bins


def out_statistics(iota2_output_path: str, tile: str, runs: int) -> None:
    """
    compute statistics (histograms of training/validation samples
    well/bad classified) to a given tile

    Parameters
    ----------
    iota2_output_path : str
        iota2 output directory
    tile : str
        tile to compute statistics
    runs : int
        number of random learning/validation sample-set
    """

    # 1 valid NOK
    # 2 valid OK
    # 3 app NOK
    # 4 app OK
    stats_name = ["ValidNOK", "ValidOK", "AppNOK", "AppOK"]

    conf_step = 1
    conf_min = 1
    conf_max = 100
    cloud_all_tile = iota2_output_path + "/final/PixelsValidity.tif"
    src_ds = gdal.Open(cloud_all_tile)
    if src_ds is None:
        print('Unable to open %s' % cloud_all_tile)
        sys.exit(1)
    srcband = src_ds.GetRasterBand(1).ReadAsArray()
    max_view = np.amax(srcband)
    cloud = raster2array(iota2_output_path + "/final/TMP/" + tile +
                         "_Cloud_StatsOK.tif")
    for seed in range(runs):
        confidence = raster2array(iota2_output_path + "/final/TMP/" + tile +
                                  "_GlobalConfidence_seed_" + str(seed) +
                                  ".tif")
        difference = raster2array(iota2_output_path + "/final/TMP/" + tile +
                                  "_seed_" + str(seed) + "_CompRef.tif")
        diff_histo = get_diff_histo(conf_min, conf_max, conf_step, confidence,
                                    difference)
        stats_tile = os.path.join(iota2_output_path, "final", "TMP",
                                  f"{tile}_stats_seed_f{seed}.cfg")
        if os.path.exists(stats_tile):
            os.remove(stats_tile)
        stats = open(stats_tile, "a")
        stats.write("AllDiffStats:'" + ", ".join(stats_name) + "'\n")
        stats.close()
        for i in range(len(stats_name)):
            hist, bin_edges = histo(diff_histo[i + 1],
                                    bins=np.arange(conf_min, conf_max + 1,
                                                   conf_step))
            hist_str = " ".join([str(currentVal) for currentVal in hist])
            bin_edges_str = " ".join(
                [str(currentVal) for currentVal in bin_edges])
            gen_stats_diff(stats_tile, stats_name[i], hist_str, bin_edges_str)
        hist_n_view, bins_n_view = histo(cloud,
                                         bins=np.arange(0, max_view + 1, 1))
        hist_str = " ".join([str(currentVal) for currentVal in hist_n_view])
        bin_edges_str = " ".join(
            [str(currentVal) for currentVal in bins_n_view])
        gen_stats_diff(stats_tile, "TileValidity", hist_str, bin_edges_str)


if __name__ == "__main__":

    PARSER = argparse.ArgumentParser(description="")
    PARSER.add_argument("-i2_output_path",
                        dest="iota2_output_path",
                        help="iota2 output directory",
                        required=True)
    PARSER.add_argument("-tile",
                        dest="tile",
                        help="Tile to extract statistics",
                        required=True)
    PARSER.add_argument(
        "-runs",
        dest="runs",
        help="number of random learning/validation sample-sets",
        required=True)
    ARGS = PARSER.parse_args()

    out_statistics(ARGS.iota2_output_path, ARGS.tile, ARGS.runs)
