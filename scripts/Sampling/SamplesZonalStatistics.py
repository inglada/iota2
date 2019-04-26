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

import logging
import os
import glob
import shutil
import subprocess
import time

from Common import OtbAppBank as otb
from Common import FileUtils as fut
from Common.Utils import run
from Sensors.Sensors_container import Sensors_container
from VectorTools import XMLStatsToShape
from MPI.launch_tasks import queuedProcess

logger = logging.getLogger(__name__)

def tile_samples_zonal_statistics(tile, cfg, workingDirectory=None):
    """ Compute zonal statistics of a tile

    Parameters
    ----------
    tile : string
        tile name
    cfg : serviceConfig obj
        configuration object for parameters
    workingDirectory : string
        path to the working directory

    Note
    ------
    """
    from Common import ServiceConfigFile as SCF
    #because serviceConfigFile's objects are not serializable
    if not isinstance(cfg, SCF.serviceConfigFile):
        config_path = cfg
        cfg = SCF.serviceConfigFile(cfg)

    iota2_directory = cfg.getParam('chain', 'outputPath')
    seg_directory = os.path.join(iota2_directory, "segmentation")
    tsamples_directory = os.path.join(iota2_directory, "tilesSamples")
    if not os.path.exists(os.path.join(tsamples_directory,tile)):
        os.mkdir(os.path.join(tsamples_directory,tile))

    region_path = cfg.getParam('chain','regionPath')
    if not region_path :
        region_path = os.path.join(cfg.getParam('chain', 'outputPath'), "MyRegion.shp")
    region_pattern = os.path.basename(region_path).split(".")[0]

    logger.info("Compute zonal statistics for {}".format(tile))
    tileRegionShps = glob.glob(os.path.join(iota2_directory, "shapeRegion", "{}_region_*_{}.shp".format(region_pattern, tile)))
    regions = [region.split('_')[-2] for region in tileRegionShps]
    for region in regions :
        samples_list = glob.glob(os.path.join(seg_directory, tile, "{}_region_{}_seg_*.shp".format(tile, region)))
        sensor_tile_container = Sensors_container(config_path,
                                          tile,
                                          working_dir=None)
        sensors_features = sensor_tile_container.get_sensors_features(available_ram=1000)
        outputs_list = []
        labels=[]
        n_list = []
        for sensor_name, ((sensor_features, sensor_features_dep), features_labels) in sensors_features:
            # Stack every feature
            sensor_features.Execute()
            labels+=features_labels
            for samples in samples_list :
                n = os.path.splitext(samples)[0].split('_')[-1]
                n_list.append(n)
                output_xml = os.path.join(tsamples_directory, tile, "{}_{}_tile_samples_region_{}_{}_stats.xml".format(sensor_name, tile, region, n))
                key = "DN"
                # Do zonal statistics
                ZonalStatisticsApp = otb.CreateZonalStatistics({"in":sensor_features,
                                                                "inbv": "0",
                                                                "inzone.vector.iddatafield": key,
                                                                "inzone.vector.in": samples,
                                                                "out.xml.filename": output_xml
                                                                })
                ZonalStatisticsApp.ExecuteAndWriteOutput()
        logger.info("Statistics management")
        cmd_list=[]
        for n in n_list :
            outputs_list = glob.glob(os.path.join(tsamples_directory, tile, "*_{}_tile_samples_region_{}_{}_stats.xml".format(tile, region, n)))
            tile_stats_xml = os.path.join(tsamples_directory, tile, "{}_tile_samples_region_{}_{}_stats.xml".format(tile, region, n))
            if len(outputs_list)>1 :
                # Merge xml files
                XMLStatsToShape.merge_xml_stats(tile_stats_xml, outputs_list)
            else :
                shutil.copy(outputs_list[0], tile_stats_xml)
                XMLStatsToShape.clean_xml_stats(tile_stats_xml)
            # Convert xml to csv (supported by ogr)
            csv_stats = XMLStatsToShape.convert_XML_to_CSV(tile_stats_xml,key,labels)
            logger.info("Creating output")
            # Join features statistics on the id key
            labels_dbf = XMLStatsToShape.labels_format_to_DBF(labels)
            samples = os.path.join(seg_directory, tile, "{}_region_{}_seg_{}.shp".format(tile, region, n))
            input_fields= XMLStatsToShape.list_shp_field(samples)
            tile_samples_vector_stats = os.path.join(tsamples_directory, tile,"{}_tile_samples_region_{}_{}_stats.shp".format(tile, region, n))
            cmd = '''ogr2ogr -f "ESRI Shapefile" -sql "SELECT'''
            for field in input_fields :
                cmd += ''' shp.{} as {} ,'''.format(field, field)
            for label in labels_dbf :
                cmd += ''' CAST(csv.{} as integer(6)) as {} ,'''.format(label, label)
            cmd = cmd[:-1]
            cmd += ''' FROM {} shp LEFT JOIN '{}'.{} csv ON shp.{} = csv.{}"'''.format(os.path.splitext(os.path.basename(samples))[0],
                                                                                   csv_stats, os.path.splitext(os.path.basename(csv_stats))[0],
                                                                                   key, key)
            cmd += " {} {}".format(tile_samples_vector_stats,samples)
            cmd_list.append(cmd)
            
        queuedProcess(cmd_list, N_processes=6, shell=True)
        labels_out = os.path.join(tsamples_directory, "{}_tile_samples_region_{}_stats_label.txt".format(tile, region))
        with open(labels_out, 'w') as label_file :
            for l in labels_dbf:
                label_file.write(str(l)+'\n')

