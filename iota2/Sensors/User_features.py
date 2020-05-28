# !/usr/bin/env python3
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
"""
user_features class definition
"""

import logging
import os

LOGGER = logging.getLogger(__name__)

#in order to avoid issue 'No handlers could be found for logger...'
LOGGER.addHandler(logging.NullHandler())


class user_features():
    """user_feature class definition
    """
    name = 'userFeatures'

    def __init__(self, tile_name, image_directory, i2_output_path, target_proj,
                 patterns, **kwargs):
        """
        """
        self.tile_name = tile_name
        self.user_feat_data = image_directory
        tile_dir_name = [
            dir_name for dir_name in os.listdir(self.user_feat_data)
            if tile_name in dir_name
        ][0]

        # run attributes
        self.tile_directory = os.path.join(self.user_feat_data, tile_dir_name)
        self.features_dir = os.path.join(i2_output_path, "features", tile_name)
        self.target_proj = target_proj

        # sensors attributes
        self.data_type = patterns

        # output's names
        self.time_series_masks_name = "{}_{}_MASKS.tif".format(
            self.__class__.name, tile_name)
        self.features_names = "{}_{}_Features.tif".format(
            self.__class__.name, tile_name)
        self.footprint_name = "{}_{}_footprint.tif".format(
            self.__class__.name, tile_name)
        ref_image_name = "{}_{}_reference.tif".format(self.__class__.name,
                                                      tile_name)
        self.ref_image = os.path.join(i2_output_path, "features", tile_name,
                                      "tmp", ref_image_name)
        self.working_resolution = kwargs["working_resolution"]

    def footprint(self, ram=128, data_value=1):
        """get footprint
        """
        from gdal import Warp
        from osgeo.gdalconst import GDT_Byte
        from iota2.Common.FileUtils import FileSearch_AND
        from iota2.Common.OtbAppBank import CreateBandMathApplication
        from iota2.Common.FileUtils import ensure_dir
        from iota2.Common.FileUtils import getRasterProjectionEPSG
        from iota2.Common.FileUtils import getRasterResolution

        footprint_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(footprint_dir, raise_exe=False)
        footprint_out = os.path.join(footprint_dir, self.footprint_name)

        user_feature = FileSearch_AND(self.tile_directory, True,
                                      self.data_type[0])

        # tile reference image generation
        base_ref = user_feature[0]
        LOGGER.info("reference image generation {} from {}".format(
            self.ref_image, base_ref))
        ensure_dir(os.path.dirname(self.ref_image), raise_exe=False)
        base_ref_projection = getRasterProjectionEPSG(base_ref)
        base_ref_res_x, base_ref_res_y = getRasterResolution(base_ref)
        if self.working_resolution:
            base_ref_res_x = self.working_resolution[0]
            base_ref_res_y = self.working_resolution[1]
        if not os.path.exists(self.ref_image):
            Warp(self.ref_image,
                 base_ref,
                 multithread=True,
                 format="GTiff",
                 xRes=base_ref_res_x,
                 yRes=base_ref_res_y,
                 outputType=GDT_Byte,
                 srcSRS="EPSG:{}".format(base_ref_projection),
                 dstSRS="EPSG:{}".format(self.target_proj))

        # user features must not contains NODATA
        # -> "exp" : 'data_value' mean every data available
        footprint = CreateBandMathApplication({
            "il": self.ref_image,
            "out": footprint_out,
            "exp": str(data_value),
            "pixType": "uint8",
            "ram": str(ram)
        })

        # needed to travel throught iota2's library
        app_dep = []

        return footprint, app_dep

    def get_time_series_masks(self, ram=128, logger=LOGGER):
        """
        """
        from iota2.Common.OtbAppBank import CreateConcatenateImagesApplication
        from iota2.Common.FileUtils import ensure_dir
        from iota2.Common.FileUtils import FileSearch_AND

        time_series_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(time_series_dir, raise_exe=False)
        times_series_mask = os.path.join(time_series_dir,
                                         self.time_series_masks_name)

        # check patterns
        for pattern in self.data_type:
            user_feature = FileSearch_AND(self.tile_directory, True, pattern)
            if not user_feature:
                msg = "WARNING : '{}' not found in {}".format(
                    pattern, self.tile_directory)
                logger.error(msg)
                raise Exception(msg)
        nb_patterns = len(self.data_type)
        masks = []
        app_dep = []
        for _ in range(nb_patterns):
            dummy_mask, _ = self.footprint(data_value=0)
            dummy_mask.Execute()
            app_dep.append(dummy_mask)
            masks.append(dummy_mask)
        masks_stack = CreateConcatenateImagesApplication({
            "il": masks,
            "out": times_series_mask,
            "ram": str(ram)
        })

        return masks_stack, app_dep, nb_patterns

    def get_features(self, ram=128, logger=LOGGER):
        """generate user features. Concatenates all of them
        """
        from gdal import Warp
        from osgeo.gdalconst import GDT_Byte
        from iota2.Common.OtbAppBank import CreateConcatenateImagesApplication
        from iota2.Common.OtbAppBank import CreateSuperimposeApplication
        from iota2.Common.FileUtils import FileSearch_AND
        from iota2.Common.FileUtils import ensure_dir
        from iota2.Common.FileUtils import getRasterProjectionEPSG
        from iota2.Common.FileUtils import getRasterResolution
        from iota2.Common.FileUtils import getRasterNbands

        features_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(features_dir, raise_exe=False)
        features_out = os.path.join(features_dir, self.features_names)

        user_features_found = []
        user_features_bands = []
        for pattern in self.data_type:
            user_feature = FileSearch_AND(self.tile_directory, True, pattern)
            if user_feature:
                user_features_bands.append(getRasterNbands(user_feature[0]))
                user_features_found.append(user_feature[0])
            else:
                msg = "WARNING : '{}' not found in {}".format(
                    pattern, self.tile_directory)
                logger.error(msg)
                raise Exception(msg)

        user_feat_stack = CreateConcatenateImagesApplication({
            "il":
            user_features_found,
            "ram":
            str(ram),
            "out":
            features_out
        })
        base_ref = user_features_found[0]
        base_ref_projection = getRasterProjectionEPSG(base_ref)
        base_ref_res_x, base_ref_res_y = getRasterResolution(base_ref)
        if self.working_resolution:
            base_ref_res_x = self.working_resolution[0]
            base_ref_res_y = self.working_resolution[1]
        if not os.path.exists(self.ref_image):
            Warp(self.ref_image,
                 base_ref,
                 multithread=True,
                 format="GTiff",
                 xRes=base_ref_res_x,
                 yRes=base_ref_res_y,
                 outputType=GDT_Byte,
                 srcSRS="EPSG:{}".format(base_ref_projection),
                 dstSRS="EPSG:{}".format(self.target_proj))
        app_dep = []

        same_res = getRasterResolution(base_ref) == (base_ref_res_x,
                                                     base_ref_res_y)
        if int(base_ref_projection) != (self.target_proj) or not same_res:
            user_feat_stack.Execute()
            app_dep.append(user_feat_stack)
            user_feat_stack, _ = CreateSuperimposeApplication({
                "inr": self.ref_image,
                "inm": user_feat_stack,
                "out": features_out,
                "ram": str(ram)
            })
        features_labels = [
            "{}_band_{}".format(pattern, band_num)
            for pattern, nb_bands in zip(self.data_type, user_features_bands)
            for band_num in range(nb_bands)
        ]
        return (user_feat_stack, app_dep), features_labels
