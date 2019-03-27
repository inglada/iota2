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
        merge_xml_stats(tile_stats_xml, outputs_list)
        labels_out = os.path.join(seg_directory,"{}_tile_samples_region_{}_seed_{}_stats_label.txt".format(sensor_name, tile, region, seed))
        with open(labels_out,'w') as file :
            for lab in labels:
                file.write(str(lab)+'\n')


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
        learning_samples = os.path.join(seg_directory, "{}_samples_region_{}_seed_{}.shp".format(tile, region, seed))
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
                                                            "out.shp.filename": os.path.splitext(output_xml)[0]+'.shp'
                                                            })
            ZonalStatisticsApp.ExecuteAndWriteOutput()
            outputs_list.append(output_xml)

    learning_samples_stats = os.path.join(seg_directory,"learn_samples_region_{}_seed_{}_stats.xml".format(region, seed))
    merge_xml_stats(learning_samples_stats,outputs_list)
    labels_out = os.path.join(seg_directory,"learn_samples_region_{}_seed_{}_stats_lable.txt".format(region, seed))
    with open(labels_out,'w') as file :
        for lab in labels:
            file.write(str(lab)+'\n')

def merge_xml_stats(output,stats_files):
    from xml.etree import ElementTree as ET

    generalStatistics = ET.Element('GeneralStatistics')
    statMean = ET.SubElement(generalStatistics,'Statistic', name='mean')
    statStd = ET.SubElement(generalStatistics,'Statistic', name='std')

    for file in stats_files :
        data = ET.parse(file).getroot()
        for stat in data.iter('Statistic'):
            if stat.attrib['name']=='mean':
                for res in stat.iter('StatisticMap'):
                    k = res.attrib['key']
                    if statMean.find(".//StatisticMap[@key='{}']".format(k)) == None :
                        statMean.append(res)
                    else :
                        row = statMean.find(".//StatisticMap[@key='{}']".format(k))
                        array = row.attrib['value'][1:-1].split(',')
                        array += res.attrib['value'][1:-1].split(',')
                        row.attrib['value'] = [float(x) for x in array]
            if stat.attrib['name']=='std':
                for res in stat.iter('StatisticMap'):
                    k = res.attrib['key']
                    if statStd.find(".//StatisticMap[@key='{}']".format(k)) == None :
                        statStd.append(res)
                    else :
                        row = statStd.find(".//StatisticMap[@key='{}']".format(k))
                        array = row.attrib['value'][1:-1].split(',')
                        array += res.attrib['value'][1:-1].split(',')
                        row.attrib['value'] = [float(x) for x in array]
    wrap = ET.ElementTree(generalStatistics)
    wrap.write(output,encoding="UTF-8",xml_declaration=True)

# def clean_xml_stats(stats_file):
#     from xml.etree import ElementTree as ET

#     rm_names=['count','min','max']
#     generalStatistics = ET.parse(stats_file).getroot()
#     for name in rm_names:
#         sub_element = generalStatistics.find('.//Statistic[@name="{}"'.format(name))
#         generalStatistics.remove(sub_element)
#     wrap = ET.ElementTree(generalStatistics)
#     wrap.write(stats_file,encoding="UTF-8",xml_declaration=True)