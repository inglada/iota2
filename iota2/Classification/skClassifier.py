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
import numpy as np
from typing import List
from functools import wraps
from rasterio import Affine

from iota2.Common.Utils import time_it

logger = logging.getLogger(__name__)


def do_predict(array, model, dtype="float"):
    """
    """
    import numpy as np
    # ~ TODO : is there a more effective way to invoke model.predict_proba ?

    def wrapper(*args, **kwargs):
        return model.predict_proba([args[0]])

    predicted_array = np.apply_along_axis(func1d=wrapper, axis=-1, arr=array)
    predicted_array = np.reshape(predicted_array, (predicted_array.shape[0],
                                                   predicted_array.shape[1],
                                                   predicted_array.shape[-1]))
    return predicted_array.astype(dtype)


def get_class(*args, **kwargs):
    """
    """
    import numpy as np
    return kwargs["labels"][np.argmax(args)]


def proba_to_label(proba_map: np.ndarray,
                   out_classif: str,
                   labels: List[int],
                   transform: Affine,
                   epsg_code: int):
    """
    """
    import rasterio
    import numpy as np
    labels_map = np.apply_along_axis(func1d=get_class,
                                     axis=0,
                                     arr=proba_map,
                                     labels=labels)
    labels_map = labels_map.astype("int32")
    labels_map = np.expand_dims(labels_map, axis=0)

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
                               out_max_confidence: str):
    """
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


def predict(mask: str, model: str, stat: str, out_classif: str, out_confidence: str,
            out_proba: str, working_dir: str, configuration_file: str, pixel_type: str,
            ram: int, logger=logger):
    """
    """
    import os
    import shutil
    import pickle
    from functools import partial

    from iota2.POC import rasterUtils as rasterU
    from iota2.Common import ServiceConfigFile as serviceConf
    from iota2.Common.GenerateFeatures import generateFeatures
    from iota2.Common.FileUtils import findCurrentTileInString

    with open(model, 'rb') as model_file:
        model = pickle.load(model_file)

    function_partial = partial(do_predict, model=model)

    cfg = serviceConf.serviceConfigFile(configuration_file)
    tile_name = findCurrentTileInString(mask, cfg.getParam("chain", "listTile").split(" "))
    classification_dir = os.path.join(cfg.getParam("chain", "outputPath"), "classif")
    feat_stack, feat_labels, _ = generateFeatures(working_dir, tile_name, cfg)

    logger.info("producing {}".format(out_classif))
    # ~ TODO :
    # ~ sk-learn provide only methods 'predict' and 'predict_proba', no proba_max.
    # ~ Then we have to compute the full probability vector to get the maximum
    # ~ confidence and generate the maximum confidence map

    out_proba=out_confidence.replace(".tif", "_PROBA.tif")

    predicted_proba, _, transform, epsg = rasterU.apply_function(feat_stack,
                                                                 feat_labels,
                                                                 working_dir,
                                                                 function_partial,
                                                                 out_proba,
                                                                 chunck_size_x=30,
                                                                 chunck_size_y=30,
                                                                 ram=ram)
    logger.info("predictions done")
    proba_to_label(predicted_proba, out_classif, model.classes_, transform, epsg)
    probabilities_to_max_proba(predicted_proba, transform, epsg, out_confidence)

    if working_dir:
        shutil.copy(out_classif, classification_dir)
        shutil.copy(out_confidence, classification_dir)
        shutil.copy(out_proba, classification_dir)
        os.remove(out_classif)
        os.remove(out_confidence)
        os.remove(out_proba)
