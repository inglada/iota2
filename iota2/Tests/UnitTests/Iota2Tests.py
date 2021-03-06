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
import os
import unittest

import filecmp
import string
import random
import shutil
import sys
import osr
import ogr
import subprocess

iota2dir = os.environ.get('IOTA2DIR')
iota2_script = iota2dir + "/iota2"
iota2_script_tests = iota2dir + "/data/test_scripts"
sys.path.append(iota2_script)
sys.path.append(iota2_script_tests)

from Sampling import VectorSampler
from Common import FileUtils as fu
import test_genGrid as test_genGrid
from Sampling import TileEnvelope
from gdalconst import *
from osgeo import gdal
from config import Config
import numpy as np
import otbApplication as otb
import argparse
from iota2.Common import ServiceConfigFile as SCF
from iota2.Common import ServiceLogger as sLog
from iota2.Common import IOTA2Directory
from iota2.Common import Utils

from VectorTools.AddField import addField
from VectorTools.DeleteField import deleteField

#python -m unittest discover ./ -p "*Tests*.py"
# python -m coverage run -m unittest discover ./ -p "*Tests*"
# coverage report

iota2dir = os.environ.get('IOTA2DIR')
iota2_dataTest = os.path.join(os.environ.get('IOTA2DIR'), "data")

# Init of logging service
# We need an instance of serviceConfigFile
cfg = SCF.serviceConfigFile(iota2dir +
                            "/config/Config_4Tuiles_Multi_FUS_Confidence.cfg")
# We force the logFile value
cfg.setParam('chain', 'logFile', iota2_dataTest + "/OSOlogFile.log")
# We call the serviceLogger
sLog.serviceLogger(cfg, __name__)
SCF.clearConfig()


def shapeReferenceVector(refVector, outputName):
    """
    modify reference vector (add field, rename...)
    """
    from Common.Utils import run

    path, name = os.path.split(refVector)

    tmp = path + "/" + outputName + "_TMP"
    fu.cpShapeFile(refVector.replace(".shp", ""), tmp,
                   [".prj", ".shp", ".dbf", ".shx"])
    addField(tmp + ".shp", "region", "1", str)
    addField(tmp + ".shp", "seed_0", "learn", str)
    cmd = "ogr2ogr -dialect 'SQLite' -sql 'select GEOMETRY,seed_0, region, CODE as code from " + outputName + "_TMP' " + path + "/" + outputName + ".shp " + tmp + ".shp"
    run(cmd)

    os.remove(tmp + ".shp")
    os.remove(tmp + ".shx")
    os.remove(tmp + ".prj")
    os.remove(tmp + ".dbf")
    return path + "/" + outputName + ".shp"


def random_update(vect_file, table_name, field, value, nb_update):
    """
    use in test_split_selection Test
    """
    import sqlite3 as lite

    sql_clause = "UPDATE {} SET {}='{}' WHERE ogc_fid in (SELECT ogc_fid FROM {} ORDER BY RANDOM() LIMIT {})".format(
        table_name, field, value, table_name, nb_update)

    conn = lite.connect(vect_file)
    cursor = conn.cursor()
    cursor.execute(sql_clause)
    conn.commit()


def prepare_test_selection(vector, raster_ref, outputSelection, wd, dataField):
    """
    """
    from Common import OtbAppBank as otb
    stats_path = os.path.join(wd, "stats.xml")
    if os.path.exists(stats_path):
        os.remove(stats_path)
    stats = otb.CreatePolygonClassStatisticsApplication({
        "in": raster_ref,
        "vec": vector,
        "field": dataField,
        "out": stats_path
    })
    stats.ExecuteAndWriteOutput()
    sampleSel = otb.CreateSampleSelectionApplication({
        "in": raster_ref,
        "vec": vector,
        "out": outputSelection,
        "instats": stats_path,
        "sampler": "random",
        "strategy": "all",
        "field": dataField
    })
    if os.path.exists(outputSelection):
        os.remove(outputSelection)
    sampleSel.ExecuteAndWriteOutput()
    os.remove(stats_path)


def delete_uselessFields(test_vector, field_to_rm="region"):
    """
    """
    #const

    fields = fu.get_all_fields_in_shape(test_vector, driver='SQLite')

    rm_field = [field for field in fields if field_to_rm in field]

    for rm in rm_field:
        deleteField(test_vector, rm)


def generateRandomString(size):
    """
    usage : generate a random string of 'size' character

    IN
    size [int] : size of output string

    OUT
    a random string of 'size' character
    """
    return ''.join(
        random.SystemRandom().choice(string.ascii_uppercase + string.digits +
                                     string.ascii_lowercase)
        for _ in range(size))


def checkSameFile(files, patterns=["res_ref", "res_test"]):
    """
    usage : check if input files are the equivalent, after replacing all
    patters by XXXX

    IN
    files [list of string] : list of files to compare

    OUT
    [bool]
    """
    replacedBy = "XXXX"

    Alltmp = []
    for file_ in files:
        file_tmp = file_.split(".")[0] + "_tmp." + file_.split(".")[-1]
        if os.path.exists(file_tmp):
            os.remove(file_tmp)
        Alltmp.append(file_tmp)
        with open(file_, "r") as f1:
            for line in f1:
                line_tmp = line
                for patt in patterns:
                    if patt in line:
                        line_tmp = line.replace(patt, replacedBy)
                with open(file_tmp, "a") as f2:
                    f2.write(line_tmp)
    same = filecmp.cmp(Alltmp[0], Alltmp[1])

    for fileTmp in Alltmp:
        os.remove(fileTmp)

    return same


def checkSameEnvelope(EvRef, EvTest):
    """
    usage get input extent and compare them. Return true if same, else false

    IN
    EvRef [string] : path to a vector file
    EvTest [string] : path to a vector file

    OUT
    [bool]
    """
    miX_ref, miY_ref, maX_ref, maY_ref = fu.getShapeExtent(EvRef)
    miX_test, miY_test, maX_test, maY_test = fu.getShapeExtent(EvTest)

    if ((miX_ref == miX_test) and (miY_test == miY_ref)
            and (maX_ref == maX_test) and (maY_ref == maY_test)):
        return True
    return False