def learning_samples_zonal_statistics(region_seed_tile, cfg, workingDirectory=None):
    """ Compute zonal statistics of a tile

    Parameters
    ----------
    region_seed_tile : list
        list [region, tiles, seed], cf. Sampling/SamplesMerge
    cfg : serviceConfig obj
        configuration object for parameters
    workingDirectory : string
        path to the working directory

    Note
    ------
    """
    from Common import ServiceConfigFile as SCF
    #because serviceConfigFile's objects are not serializable
    if not isinstance(cfg, SCF.serviceConfigFile):
        config_path = cfg
        cfg = SCF.serviceConfigFile(cfg)

    region, tiles, seed = region_seed_tile

    iota2_directory = cfg.getParam('chain', 'outputPath')
    seg_directory = os.path.join(iota2_directory, "segmentation")
    lsamples_directory = os.path.join(iota2_directory, "learningSamples")

    outputs_list = []
    logger.info("Compute zonal statistics for learning samples region {} seed {}".format(region, seed))
    #Compute zonal stats of learning samples for each tiles
    for tile in tiles :
        learning_samples = os.path.join(seg_directory, "{}_learn_samples_region_{}_seed_{}.shp".format(tile, region, seed))
        sensor_tile_container = Sensors_container(config_path,
                                          tile,
                                          working_dir=None)
        sensors_features = sensor_tile_container.get_sensors_features(available_ram=1000)
        labels=[]
        for sensor_name, ((sensor_features, sensor_features_dep), features_labels) in sensors_features:
            # Stack every feature
            sensor_features.Execute()
            labels+=features_labels
            output_xml = os.path.join(lsamples_directory, "{}_{}_learn_samples_region_{}_seed_{}_stats.xml".format(sensor_name, tile, region, seed))
            output_shp = os.path.join(lsamples_directory, "{}_{}_learn_samples_region_{}_seed_{}_stats.shp".format(sensor_name, tile, region, seed))
            key = "ID"
            # Do zonal statistics
            ZonalStatisticsApp = otb.CreateZonalStatistics({"in":sensor_features,
                                                            "inbv": "0",
                                                            "inzone.vector.in": learning_samples,
                                                            "inzone.vector.iddatafield": key,
                                                            "out.xml.filename": output_xml
                                                            })
            ZonalStatisticsApp.ExecuteAndWriteOutput()
            outputs_list.append(output_xml)

    logger.info("Statistics management")
    # Merge xml files (for each sensor and tiles)
    learning_samples_stats = os.path.join(lsamples_directory, "learn_samples_region_{}_seed_{}_stats.xml".format(region, seed))
    XMLStatsToShape.merge_xml_stats(learning_samples_stats, outputs_list)
    # Convert xml to csv (supported by ogr)
    csv_stats = XMLStatsToShape.convert_XML_to_CSV(learning_samples_stats, key, labels)
    labels = XMLStatsToShape.labels_format_to_DBF(labels)
    logger.info("Creating output")
    # Join features statistics on the id key
    learning_samples_vector = os.path.join(seg_directory, "learn_samples_region_{}_seed_{}.shp".format(region, seed))
    input_fields= XMLStatsToShape.list_shp_field(learning_samples_vector)
    learning_samples_vector_stats = os.path.join(lsamples_directory, "learn_samples_region_{}_seed_{}_stats.shp".format(region, seed))
    cmd = '''ogr2ogr -f "ESRI Shapefile" -sql "SELECT'''
    for field in input_fields :
        cmd += ''' shp.{} as {} ,'''.format(field, field)
    for label in labels :
        cmd += ''' CAST(csv.{} as integer(6)) as {} ,'''.format(label, label)
    cmd = cmd[:-1]
    cmd += ''' FROM {} shp LEFT JOIN '{}'.{} csv ON shp.{} = csv.{}"'''.format(os.path.splitext(os.path.basename(learning_samples_vector))[0],
                                                                           csv_stats, os.path.splitext(os.path.basename(csv_stats))[0],
                                                                           key, key)
    cmd += " {} {}".format(learning_samples_vector_stats,learning_samples_vector)
    os.system(cmd)
    labels_out = os.path.join(lsamples_directory, "learn_samples_region_{}_seed_{}_stats_label.txt".format(region, seed))
    with open(labels_out, 'w') as label_file :
        for l in labels:
            label_file.write(str(l)+'\n')
