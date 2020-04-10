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


def launch_unskew(region_seed_tile, iota2_directory):
    """ Compute command line for features statistics (one per region and run)

    Parameters
    ----------
    region_seed_tile : list
        list [region, tiles, seed], cf. Sampling/SamplesMerge
    iota2_directory : str
        path where iota2 directories have been created
    Note
    ------
    """

    lsamples_directory = os.path.join(iota2_directory, "learningSamples")
    stats_directory = os.path.join(iota2_directory, "stats")

    cmd_list = []
    # compute feature statistics for each model
    for region, _, seed in region_seed_tile:
        shp = os.path.join(
            lsamples_directory,
            f"learn_samples_region_{region}_seed_{seed}_stats.shp")
        output = os.path.join(
            stats_directory, f"features_stats_region_{region}_seed_{seed}.xml")
        ft_file = os.path.join(
            lsamples_directory,
            f"learn_samples_region_{region}_seed_{seed}_stats_label.txt")
        feats = open(ft_file).read().replace('\n', ' ')
        cmd = (f"otbcli_ComputeVectorFeaturesStatistics -io.vd {shp} "
               f" -io.stats {output} -feat {feats}")
        cmd_list.append(cmd)
    return cmd_list