def prepareAnnualFeatures(workingDirectory, referenceDirectory, pattern):
    """
    double all rasters's pixels
    """
    from Common.Utils import run
    shutil.copytree(referenceDirectory, workingDirectory)
    rastersPath = fu.FileSearch_AND(workingDirectory, True, pattern)
    for raster in rastersPath:
        cmd = 'otbcli_BandMathX -il ' + raster + ' -out ' + raster + ' -exp "im1+im1"'
        run(cmd)


class iota_testServiceCompareImageFile(unittest.TestCase):
    """
    Test class ServiceCompareImageFile
    """
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.refData = os.path.join(iota2_dataTest, "references",
                                    "ServiceCompareImageFile")

    def test_SameImage(self):
        serviceCompareImageFile = fu.serviceCompareImageFile()
        file1 = os.path.join(self.refData, "raster1.tif")
        nbDiff = serviceCompareImageFile.gdalFileCompare(file1, file1)
        # we check if it is the same file
        self.assertEqual(nbDiff, 0)

    def test_DifferentImage(self):
        serviceCompareImageFile = fu.serviceCompareImageFile()
        file1 = os.path.join(self.refData, "raster1.tif")
        file2 = os.path.join(self.refData, "raster2.tif")
        nbDiff = serviceCompareImageFile.gdalFileCompare(file1, file2)
        # we check if differences are detected
        self.assertNotEqual(nbDiff, 0)

    def test_ErrorImage(self):
        serviceCompareImageFile = fu.serviceCompareImageFile()
        file1 = os.path.join(self.refData, "rasterNotHere.tif")
        file2 = os.path.join(self.refData, "raster2.tif")
        # we check if an error is detected
        self.assertRaises(Exception, serviceCompareImageFile.gdalFileCompare,
                          file1, file2)


class iota_testServiceCompareVectorFile(unittest.TestCase):
    """
    Test class serviceCompareVectorFile
    """
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.refData = os.path.join(iota2_dataTest, "references",
                                    "ServiceCompareVectorFile")

    def test_SameVector(self):
        serviceCompareVectorFile = fu.serviceCompareVectorFile()
        file1 = os.path.join(self.refData, "vector1.shp")
        # we check if it is the same file
        self.assertTrue(
            serviceCompareVectorFile.testSameShapefiles(file1, file1))

    def test_DifferentVector(self):
        serviceCompareVectorFile = fu.serviceCompareVectorFile()
        file1 = os.path.join(self.refData, "vector1.shp")
        file2 = os.path.join(self.refData, "vector2.shp")
        # we check if differences are detected
        self.assertFalse(
            serviceCompareVectorFile.testSameShapefiles(file1, file2))

    def test_ErrorVector(self):
        serviceCompareVectorFile = fu.serviceCompareVectorFile()
        file1 = os.path.join(self.refData, "vectorNotHere.shp")
        file2 = os.path.join(self.refData, "vector2.shp")
        # we check if an error is detected
        self.assertRaises(Exception,
                          serviceCompareVectorFile.testSameShapefiles, file1,
                          file2)


class iota_testStringManipulations(unittest.TestCase):
    """
    Test iota2 string manipulations
    """
    @classmethod
    def setUpClass(self):
        self.AllL8Tiles = "D00005H0010 D0002H0007 D0003H0006 D0004H0004 \
                           D0005H0002 D0005H0009 D0006H0006 D0007H0003 \
                           D0007H0010 D0008H0008 D0009H0007 D0010H0006 \
                           D0000H0001 D0002H0008 D0003H0007 D0004H0005 \
                           D0005H0003 D0005H0010 D0006H0007 D0007H0004 \
                           D0008H0002 D0008H0009 D0009H0008 D0010H0007 \
                           D0000H0002 D0003H0001 D0003H0008 D0004H0006 \
                           D0005H0004 D0006H0001 D0006H0008 D0007H0005 \
                           D0008H0003 D0009H0002 D0009H0009 D0010H0008 \
                           D00010H0005 D0003H0002 D0003H0009 D0004H0007 \
                           D0005H0005 D0006H0002 D0006H0009 D0007H0006 \
                           D0008H0004 D0009H0003 D0010H0002 D0001H0007 \
                           D0003H0003 D0004H0001 D0004H0008 D0005H0006 \
                           D0006H0003 D0006H0010 D0007H0007 D0008H0005 \
                           D0009H0004 D0010H0003 D0001H0008 D0003H0004 \
                           D0004H0002 D0004H0009 D0005H0007 D0006H0004 \
                           D0007H0001 D0007H0008 D0008H0006 D0009H0005 \
                           D0010H0004 D0002H0006 D0003H0005 D0004H0003 \
                           D0005H0001 D0005H0008 D0006H0005 D0007H0002 \
                           D0007H0009 D0008H0007 D0009H0006 D0010H0005".split(
        )
        self.AllS2Tiles = "T30TVT T30TXP T30TYN T30TYT T30UWU T30UYA T31TCK \
                           T31TDJ T31TEH T31TEN T31TFM T31TGL T31UCR T31UDS \
                           T31UFP T32TLP T32TMN T32ULV T30TWP T30TXQ T30TYP \
                           T30UUU T30UWV T30UYU T31TCL T31TDK T31TEJ T31TFH \
                           T31TFN T31TGM T31UCS T31UEP T31UFQ T32TLQ T32TNL \
                           T32UMU T30TWS T30TXR T30TYQ T30UVU T30UXA T30UYV \
                           T31TCM T31TDL T31TEK T31TFJ T31TGH T31TGN T31UDP \
                           T31UEQ T31UFR T32TLR T32TNM T32UMV T30TWT T30TXS \
                           T30TYR T30UVV T30UXU T31TCH T31TCN T31TDM T31TEL \
                           T31TFK T31TGJ T31UCP T31UDQ T31UER T31UGP T32TLT \
                           T32TNN T30TXN T30TXT T30TYS T30UWA T30UXV T31TCJ \
                           T31TDH T31TDN T31TEM T31TFL T31TGK T31UCQ T31UDR \
                           T31UES T31UGQ T32TMM T32ULU".split()
        self.dateFile = os.path.join(iota2_dataTest, "references", "dates.txt")
        self.fakeDateFile = os.path.join(iota2_dataTest, "references",
                                         "fakedates.txt")

    def test_getTile(self):
        """
        get tile name in random string
        """
        rString_head = generateRandomString(100)
        rString_tail = generateRandomString(100)

        S2 = True
        for currentTile in self.AllS2Tiles:
            try:
                fu.findCurrentTileInString(
                    rString_head + currentTile + rString_tail, self.AllS2Tiles)
            except Exception:
                S2 = False
        self.assertTrue(S2)
        L8 = True
        for currentTile in self.AllL8Tiles:
            try:
                fu.findCurrentTileInString(
                    rString_head + currentTile + rString_tail, self.AllL8Tiles)
            except Exception:
                L8 = False
        self.assertTrue(L8)

    def test_getDates(self):
        """
        get number of dates
        """
        try:
            nbDates = fu.getNbDateInTile(self.dateFile, display=False)
            self.assertTrue(nbDates == 35)
        except Exception:
            self.assertTrue(False)

        try:
            fu.getNbDateInTile(self.fakeDateFile, display=False)
            self.assertTrue(False)
        except:
            self.assertTrue(True)


