#!/usr/bin/python

from osgeo import ogr
import sys, os
import argparse
from xml.etree import ElementTree as ET

def add_field_from_XML(filein,xml,labels):
	driver = ogr.GetDriverByName('ESRI Shapefile')
	source = driver.Open(filein, 1)
	layer = source.GetLayer()
	
	labels = labels_format_to_DBF(labels)
	clean_all_features_field(layer,labels)

	layer_defn = layer.GetLayerDefn()
	nb = layer_defn.GetFieldCount()

	for label in labels:
		field = ogr.FieldDefn(label,ogr.OFTInteger)
		layer.CreateField(field)

	data = ET.parse(xml).getroot()
	statmean = data.find('.//Statistic[@name="mean"]')
	for layerfeat in statmean.iter('StatisticMap'):
		ID = layerfeat.attrib['key']
		layer.SetAttributeFilter('ID = %s'%ID)
		feat = layer.GetNextFeature()
		if feat is not None :
			values = [int(float(x)) if float(x) == float(x) else None for x in layerfeat.attrib['value'][1:-1].split(',')]
			for i,value in enumerate(values):
				if value != None:
					feat.SetField(nb+i,value)
			layer.SetFeature(feat)
	return 0

def clean_all_features_field(layer,labels):
	layer_defn = layer.GetLayerDefn()
	for label in labels:
		if layer_defn.GetFieldIndex(label) != -1 :
			ind = layer_defn.GetFieldIndex(label)
			layer.DeleteField(ind)

def labels_format_to_DBF(labels):
	out_labels=[]
	#sensor type
	T=[]
	#feature
	F=[]
	#date
	D=[]
	TFD=[T,F,D]
	
	for label in labels:
		label_elements=label.split('_')
		for i,element in enumerate(label_elements):
			if element not in TFD[i]:
				TFD[i].append(element)
	for label in labels:
		label_elements = label.split('_')
		ind = [TFD[i].index(label_elements[i]) for i in range(0,3)]
		out_labels.append('T%sF%sD%s'%tuple(ind))

	return out_labels


def merge_xml_stats(output,stats_files):
    from xml.etree import ElementTree as ET

    generalStatistics = ET.Element('GeneralStatistics')
    statMean = ET.SubElement(generalStatistics,'Statistic', name='mean')
    # statStd = ET.SubElement(generalStatistics,'Statistic', name='std')

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
            # if stat.attrib['name']=='std':
            #     for res in stat.iter('StatisticMap'):
            #         k = res.attrib['key']
            #         if statStd.find(".//StatisticMap[@key='{}']".format(k)) == None :
            #             statStd.append(res)
            #         else :
            #             row = statStd.find(".//StatisticMap[@key='{}']".format(k))
            #             array = row.attrib['value'][1:-1].split(',')
            #             array += res.attrib['value'][1:-1].split(',')
            #             row.attrib['value'] = [float(x) for x in array]
    wrap = ET.ElementTree(generalStatistics)
    wrap.write(output,encoding="UTF-8",xml_declaration=True)

def clean_xml_stats(stats_file):
    from xml.etree import ElementTree as ET

    rm_names=['count','min','max','std']
    generalStatistics = ET.parse(stats_file).getroot()
    for name in rm_names:
        sub_element = generalStatistics.find('.//Statistic[@name="{}"'.format(name))
        generalStatistics.remove(sub_element)
    wrap = ET.ElementTree(generalStatistics)
    wrap.write(stats_file,encoding="UTF-8",xml_declaration=True)  