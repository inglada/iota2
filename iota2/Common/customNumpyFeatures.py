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
from typing import Dict, Union, List, Optional

sensors_params_type = Dict[str, Union[str, List[str], int]]


class data_container:
    """ This class contains all methods to access data in image"""
    def __init__(self,
                 tile_name: str,
                 output_path: str,
                 sensors_parameters: sensors_params_type,
                 working_dir: Optional[str] = None):
        from iota2.Sensors.Sensors_container import sensors_container

        self.data = None  # empty attribute to address data

        # Get the first tile, all the tiles must come from same sensor

        def compute_indices_after_gapfilling(sensor, bands):
            _, dates = sensor.write_interpolation_dates_file(write=False)
            indices = []
            for i, band in enumerate(bands):
                # print(i, band)
                ind = [i + len(bands) * x for x, _ in enumerate(dates)]
                print(band, ind)
                indices.append(ind)
            return indices

        # From this tile get enabled sensors
        sensor_tile_container = sensors_container(tile_name, working_dir,
                                                  output_path,
                                                  **sensors_parameters)

        list_of_bands = []
        time_series_indices = []
        list_sensors = []
        for sensor in sensor_tile_container.get_enabled_sensors():

            bands = sensor.stack_band_position
            tmp_indices = compute_indices_after_gapfilling(sensor, bands)
            list_of_bands += bands
            time_series_indices += tmp_indices
            list_sensors += [sensor.name] * len(bands)
        # TODO: handle user feature selection
        print(list_of_bands)
        # [[0, 3], [1, 4], [2, 5]]

        for band, indices, sensor in zip(list_of_bands, time_series_indices,
                                         list_sensors):

            def get_band(indices=indices):
                import numpy as np
                data = np.take(self.data, indices, axis=2)
                return data

            setattr(data_container, f"get_{sensor}_band_{band}", get_band)


class custom_numpy_features(data_container):
    """ This class add functions provided by an user.
        and concatenate the results to the original feature stack"""
    def __init__(self,
                 tile_name: str,
                 output_path: str,
                 sensors_params: sensors_params_type,
                 code_path: str,
                 module_name: str,
                 list_functions: List[str],
                 working_dir: Optional[str] = None):
        import sys
        import os
        import importlib
        import types  # solves issues about type and inheritance
        super(custom_numpy_features,
              self).__init__(tile_name, output_path, sensors_params,
                             working_dir)
        if code_path is None:
            raise "For use custom features, the codePath must no be None"
        if not os.path.isdir(code_path):
            raise f"Error: {code_path} is not a correct path"
        sys.path.insert(0, code_path)
        # TODO: check if module is a module and func a function
        mod = importlib.import_module(module_name)
        # Function can be multiple
        self.fun_name_list = []

        if list_functions is not None and len(list_functions) != 0:
            self.fun_name_list = list_functions
            for fun_name in self.fun_name_list:
                func = getattr(mod, fun_name)
                setattr(self, fun_name, types.MethodType(func, data_container))

    def process(self, data):
        """ This function apply a set of functions to data"""
        import numpy as np

        self.data = data
        new_labels = []
        try:
            for i, fun_name in enumerate(self.fun_name_list):
                func = getattr(self, fun_name)
                feat, labels = func()
                # feat is a numpy array with shape [row, cols, bands]
                # check if user defined well labels
                if len(labels) != feat.shape[2]:
                    labels = [
                        f"custFeat_{i+1}_b{j+1}" for j in range(feat.shape[2])
                    ]
                new_labels += labels
                self.data = np.concatenate((self.data, feat), axis=2)
            return self.data, new_labels
        except Exception as e:
            print(f"Error during custom_features computation : {fun_name}")
            print(e)
