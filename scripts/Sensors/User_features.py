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

from config import Config
import logging
import glob
import os

from Sensors.GenSensors import Sensor
from collections import OrderedDict

logger = logging.getLogger(__name__)

#in order to avoid issue 'No handlers could be found for logger...'
logger.addHandler(logging.NullHandler())

class User_features(Sensor):

    name = 'userFeatures'

    def __init__(self, config_path, tile_name):
        """
        """
        from Common import ServiceConfigFile as SCF

        self.tile_name = tile_name
        self.cfg_IOTA2 = SCF.serviceConfigFile(config_path)
        self.user_feat_data = self.cfg_IOTA2.getParam("chain", "userFeatPath")
        tile_dir_name = [dir_name for dir_name in os.listdir(self.user_feat_data) if tile_name in dir_name][0]

        # run attributes
        self.tile_directory = os.path.join(self.user_feat_data, tile_dir_name)
        self.features_dir = os.path.join(self.cfg_IOTA2.getParam("chain", "outputPath"),
                                         "features", tile_name)
        self.target_proj = int(self.cfg_IOTA2.getParam("GlobChain", "proj").lower().replace(" ","").replace("epsg:",""))
        
        # sensors attributes
        self.data_type = self.cfg_IOTA2.getParam("userFeat", "patterns").replace(" ","").split(",")

        # output's names
        self.time_series_masks_name = "{}_{}_MASKS.tif".format(self.__class__.name,
                                                               tile_name)
        self.features_names = "{}_{}_Features.tif".format(self.__class__.name,
                                                          tile_name)
        self.footprint_name = "{}_{}_footprint.tif".format(self.__class__.name,
                                                           tile_name)
        ref_image_name = "{}_{}_reference.tif".format(self.__class__.name,
                                                           tile_name)
        self.ref_image = os.path.join(self.cfg_IOTA2.getParam("chain", "outputPath"),
                                      "features",
                                      tile_name,
                                      "tmp",
                                      ref_image_name)

    def footprint(self, ram=128, data_value=1):
        """
        """
        from gdal import Warp
        from osgeo.gdalconst import  GDT_Byte
        from Common.FileUtils import FileSearch_AND
        from Common.OtbAppBank import CreateBandMathApplication
        from Common.FileUtils import ensure_dir
        from Common.FileUtils import getRasterProjectionEPSG
        from Common.FileUtils import getRasterResolution

        footprint_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(footprint_dir,raise_exe=False)
        footprint_out = os.path.join(footprint_dir, self.footprint_name)

        user_feature = FileSearch_AND(self.tile_directory, True, self.data_type[0])

        # tile reference image generation
        base_ref = user_feature[0]
        logger.info("reference image generation {} from {}".format(self.ref_image, base_ref))
        ensure_dir(os.path.dirname(self.ref_image), raise_exe=False)
        base_ref_projection = getRasterProjectionEPSG(base_ref)
        base_ref_res_x, _ = getRasterResolution(base_ref)
        if not os.path.exists(self.ref_image):
            ds = Warp(self.ref_image, base_ref, multithread=True,
                      format="GTiff", xRes=base_ref_res_x, yRes=base_ref_res_x,
                      outputType=GDT_Byte, srcSRS="EPSG:{}".format(base_ref_projection),
                      dstSRS="EPSG:{}".format(self.target_proj))

        # user features must not contains NODATA -> "exp" : 'data_value' mean every data available
        footprint = CreateBandMathApplication({"il": self.ref_image,
                                               "out": footprint_out,
                                               "exp" : str(data_value),
                                               "pixType":"uint8",
                                               "ram": str(ram)})
        
        # needed to travel throught iota2's library
        app_dep = []

        return footprint, app_dep

    def get_time_series_masks(self, ram=128, logger=logger):
        """
        """
        from Common.OtbAppBank import CreateConcatenateImagesApplication
        from Common.FileUtils import ensure_dir
        from Common.FileUtils import FileSearch_AND

        time_series_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(time_series_dir, raise_exe=False)
        times_series_mask = os.path.join(time_series_dir, self.time_series_masks_name)
        
        # check patterns
        for pattern in self.data_type:
            user_feature = FileSearch_AND(self.tile_directory, True, pattern)
            if not user_feature:
                msg = "WARNING : '{}' not found in {}".format(pattern, self.tile_directory)
                logger.error(msg)
                raise Exception(msg)
        nb_patterns = len(self.data_type)
        masks = []
        app_dep = []
        for fake_band in range(nb_patterns):
            dummy_mask, _ = self.footprint(data_value=0)
            dummy_mask.Execute()
            app_dep.append(dummy_mask)
            masks.append(dummy_mask)
        masks_stack = CreateConcatenateImagesApplication({"il": masks,
                                                          "out": times_series_mask,
                                                          "ram": str(ram)})
        
        return masks_stack, app_dep, nb_patterns

    def get_features(self, ram=128, logger=logger):
        """
        """
        from gdal import Warp
        from osgeo.gdalconst import  GDT_Byte
        from Common.OtbAppBank import CreateConcatenateImagesApplication
        from Common.OtbAppBank import CreateSuperimposeApplication
        from Common.FileUtils import FileSearch_AND
        from Common.FileUtils import ensure_dir
        from Common.FileUtils import getRasterProjectionEPSG
        from Common.FileUtils import getRasterResolution
        from Common.FileUtils import getRasterNbands

        features_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(features_dir, raise_exe=False)
        features_out = os.path.join(features_dir, self.features_names)

        user_features = []
        user_features_bands = []
        for pattern in self.data_type:
            user_feature = FileSearch_AND(self.tile_directory, True, pattern)
            if user_feature:
                user_features_bands.append(getRasterNbands(user_feature[0]))
                user_features.append(user_feature[0])
            else :
                msg = "WARNING : '{}' not found in {}".format(pattern, self.tile_directory)
                logger.error(msg)
                raise Exception(msg)

        user_feat_stack = CreateConcatenateImagesApplication({"il": user_features,
                                                              "ram": str(ram),
                                                              "out": features_out})
        base_ref = user_features[0]
        base_ref_projection = getRasterProjectionEPSG(base_ref)
        if not os.path.exists(self.ref_image):
            base_ref_res_x, _ = getRasterResolution(base_ref)
            ds = Warp(self.ref_image, base_ref, multithread=True,
                      format="GTiff", xRes=base_ref_res_x, yRes=base_ref_res_x,
                      outputType=GDT_Byte, srcSRS="EPSG:{}".format(base_ref_projection),
                      dstSRS="EPSG:{}".format(self.target_proj))
        app_dep = []
        if int(base_ref_projection) != (self.target_proj):
            user_feat_stack.Execute()
            app_dep.append(user_feat_stack)
            user_feat_stack, _ = CreateSuperimposeApplication({"inr": self.ref_image,
                                                               "inm": user_feat_stack,
                                                               "out": features_out,
                                                               "ram": str(ram)})
        features_labels = ["{}_band_{}".format(pattern, band_num) for pattern, nb_bands in zip(self.data_type, user_features_bands) for band_num in range(nb_bands)]
        return (user_feat_stack, app_dep), features_labels