def compareSQLite(vect_1, vect_2, CmpMode='table', ignored_fields=[]):
    """
    compare SQLite, table mode is faster but does not work with
    connected OTB applications.

    return true if vectors are the same
    """

    from collections import OrderedDict

    def getFieldValue(feat, fields):
        """
        usage : get all fields's values in input feature

        IN
        feat [gdal feature]
        fields [list of string] : all fields to inspect

        OUT
        [dict] : values by fields
        """
        return OrderedDict([(currentField, feat.GetField(currentField))
                            for currentField in fields])

    def priority(item):
        """
        priority key
        """
        return (item[0], item[1])

    def getValuesSortedByCoordinates(vector):
        """
        usage return values sorted by coordinates (x,y)

        IN
        vector [string] path to a vector of points

        OUT
        values [list of tuple] : [(x,y,[val1,val2]),()...]
        """
        values = []
        driver = ogr.GetDriverByName("SQLite")
        ds = driver.Open(vector, 0)
        lyr = ds.GetLayer()
        fields = fu.get_all_fields_in_shape(vector, 'SQLite')
        for feature in lyr:
            x = feature.GetGeometryRef().GetX()
            y = feature.GetGeometryRef().GetY()
            fields_val = getFieldValue(feature, fields)
            values.append((x, y, fields_val))

        values = sorted(values, key=priority)
        return values

    fields_1 = fu.get_all_fields_in_shape(vect_1, 'SQLite')
    fields_2 = fu.get_all_fields_in_shape(vect_2, 'SQLite')

    if len(fields_1) != len(fields_2):
        return False

    if CmpMode == 'table':
        import sqlite3 as lite
        import pandas as pad
        connection_1 = lite.connect(vect_1)
        df_1 = pad.read_sql_query("SELECT * FROM output", connection_1)

        connection_2 = lite.connect(vect_2)
        df_2 = pad.read_sql_query("SELECT * FROM output", connection_2)

        try:
            table = (df_1 != df_2).any(1)
            if True in table.tolist():
                return False
            else:
                return True
        except ValueError:
            return False

    elif CmpMode == 'coordinates':
        values_1 = getValuesSortedByCoordinates(vect_1)
        values_2 = getValuesSortedByCoordinates(vect_2)
        sameFeat = []
        for val_1, val_2 in zip(values_1, values_2):
            for (k1, v1), (k2, v2) in zip(list(val_1[2].items()),
                                          list(val_2[2].items())):
                if not k1 in ignored_fields and k2 in ignored_fields:
                    sameFeat.append(cmp(v1, v2) == 0)
        if False in sameFeat:
            return False
        return True
    else:
        raise Exception("CmpMode parameter must be 'table' or 'coordinates'")


