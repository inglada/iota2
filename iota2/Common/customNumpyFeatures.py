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
""" This module allow to use python function in an OTB pipeline"""
import logging
from typing import Dict, Union, List, Optional
from rasterio.plot import reshape_as_image
from iota2.Common import FileUtils as fu
LOGGER = logging.getLogger(__name__)

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
                 module_name: str,
                 list_functions: List[str],
                 working_dir: Optional[str] = None):
        import os
        import types  # solves issues about type and inheritance
        super(custom_numpy_features,
              self).__init__(tile_name, output_path, sensors_params,
                             working_dir)

        def check_import(module_path):
            import importlib

            spec = importlib.util.spec_from_file_location(
                module_path.split(os.sep)[-1].split('.')[0], module_path)
            print(spec)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print(dir(module))
            return module

        mod = check_import(module_name)
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
            print(f"Error during custom_features computation")
            print(e)


def compute_custom_features(tile,
                            output_path,
                            sensors_parameters,
                            module_path,
                            list_functions,
                            otb_pipeline,
                            feat_labels,
                            path_wd,
                            chunk_size_mode,
                            targeted_chunk,
                            number_of_chunks,
                            chunk_size_x,
                            chunk_size_y,
                            logger=LOGGER):
    """
    This function apply a list of function to an otb pipeline data and
    return an otbimage object.
    Parameters
    ----------

    Return
    ------

    """
    from iota2.Common.rasterUtils import insert_external_function_to_pipeline
    from functools import partial

    cust = custom_numpy_features(tile, output_path, sensors_parameters,
                                 module_path, list_functions)
    function_partial = partial(cust.process)
    labels_features_name = ""
    # TODO : how to feel labels_features_name ?
    # The output path is empty to ensure the image was not writed
    (feat_array, new_labels, out_transform, _, _,
     otbimage) = insert_external_function_to_pipeline(
         otb_pipeline=otb_pipeline,
         labels=labels_features_name,
         working_dir=path_wd,
         chunk_size_mode=chunk_size_mode,
         function=function_partial,
         targeted_chunk=targeted_chunk,
         number_of_chunks=number_of_chunks,
         chunk_size_x=chunk_size_x,
         chunk_size_y=chunk_size_y,
         ram=128,
     )
    # rasterio shape [bands, row, cols] OTB shape [row, cols, bands]
    # use rasterio reshape_as_image function to move axis
    # otbimage["array"] = reshape_as_image(feat_array)
    # logger.debug("Numpy image inserted in otb pipeline: "
    #              f"{fu.memory_usage_psutil()} MB")
    # # get the chunk size
    # size = otbimage["array"].shape
    # # get the chunk origin
    # origin = out_transform * (0, 0)
    # # add a demi pixel size to origin
    # # offset between rasterio (gdal) and OTB
    # otbimage["origin"].SetElement(0, origin[0] + (otbimage["spacing"][0] / 2))
    # otbimage["origin"].SetElement(1, origin[1] + (otbimage["spacing"][1] / 2))
    # # Set buffer image region
    # # Mandatory to keep the projection in OTB pipeline
    # otbimage["region"].SetIndex(0, 0)
    # otbimage["region"].SetIndex(1, 0)
    # otbimage["region"].SetSize(0, size[1])
    # otbimage["region"].SetSize(1, size[0])
    # # TODO: remove this bandmath and return an OTB image
    # bandmath = otb.Registry.CreateApplication("BandMathX")
    # bandmath.ImportVectorImage("il", otbimage)
    # bandmath.SetParameterString("out", features_raster)
    # bandmath.SetParameterString("exp", "im1")
    # # bandmath.SetParameterString("ram", "200000")
    # all_features = bandmath
    # dep.append(bandmath)
    # dep.append(otbimage)
    # new_labels can never be empty
    crop_otbimage = convert_numpy_array_to_otb_image(otbimage, feat_array,
                                                     out_transform)

    feat_labels += new_labels
    return crop_otbimage, feat_labels


def convert_numpy_array_to_otb_image(otbimage,
                                     array,
                                     out_transform,
                                     logger=LOGGER):
    """
        This function allow to convert a numpy array to an otb image
    Parameters
    ----------
    otbimage : an otb image dictionary
    array : a rasterio array (shape is [bands, row, cols])
    out_transform : the geotransform corresponding to array
    """
    otbimage["array"] = reshape_as_image(array)
    logger.debug("Numpy image inserted in otb pipeline: "
                 f"{fu.memory_usage_psutil()} MB")
    # get the chunk size
    size = otbimage["array"].shape
    # get the chunk origin
    origin = out_transform * (0, 0)
    # add a demi pixel size to origin
    # offset between rasterio (gdal) and OTB
    otbimage["origin"].SetElement(0, origin[0] + (otbimage["spacing"][0] / 2))
    otbimage["origin"].SetElement(1, origin[1] + (otbimage["spacing"][1] / 2))
    # Set buffer image region
    # Mandatory to keep the projection in OTB pipeline
    otbimage["region"].SetIndex(0, 0)
    otbimage["region"].SetIndex(1, 0)
    otbimage["region"].SetSize(0, size[1])
    otbimage["region"].SetSize(1, size[0])
    return otbimage
