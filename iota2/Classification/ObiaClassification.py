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
import glob
from iota2.Common import FileUtils as fu
from iota2.MPI import launch_tasks


def launchObiaClassification(seed,
                             nb_cpu,
                             data_field,
                             output_path,
                             path_wd=None):
    """Do classification for every model of a seed

    Parameters
    ----------
    seed : int
        number of the seed
    nb_cpu : int
        number of cpu used for Classification
    data_field: str
        name for classes in vector files
    output_path: str
        root output path, from which all subdirectories are deduced
    pathWd : string
        path to the working directory

    Note
    ------
    """

    tsamples_dir = os.path.join(output_path, "tilesSamples")
    lsamples_dir = os.path.join(output_path, "learningSamples")
    model_dir = os.path.join(output_path, "model")
    stats_dir = os.path.join(output_path, "stats")
    classif_dir = os.path.join(output_path, "classif")
    work_dir = classif_dir
    #if path_wd is not None:
    #    work_dir = path_wd
    all_cmd = []

    models = fu.FileSearch_AND(model_dir, True, "model_region",
                               f"seed_{seed}.txt")
    for model in models:
        region = os.path.splitext(os.path.basename(model))[0].split('_')[2]
        features_stats = os.path.join(
            stats_dir, f"features_stats_region_{region}_seed_{seed}.xml")

        samples_list = fu.FileSearch_AND(tsamples_dir, True,
                                         f"_region_{region}", "_stats.shp")
        for samples in samples_list:
            tile = samples.split('/')[-2]
            if not os.path.exists(os.path.join(work_dir, tile)):
                os.mkdir(os.path.join(work_dir, tile))
            part = samples.split('_')[-2]
            ft_file = os.path.join(
                lsamples_dir,
                f"learn_samples_region_{region}_seed_{seed}_stats_label.txt")
            feats = open(ft_file).read().replace('\n', ' ')
            out = os.path.join(
                work_dir, tile,
                f"{tile}_model_{region}_seed_{seed}_part_{part}.shp")
            cmd = (f"otbcli_VectorClassifier -in {samples} "
                   f"-instat {features_stats} "
                   f"-model {model} -cfield {data_field} -feat {feats} "
                   f"-out {out} -confmap 1")
            all_cmd.append(cmd)
    launch_tasks.queuedProcess(all_cmd, N_processes=nb_cpu, shell=True)
    return


def reassembleParts(seed,
                    nb_cpu,
                    tiles,
                    data_field,
                    output_path,
                    im_ref,
                    path_wd=None):
    """Merge parts (resulting of SpliSegmentationByTiles step)

    Parameters
    ----------
    seed : int
        number of the seed
    nb_cpu : int
        number of cpu used for Classification
    cfg : serviceConfig obj
        configuration object for parameters
    pathWd : string
        path to the working directory

    Note
    ------
    """
    from iota2.Common.Tools import ExtractROIRaster

    model_dir = os.path.join(output_path, "model")
    classif_dir = os.path.join(output_path, "classif")
    work_dir = classif_dir
    # if path_wd is not None:
    #    work_dir = path_wd

    # im_ref = cfg.getParam('chain', 'OBIA_segmentation_path')
    spx, spy = ExtractROIRaster.getRasterResolution(im_ref)

    models = glob.glob(
        os.path.join(model_dir, 'model_region_*_seed_{}.txt'.format(seed)))
    models = fu.FileSearch_AND(model_dir, True, "model_region_",
                               f"seed_{seed}.txt")
    for model in models:
        region = os.path.splitext(os.path.basename(model))[0].split('_')[2]
        for tile in tiles:
            # parts = glob.glob(
            #     os.path.join(
            #         classif_dir, tile, "{}_model_{}_seed_{}_part_*.shp".format(
            #             tile, region, seed)))
            parts = fu.FileSearch_AND(
                os.path.join(classif_dir, tile), True,
                f"{tile}_model_{region}_seed"
                f"_{seed}_part", ".shp")

            out_parts = ''
            out_parts_conf = ''
            allcmd = []
            for part in parts:
                out = os.path.splitext(part)[0] + '.tif'
                p = os.path.splitext(out)[0].split('_')[-1]
                out_parts += ' ' + out
                out_confmap = os.path.join(
                    work_dir, tile, f"{tile}_model_{region}_confidence_seed"
                    f"_{seed}_part_{p}.tif")
                out_parts_conf += ' ' + out_confmap
                cmd = (f'otbcli_Rasterization -in {part} -out {out} -mode '
                       f'attribute -mode.attribute.field {data_field}'
                       f' -spx {spx} -spy {spy}')
                allcmd.append(cmd)
                cmd = (f'otbcli_Rasterization -in {part} -out {out_confmap} '
                       f'-mode attribute -mode.attribute.field confidence '
                       f'-spx {spx} -spy {spy}')
                allcmd.append(cmd)
            if len(allcmd) > 0:
                launch_tasks.queuedProcess(allcmd,
                                           N_processes=nb_cpu,
                                           shell=True)
                out_merge = os.path.join(
                    work_dir, f"Classif_{tile}_model_{region}_seed_{seed}.tif")
                out_conf_merge = os.path.join(
                    work_dir,
                    f"{tile}_model_{region}_confidence_seed_{seed}.tif")
                cmd = (f'gdal_merge.py -o {out_merge} -ot Int32 -co'
                       f' COMPRESS=DEFLATE -n 0 -a_nodata 0 {out_parts}')
                launch_tasks.launchBashCmd(cmd)
                cmd = (f'gdal_merge.py -o {out_conf_merge} -co '
                       f'COMPRESS=DEFLATE -n 0 -a_nodata 0 {out_parts_conf}')
                launch_tasks.launchBashCmd(cmd)
