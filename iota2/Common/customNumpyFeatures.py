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
        from iota2.Common import ServiceConfigFile as SCF
        from iota2.Sensors.Sensors_container import Sensors_container
        self.data = None  # empty attribute to address data
        cfg = SCF.serviceConfigFile(cfg_file)
        # Get the first tile, all the tiles must come from same sensor
        first_tile = cfg.getParam("chain", "listTile").split(" ")[0]

        def compute_indices_after_gapfilling(sensor, bands):
            _, dates = sensor.write_interpolation_dates_file(write=False)
            indices = []
            for i, band in enumerate(bands):
                # print(i, band)
                ind = [i + len(bands) * x for x, dates in enumerate(dates)]
                print(band, ind)
                indices.append(ind)
            return indices
        # From this tile get enabled sensors
        sensor_tile_container = Sensors_container(cfg_file,
                                                  first_tile,
                                                  working_dir=None)
        list_of_bands = []
        time_series_indices = []
        for sensor in sensor_tile_container.get_enabled_sensors():
            bands = sensor.stack_band_position
            tmp_indices = compute_indices_after_gapfilling(sensor, bands)
            list_of_bands += bands
            time_series_indices += tmp_indices

        # TODO: handle user feature selection
        print(list_of_bands)
        # [[0, 3], [1, 4], [2, 5]]
        for band, indices in zip(list_of_bands, time_series_indices):
            def get_band(band=band, indices=indices):
                import numpy as np
                data = np.take(self.data, indices, axis=2)
                return data
            setattr(dataContainer, 'get_band_{}'.format(band), get_band)


class customNumpyFeatures(dataContainer):

    def __init__(self, cfg_file):
        import sys
        import importlib
        import types  # solves issues about type and inheritance
        from iota2.Common import ServiceConfigFile as SCF
        super(customNumpyFeatures, self).__init__(cfg_file)
        cfg = SCF.serviceConfigFile(cfg_file)
        path = cfg.getParam("Features", "codePath")
        module = cfg.getParam("Features", "namefile")
        sys.path.insert(0, path)
        # TODO: check if module is a module and func a function
        mod = importlib.import_module(module)
        # Function can be multiple
        self.fun_name_list = []
        param = cfg.getParam("Features", "functions")
        if (param is not None and len(param) != 0):
            self.fun_name_list = cfg.getParam("Features",
                                              "functions").split(" ")
            for fun_name in self.fun_name_list:
                func = (getattr(mod, fun_name))
                # self.custom_features = types.MethodType(func, dataContainer)
                setattr(self, fun_name, types.MethodType(func, dataContainer))

    def process(self, data):
        import numpy as np
        self.data = data

        try:
            for fun_name in self.fun_name_list:
                func = (getattr(self, fun_name))
                feat = func()
                self.data = np.concatenate((self.data, feat), axis=2)
            return self.data
        except Exception as e:
            print("Error during custom_features computation : {}".format(
                fun_name))
            print(e)