class iota_testShapeManipulations(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.referenceShape = iota2_dataTest + "/references/D5H2_groundTruth_samples.shp"
        self.nbFeatures = 28
        self.fields = ['ID', 'LC', 'CODE', 'AREA_HA']
        self.dataField = 'CODE'
        self.epsg = 2154
        self.typeShape = iota2_dataTest + "/references/typo.shp"
        self.regionField = "DN"

        self.priorityEnvelope_ref = iota2_dataTest + "/references/priority_ref"
        self.splitRatio = 0.5

        self.test_vector = iota2_dataTest + "/test_vector"
        if not os.path.exists(self.test_vector):
            os.mkdir(self.test_vector)

    def test_CountFeatures(self):
        features = fu.getFieldElement(self.referenceShape,
                                      driverName="ESRI Shapefile",
                                      field="CODE",
                                      mode="all",
                                      elemType="int")
        self.assertTrue(len(features) == self.nbFeatures)

    def test_MultiPolygons(self):
        detectMulti = fu.multiSearch(self.referenceShape)
        single = iota2_dataTest + "/test_MultiToSinglePoly.shp"
        fu.multiPolyToPoly(self.referenceShape, single)

        detectNoMulti = fu.multiSearch(single)
        self.assertTrue(detectMulti)
        self.assertFalse(detectNoMulti)

        testFiles = fu.fileSearchRegEx(iota2_dataTest + "/test_*")

        for testFile in testFiles:
            if os.path.isfile(testFile):
                os.remove(testFile)

    def test_getField(self):
        allFields = fu.get_all_fields_in_shape(self.referenceShape,
                                               "ESRI Shapefile")
        self.assertTrue(self.fields == allFields)

    def test_Envelope(self):
        from Common import FileUtils as fut
        self.test_envelopeDir = iota2_dataTest + "/test_vector/test_envelope"
        if os.path.exists(self.test_envelopeDir):
            shutil.rmtree(self.test_envelopeDir)
        os.mkdir(self.test_envelopeDir)

        self.priorityEnvelope_test = self.test_envelopeDir + "/priority_test"
        if os.path.exists(self.priorityEnvelope_test):
            shutil.rmtree(self.priorityEnvelope_test)
        os.mkdir(self.priorityEnvelope_test)

        #Create a 3x3 grid (9 vectors shapes). Each tile are 110.010 km with 10 km overlaping to fit L8 datas.
        test_genGrid.genGrid(self.test_envelopeDir,
                             X=3,
                             Y=3,
                             overlap=10,
                             size=110.010,
                             raster="True",
                             pixSize=30)

        tilesPath = fu.fileSearchRegEx(self.test_envelopeDir + "/*.tif")

        ObjListTile = [
            TileEnvelope.Tile(
                currentTile,
                currentTile.split("/")[-1].split(".")[0].split("_")[0])
            for currentTile in tilesPath
        ]
        ObjListTile_sort = sorted(ObjListTile, key=TileEnvelope.priorityKey)

        TileEnvelope.genTileEnvPrio(ObjListTile_sort,
                                    self.priorityEnvelope_test,
                                    self.priorityEnvelope_test, self.epsg)

        envRef = fu.fileSearchRegEx(self.priorityEnvelope_ref + "/*.shp")

        comp = []
        for eRef in envRef:
            tile_number = os.path.split(eRef)[-1].split("_")[1]
            comp.append(
                fut.FileSearch_AND(self.priorityEnvelope_test, True,
                                   "Tile" + tile_number + "_PRIO.shp")[0])

        cmpEnv = [
            checkSameEnvelope(currentRef, test_env)
            for currentRef, test_env in zip(envRef, comp)
        ]
        self.assertTrue(all(cmpEnv))

    def test_regionsByTile(self):
        from Common.Tools import CreateRegionsByTiles as RT
        self.test_regionsByTiles = iota2_dataTest + "/test_vector/test_regionsByTiles"
        if os.path.exists(self.test_regionsByTiles):
            shutil.rmtree(self.test_regionsByTiles)
        os.mkdir(self.test_regionsByTiles)

        RT.createRegionsByTiles(self.typeShape, self.regionField,
                                self.priorityEnvelope_ref,
                                self.test_regionsByTiles, None)


class iota_testServiceConfigFile(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.iota2_directory = os.environ.get('IOTA2DIR')
        #the configuration file tested must be the one in /config.
        self.fichierConfig = os.path.join(
            self.iota2_directory, "config",
            "Config_4Tuiles_Multi_FUS_Confidence.cfg")
        self.fichierConfigBad1 = iota2_dataTest + "/config/test_config_serviceConfigFileBad1.cfg"
        self.fichierConfigBad2 = iota2_dataTest + "/config/test_config_serviceConfigFileBad2.cfg"
        self.fichierConfigBad3 = iota2_dataTest + "/config/test_config_serviceConfigFileBad3.cfg"

    def test_initConfigFile(self):
        from Common import ServiceError as sErr
        # the class is instantiated with self.fichierConfig config file
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        cfg.setParam('chain', 'runs', 2)
        cfg.setParam('chain', 'regionPath',
                     '../../../data/references/region_need_To_env.shp')
        cfg.setParam('chain', 'regionField', 'DN_char')
        cfg.setParam('argClassification', 'classifMode', 'separate')

        # we check the config file
        self.assertTrue(cfg.checkConfigParameters())

        # we get outputPath variable
        self.assertEqual(cfg.getParam('chain', 'outputPath'),
                         '../../../data/tmp/')

        # we check if bad section is detected
        self.assertRaises(Exception, cfg.getParam, 'BADchain', 'outputPath')

        # we check if bad param is detected
        self.assertRaises(Exception, cfg.getParam, 'chain', 'BADoutputPath')

    def test_initConfigFileBad1(self):

        # the class is instantiated with self.fichierConfigBad1 config file
        # A mandatory variable is missing
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfigBad1)
        # we check if the bad config file is detected
        self.assertRaises(Exception, cfg.checkConfigParameters)

    def test_initConfigFileBad2(self):

        # the class is instantiated with self.fichierConfigBad2 config file
        # Bad type of variable
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfigBad2)
        # we check if the bad config file is detected
        self.assertRaises(Exception, cfg.checkConfigParameters)

    def test_initConfigFileBad3(self):

        # the class is instantiated with self.fichierConfigBad3 config file
        # Bad value in a variable
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfigBad3)
        # we check if the bad config file is detected
        self.assertRaises(Exception, cfg.checkConfigParameters)


# test ok


