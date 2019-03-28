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
import shutil

from Common import OtbAppBank as otb
from Common import FileUtils as fut
from Common.Utils import run
from Sensors.Sensors_container import Sensors_container
from VectorTools import XMLStatsToShape

logger = logging.getLogger(__name__)

def tile_samples_zonal_statistics(region_seed_tile, cfg, workingDirectory=None):
    """
    """
    from Common import ServiceConfigFile as SCF
    #because serviceConfigFile's objects are not serializable
    if not isinstance(cfg, SCF.serviceConfigFile):
        config_path = cfg
        cfg = SCF.serviceConfigFile(cfg)

    region, tiles, seed = region_seed_tile

    iota2_directory = cfg.getParam('chain', 'outputPath')
    seg_directory = os.path.join(iota2_directory, "segmentation")

    for tile in tiles :
        samples = os.path.join(seg_directory, "{}_{}_seg.shp".format(tile, region))
        sensor_tile_container = Sensors_container(config_path,
                                          tile,
                                          working_dir=None)
        sensors_features = sensor_tile_container.get_sensors_features(available_ram=1000)
        outputs_list = []
        labels=[]
        for sensor_name, ((sensor_features, sensor_features_dep), features_labels) in sensors_features:
            sensor_features.Execute()
            labels+=features_labels
            output_xml = os.path.join(seg_directory, "{}_{}_tile_samples_region_{}_seed_{}_stats.xml".format(sensor_name, tile, region, seed))
            ZonalStatisticsApp = otb.CreateZonalStatistics({"in":sensor_features,
                                                            "inbv": "0",
                                                            "inzone.vector.iddatafield": "DN",
                                                            "inzone.vector.in": samples,
                                                            "out.xml.filename": output_xml
                                                            })
            ZonalStatisticsApp.ExecuteAndWriteOutput()
            outputs_list.append(output_xml)
        tile_stats_xml = os.path.join(seg_directory, "{}_tile_samples_region_{}_seed_{}_stats.xml".format(tile, region, seed))
        XMLStatsToShape.merge_xml_stats(tile_stats_xml, outputs_list)
        XMLStatsToShape.add_field_from_XML(samples, tile_stats_xml,labels)
        labels = XMLStatsToShape.labels_format_to_DBF(labels)
        labels_out = os.path.join(seg_directory,"{}_tile_samples_region_{}_seed_{}_stats_label.txt".format(sensor_name, tile, region, seed))
        with open(labels_out,'w') as label_file :
            for l in labels:
                file.write(str(l)+'\n')


def learning_samples_zonal_statistics(region_seed_tile, cfg, workingDirectory=None):
    """
    """
    from Common import ServiceConfigFile as SCF
    #because serviceConfigFile's objects are not serializable
    if not isinstance(cfg, SCF.serviceConfigFile):
        config_path = cfg
        cfg = SCF.serviceConfigFile(cfg)

    region, tiles, seed = region_seed_tile

    iota2_directory = cfg.getParam('chain', 'outputPath')
    seg_directory = os.path.join(iota2_directory, "segmentation")

    outputs_list = []
    for tile in tiles :
        learning_samples = os.path.join(seg_directory, "{}_learn_samples_region_{}_seed_{}.shp".format(tile, region, seed))
        sensor_tile_container = Sensors_container(config_path,
                                          tile,
                                          working_dir=None)
        sensors_features = sensor_tile_container.get_sensors_features(available_ram=1000)
        labels=[]
        for sensor_name, ((sensor_features, sensor_features_dep), features_labels) in sensors_features:
            sensor_features.Execute()
            labels+=features_labels
            output_xml = os.path.join(seg_directory, "{}_{}_learn_samples_region_{}_seed_{}_stats.xml".format(sensor_name, tile, region, seed))
            ZonalStatisticsApp = otb.CreateZonalStatistics({"in":sensor_features,
                                                            "inbv": "0",
                                                            "inzone.vector.in": learning_samples,
                                                            "inzone.vector.iddatafield": "ID",
                                                            "out.xml.filename": output_xml
                                                            })
            ZonalStatisticsApp.ExecuteAndWriteOutput()
            outputs_list.append(output_xml)

    learning_samples_stats = os.path.join(seg_directory,"learn_samples_region_{}_seed_{}_stats.xml".format(region, seed))
    XMLStatsToShape.merge_xml_stats(learning_samples_stats,outputs_list)
    learning_samples_vector = os.path.join(seg_directory,"learn_samples_region_{}_seed_{}.shp".format(region, seed))
    XMLStatsToShape.add_field_from_XML(learning_samples_vector, learning_samples_stats, labels)
    labels = XMLStatsToShape.labels_format_to_DBF(labels)
    labels_out = os.path.join(seg_directory,"learn_samples_region_{}_seed_{}_stats_label.txt".format(region, seed))
    with open(labels_out,'w') as file :
        for l in labels:
            file.write(str(l)+'\n')
