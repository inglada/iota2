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
import sys
import unicodedata
from collections import Counter, defaultdict
import csv
import numpy as np
from pandas import MultiIndex, DataFrame
import codecs
import createSymbologyQGIS as csq
from Common import FileUtils as fu


def convertHextoRGB(color):
    
    h=color.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2 ,4))    

def convertRGBtoHEX(rgb):
    
    return '#%02x%02x%02x'%(rgb)

def get_unique(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]

def convertDictToList(dictnomenc):

    levels = dictnomenc.keys()
    lastlevel = levels[len(levels) - 1]
    tabclasses = []
    for idx, cls in enumerate(dictnomenc[lastlevel]):
        tabclasses.append([cls, str(dictnomenc[lastlevel][cls]['code']), \
                           dictnomenc[lastlevel][cls]['color'], \
                           dictnomenc[lastlevel][cls]['alias']])
        for level in reversed(levels):
            if level != lastlevel:
                for classe in dictnomenc[level]:
                    if dictnomenc[level][classe]['code'] == dictnomenc[lastlevel][cls]['parent']:
                        tabclasses[idx].insert(0, dictnomenc[level][classe]['alias'])
                        tabclasses[idx].insert(0, dictnomenc[level][classe]['color'])
                        tabclasses[idx].insert(0, dictnomenc[level][classe]['code'])
                        tabclasses[idx].insert(0, classe)
        tabclasses[idx] = tuple(tabclasses[idx])

    return tabclasses


def getNomenclature(qml, outpath):

    classes = csq.getClassesFromQML(qml)
    out = [[x[0], x[1], convertRGBtoHEX(tuple(x[2])), "".join(unicodedata.normalize('NFKD', x[0][0:11].decode("utf-8", "ignore")).encode('ascii','ignore').split())] for x in classes]

    for line in out:
        line[3] = ''.join(e for e in line[3] if e.isalnum())
    with open(outpath, 'w') as filenom:
        writer = csv.writer(filenom)
        writer.writerows(out)

    duplicates = [item for item, count in Counter([x[3] for x in out]).items() if count > 1]
    if duplicates is not None:
        print("Automatic procedure generated duplicates of Alias, "\
              "please change manually aliases of the nomenclature file")
    else:
        print("Please, check aliases in the nomenclature file "\
              "automatically generated by this procedure")


