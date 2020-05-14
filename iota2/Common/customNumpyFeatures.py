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
import os
import logging
from typing import Dict, Union, List, Optional
from rasterio.plot import reshape_as_image
from iota2.Common import FileUtils as fu
# Only for typing
import otbApplication

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

        # self.data = None  # empty attribute to address data
        self.data = None
        print(f"ID de SELF data_container: {id(self)}")

        # Get the first tile, all the tiles must come from same sensor

        def compute_reflectances_indices_after_gapfilling(sensor, bands):
            _, dates = sensor.write_interpolation_dates_file(write=False)
            indices = []
            for i, band in enumerate(bands):
                # print(i, band)
                ind = [i + len(bands) * x for x, _ in enumerate(dates)]

                indices.append(ind)
            return indices

        def compute_indices_after_gapfilling(sensor,
                                             spectral_bands,
                                             spectral_indices,
                                             shift=0):
            _, dates = sensor.write_interpolation_dates_file(write=False)
            indices = []
            for i, _ in enumerate(spectral_bands):
                ind = [
                    shift + i + len(spectral_bands) * x
                    for x, _ in enumerate(dates)
                ]
                indices.append(ind)

            len_spectral_band = len(dates) * len(spectral_bands) + shift
            for i, _ in enumerate(spectral_indices):
                spect_begin = len_spectral_band + i * len(dates)
                ind = range(spect_begin, spect_begin + len(dates))
                indices.append(ind)

            new_shift = (len(dates) * len(spectral_bands) +
                         len(dates) * len(spectral_indices) + shift)
            return indices, new_shift

        # From this tile get enabled sensors
        sensor_tile_container = sensors_container(tile_name, working_dir,
                                                  output_path,
                                                  **sensors_parameters)

        list_of_bands = []
        time_series_indices = []
        list_sensors = []
        shift = 0
        for sensor in sensor_tile_container.get_enabled_sensors():
            if sensor.name != "userFeatures":
                spectral_bands = sensor.stack_band_position
                spectral_indices = sensor.features_names_list
                # tmp_indices = compute_indices_after_gapfilling(sensor, bands)
                tmp_indices, shift = compute_indices_after_gapfilling(
                    sensor, spectral_bands, spectral_indices, shift)

                list_of_bands += spectral_bands
                list_of_bands += spectral_indices
                time_series_indices += tmp_indices
                list_sensors += [sensor.name] * (len(spectral_bands) +
                                                 len(spectral_indices))
            else:
                LOGGER.info("userFeatures sensor is not supported")
        # TODO: handle user feature selection

        for band, indices, sensor in zip(list_of_bands, time_series_indices,
                                         list_sensors):

            def get_band(indices=indices):
                import numpy as np
                current_self = self
                # print(
                #     f"********* id(self.data): {id(self.data)}, type(data) : {type(self.data)}, id(self) : {id(self)}, id(get_band) : {id(get_band)}"
                # )
                print(
                    f"********* id(current_self.data): {id(current_self.data)}, type(data) : {type(current_self.data)}, id(current_self) : {id(current_self)}, id(get_band) : {id(get_band)}"
                )
                data = np.take(self.data, indices, axis=2)
                return data

            setattr(data_container, f"get_{sensor}_{band}", get_band)

            # print(f"self {self}")
            # print(f"dir(self) {dir(self)}")
            # setattr(self.__class__, f"get_{sensor}_{band}", get_band)


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
        """
        Parameters
        ----------
        tile_name: str
            The tile name, mandatory to get the sensor container
        output_path: str
        sensors_param:
            A dictionary containing all requiered information to instanciate
            the enabled sensors
        module_name: str
            The user provided python code. The full path to a file is requiered
        list_functions: list[str]
            A lisf of function name that will be applied
        working_dir: optional (str)
            Use to store temporary data
        """
        import types  # solves issues about type and inheritance
        super(custom_numpy_features,
              self).__init__(tile_name, output_path, sensors_params,
                             working_dir)
        print(
            f"/////////////////// ID de SELF custom_numpy_features: {id(self)}"
        )

        def check_import(module_path: str):
            """ This fonction check if the user provided module can be 
            imported"""
            import importlib

            spec = importlib.util.spec_from_file_location(
                module_path.split(os.sep)[-1].split('.')[0], module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module

        mod = check_import(module_name)
        self.fun_name_list = []

        if list_functions is not None and len(list_functions) != 0:
            self.fun_name_list = list_functions
            for fun_name in self.fun_name_list:
                func = getattr(mod, fun_name)
                setattr(self, fun_name, types.MethodType(func, data_container))

    def process(self, data):
        """ 
        This function apply a set of functions to data
        Parameters
        ----------
        data: numpy array
            the numpy array to process
        Return
        ------
        data: numpy array
            the original numpy array concatenated with the custom features processed
        new_labels: list[str]
            the labels corresponding to the features computed
        """
        import numpy as np
        print(f"+++++++ ID de data AVANT MAJ: {id(self.data)}")
        self.data = data
        print(f"+++++++ ID de data APRES MAJ: {id(self.data)}")

        new_labels = []
        try:
            for i, fun_name in enumerate(self.fun_name_list):
                func = getattr(self, fun_name)
                feat, labels = func()
                # ensure that feat is fill with number
                if not np.isfinite(feat).all():
                    raise ValueError("Error during custom_features computation"
                                     " np.nan or infinite founded."
                                     " Check if there is no division by zero")
                # feat is a numpy array with shape [row, cols, bands]

                # handle the case when return a 1d feature
                if len(feat.shape) == 2:
                    feat = feat[:, :, None]
                elif len(feat.shape) != 3:
                    raise ValueError(
                        "The return feature must be a 2d or 3d array")
                # check if user defined well labels
                if len(labels) != feat.shape[2]:
                    labels = [
                        f"custFeat_{i+1}_b{j+1}" for j in range(feat.shape[2])
                    ]
                new_labels += labels
                #     self.data = np.concatenate((self.data, feat), axis=2)
                # return self.data, new_labels
                stack = np.concatenate((self.data, feat), axis=2)
            return stack, new_labels

        except Exception as err:
            print(f"Error during custom_features computation")
            raise err


def compute_custom_features(tile: str,
                            output_path: str,
                            sensors_parameters: sensors_params_type,
                            module_path: str,
                            list_functions: List[str],
                            otb_pipeline: otbApplication,
                            feat_labels: List[str],
                            path_wd: str,
                            chunk_size_mode: str,
                            targeted_chunk: int,
                            number_of_chunks: int,
                            chunk_size_x: int,
                            chunk_size_y: int,
                            write_mode: Optional[bool] = False,
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
    output_name = None
    if write_mode:
        opath = os.path.join(output_path, "customF")
        if not os.path.exists(opath):
            os.mkdir(opath)
        output_name = os.path.join(opath, f"{tile}_chunk_{targeted_chunk}.tif")
    # print(f"------> avant le pipeline : {cust.data} <------")
    print(
        f"------> ID AVANT le pipeline : {id(cust.data)} <------ targeted_chunk : {targeted_chunk}"
    )
    # print(f"+++++++++++ id(cust)={id(cust)}")

    (feat_array, new_labels, out_transform, _, _,
     otbimage) = insert_external_function_to_pipeline(
         otb_pipeline=otb_pipeline,
         labels=labels_features_name,
         working_dir=path_wd,
         chunk_size_mode=chunk_size_mode,
         function=function_partial,
         output_path=output_name,
         targeted_chunk=targeted_chunk,
         number_of_chunks=number_of_chunks,
         chunk_size_x=chunk_size_x,
         chunk_size_y=chunk_size_y,
         ram=128,
     )
    # print(
    #     f"------> apres le pipeline : {cust.data.shape} <------ targeted_chunk : {targeted_chunk}"
    # )
    # print(
    #     f"------> ID apres le pipeline : {id(cust.data)} <------ targeted_chunk : {targeted_chunk}"
    # )
    # feat_array is an raster array with shape
    # [band, rows, cols] but otb requires [rows, cols, bands]
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
