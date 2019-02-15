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

from config import Config
import logging
import glob
import os

from GenSensors import Sensor
from collections import OrderedDict

logger = logging.getLogger(__name__)

#in order to avoid issue 'No handlers could be found for logger...'
logger.addHandler(logging.NullHandler())

class Landsat_8_old(Sensor):

    name = 'Landsat8Old'

    def __init__(self, config_path, tile_name):
        from Common import ServiceConfigFile as SCF
        Sensor.__init__(self)

        if not os.path.exists(config_path):
            return

        self.tile_name = tile_name
        self.cfg_IOTA2 = SCF.serviceConfigFile(config_path)
        cfg_sensors = os.path.join(os.environ.get('IOTA2DIR'), "config", "sensors.cfg")
        cfg_sensors = SCF.serviceConfigFile(cfg_sensors, iota_config=False)

        # running attributes
        self.target_proj = int(self.cfg_IOTA2.getParam("GlobChain", "proj").lower().replace(" ","").replace("epsg:",""))
        self.all_tiles = self.cfg_IOTA2.getParam("chain", "listTile")
        self.l8_old_data = self.cfg_IOTA2.getParam("chain", "L8Path_old")
        self.tile_directory = os.path.join(self.l8_old_data, tile_name)
        self.full_pipeline = self.cfg_IOTA2.getParam("Landsat8_old", "full_pipline")
        self.features_dir = os.path.join(self.cfg_IOTA2.getParam("chain", "outputPath"),
                                         "features", tile_name)
        extract_bands = self.cfg_IOTA2.getParam("Landsat8_old", "keepBands")
        extract_bands_flag = self.cfg_IOTA2.getParam("iota2FeatureExtraction", "extractBands")
        output_target_dir = self.cfg_IOTA2.getParam("chain", "L8_old_output_path")
        if output_target_dir:
            self.output_preprocess_directory = os.path.join(output_target_dir, tile_name)
            if not os.path.exists(self.output_preprocess_directory):
                try:
                    os.mkdir(self.output_preprocess_directory)
                except:
                    pass
        else :
            self.output_preprocess_directory = self.tile_directory

        # sensors attributes
        self.native_res = 30
        self.data_type = "CORR_PENTE"
        self.suffix = "STACK"
        self.masks_date_suffix = "BINARY_MASK"
        self.date_position = 3# if date's name split by "_"
        self.NODATA_VALUE = -10000
        #~ self.masks_rules = OrderedDict({"CLM_XS.tif":0, "SAT_XS.tif":0, "EDG_ALL.tif":0})# 0 mean data, else noData
        #~ self.border_pos = 2
        self.features_names_list = ["NDVI", "NDWI", "Brightness"]

        # define bands to get and their order
        self.stack_band_position = ["B1", "B2", "B3", "B4", "B5", "B6", "B7"]
        self.extracted_bands = None
        if extract_bands_flag:
            self.extracted_bands = [(band_name, band_position + 1) for band_position, band_name in enumerate(self.stack_band_position) if band_name in self.cfg_IOTA2.getParam("Landsat8", "keepBands")]

        # output's names
        self.footprint_name = "{}_{}_footprint.tif".format(self.__class__.name,
                                                           tile_name)
        ref_image_name = "{}_{}_reference.tif".format(self.__class__.name,
                                                           tile_name)
        self.ref_image = os.path.join(self.cfg_IOTA2.getParam("chain", "outputPath"),
                                      "features",
                                      tile_name,
                                      "tmp",
                                      ref_image_name)
        self.time_series_name = "{}_{}_TS.tif".format(self.__class__.name,
                                                      tile_name)
        self.time_series_masks_name = "{}_{}_MASKS.tif".format(self.__class__.name,
                                                               tile_name)
        self.time_series_gapfilling_name = "{}_{}_TSG.tif".format(self.__class__.name,
                                                                  tile_name)
        self.features_names = "{}_{}_Features.tif".format(self.__class__.name,
                                                          tile_name)
        # about gapFilling interpolations
        self.temporal_res = self.cfg_IOTA2.getParam("Landsat8", "temporalResolution")
        self.input_dates = "{}_{}_input_dates.txt".format(self.__class__.name,
                                                           tile_name)
        self.interpolated_dates = "{}_{}_interpolation_dates.txt".format(self.__class__.name,
                                                                         tile_name)
        
    def get_available_dates(self):
        """
        return sorted available dates
        """
        pass

    def get_available_dates_masks(self):
        """
        return sorted available masks
        """
        pass

    def preprocess(self, working_dir=None, ram=128, logger=logger):
        """
        """
        pass

    def footprint(self, ram=128):
        """
        """
        pass

    def get_time_series(self, ram=128):
        """
        """
        pass

    def get_time_series_masks(self, ram=128, logger=logger):
        """
        """
        pass

    def get_time_series_gapFilling(self, ram=128):
        """
        """
        pass

    def get_features(self, ram=128, logger=logger):
        """
        """
        pass