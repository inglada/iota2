#!/usr/bin/env python3
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

from xml.etree import cElementTree as ET
from collections import Counter, defaultdict
import csv
import codecs
import unicodedata
from pandas import MultiIndex, DataFrame
from Common import FileUtils as fu


def convertHextoRGB(color):

    h = color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def convertRGBtoHEX(rgb):

    return "#%02x%02x%02x" % (rgb)


def get_unique(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def convertDictToList(dictnomenc):
    """Convert dict obect in list

    Parameters
    ----------
    dictnomenc : dict
        dict from config file (cfg) which discribe a multi-level nomenclature

    Return
    ------
    list
        list of classes (code, classename, color, alias) to instanciate a Iota2Nomenclature object
    """

    levels = list(dictnomenc.keys())
    lastlevel = levels[len(levels) - 1]
    tabclasses = []
    for idx, cls in enumerate(dictnomenc[lastlevel]):
        tabclasses.append(
            [
                cls,
                str(dictnomenc[lastlevel][cls]["code"]),
                dictnomenc[lastlevel][cls]["color"],
                dictnomenc[lastlevel][cls]["alias"],
            ]
        )
        for level in reversed(levels):
            if level != lastlevel:
                for classe in dictnomenc[level]:
                    if (
                        dictnomenc[level][classe]["code"]
                        == dictnomenc[lastlevel][cls]["parent"]
                    ):
                        tabclasses[idx].insert(0, dictnomenc[level][classe]["alias"])
                        tabclasses[idx].insert(0, dictnomenc[level][classe]["color"])
                        tabclasses[idx].insert(0, dictnomenc[level][classe]["code"])
                        tabclasses[idx].insert(0, classe)
        tabclasses[idx] = tuple(tabclasses[idx])

    return tabclasses


def getClassesFromVectorQML(qml):
    """Get classes from QGIS layer style (QML)

    Parameters
    ----------
    qml : str
        path of a QGIS layer style file

    Return
    ------
    list
        list of classes (code, classename, color, alias (auto-generated)) to instanciate a Iota2Nomenclature object
    """

    tree = ET.parse(qml).getroot()

    classes = []
    nomenclature = []
    for item in tree.findall("renderer-v2"):
        for subitem in item.findall("categories"):
            for category in subitem:
                classes.append(
                    [
                        category.attrib["symbol"],
                        category.attrib["value"],
                        category.attrib["label"],
                    ]
                )

    for classe in classes:
        for item in tree.findall("renderer-v2"):
            for subitem in item.findall("symbols"):
                for symbol in subitem:
                    if int(symbol.attrib["name"]) == int(classe[0]):
                        for layer in symbol.findall("layer"):
                            for prop in layer.findall("prop"):
                                if prop.attrib["k"] == "color":
                                    nomenclature.append(
                                        [
                                            classe[2].encode("utf-8"),
                                            classe[1],
                                            [
                                                int(x)
                                                for x in prop.attrib["v"].split(",")[
                                                    0:3
                                                ]
                                            ],
                                        ]
                                    )

    out = [
        [
            x[0],
            x[1],
            convertRGBtoHEX(tuple(x[2])),
            "".join(
                str(
                    unicodedata.normalize("NFKD", x[0][0:11].decode("utf-8", "ignore"))
                    .encode("ascii", "ignore")
                    .split()
                )
            ),
        ]
        for x in nomenclature
    ]
    for line in out:
        line[3] = "".join(e for e in line[3] if e.isalnum())

    duplicates = [
        item for item, count in list(Counter([x[3] for x in out]).items()) if count > 1
    ]

    if duplicates is not None:
        print(
            "Automatic procedure generated duplicates of Alias, "
            "please change manually aliases of the nomenclature file"
        )
        print(duplicates)
    else:
        print(
            "Please, check aliases in the nomenclature file "
            "automatically generated by this procedure"
        )

    return out


class symbolraster:
    """Class for manipulating QGIS raster symbol:

    Parameters
    ----------
    typec : cElementTree object (colorrampshader)
        cElementTree object of QML in which create nomenclature style

    codefield : string
        field name to represent (map)

    valeurs : list
        list of values (code, classname, red, green, blue, hex color) to describe each classe

    Return
    ------
    symbol
        symbolraster object
    """

    def __init__(self, colorrampshader, codefield, valeurs=[]):
        self.valeurs = valeurs
        self.cle = [codefield, "classname", "R", "G", "B", "HEX"]
        self.donnees = dict(list(zip(self.cle, self.valeurs)))
        self.item = ET.SubElement(colorrampshader, "item")

    def creation(self, codefield):
        self.item.set("alpha", "255")
        self.item.set("value", str(self.donnees[codefield]))
        self.item.set("label", self.donnees[self.cle[1]])
        self.item.set("color", self.donnees["HEX"])


class symbol:
    """Class for manipulating QGIS vector symbol:

    Parameters
    ----------
    typec : cElementTree object
        cElementTree object of QML in which create nomenclature style

    codefield : string
        field name to represent (map)

    valeurs : list
        list of values (code, classname, red, green, blue, hex color) to describe each classe

    Return
    ------
    symbol
        symbol object
    """

    def __init__(self, typec, codefield, valeurs=[]):

        self.typec = typec
        self.valeurs = valeurs
        self.cle = [codefield, "classname", "R", "G", "B", "HEX"]
        self.donnees = dict(list(zip(self.cle, self.valeurs)))
        self.symb = ET.SubElement(typec, "symbol")
        self.lower = ET.SubElement(self.symb, "lowervalue")
        self.upper = ET.SubElement(self.symb, "uppervalue")
        self.label = ET.SubElement(self.symb, "label")
        self.outline = ET.SubElement(self.symb, "outlinecolor")
        self.outsty = ET.SubElement(self.symb, "outlinestyle")
        self.outtail = ET.SubElement(self.symb, "outlinewidth")
        self.fillc = ET.SubElement(self.symb, "fillcolor")
        self.fillp = ET.SubElement(self.symb, "fillpattern")

    def creation(self, codefield, outlinestyle):
        self.lower.text = str(self.donnees[codefield])
        self.upper.text = str(self.donnees[codefield])
        self.label.text = self.donnees[self.cle[1]]
        self.outsty.text = outlinestyle
        self.outtail.text = "0.26"
        self.outline.set("red", self.donnees["R"])
        self.outline.set("green", self.donnees["G"])
        self.outline.set("blue", self.donnees["B"])
        self.fillc.set("red", self.donnees["R"])
        self.fillc.set("green", self.donnees["G"])
        self.fillc.set("blue", self.donnees["B"])
        self.fillp.text = "SolidPattern"


class Iota2Nomenclature:
    """Class for manipulating multi-level nomenclature :
    - extract specific attributes (code, name, alias, color) on a specfic level
    - prepare multi-level index (nomenclature)
    - prepare multi-level confusion matrix (OTB style)
    - prepare QGIS layer style (QML)
    - extract nomenclature from QML file

    Parameters
    ----------
    nomenclature : string
        Path to a nomenclature file

    Example
    -------
    >>> nomenclature = Iota2Nomenclature("nomenclature.csv")

    Return
    ------
    iota_nomenclature
        nomenclature object
    """

    def __init__(self, nomenclature, typefile="csv"):

        self.nomenclature = self.readNomenclatureFile(nomenclature, typefile)
        self.level = self.getLevelNumber()
        self.HierarchicalNomenclature = self.setHierarchicalNomenclature(
            self.nomenclature
        )

    def __str__(self):

        return "Nomenclature : %s level(s) with %s classes for the last level" % (
            self.level,
            len(self),
        )

    def __repr__(self):

        return str(self.nomenclature)

    def __len__(self):

        return len(self.nomenclature)

    def getLevelNumber(self):
        """Get the number of levels of a nomenclature

        Return
        ------
        int
            number of levels.
        """

        return len(self.nomenclature[0]) / 4

    def getColor(self, level, typec="RGB"):
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
                if "#" in list(index.get_level_values(level - 1))[0][2]:
                    return get_unique(
                        [
                            (convertHextoRGB(x[2]))
                            for x in list(index.get_level_values(level - 1))
                        ]
                    )
                else:
                    raise Exception("Color already in RGB format or in unknown format")
            elif typec == "HEX":
                return get_unique(
                    [x[2] for x in list(index.get_level_values(level - 1))]
                )
            else:
                raise Exception("Unknown color format provided")
        else:
            raise Exception("Level %s does not exists" % (level))

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
            raise Exception("Level %s does not exists" % (level))

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
            raise Exception("Level %s does not exists" % (level))

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
            return get_unique(
                [int(x[0]) for x in list(index.get_level_values(level - 1))]
            )
        else:
            raise Exception("Level %s does not exists" % (level))

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
            for lev in range(int(self.level)):
                if len(levelname) < self.level:
                    levelname.append("level%s" % (lev + 1))

                classeslist[ind].append(
                    (
                        int(line[(4 * lev) + 1]),
                        line[4 * lev],
                        line[(4 * lev) + 2],
                        line[(4 * lev) + 3],
                    )
                )

        index = MultiIndex.from_tuples([tuple(x) for x in classeslist], names=levelname)

        return index

    def readNomenclatureFile(self, nomen, typefile="csv"):
        """Read a csv nomenclature file

        Example of csv structure for 2 nested levels (l1 = level 1, l2 = level 2) :

           classname_l1, code_l1, colour_l1, alias_l1, classname_l2, code_l2, colour_l2, alias_l2
           Urbain, 100, #b106b1, Urbain, Urbain dense, 1, #b186c1, Urbaindens

        Example of config structure for 2 nested levels (l1 = level 1, l2 = level 2) :
                   >>> Classes:
                   >>> {
                   >>>     Level1:
                   >>>     {
                   >>>         "Urbain":
                   >>>         {
                   >>>         code:100
                   >>>         alias:'Urbain'
                   >>>         color:'#b106b1'
                   >>>         }
                   >>>         ...
                   >>>     }
                   >>>     Level2:
                   >>>     {
                   >>>         "Urbain dense":
                   >>>         {
                   >>>         code:1
                   >>>         ...
                   >>>         parent:100
                   >>>         }
                   >>>     ...
                   >>>     }
                   >>> }

        Example of config structure for 2 nested levels (l1 = level 1, l2 = level 2) :
                   >>> {'Level1': {'Urbain': {'color': '#b106b1', 'alias': 'Urbain', 'code': 100}, ...},
                        'Level2': {'Zones indus. et comm.': {'color': ..., 'parent' : 100}, ...}}

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
                raise Exception(
                    "Nomenclature reading failed, nomenclature is not properly built"
                )

        elif typefile == "cfg":
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
                raise Exception(
                    "Nomenclature reading failed, nomenclature is not properly built"
                )

        elif typefile == "csv" or isinstance(nomen, list):
            if isinstance(nomen, list):
                tabnomenc = nomen
            else:
                try:
                    fileclasses = codecs.open(nomen, "r", "utf-8")
                    tabnomenc = [
                        tuple(line.rstrip("\n").split(","))
                        for line in fileclasses.readlines()
                    ]
                except IOError:
                    raise Exception(
                        "Nomenclature reading failed, nomenclature is not properly built"
                    )

        else:
            raise Exception("The type of nomenclature file is not handled")

        return tabnomenc

    def createVectorQML(self, outpath, codefield, level, outlinestyle="SolidLine"):
        """Create a QML QGIS style file for vector data

        Parameters
        ----------
        outpath: str
            output path of QML QGIS style file

        codefield: str
            field name to represent (map)

        level: int
            level of the nomenclature

        outlinestyle: str
            SolidLine or not for outlinestyle of polygons

        """

        intro = ET.Element("qgis")
        transp = ET.SubElement(intro, "transparencyLevelInt")
        transp.text = "255"
        classatr = ET.SubElement(intro, "classificationattribute")
        classatr.text = codefield
        typec = ET.SubElement(intro, "uniquevalue")
        classif = ET.SubElement(typec, "classificationfield")
        classif.text = codefield

        if len(self.getClass(level)) == len(self.getColor(level)):
            colorRGBlist = [
                [
                    x[0],
                    x[1].decode("utf-8"),
                    str(x[2][0]),
                    str(x[2][1]),
                    str(x[2][2]),
                    x[3],
                ]
                for x in zip(
                    self.getCode(level),
                    self.getClass(level),
                    self.getColor(level),
                    self.getColor(level, "HEX"),
                )
            ]

            for elem in colorRGBlist:
                symb = symbol(typec, codefield, elem)
                symb.creation(codefield, outlinestyle)

            # write QML style file
            fich_style = ET.ElementTree(intro)
            fich_style.write(outpath)

        else:
            raise Exception(
                "Duplicates colors or classes found in the nomenclature file"
            )

    def createRasterQML(self, outpath, classfield, level, nodata="0"):
        """Create a QML QGIS style file for raster data

        Parameters
        ----------
        outpath: str
            output path of QML QGIS style file

        classfield: str
            field name to represent (map)

        level: int
            level of the nomenclature

        nodata: str
            pixel value of nodata (default: 0)

        """

        intro = ET.Element("qgis")
        pipe = ET.SubElement(intro, "pipe")
        rasterrenderer = ET.SubElement(
            pipe,
            "rasterrenderer",
            opacity="1",
            alphaBand="0",
            classificationMax="211",
            classificationMinMaxOrigin="CumulativeCutFullExtentEstimated",
            band="1",
            classificationMin="0",
            type="singlebandpseudocolor",
        )
        rastershader = ET.SubElement(rasterrenderer, "rastershader")
        colorrampshader = ET.SubElement(
            rastershader, "colorrampshader", colorRampType="INTERPOLATED", clip="0"
        )

        if len(self.getClass(level)) == len(self.getColor(level)):
            colorRGBlist = [
                [
                    x[0],
                    x[1].decode("utf-8"),
                    str(x[2][0]),
                    str(x[2][1]),
                    str(x[2][2]),
                    x[3],
                ]
                for x in zip(
                    self.getCode(level),
                    self.getClass(level),
                    self.getColor(level),
                    self.getColor(level, "HEX"),
                )
            ]

            for elem in colorRGBlist:
                symb = symbolraster(colorrampshader, classfield, elem)
                symb.creation(classfield)

            itemnd = ET.SubElement(
                colorrampshader,
                "item",
                alpha="0",
                value="%s" % (nodata),
                label="",
                color="#0000ff",
            )
            brightnesscontrast = ET.SubElement(
                pipe, "brightnesscontrast", brightness="0", contrast="0"
            )
            huesaturation = ET.SubElement(
                pipe,
                "huesaturation",
                colorizeGreen="128",
                colorizeOn="0",
                colorizeRed="255",
                colorizeBlue="128",
                grayscaleMode="0",
                saturation="0",
                colorizeStrength="100",
            )
            rasterresampler = ET.SubElement(
                pipe, "rasterresampler", maxOversampling="2"
            )
            tree = ET.ElementTree(intro)
            tree.write(outpath, xml_declaration=True, encoding="utf-8", method="xml")

        else:
            raise Exception(
                "Duplicates colors or classes found in the nomenclature file"
            )

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
        cmdf = DataFrame(
            matrix,
            index=self.HierarchicalNomenclature,
            columns=self.HierarchicalNomenclature,
        )
        cmdf.sort_index(level=self.level - 1, inplace=True, axis=1)
        cmdf.sort_index(level=self.level - 1, inplace=True, axis=0)

        return cmdf

    def createColorFileTheia(self, filecolor):
        """Create Color file for THEIA distribution

        filecolor :  colors file path
            text/csv file (csv structure : code R G B)
        """
        tabcolors = [
            [x, y[0], y[1], y[2]]
            for x, y in zip(self.getCode(self.level), self.getColor(self.level))
        ]
        tabcolors.insert(0, [0, 255, 255, 255])
        tabcolors.append([255, 0, 0, 0])
        with open(filecolor, "w") as ofile:
            writer = csv.writer(ofile, delimiter=" ")
            writer.writerows(tabcolors)

    def createNomenclatureFileTheia(self, filenom):
        """Create Nomencature file for THEIA distribution

        filecolor :  nomenclature file path
            text/csv file (csv structure : classname:code)
        """
        tabclasses = [
            [x.encode("utf8"), y]
            for x, y in zip(self.getClass(self.level), self.getCode(self.level))
        ]
        tabclasses.append([255, "autres"])
        with open(filenom, "w") as ofile:
            writer = csv.writer(ofile, delimiter=":")
            writer.writerows(tabclasses)
