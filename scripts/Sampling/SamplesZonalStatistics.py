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

logger = logging.getLogger(__name__)

def tile_samples_zonal_statistics(tile, cfg, workingDirectory=None):
    """
    """
    from Common import ServiceConfigFile as SCF
    #because serviceConfigFile's objects are not serializable
    if not isinstance(cfg, SCF.serviceConfigFile):
        config_path = cfg
        cfg = SCF.serviceConfigFile(cfg)

    iota2_directory = cfg.getParam('chain', 'outputPath')
    seg_directory = os.path.join(iota2_directory, "segmentation")

    tile_samples = os.path.join(seg_directory, "{}_seg.shp".format(tile))
    sensor_tile_container = Sensors_container(config_path,
                                      tile,
                                      working_dir=None)
    sensors_features = sensor_tile_container.get_sensors_features(available_ram=1000)
    for sensor_name, ((sensor_features, sensor_features_dep), features_labels) in sensors_features:
        sensor_features.Execute()
        output_xml = os.path.join(seg_directory, "{}_{}_samples_region_{}_seed_{}_stats.xml".format(sensor_name, tile, region, seed))
        output_shp = os.path.join(seg_directory, "{}_{}_samples_region_{}_seed_{}_stats.shp".format(sensor_name, tile, region, seed))
        ZonalStatisticsApp = otb.CreateZonalStatistics({"in":sensor_features,
                                                        "inbv": "0",
                                                        "inzone.vector.in": tiles_samples,
                                                        "out": "vector",
                                                        "out.vector.filename": output_shp
                                                        })
        ZonalStatisticsApp.ExecuteAndWriteOutput()

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

    for tile in tiles :
        learning_samples = os.path.join(seg_directory, "{}_samples_region_{}_seed_{}.shp".format(tile, region, seed))
        sensor_tile_container = Sensors_container(config_path,
                                          tile,
                                          working_dir=None)
        sensors_features = sensor_tile_container.get_sensors_features(available_ram=1000)
        for sensor_name, ((sensor_features, sensor_features_dep), features_labels) in sensors_features:
            sensor_features.Execute()
            output_xml = os.path.join(seg_directory, "{}_{}_samples_region_{}_seed_{}_stats.xml".format(sensor_name, tile, region, seed))
            output_shp = os.path.join(seg_directory, "{}_{}_samples_region_{}_seed_{}_stats.shp".format(sensor_name, tile, region, seed))
            ZonalStatisticsApp = otb.CreateZonalStatistics({"in":sensor_features,
                                                            "inbv": "0",
                                                            "inzone.vector.in": learning_samples,
                                                            "out": "vector",
                                                            "out.vector.filename": output_shp
                                                            })
            ZonalStatisticsApp.ExecuteAndWriteOutput()