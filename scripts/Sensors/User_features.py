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
        # sensors attributes
        self.data_type = self.cfg_IOTA2.getParam("userFeat", "patterns").replace(" ","").split(",")

        # output's names
        self.features_names = "{}_{}_Features.tif".format(self.__class__.name,
                                                          tile_name)
    def get_features(self, ram=128, logger=logger):
        """
        """
        from Common.OtbAppBank import CreateConcatenateImagesApplication
        from Common.FileUtils import FileSearch_AND
        from Common.FileUtils import ensure_dir

        features_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(features_dir, raise_exe=False)
        features_out = os.path.join(features_dir, self.features_names)

        user_features = []
        for pattern in self.data_type:
            user_feature = FileSearch_AND(self.tile_directory, True, pattern)
            if user_feature:
                user_features.append(user_feature[0])
            else :
                msg = "WARNING : '{}' not found in {}".format(pattern, self.tile_directory)
                logger.error(msg)
                raise Exception(msg)

        user_feat_stack = CreateConcatenateImagesApplication({"il": user_features,
                                                              "ram": str(ram),
                                                              "out": features_out})
        features_labels = [pattern for pattern in self.data_type]
        return (user_feat_stack, []), features_labels




        