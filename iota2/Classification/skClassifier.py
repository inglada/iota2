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
import logging
import os
import numpy as np
from typing import List, Optional, Dict, Union, Tuple
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.preprocessing import StandardScaler
from rasterio.transform import Affine

from iota2.Common.Utils import time_it

sensors_params = Dict[str, Union[str, List[str], int]]

logger = logging.getLogger(__name__)


def merge_sk_classifications(rasters_to_merge: Tuple[List[str], List[str]],
                             mosaic_file: Tuple[str, str],
                             epsg_code: int,
                             working_dir: str,
                             logger=logger) -> None:
    """mosaic rasters

    Parameters
    ----------
    rasters_to_merge_dic : dict
        dictionary containing the two keys 'rasters_list', 'merge_path'
        example :
        [{'rasters_list':[list of raster to mosaic], 'merge_path': output mosaic path}, ...]
    epsg_code : int
        epsg code
    working_dir : str
        working direction
    logger : logging
        root logger
    """
    from iota2.Common.rasterUtils import merge_rasters
    classifications = list(filter(os.path.exists, rasters_to_merge[0]))
    classif_mosaic = mosaic_file[0]
    confidences = list(filter(os.path.exists, rasters_to_merge[1]))
    confidence_mosaic = mosaic_file[1]
    logger.info("creating : {}".format(mosaic_file))
    merge_rasters(classifications, classif_mosaic, epsg_code, working_dir)
    merge_rasters(confidences, confidence_mosaic, epsg_code, working_dir)

    if os.path.exists(classif_mosaic):
        for classif in classifications:
            os.remove(classif)
    if os.path.exists(confidence_mosaic):
        for confidence in confidences:
            os.remove(confidence)


def do_predict(array: np.ndarray,
               model: Union[SVC, RandomForestClassifier, ExtraTreesClassifier],
               scaler: Optional[StandardScaler] = None,
               dtype: Optional[str] = "float") -> np.ndarray:
    """perform scikit-learn prediction

    Parameters
    ----------
    array : np.array
        array of features to predict, shape = (y, x, features)
    model : SVC / RandomForestClassifier / ExtraTreesClassifier
        scikit-learn classifier
    scaler : StandardScaler
        scaler to standardize features
    dtype : str
        output array format

    Return
    ------
    np.array
        predictions
    """
    array_reshaped = array.reshape((array.shape[0] * array.shape[1]),
                                   array.shape[2])
    if scaler is not None:
        predicted_array = model.predict_proba(scaler.transform(array_reshaped))
    else:
        predicted_array = model.predict_proba(array_reshaped)

    predicted_array = predicted_array.reshape(array.shape[0], array.shape[1],
                                              predicted_array.shape[-1])
    return predicted_array.astype(dtype)


def get_class(*args, **kwargs):
    """
    """
    import numpy as np
    return kwargs["labels"][np.argmax(args)]


@time_it
def proba_to_label(proba_map: np.ndarray,
                   out_classif: str,
                   labels: List[int],
                   transform: Affine,
                   epsg_code: int,
                   mask_arr: Optional[np.ndarray] = None) -> np.ndarray:
    """from the prediction probabilities, get the class' label

    Parameters
    ----------
    proba_map: numpy.array
        array of predictions probabilities (one probability for each class)
    out_classif: str
        output classification
    labels: list
        list of class labels
    transform: Affine
        geo transform
    epsg_code: int
        epsg code
    mask_arr: numpy.array
        mask
    """
    import rasterio
    import numpy as np
    from sklearn.preprocessing import binarize

    labels_map = np.apply_along_axis(func1d=get_class,
                                     axis=0,
                                     arr=proba_map,
                                     labels=labels)
    labels_map = labels_map.astype("int32")
    labels_map = np.expand_dims(labels_map, axis=0)
    if mask_arr is not None:
        mask_arr = binarize(mask_arr)
        labels_map = labels_map * mask_arr

    with rasterio.open(out_classif,
                       "w",
                       driver='GTiff',
                       height=labels_map.shape[1],
                       width=labels_map.shape[2],
                       count=labels_map.shape[0],
                       crs="EPSG:{}".format(epsg_code),
                       transform=transform,
                       dtype=labels_map.dtype) as dest:
        dest.write(labels_map)
    return labels_map


def probabilities_to_max_proba(proba_map: np.ndarray,
                               transform: Affine,
                               epsg_code: int,
                               out_max_confidence: Optional[str] = None
                               ) -> np.ndarray:
    """from the prediction probabilities vector, get the max probility

    Parameters
    ----------
    proba_map: numpy.array
        array of probilities
    transform: Affine
        geo transform
    epsg_code: int
        epsg code
    out_max_confidence: str
        output raster path

    Return
    ------
    numpy.array
        confidence
    """
    import rasterio
    import numpy as np
    max_confidence_arr = np.amax(proba_map, axis=0)
    max_confidence_arr = np.expand_dims(max_confidence_arr, axis=0)

    if out_max_confidence:
        with rasterio.open(out_max_confidence,
                           "w",
                           driver='GTiff',
                           height=max_confidence_arr.shape[1],
                           width=max_confidence_arr.shape[2],
                           count=max_confidence_arr.shape[0],
                           crs="EPSG:{}".format(epsg_code),
                           transform=transform,
                           dtype=max_confidence_arr.dtype) as dest:
            dest.write(max_confidence_arr)
    return max_confidence_arr