# test ok
class iota_testGenerateRegionShape(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.fichierConfig = iota2dir + "/config/Config_4Tuiles_Multi_FUS_Confidence.cfg"
        self.test_vector = iota2_dataTest + "/test_vector/"
        self.pathOut = iota2_dataTest + "/test_vector/test_GenerateRegionShape/"
        self.pathEnvelope = iota2_dataTest + "/references/GenerateShapeTile/"
        self.MODE = 'one_region'
        self.model = ''
        self.shapeRegion = self.pathOut + 'region_need_To_env.shp'
        self.field_Region = 'DN'

        # test and creation of test_vector
        if not os.path.exists(self.test_vector):
            os.mkdir(self.test_vector)
        # test and creation of pathOut
        if not os.path.exists(self.pathOut):
            os.mkdir(self.pathOut)

    def test_GenerateRegionShape(self):
        from Sampling import TileArea as area

        print("pathEnvelope: " + self.pathEnvelope)
        print("model: " + self.model)
        print("shapeRegion: " + self.shapeRegion)
        print("field_Region: " + self.field_Region)
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        i2_output_path = cfg.getParam("chain", "outputPath")
        area.generate_region_shape(self.pathEnvelope, self.shapeRegion,
                                   self.field_Region, i2_output_path, None)

        # generate filename
        referenceShapeFile = iota2_dataTest + "/references/GenerateRegionShape/region_need_To_env.shp"
        ShapeFile = self.pathOut + "region_need_To_env.shp"
        serviceCompareVectorFile = fu.serviceCompareVectorFile()
        # Launch shapefile comparison
        self.assertTrue(
            serviceCompareVectorFile.testSameShapefiles(
                referenceShapeFile, ShapeFile))


# test ok
class iota_testLaunchTraining(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.fichierConfig = iota2dir + "/config/Config_4Tuiles_Multi_FUS_Confidence.cfg"
        self.test_vector = iota2_dataTest + "/test_vector/"
        self.pathOut = iota2_dataTest + "/test_vector/test_LaunchTraining/"
        self.pathAppVal = self.pathOut + "/dataAppVal"
        self.pathTilesFeat = iota2_dataTest + "/references/features/"
        self.refData = iota2_dataTest + "/references/LaunchTraining/"
        self.pathStats = self.pathOut + "/stats"
        self.cmdPath = self.pathOut + "/cmd"
        self.pathModels = self.pathOut + "/model"
        self.pathConfigModels = self.pathOut + "/config_model"
        self.pathLearningSamples = self.pathOut + "/learningSamples"
        self.pathFormattingSamples = self.pathOut + "/formattingVectors"
        self.vector_formatting = self.refData + "/Input/D0005H0002.shp"
        #        self.vector_formatting = iota2_dataTest + "/references/sampler/D0005H0002.shp"

        # test and creation of test_vector
        if not os.path.exists(self.test_vector):
            os.mkdir(self.test_vector)
        # test and creation of pathOut
        if not os.path.exists(self.pathOut):
            os.mkdir(self.pathOut)
        else:
            shutil.rmtree(self.pathOut)
            os.mkdir(self.pathOut)
        # test and creation of pathAppVal
        if not os.path.exists(self.pathAppVal):
            os.mkdir(self.pathAppVal)
        # test and creation of pathStats
        if not os.path.exists(self.pathStats):
            os.mkdir(self.pathStats)
        # test and creation of cmdPath
        if not os.path.exists(self.cmdPath):
            os.mkdir(self.cmdPath)
        # test and creation of cmdPath
        if not os.path.exists(self.cmdPath + "/train"):
            os.mkdir(self.cmdPath + "/train")
        # test and creation of pathModels
        if not os.path.exists(self.pathModels):
            os.mkdir(self.pathModels)
        # test and creation of pathConfigModels
        if not os.path.exists(self.pathConfigModels):
            os.mkdir(self.pathConfigModels)
        # test and creation of pathLearningSamples
        if not os.path.exists(self.pathLearningSamples):
            os.mkdir(self.pathLearningSamples)
        if not os.path.exists(self.pathFormattingSamples):
            os.mkdir(self.pathFormattingSamples)
        # copy input data
        fu.cpShapeFile(self.vector_formatting.replace(".shp", ""),
                       self.pathFormattingSamples,
                       [".prj", ".shp", ".dbf", ".shx"],
                       spe=True)

        src_files = os.listdir(self.refData + "/Input/learningSamples")
        for file_name in src_files:
            full_file_name = os.path.join(
                self.refData + "/Input/learningSamples", file_name)
            shutil.copy(full_file_name, self.pathLearningSamples)

    def test_LaunchTraining(self):
        from iota2.Learning import TrainingCmd as TC
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        dataField = 'CODE'
        N = 1
        cfg.setParam('chain', 'outputPath', self.pathOut)
        cfg.setParam('chain', 'regionField', "region")

        TC.launch_training(
            classifier_name=cfg.getParam("argTrain", "classifier"),
            classifier_options=cfg.getParam("argTrain", "options"),
            output_path=self.pathOut,
            ground_truth=cfg.getParam("chain", "groundTruth"),
            data_field="CODE",
            region_field="region",
            path_to_cmd_train=os.path.join(self.cmdPath, "train"),
            out=self.pathModels)

        # file comparison to ref file
        File1 = self.cmdPath + "/train/train.txt"
        self.assertTrue(os.path.getsize(File1) > 0)
        File2 = self.pathConfigModels + "/configModel.cfg"
        referenceFile2 = self.refData + "/Output/configModel.cfg"

        self.assertTrue(filecmp.cmp(File2, referenceFile2))


class iota_testLaunchClassification(unittest.TestCase):
    # Test ok
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.fichierConfig = iota2dir + "/config/Config_4Tuiles_Multi_FUS_Confidence.cfg"
        self.test_vector = iota2_dataTest + "/test_vector/"
        self.pathOut = iota2_dataTest + "/test_vector/test_LaunchClassification/"
        self.shapeRegion = iota2_dataTest + "/references/GenerateRegionShape/region_need_To_env.shp"
        self.pathTileRegion = self.pathOut + "/shapeRegion/"
        self.pathTilesFeat = iota2_dataTest + "/references/features/"
        self.pathStats = self.pathOut + "/stats"
        self.cmdPath = self.pathOut + "/cmd"
        self.pathModels = self.pathOut + "/model"
        self.pathConfigModels = self.pathOut + "/config_model"
        self.pathClassif = self.pathOut + "/Classif"
        self.refData = iota2_dataTest + "/references/LaunchClassification/"

        # test and creation of test_vector
        if not os.path.exists(self.test_vector):
            os.mkdir(self.test_vector)
        # test and creation of pathOut
        if not os.path.exists(self.pathOut):
            os.mkdir(self.pathOut)
        else:
            shutil.rmtree(self.pathOut)
            os.mkdir(self.pathOut)
        # test and creation of pathTileRegion
        if not os.path.exists(self.pathTileRegion):
            os.mkdir(self.pathTileRegion)
        # test and creation of pathTilesFeat
        if not os.path.exists(self.pathTilesFeat):
            os.mkdir(self.pathTilesFeat)
        # test and creation of pathStats
        if not os.path.exists(self.pathStats):
            os.mkdir(self.pathStats)
        # test and creation of cmdPath
        if not os.path.exists(self.cmdPath):
            os.mkdir(self.cmdPath)
        # test and creation of cmdPath
        if not os.path.exists(self.cmdPath + "/cla"):
            os.mkdir(self.cmdPath + "/cla")
        # test and creation of pathModels
        if not os.path.exists(self.pathModels):
            os.mkdir(self.pathModels)
        # test and creation of pathConfigModels
        if not os.path.exists(self.pathConfigModels):
            os.mkdir(self.pathConfigModels)
        # test and creation of pathClassif
        if not os.path.exists(self.pathClassif):
            os.mkdir(self.pathClassif)
        if not os.path.exists(self.pathClassif + "/MASK"):
            os.mkdir(self.pathClassif + "/MASK")

        # copy input data
        shutil.copy(self.refData + "/Input/configModel.cfg",
                    self.pathConfigModels)
        shutil.copy(self.refData + "/Input/model_1_seed_0.txt",
                    self.pathModels)
        src_files = os.listdir(self.refData + "/Input/shapeRegion")
        for file_name in src_files:
            full_file_name = os.path.join(self.refData + "/Input/shapeRegion",
                                          file_name)
            shutil.copy(full_file_name, self.pathTileRegion)
        src_files = os.listdir(self.refData + "/Input/Classif/MASK")
        for file_name in src_files:
            full_file_name = os.path.join(self.refData + "/Input/Classif/MASK",
                                          file_name)
            shutil.copy(full_file_name, self.pathClassif + "/MASK")

    def test_LaunchClassification(self):
        from Classification import ClassificationCmd as CC
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        cfg.setParam('chain', 'outputPath', self.pathOut)
        nomenclature_path = cfg.getParam("chain", "nomenclaturePath")
        field_Region = cfg.getParam('chain', 'regionField')
        N = 1
        CC.write_classification_command(
            self.pathModels, cfg.pathConf, self.pathOut, "rf", "separate",
            nomenclature_path, self.pathStats, self.pathTileRegion,
            self.pathTilesFeat, self.shapeRegion, field_Region,
            self.cmdPath + "/cla", self.pathClassif, 128, None)

        # file comparison to ref file
        File1 = self.cmdPath + "/cla/class.txt"
        self.assertTrue(os.path.getsize(File1) > 0)


class iota_testVectorSamplesMerge(unittest.TestCase):
    # Test ok
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.fichierConfig = iota2dir + "/config/Config_4Tuiles_Multi_FUS_Confidence.cfg"
        self.test_vector = iota2_dataTest + "/test_vector/"
        self.pathOut = iota2_dataTest + "/test_vector/test_VectorSamplesMerge/"
        self.learningSamples = self.pathOut + "/learningSamples/"
        self.cmdPath = self.pathOut + "/cmd"
        self.refData = iota2_dataTest + "/references/VectorSamplesMerge/"

        # test and creation of test_vector
        if not os.path.exists(self.test_vector):
            os.mkdir(self.test_vector)
        # test and creation of pathOut
        if not os.path.exists(self.pathOut):
            os.mkdir(self.pathOut)
        else:
            shutil.rmtree(self.pathOut)
            os.mkdir(self.pathOut)
        # test and creation of learningSamples
        if not os.path.exists(self.learningSamples):
            os.mkdir(self.learningSamples)
        # test and creation of cmdPath
        if not os.path.exists(self.cmdPath):
            os.mkdir(self.cmdPath)

        # copy input data
        shutil.copy(
            self.refData +
            "/Input/D0005H0003_region_1_seed0_learn_Samples.sqlite",
            self.learningSamples)

    def test_VectorSamplesMerge(self):
        from iota2.Sampling import VectorSamplesMerge as VSM
        from iota2.Sampling import VectorSampler as vs
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        cfg.setParam('chain', 'outputPath', self.pathOut)

        vl = fu.FileSearch_AND(self.learningSamples, True, ".sqlite")
        VSM.vector_samples_merge(vl, self.pathOut)

        # file comparison to ref file
        File1 = self.learningSamples + "Samples_region_1_seed0_learn.sqlite"
        referenceFile1 = self.refData + "/Output/Samples_region_1_seed0_learn.sqlite"
        self.assertTrue(
            compareSQLite(File1,
                          referenceFile1,
                          CmpMode='coordinates',
                          ignored_fields=[]))


class iota_testFusion(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.fichierConfig = iota2dir + "/config/Config_4Tuiles_Multi_FUS_Confidence.cfg"
        self.test_vector = iota2_dataTest + "/test_vector/"
        self.pathOut = iota2_dataTest + "/test_vector/test_Fusion/"
        self.pathTilesFeat = iota2_dataTest + "/references/features/"
        self.shapeRegion = iota2_dataTest + "/references/GenerateRegionShape/region_need_To_env.shp"
        self.pathClassif = self.pathOut + "/classif"
        self.classifFinal = self.pathOut + "/final"
        self.refData = iota2_dataTest + "/references/Fusion/"
        self.cmdPath = self.pathOut + "/cmd"

        # test and creation of test_vector
        if not os.path.exists(self.test_vector):
            os.mkdir(self.test_vector)
        # test and creation of pathOut
        if not os.path.exists(self.pathOut):
            os.mkdir(self.pathOut)
        else:
            shutil.rmtree(self.pathOut)
            os.mkdir(self.pathOut)
        # test and creation of pathClassif
        if not os.path.exists(self.pathClassif):
            os.mkdir(self.pathClassif)
        if not os.path.exists(self.pathClassif + "/MASK"):
            os.mkdir(self.pathClassif + "/MASK")
        if not os.path.exists(self.pathClassif + "/tmpClassif"):
            os.mkdir(self.pathClassif + "/tmpClassif")
        # test and creation of classifFinal
        if not os.path.exists(self.classifFinal):
            os.mkdir(self.classifFinal)
        # test and creation of cmdPath
        if not os.path.exists(self.cmdPath):
            os.mkdir(self.cmdPath)
        if not os.path.exists(self.cmdPath + "/fusion"):
            os.mkdir(self.cmdPath + "/fusion")

        src_files = os.listdir(self.refData + "/Input/Classif/MASK")
        for file_name in src_files:
            full_file_name = os.path.join(self.refData + "/Input/Classif/MASK",
                                          file_name)
            shutil.copy(full_file_name, self.pathClassif + "/MASK")

        src_files = os.listdir(self.refData + "/Input/Classif/classif")
        for file_name in src_files:
            full_file_name = os.path.join(
                self.refData + "/Input/Classif/classif/", file_name)
            shutil.copy(full_file_name, self.pathClassif)

    def test_Fusion(self):
        from Classification import Fusion as FUS
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        cfg.setParam('chain', 'outputPath', self.pathOut)
        cfg.setParam('argClassification', 'classifMode', 'fusion')

        field_Region = cfg.getParam('chain', 'regionField')
        N = 1

        cmdFus = FUS.fusion(
            self.pathClassif, cfg.getParam('chain', 'runs'),
            cfg.getParam('chain', 'listTile').split(" "),
            cfg.getParam('argClassification', 'fusionOptions'),
            cfg.getParam('chain', 'nomenclaturePath'),
            cfg.getParam('chain', 'regionPath'),
            cfg.getParam('argTrain', 'dempster_shafer_SAR_Opt_fusion'), None)


class iota_test_classification_shaping(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.fichierConfig = iota2dir + "/config/Config_4Tuiles_Multi_FUS_Confidence.cfg"
        self.test_vector = iota2_dataTest + "/test_vector/"
        self.pathOut = iota2_dataTest + "/test_vector/test_ClassificationShaping/"
        self.pathTilesFeat = iota2_dataTest + "/references/features/"
        self.pathEnvelope = self.pathOut + "/envelope"
        self.pathClassif = self.pathOut + "/classif"
        self.classifFinal = self.pathOut + "/final"
        self.refData = iota2_dataTest + "/references/ClassificationShaping/"

        # test and creation of test_vector
        if not os.path.exists(self.test_vector):
            os.mkdir(self.test_vector)
        # test and creation of pathOut
        if not os.path.exists(self.pathOut):
            os.mkdir(self.pathOut)
        else:
            shutil.rmtree(self.pathOut)
            os.mkdir(self.pathOut)
        # test and creation of pathClassif
        if not os.path.exists(self.pathClassif):
            os.mkdir(self.pathClassif)
        if not os.path.exists(self.pathClassif + "/MASK"):
            os.mkdir(self.pathClassif + "/MASK")
        if not os.path.exists(self.pathClassif + "/tmpClassif"):
            os.mkdir(self.pathClassif + "/tmpClassif")
        # test and creation of classifFinal
        if not os.path.exists(self.classifFinal):
            os.mkdir(self.classifFinal)

        # copy input file
        src_files = os.listdir(self.refData + "/Input/Classif/MASK")
        for file_name in src_files:
            full_file_name = os.path.join(self.refData + "/Input/Classif/MASK",
                                          file_name)
            shutil.copy(full_file_name, self.pathClassif + "/MASK")

        src_files = os.listdir(self.refData + "/Input/Classif/classif")
        for file_name in src_files:
            full_file_name = os.path.join(
                self.refData + "/Input/Classif/classif/", file_name)
            shutil.copy(full_file_name, self.pathClassif)

    def test_classification_shaping(self):
        from iota2.Validation import ClassificationShaping as CS
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        features_ref = "../../../data/references/features"
        features_ref_test = os.path.join(self.pathOut, "features")
        os.mkdir(features_ref_test)
        shutil.copytree(features_ref + "/D0005H0002",
                        features_ref_test + "/D0005H0002")
        shutil.copytree(features_ref + "/D0005H0003",
                        features_ref_test + "/D0005H0003")

        N = 1
        COLORTABLE = cfg.getParam('chain', 'colorTable')
        CS.classification_shaping(self.pathClassif, N, self.classifFinal, None,
                                  "separate", self.pathOut, False, 2154,
                                  cfg.getParam("chain", "nomenclaturePath"),
                                  False, [30, 30], False,
                                  cfg.getParam("chain",
                                               "regionPath"), COLORTABLE)

        # file comparison to ref file
        serviceCompareImageFile = fu.serviceCompareImageFile()
        src_files = os.listdir(self.refData + "/Output/")
        for file_name in src_files:
            File1 = os.path.join(self.classifFinal, file_name)
            referenceFile1 = os.path.join(self.refData + "/Output/", file_name)
            nbDiff = serviceCompareImageFile.gdalFileCompare(
                File1, referenceFile1)
            self.assertEqual(nbDiff, 0)


class iota_test_gen_conf_matrix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """ init class from unitest"""
        # definition of local variables
        cls.fichierConfig = (iota2dir +
                             "/config/Config_4Tuiles_Multi_FUS_Confidence.cfg")
        cls.test_vector = iota2_dataTest + "/test_vector/"
        cls.pathOut = iota2_dataTest + "/test_vector/test_GenConfMatrix/"
        cls.pathTilesFeat = iota2_dataTest + "/references/features/"
        cls.pathEnvelope = cls.pathOut + "/envelope"
        cls.pathAppVal = cls.pathOut + "/dataAppVal"
        cls.pathClassif = cls.pathOut + "/classif"
        cls.Final = cls.pathOut + "/final"
        cls.refData = iota2_dataTest + "/references/GenConfMatrix/"
        cls.cmdPath = cls.pathOut + "/cmd"

        # test and creation of test_vector
        if not os.path.exists(cls.test_vector):
            os.mkdir(cls.test_vector)
        # test and creation of pathOut
        if not os.path.exists(cls.pathOut):
            os.mkdir(cls.pathOut)
        else:
            shutil.rmtree(cls.pathOut)
            os.mkdir(cls.pathOut)
        # test and creation of pathClassif
        if not os.path.exists(cls.pathClassif):
            os.mkdir(cls.pathClassif)
        if not os.path.exists(cls.pathClassif + "/MASK"):
            os.mkdir(cls.pathClassif + "/MASK")
        if not os.path.exists(cls.pathClassif + "/tmpClassif"):
            os.mkdir(cls.pathClassif + "/tmpClassif")
        # test and creation of Final
        if not os.path.exists(cls.Final):
            os.mkdir(cls.Final)
        if not os.path.exists(cls.Final + "/TMP"):
            os.mkdir(cls.Final + "/TMP")

        # test and creation of cmdPath
        if not os.path.exists(cls.cmdPath):
            os.mkdir(cls.cmdPath)
        if not os.path.exists(cls.cmdPath + "/confusion"):
            os.mkdir(cls.cmdPath + "/confusion")

        # test and creation of pathAppVal
        if not os.path.exists(cls.pathAppVal):
            os.mkdir(cls.pathAppVal)

        # copy input data
        src_files = os.listdir(cls.refData + "/Input/dataAppVal")
        for file_name in src_files:
            full_file_name = os.path.join(cls.refData + "/Input/dataAppVal",
                                          file_name)
            shutil.copy(full_file_name, cls.pathAppVal)
        src_files = os.listdir(cls.refData + "/Input/Classif/MASK")
        for file_name in src_files:
            full_file_name = os.path.join(cls.refData + "/Input/Classif/MASK",
                                          file_name)
            shutil.copy(full_file_name, cls.pathClassif + "/MASK")
        src_files = os.listdir(cls.refData + "/Input/Classif/classif")
        for file_name in src_files:
            full_file_name = os.path.join(
                cls.refData + "/Input/Classif/classif/", file_name)
            shutil.copy(full_file_name, cls.pathClassif)
        src_files = os.listdir(cls.refData + "/Input/final/TMP")
        for file_name in src_files:
            full_file_name = os.path.join(cls.refData + "/Input/final/TMP/",
                                          file_name)
            shutil.copy(full_file_name, cls.Final + "/TMP")

    def test_gen_conf_matrix(self):
        """test generate confusion matrix"""
        from iota2.Validation import GenConfusionMatrix as GCM
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        cfg.setParam('chain', 'outputPath', self.pathOut)
        cfg.setParam('chain', 'listTile', 'D0005H0002')
        runs = 1
        data_field = 'CODE'

        GCM.gen_conf_matrix(self.Final, self.pathAppVal, runs, data_field,
                            self.cmdPath + "/confusion", None, self.pathOut,
                            [30, 30], cfg.getParam('chain', 'listTile'),
                            cfg.getParam('chain', 'enableCrossValidation'))

        # file comparison to ref file
        service_compare_image_file = fu.serviceCompareImageFile()
        reference_file1 = self.refData + "/Output/diff_seed_0.tif"
        file1 = self.Final + "/diff_seed_0.tif"
        nb_diff = service_compare_image_file.gdalFileCompare(
            file1, reference_file1)
        print(nb_diff)
        self.assertEqual(nb_diff, 0)


class iota_testConfFusion(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.fichierConfig = iota2dir + "/config/Config_4Tuiles_Multi_FUS_Confidence.cfg"
        self.test_vector = iota2_dataTest + "/test_vector/"
        self.pathOut = iota2_dataTest + "/test_vector/test_ConfFusion/"
        self.Final = self.pathOut + "/final"
        self.refData = iota2_dataTest + "/references/ConfFusion/"

        # test and creation of test_vector
        if not os.path.exists(self.test_vector):
            os.mkdir(self.test_vector)
        # test and creation of pathOut
        if not os.path.exists(self.pathOut):
            os.mkdir(self.pathOut)
        else:
            shutil.rmtree(self.pathOut)
            os.mkdir(self.pathOut)

        # test and creation of Final
        if not os.path.exists(self.Final):
            os.mkdir(self.Final)
        if not os.path.exists(self.Final + "/TMP"):
            os.mkdir(self.Final + "/TMP")

        # copy input data
        src_files = os.listdir(self.refData + "/Input/final/TMP")
        for file_name in src_files:
            full_file_name = os.path.join(self.refData + "/Input/final/TMP/",
                                          file_name)
            shutil.copy(full_file_name, self.Final + "/TMP")

    def test_ConfFusion(self):
        from Validation import ConfusionFusion as confFus
        SCF.clearConfig()
        cfg = SCF.serviceConfigFile(self.fichierConfig)
        cfg.setParam('chain', 'outputPath', self.pathOut)
        shapeData = cfg.getParam('chain', 'groundTruth')
        dataField = 'CODE'

        confFus.confusion_fusion(shapeData, dataField, self.Final + "/TMP",
                                 self.Final + "/TMP", self.Final + "/TMP", 1,
                                 False, [], None)

        # file comparison to ref file
        File1 = self.Final + "/TMP/ClassificationResults_seed_0.txt"
        referenceFile1 = self.refData + "/Output/ClassificationResults_seed_0.txt"
        self.assertTrue(filecmp.cmp(File1, referenceFile1))


class iota_testServiceLogging(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # definition of local variables
        self.fichierConfig = iota2dir + "/config/Config_4Tuiles_Multi_FUS_Confidence.cfg"

    def test_ServiceLogging(self):

        import logging
        File1 = iota2_dataTest + "/OSOlogFile.log"
        if os.path.exists(File1):
            os.remove(File1)
            with open(File1, "w") as F1:
                pass
        SCF.clearConfig()

        cfg = SCF.serviceConfigFile(self.fichierConfig)
        cfg.setParam('chain', 'logFileLevel', "DEBUG")
        cfg.setParam('chain', 'logConsole', "DEBUG")
        # We call the serviceLogger to set the logLevel parameter
        sLog.serviceLogger(cfg, __name__)
        # Init logging service
        logger = logging.getLogger("test_ServiceLogging1")

        logger.info("Enter in DEBUG mode for file")
        logger.error("This log should always be seen")
        logger.info("This log should always be seen")
        logger.debug("This log should only be seen in DEBUG mode")

        cfg.setParam('chain', 'logFileLevel', "INFO")
        cfg.setParam('chain', 'logConsole', "INFO")
        # We call the serviceLogger to set the logLevel parameter
        sLog.serviceLogger(cfg, __name__)
        # On initialise le service de log
        logger = logging.getLogger("test_ServiceLogging2")
        logger.info("Enter in INFO mode for file")
        logger.error("This log should always be seen")
        logger.info("This log should always be seen")
        logger.debug("If we see this, there is a problem...")

        # file comparison to ref file

        referenceFile1 = iota2_dataTest + "/references/OSOlogFile.log"
        l1 = open(File1, "r").readlines()
        l2 = open(referenceFile1, "r").readlines()
        # we compare only the fourth column

        for i in range(l1.__len__()):
            self.assertEqual(l1[i].split(' ')[3], l2[i].split(' ')[3])


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Tests for iota2")
    parser.add_argument("-mode",
                        dest="mode",
                        help="Tests mode",
                        choices=["all", "largeScale", "sample"],
                        default="sample",
                        required=False)

    args = parser.parse_args()

    mode = args.mode

    loader = unittest.TestLoader()

    largeScaleTests = [iota_testFeatures]
    sampleTests = [
        iota_testShapeManipulations, iota_testStringManipulations,
        iota_testSamplerApplications
    ]

    if mode == "sample":
        testsToRun = unittest.TestSuite(
            [loader.loadTestsFromTestCase(cTest) for cTest in sampleTests])
        runner = unittest.TextTestRunner()
        results = runner.run(testsToRun)

    elif mode == "largeScale":
        testsToRun = unittest.TestSuite(
            [loader.loadTestsFromTestCase(cTest) for cTest in largeScaleTests])
        runner = unittest.TextTestRunner()
        results = runner.run(testsToRun)

    elif mode == "all":
        allTests = sampleTests + largeScaleTests
        testsToRun = unittest.TestSuite(
            [loader.loadTestsFromTestCase(cTest) for cTest in allTests])
        runner = unittest.TextTestRunner()
        results = runner.run(testsToRun)
