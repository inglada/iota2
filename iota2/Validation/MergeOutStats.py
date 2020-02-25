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
module dedicated to merge tile's statistics
"""

import argparse
import math
from typing import List
from config import Config
from osgeo.gdalconst import *
import numpy as np
import matplotlib
matplotlib.use("AGG")
import matplotlib.pyplot as plt
from iota2.Common import FileUtils as fu


def get_valid_ok(config_stats):
    """
    """
    histo_valid_ok = Config(open(config_stats)).ValidOK.histogram
    bins = Config(open(config_stats)).ValidOK.bins

    histo_valid_ok_s = histo_valid_ok.split(" ")
    histo_valid_ok = [int(currentVal) for currentVal in histo_valid_ok_s]
    bins = bins.split(" ")
    bins_ = [int(currentVal) for currentVal in bins]
    return histo_valid_ok, bins_


def get_valid_nok(config_stats):
    """
    """
    histo_valid_nok = Config(open(config_stats)).ValidNOK.histogram
    bins = Config(open(config_stats)).ValidNOK.bins

    histo_valid_nok_s = histo_valid_nok.split(" ")
    histo_valid_nok = [int(currentVal) for currentVal in histo_valid_nok_s]
    bins = bins.split(" ")
    bins_ = [int(currentVal) for currentVal in bins]

    return histo_valid_nok, bins_


def get_app_ok(config_stats):
    """
    """
    histo_app_ok = Config(open(config_stats)).AppOK.histogram
    bins = Config(open(config_stats)).AppOK.bins

    histo_app_ok_s = histo_app_ok.split(" ")
    histo_app_ok = [int(currentVal) for currentVal in histo_app_ok_s]
    bins = bins.split(" ")
    bins_ = [int(currentVal) for currentVal in bins]

    return histo_app_ok, bins_


def get_app_nok(config_stats: str):
    """
    """
    histo_app_nok = Config(open(config_stats)).AppNOK.histogram
    bins = Config(open(config_stats)).AppNOK.bins

    histo_app_nok_s = histo_app_nok.split(" ")
    histo_app_nok = [int(current_val) for current_val in histo_app_nok_s]
    bins = bins.split(" ")
    bins_ = [int(current_val) for current_val in bins]

    return histo_app_nok, bins_


def get_validity(config_stats: str):
    """
    """
    histo_validity = Config(open(config_stats)).TileValidity.histogram
    bins = Config(open(config_stats)).TileValidity.bins

    histo_validity_s = histo_validity.split(" ")
    histo_validity = [int(current_val) for current_val in histo_validity_s]
    bins = bins.split(" ")
    bins_ = [int(currentVal) for currentVal in bins]
    return histo_validity, bins_


def sum_in_list(histo_list: List[List[str]]):
    """
    """
    histo_sum = [0] * len(histo_list[0])
    for i in range(len(histo_list)):  #current Tile
        for j in range(len(histo_list[i])):  #current bin
            histo_sum[j] += histo_list[i][j]
    return histo_sum


def save_histogram(save_path: str, histo: List[str], bins: List[str]):
    """save histogram"""

    save_histog = " ".join([str(current_val) for current_val in histo])
    save_bins = " ".join([str(current_val) for current_val in bins])
    with open(save_path, "w") as save_file:
        save_file.write("Pixels validity\nBins:" + save_bins + "\nHistogram:" +
                        save_histog)


def compute_mean_std(histo: List[int], bins: List[int]):
    """compute mearn and std
    """
    #Mean
    mean_nom = 0.0
    for current_val, current_bin in zip(histo, bins):
        mean_nom += (current_val * current_bin)
    mean = 0
    if np.sum(histo) != 0.0:
        mean = mean_nom / (np.sum(histo))

    #Var
    var_nom = 0.0
    for current_val, current_bin in zip(histo, bins):
        var_nom += current_val * (current_bin - mean)**2
    var = 0
    if np.sum(histo) != 0.0:
        var = var_nom / (np.sum(histo))
    return mean, math.sqrt(var)


def merge_output_statistics(i2_output_path: str, runs: int) -> None:
    """merge tile's statistics to a gloable one

    Parameters
    ----------
    i2_output_path : str
        iota2 output directory
    runs : int
        nomber of random learning/validation samples-set
    """

    for seed in range(runs):
        seed_stats = fu.fileSearchRegEx(i2_output_path +
                                        "/final/TMP/*_stats_seed_" +
                                        str(seed) + ".cfg")
        all_diff_test = Config(open(seed_stats[0])).AllDiffStats
        all_diff_test = all_diff_test.split(",")
        vok_buff = []
        vnok_buff = []
        aok_buff = []
        anok_buff = []
        validity_buff = []
        for current_tile_stats in seed_stats:
            histo_vok, bins_vok = get_valid_ok(current_tile_stats)
            histo_vnok, bins_vnok = get_valid_nok(current_tile_stats)
            histo_aok, bins_aok = get_app_ok(current_tile_stats)
            histo_anok, bins_anok = get_app_nok(current_tile_stats)
            histo_validity, bins_validity = get_validity(current_tile_stats)

            vok_buff.append(histo_vok)
            vnok_buff.append(histo_vnok)
            aok_buff.append(histo_aok)
            anok_buff.append(histo_anok)
            validity_buff.append(histo_validity)

        sum_vok = sum_in_list(vok_buff)
        sum_vnok = sum_in_list(vnok_buff)
        sum_aok = sum_in_list(aok_buff)
        sum_anok = sum_in_list(anok_buff)
        sum_validity = sum_in_list(validity_buff)

        mean_vok, std_vok = compute_mean_std(sum_vok, bins_vok)
        mean_vnok, std_vnok = compute_mean_std(sum_vnok, bins_vnok)
        plt.plot(bins_vok,
                 sum_vok,
                 label="Valid OK\nmean: " + "{0:.2f}".format(mean_vok) +
                 "\nstd: " + "{0:.2f}".format(std_vok) + "\n",
                 color="green")
        plt.plot(bins_vnok,
                 sum_vnok,
                 label="Valid NOK\nmean: " + "{0:.2f}".format(mean_vnok) +
                 "\nstd: " + "{0:.2f}".format(std_vnok) + "\n",
                 color="red")
        plt.ylabel("Nb pix")
        plt.xlabel("Confidence")
        lgd = plt.legend(loc="center left",
                         bbox_to_anchor=(1, 0.8),
                         numpoints=1)
        plt.title('Histogram')
        plt.savefig(i2_output_path + "/final/Stats_VOK_VNOK.png",
                    bbox_extra_artists=(lgd, ),
                    bbox_inches='tight')
        # We clear the buffer and close the figure
        plt.clf()
        plt.close()
        save_histogram(i2_output_path + "/final/Stats_VNOK.txt", sum_vnok,
                       bins_vnok)
        save_histogram(i2_output_path + "/final/Stats_VOK.txt", sum_vok,
                       bins_vok)

        plt.figure()
        mean_aok, std_aok = compute_mean_std(sum_aok, bins_aok)
        mean_anok, std_anok = compute_mean_std(sum_anok, bins_anok)
        plt.plot(bins_aok,
                 sum_aok,
                 label="Learning OK\nmean: " + "{0:.2f}".format(mean_aok) +
                 "\nstd: " + "{0:.2f}".format(std_aok) + "\n",
                 color="yellow")
        plt.plot(bins_anok,
                 sum_anok,
                 label="Learning NOK\nmean: " + "{0:.2f}".format(mean_anok) +
                 "\nstd: " + "{0:.2f}".format(std_anok),
                 color="blue")
        plt.ylabel("Nb pix")
        plt.xlabel("Confidence")
        lgd = plt.legend(loc="center left",
                         bbox_to_anchor=(1, 0.8),
                         numpoints=1)
        plt.title('Histogram')
        plt.savefig(i2_output_path + "/final/Stats_LOK_LNOK.png",
                    bbox_extra_artists=(lgd, ),
                    bbox_inches='tight')
        # We clear the buffer and close the figure
        plt.clf()
        plt.close()
        save_histogram(i2_output_path + "/final/Stats_LNOK.txt", sum_anok,
                       bins_anok)
        save_histogram(i2_output_path + "/final/Stats_LOK.txt", sum_aok,
                       bins_aok)

        plt.figure()
        plt.bar(bins_validity,
                sum_validity,
                label="pixels validity",
                color="red",
                align="center")
        plt.ylabel("Nb pix")
        plt.xlabel("Validity")
        plt.gca().yaxis.grid(True)
        plt.legend()
        plt.title('Histogram')
        plt.xticks(bins_validity, bins_validity)
        plt.xlim((0, max(bins_validity) + 1))
        plt.savefig(i2_output_path + "/final/Validity.png",
                    bbox_extra_artists=(lgd, ),
                    bbox_inches='tight')
        # We clear the buffer and close the figure
        plt.clf()
        plt.close()
        save_histogram(i2_output_path + "/final/Validity.txt", sum_validity,
                       bins_validity)


if __name__ == "__main__":

    PARSER = argparse.ArgumentParser(
        description="This function merges tile's statistics")
    PARSER.add_argument("-i2_output_path",
                        dest="i2_output_path",
                        help="i2 output directory",
                        required=True)
    PARSER.add_argument(
        "-runs",
        dest="runs",
        help="number of random learning/validation samples-set",
        required=True)
    ARGS = PARSER.parse_args()

    merge_output_statistics(ARGS.i2_output_path, ARGS.runs)
