#!/usr/bin/python
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

import os
from iota2.Common import FileUtils as fu


def build_obia_train_cmd(sample, classif, options, dataField, out, feats,
                         stat):
    """ Compute command line for model creation (one per region and run)

    Parameters
    ----------
    sample : strings
       path to learning samples layer
    classif : string
        name of classifier
    options : string
        string of every options of the classifier, ex : '-rf.max X -rf.min Y -rf.nbtrees Z'
    dataField : string
        field name of ground truth class
    out : string
        output model path
    feats : string
        string of fields to use, ex : 'T1F1D1 T1F1D2 T1F2D1 T1F2D2'
    stat : string
        path to the xml stats (unskew model step)

    Note
    ------
    """
    cmd = "otbcli_TrainVectorClassifier -io.vd"
    cmd += " {} -classifier {} {} -cfield {} -feat {} -io.out {}".format(
        sample, classif, options, dataField, feats, out)
    if stat is not None:
        cmd += " -io.stats {}".format(stat)
    return cmd


def launch_obia_train_model(iota2_directory, data_field, region_seed_tile,
                            path_to_cmd_train, out_folder, classifier,
                            options):
    """ Compute command line for model creation (one per region and run)

    Parameters
    ----------
    cfg : serviceConfig obj
        configuration object for parameters
    dataField : string
        field name of ground truth class
    region_seed_tile : list
        list [region, tiles, seed], cf. Sampling/SamplesMerge
    pathToCmdTrain : string
        path to the cmd folder
    outfolder : string
        path to the model folder
    pathWd : string
        path to the working directory

    Note
    ------
    """

    lsamples_directory = os.path.join(iota2_directory, "learningSamples")
    stats_directory = os.path.join(iota2_directory, "stats")

    cmd_list = []
    # Construct every cmd
    for region, _, seed in region_seed_tile:
        sample = os.path.join(
            lsamples_directory,
            f"learn_samples_region_{region}_seed_{seed}_stats.shp")
        stat = os.path.join(stats_directory,
                            f"features_stats_region_{region}_seed_{seed}.xml")
        if not os.path.exists(stat):
            stat = None
        feats = open(
            os.path.join(
                lsamples_directory,
                f"learn_samples_region_{region}_seed_{seed}_stats_label.txt")
        ).read().replace('\n', ' ')
        output = os.path.join(out_folder,
                              f"model_region_{region}_seed_{seed}.txt")
        cmd = build_obia_train_cmd(sample, classifier, options, data_field,
                                   output, feats, stat)
        cmd_list.append(cmd)
    # Save these cmd to a txt file
    fu.writeCmds(path_to_cmd_train + "/train.txt", cmd_list)
    return cmd_list