class iota_nomenclature(object):
    """Class for manipulating multi-level nomenclature :
    - extract specific attributes (code, name, alias, color) on a specfic level
    - prepare multi-level confusion matrix (OTB style)
    - prepare QGIS layer style (QML)
    - extract nomenclature from QML file

    Parameters
    ----------
    nomenclature : string
        Path to a nomenclature file

    Example
    -------
    >>> nomenclature = iota_nomenclature("nomenclature.csv")

    Return
    ------
    iota_nomenclature
        nomenclature object
    """

    def __init__(self, nomenclature, typefile='csv'):

        self.nomenclature = self.readNomenclatureFile(nomenclature, typefile)
        self.level = self.getLevelNumber()
        self.getMaxLevelClassNb = self.getMaxLevelClassNb()
        self.HierarchicalNomenclature = self.setHierarchicalNomenclature(self.nomenclature)

    def __repr__(self):

        return str(self.nomenclature)

    def __str__(self):

        return 'Nomenclature : %s level(s) with %s classes for the last level'%(self.level, \
                                                                                self.getMaxLevelClassNb)

    def getLevelNumber(self):
        """Get the number of levels of a nomenclature
   
        Return
        ------
        int
            number of levels.
        """

        return len(self.nomenclature[0]) / 4

    def getMaxLevelClassNb(self):
        """Get number of classes corresponding to lower level (more detailed) : level for classification purpose 

        Return
        ------
        list
            list of classes corresponding to lower level.
        """
  
        return len(self.nomenclature)

    def getColor(self, level, typec = "RGB"):
        """Get colors list of given level

        Parameters
        ----------
        level : int
            level of the nomenclature
        typec : string
            format of input colors (HEX / RGB)

        Return
        ------
        list
            list of colors of a given level.
        """
        if level <= self.level and level > 0:
            index = self.setHierarchicalNomenclature(self.nomenclature)
            if typec == "RGB":
                if '#' in list(index.get_level_values(level - 1))[0][2]:                
                    return get_unique([(convertHextoRGB(x[2])) for x in list(index.get_level_values(level - 1))])
                else:
                    raise Exception("Color already in RGB format or in unknown format")
            elif typec == "HEX":
                return get_unique([x[2] for x in list(index.get_level_values(level - 1))])
            else:
                raise Exception("Unknown color format provided")                
        else:
            raise Exception("Level %s does not exists"%(level))

    def getClass(self, level):
        """Get classes list of given level

        Parameters
        ----------
        level : int
            level of the nomenclature

        Return
        ------
        list
            list of classes of a given level.
        """ 
        
        if level <= self.level and level > 0:
            index = self.setHierarchicalNomenclature(self.nomenclature)
            return get_unique([x[1] for x in list(index.get_level_values(level - 1))])
        else:
            raise Exception("Level %s does not exists"%(level))

    def getAlias(self, level):
        """Get alias list of given level

        Parameters
        ----------
        level : int
            level of the nomenclature

        Return
        ------
        list
            list of aliases of a given level.        
        """

        if level <= self.level and level > 0:
            index = self.setHierarchicalNomenclature(self.nomenclature)
            return get_unique([x[3] for x in list(index.get_level_values(level - 1))])
        else:
            raise Exception("Level %s does not exists"%(level))
        
    def getCode(self, level):
        """Get codes list of given level

        Parameters
        ----------
        level : int
            level of the nomenclature

        Return
        ------
        list
            list of codes of a given level.        
        """
        
        if level <= self.level and level > 0:
            index = self.setHierarchicalNomenclature(self.nomenclature)
            return get_unique([int(x[0]) for x in list(index.get_level_values(level - 1))])
        else:
            raise Exception("Level %s does not exists"%(level))
            
    def setHierarchicalNomenclature(self, nomen):
        """Set a multi-level pandas nomenclature

        Parameters
        ----------
        nomen: csv file
            nomenclature file

        Return
        ------
        pandas.MultiIndex
            Multi-levels nomenclature        
        """
        
        classeslist = []
        levelname = []
        
        for ind, line in enumerate(nomen):
            classeslist.append([])
            for lev in range(self.level):
                if len(levelname) < self.level:
                    levelname.append("level%s"%(lev + 1))
                
                classeslist[ind].append((int(line[(4 * lev) + 1]), line[4 * lev], line[(4 * lev) + 2], line[(4 * lev) + 3]))

        index = MultiIndex.from_tuples([tuple(x) for x in classeslist], names=levelname)
        
        return index
    
    def readNomenclatureFile(self, nomen, typefile = 'csv'):
        """Read a csv nomenclature file

        Example of csv structure for 2 nested levels (l1 = level 1, l2 = level 2) :
          
           classname_l1, code_l1, colour_l1, alias_l1, classname_l2, code_l2, colour_l2, alias_l2
           Urbain, 100, #b106b1, Urbain, Urbain dense, 1, #b186c1, Urbaindens

        Example of config structure for 2 nested levels (l1 = level 1, l2 = level 2) :
                   >>> Classes:
           {
	      Level1:
	      {
	          "Urbain":
		  {
		     code:100
		     alias:'Urbain'
		     color:'#b106b1'
		  }
                  ...
              }
	      Level2:
	      {
	          "Urbain dense":
		  {
                  code:1
                  ...
                  parent:100
                  }
                  ...
              }
           }

        Example of config structure for 2 nested levels (l1 = level 1, l2 = level 2) :
           {'Level1': {'Urbain': {'color': '#b106b1', 'alias': 'Urbain', 'code': 100}, ...}, 'Level2': {'Zones indus. et comm.': {'color': ..., 'parent' : 100}, ...}}

        alias : maximum 10 caracters
        color : HEX or RGB
          
        Parameters
        ----------
        nomen: csv or config file or dict object
            nomenclature description
        
        Return
        ------
        list of tuples
            raw nomenclature
        """
        if isinstance(nomen, dict):
            try:
                tabnomenc = convertDictToList(nomen)
            except IOError:
                raise Exception("Nomenclature reading failed, nomenclature is not properly built")
        
            
        elif typefile == 'cfg':
            from Common import ServiceConfigFile as SCF        
            try:
                cfg = SCF.serviceConfigFile(nomen, False).cfg

                dictnomenc = {}
                for level in cfg.Classes:
                    cls = {}
                    for classe in cfg.Classes[level]:
                        cls[classe] = cfg.Classes[level][classe]
                    dictnomenc[level] = cls

                tabnomenc = convertDictToList(dictnomenc)
            
            except IOError:
                raise Exception("Nomenclature reading failed, nomenclature is not properly built")
            
        elif typefile == 'csv':
            try:
                fileclasses = codecs.open(nomen, "r", "utf-8")
                tabnomenc = [tuple(line.rstrip('\n').split(',')) for line in fileclasses.readlines()]
            except IOError:
                raise Exception("Nomenclature reading failed, nomenclature is not properly built")
            
        else:
            raise Exception("The type of nomenclature file is not handled")
            
        return tabnomenc

    def createNomenclatureQML(self, level, outpath, codefield, filetype = "raster", outlinestyle = "", nodata = ""):
        """Create a QGIS QML layer style (raster or vector)

        Parameters
        ----------
        level : int
            level of the nomenclature
        outpath : string
            QML file path
        codefield : string
            field name of the classification
        filetype : string
            QML file for vector or raster ?
        outlinestyle : string
            outlines style of polygon (e.g. SolidLine)
        nodata : float
            No data value for raster QML style

        Return
        ------
        QGIS QML file
            vector or raster QML style file
        """
        
        if len(self.getClass(level)) == len(self.getColor(level)):
            colorRGBlist = [[x[0], x[1], str(x[2][0]), str(x[2][1]), str(x[2][2]), x[3]] for x in zip(self.getCode(level), \
                                                                                                      self.getClass(level), \
                                                                                                      self.getColor(level), \
                                                                                                      self.getColor(level, "HEX"))]
            if filetype == "raster":                
                csq.createRasterQML(colorRGBlist, outpath, codefield, nodata)
            elif filetype == "vector":                
                csq.createVectorQML(colorRGBlist, outpath, codefield, outlinestyle)
            else:
                raise Exception("unknown option for output type of qml file (valid values : 'raster' or 'vector')")
        else:
            raise Exception("Duplicates colors or classes found in the nomenclature file")

    def createConfusionMatrix(self, otbmatrix):
        """Create a multi-level confusion matrix (pandas DataFrame)

        otbmatrix : csv file
            an OTB confusionMatrix file

        Return
        ------
        pandas.core.frame.DataFrame
            vector or raster QML style file
        """
        
        mat = fu.confCoordinatesCSV(otbmatrix)
        d = defaultdict(list)
        for k, v in mat:
            d[k].append(v)
        csv_f = list(d.items())

        # get matrix from csv
        matrix = fu.gen_confusionMatrix(csv_f, self.getCode(self.level))
        
        # MultiIndex Pandas dataframe
        cmdf = DataFrame(matrix, index = self.HierarchicalNomenclature, columns = self.HierarchicalNomenclature)
        cmdf.sort_index(level = self.level - 1, inplace = True, axis=1)
        cmdf.sort_index(level = self.level - 1, inplace = True, axis=0)
        
        return cmdf

    def createColorFileTheia(self, filecolor):
        """Create Color file for THEIA distribution

        filecolor :  colors file path
            text/csv file (csv structure : code R G B)
        """
        tabcolors = [[x, y[0], y[1], y[2]] for x, y in zip(self.getCode(self.level), \
                                                           self.getColor(self.level))]
        tabcolors.insert(0, [0, 255, 255, 255])
        tabcolors.append([255, 0, 0, 0])
        with open(filecolor, 'w') as ofile:
            writer = csv.writer(ofile, delimiter=" ")
            writer.writerows(tabcolors)

    def createNomenclatureFileTheia(self, filenom):
        """Create Nomencature file for THEIA distribution

        filecolor :  nomenclature file path
            text/csv file (csv structure : classname:code)
        """
        tabclasses = [[x.encode('utf8'), y] for x, y in zip(self.getClass(self.level), \
                                                            self.getCode(self.level))]
        tabclasses.append([255, "autres"])
        with open(filenom, 'w') as ofile:
            writer = csv.writer(ofile, delimiter=":")
            writer.writerows(tabclasses)
 
iota=iota_nomenclature("/home/vthierion/Documents/OSO/Dev/iota2/scripts/simplification/classes_iota23")
#iota=iota_nomenclature("/home/vthierion/Documents/OSO/Dev/iota2/scripts/simplification/nomenclature.cfg", 'cfg')
print iota
#iota.createColorFileTheia("/home/vthierion/tmp/colorFile.txt")
#iota.createNomenclatureFileTheia("/home/vthierion/tmp/nomenclature.txt")
print(iota.createConfusionMatrix(["/home/vthierion/tmp/Classif_Seed_0.csv"]))
#print iota.HierarchicalNomenclature
#print iota.getMaxLevelClassNb()
#print iota.HierarchicalNomenclature
#print iota.getColor(2)
#print iota.getAlias(2)
#print iota.createNomenclatureQML(2, "/home/qt/thierionv/testraster.qml", "code", "raster", "no", "0")
#print iota.getCode(2)
#getNomenclature("/home/qt/thierionv/testvector.qml", "/home/qt/thierionv/nomenclaturetest")