def predict(mask: str,
            model: str,
            stat: str,
            out_classif: str,
            out_confidence: str,
            out_proba: str,
            working_dir: str,
            tile_name: str,
            sar_optical_post_fusion: bool,
            output_path: str,
            sensors_parameters: sensors_params,
            pixel_type: str,
            number_of_chunks: Optional[int] = None,
            targeted_chunk: Optional[int] = None,
            ram: Optional[int] = 128,
            logger=logger) -> None:
    """perform scikit-learn prediction

    This function will produce 2 rasters, the classification map and the
    confidence map. The confidence map represent the classifier confidence in
    the chosen class.

    Parameters
    ----------
    mask: str
        raster mask path
    model: str
        input model path
    stat: str
        statistics path
    out_classif: str
        output classification raster path
    out_confidence: str
        output confidence raster path
    out_proba: str
        output confidence raster path
    working_dir: str
        path to a working direction to store temporary data
    tile_name: str
        tile's name
    sar_optical_post_fusion: bool
        flag to use post classification sar optical workflow
    output_path: str
        iota2 output path
    sensors_parameters: sensors_params
        sensors description
    pixel_type: str
        output pixel type
    number_of_chunks: int
        The prediction process can be done by strips. This parameter
        set the number of strips
    targeted_chunk: int
        If this parameter is provided, only the targeted strip will be compute (parallelization).
    ram: int
        ram (in mb) available
    logger : logging
        root logger
    """
    import os
    import shutil
    import pickle
    from functools import partial

    from iota2.Common import rasterUtils as rasterU
    from iota2.Common import ServiceConfigFile as serviceConf
    from iota2.Common.GenerateFeatures import generateFeatures
    from iota2.Common.FileUtils import findCurrentTileInString

    mode = "usually" if "SAR.txt" not in model else "SAR"

    if working_dir:
        _, out_classif_name = os.path.split(out_classif)
        _, out_confidence_name = os.path.split(out_confidence)
        out_classif = os.path.join(working_dir, out_classif_name)
        out_confidence = os.path.join(working_dir, out_confidence_name)
        if out_proba:
            _, out_proba_name = os.path.split(out_proba)
            out_proba = os.path.join(working_dir, out_proba_name)

    with open(model, 'rb') as model_file:
        model, scaler = pickle.load(model_file)
    # if hasattr(model, "n_jobs"):
    # model.n_jobs = -1

    if number_of_chunks and targeted_chunk:
        if targeted_chunk > number_of_chunks - 1:
            raise ValueError(
                "targeted_chunk must be inferior to the number of chunks")

    function_partial = partial(do_predict, model=model, scaler=scaler)
    classification_dir = os.path.join(output_path, "classif")
    feat_stack, feat_labels, _ = generateFeatures(
        working_dir,
        tile_name,
        sar_optical_post_fusion=sar_optical_post_fusion,
        output_path=output_path,
        sensors_parameters=sensors_parameters,
        mode=mode)

    logger.info("producing {}".format(out_classif))

    # ~ sk-learn provide only methods 'predict' and 'predict_proba', no proba_max.
    # ~ Then we have to compute the full probability vector to get the maximum
    # ~ confidence and generate the confidence map

    predicted_proba, _, transform, epsg, masks = rasterU.apply_function(
        feat_stack,
        feat_labels,
        working_dir,
        function_partial,
        out_proba,
        mask=mask,
        mask_value=0,
        chunk_size_mode="split_number",
        number_of_chunks=number_of_chunks,
        targeted_chunk=targeted_chunk,
        output_number_of_bands=len(model.classes_),
        ram=ram)
    logger.info("predictions done")
    if len(masks) > 1:
        raise ValueError("Only one mask is expected")

    if targeted_chunk is not None:
        out_classif = out_classif.replace(
            ".tif", "_SUBREGION_{}.tif".format(targeted_chunk))
        out_confidence = out_confidence.replace(
            ".tif", "_SUBREGION_{}.tif".format(targeted_chunk))

    proba_to_label(predicted_proba, out_classif, model.classes_, transform,
                   epsg, masks[0])
    probabilities_to_max_proba(predicted_proba, transform, epsg,
                               out_confidence)

    if working_dir:
        shutil.copy(out_classif, classification_dir)
        shutil.copy(out_confidence, classification_dir)
        os.remove(out_classif)
        os.remove(out_confidence)
        if out_proba:
            shutil.copy(out_proba, classification_dir)
            os.remove(out_proba)
