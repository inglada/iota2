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

class i2Error(Exception):
    """ Base class for exceptions in iota2 chain"""
    pass


class directoryError(i2Error):
    """ Base subclass for exception in the configuration file
        IN :
            msg [string] : explanation of the error
    """
    def __init__(self, directory_path):
        msg = "directory : {} cannot be created".format(directory_path)
        i2Error.__init__(self, msg)
        self.msg = msg
    def __str__(self):
        return repr(self.msg)


class intersectionError(i2Error):
    """ Base subclass for exception in the configuration file
        IN :
            msg [string] : explanation of the error
    """
    def __init__(self):
        msg = "no intersection between georeferenced inputs"
        i2Error.__init__(self, msg)
        self.msg = msg
    def __str__(self):
        return repr(self.msg)


class configFileError(i2Error):
    """ Base subclass for exception in the configuration file
        IN :
            msg [string] : explanation of the error
    """
    def __init__(self, msg):
        i2Error.__init__(self, msg)
        self.msg = msg
    def __str__(self):
        return repr("iota2 ERROR : {}".format(self.msg))


class dataBaseError(i2Error):
    """
    """
    def __init__(self, msg):
        i2Error.__init__(self, msg)
        self.msg = msg
    def __str__(self):
        return repr("dataBaseError : {}".format(self.msg))


class sqliteCorrupted(dataBaseError):
    """
    """
    def __init__(self, journalsqlite_path):
        sqlite_path = journalsqlite_path.replace("-journal", "")
        msg = "'.sqlite-journal' file detetected, please remove {} and {}".format(journalsqlite_path, sqlite_path)
        i2Error.__init__(self, msg)
        self.msg = msg
    def __str__(self):
        return repr(self.msg)


class invalidGeometry(dataBaseError):
    """
    """
    def __init__(self, msg):
        i2Error.__init__(self, msg)
        self.msg = msg
    def __str__(self):
        return repr(self.msg)


class invalidProjection(dataBaseError):
    """
    """
    def __init__(self, msg):
        i2Error.__init__(self, msg)
        self.msg = msg
    def __str__(self):
        return repr(self.msg)


class emptyFeatures(dataBaseError):
    """
    """
    def __init__(self, msg):
        i2Error.__init__(self, msg)
        self.msg = msg
    def __str__(self):
        return repr(self.msg)


class emptyGeometry(dataBaseError):
    """
    """
    def __init__(self, msg):
        i2Error.__init__(self, msg)
        self.msg = msg
    def __str__(self):
        return repr(self.msg)


class duplicatedFeatures(dataBaseError):
    """
    """
    def __init__(self, msg):
        i2Error.__init__(self, msg)
        self.msg = msg
    def __str__(self):
        return repr(self.msg)


class containsMultipolygon(dataBaseError):
    """
    """
    def __init__(self, msg):
        i2Error.__init__(self, msg)
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

class namingConvention(dataBaseError):
    """
    """
    def __init__(self, msg):
        i2Error.__init__(self, msg)
        self.msg = msg

    def __str__(self):
        return repr(self.msg)

class missingField(dataBaseError):
    """
    """
    def __init__(self, database_path, missing_field):
        msg = "{} does not contains the field '{}'".format(database_path, missing_field)
        i2Error.__init__(self, msg)
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

class fieldType(dataBaseError):
    """
    """
    def __init__(self, input_vector, data_field, expected_type):
        msg = "the field '{}' in {} must be {} type".format(data_field, input_vector, expected_type)
        i2Error.__init__(self, msg)
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

class tooSmallRegion(dataBaseError):
    """
    """
    def __init__(self, input_vector, area_threshold, nb_too_small_geoms):
        msg = "the region shape '{}' contains {} regions or sub-regions inferior than {}, please remove them.".format(input_vector, nb_too_small_geoms, area_threshold)
        i2Error.__init__(self, msg)
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

####################################################################
# List of error class definition for the configuration file,
# inherits the configFileError class
####################################################################
class parameterError(configFileError):
    """ Exception raised for errors in a parameter in the configuration file
        (like absence of a mandatory variable)
        IN :
            msg [string] : explanation of the error
    """
    def __init__(self, section, msg):
        self.section = section
        self.msg = msg
    def __str__(self):
        return "Error: In section " + repr(self.section) + ", " + self.msg

class dirError(configFileError):
    """ Exception raised for errors in mandatory directory
        IN :
            directory [string] : name of the directory
    """
    def __init__(self, directory):
        self.directory = directory
    def __str__(self):
        self.msg = "Error: " + repr(self.directory) + " doesn't exist"
        return self.msg

class configError(configFileError):
    """ Exception raised for configuration errors in the configuration file
        (like incompatible parameters)
        IN :
            msg [string] : explanation of the error
    """
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return "Error: " + repr(self.msg)

class fileError(configFileError):
    """ Exception raised for errors inside an input file
        (like a bad format or absence of a variable)
        IN :
            msg [string] : explanation of the error
    """
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return "Error: " + repr(self.msg)

####################################################################
####################################################################