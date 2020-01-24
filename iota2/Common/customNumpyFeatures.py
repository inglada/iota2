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


class dataContainer():

    def __init__(self, cfg_file):
        self.data = None  # empty attribute to address data

        # TODO: Get band indices from cfg and sensors
        bands = ["b1", "b2", "b3"]
        time_series_indices = [[0, 3], [1, 4], [2, 5]]
        for band, indices in zip(bands, time_series_indices):
            def get_band(band=band, indices=indices):
                import numpy as np
                #print("GET BAND {}".format(band), indices, self.data.shape)
                data = np.take(self.data, indices, axis=2)
                return data
            setattr(dataContainer, 'get_band_{}'.format(band), get_band)


class customNumpyFeatures(dataContainer):

    def __init__(self, cfg_file):
        import sys
        import importlib
        import types  # solves issues about type and inheritance
        from Common import ServiceConfigFile as SCF
        super(customNumpyFeatures, self).__init__(cfg_file)
        cfg = SCF.serviceConfigFile(cfg_file)
        path = cfg.getParam("Features", "codePath")
        module = cfg.getParam("Features", "namefile")
        sys.path.insert(0, path)
        # TODO: check if module is a module and func a function
        mod = importlib.import_module(module)
        self.fun_name = cfg.getParam("Features", "function")
        func = (getattr(mod, self.fun_name))
        self.custom_features = types.MethodType(func, dataContainer)

    def process(self, data):
        import numpy as np
        self.data = data
        try:
            feat = self.custom_features()
            return np.concatenate((data, feat), axis=2)
        except Exception as e:
            print("Error during custom_features computation : {}".format(
                self.fun_name))
            print(e)
