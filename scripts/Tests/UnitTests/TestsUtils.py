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

def cmp_xml_stat_files(xml_1, xml_2):
    """compare statistics xml files

    samplesPerClass and samplesPerVector tags from input files are compared without
    considering line's order

    Parameters
    ----------
    xml_1 : string
        statistics file from otbcli_PolygonClassStatistics
    xml_2 : string
        statistics file from otbcli_PolygonClassStatistics

    Return
    ------
    bool
        True if content are equivalent
    """
    import xml.etree.ElementTree as ET

    xml_1_stats = {}
    tree_1 = ET.parse(xml_1)
    root_1 = tree_1.getroot()

    xml_2_stats = {}
    tree_2 = ET.parse(xml_2)
    root_2 = tree_2.getroot()

    xml_1_stats["samplesPerClass"] = set([(samplesPerClass.attrib["key"], samplesPerClass.attrib["value"]) for samplesPerClass in root_1[0]])
    xml_1_stats["samplesPerVector"] = set([(samplesPerClass.attrib["key"], samplesPerClass.attrib["value"]) for samplesPerClass in root_1[1]])

    xml_2_stats["samplesPerClass"] = set([(samplesPerClass.attrib["key"], samplesPerClass.attrib["value"]) for samplesPerClass in root_2[0]])
    xml_2_stats["samplesPerVector"] = set([(samplesPerClass.attrib["key"], samplesPerClass.attrib["value"]) for samplesPerClass in root_2[1]])

    return xml_1_stats == xml_2_stats