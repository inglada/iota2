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
from typing import List, Optional, Dict

from iota2.Common.Utils import time_it

logger = logging.getLogger(__name__)


def merge_sk_classifications(rasters_to_merge_dic:List[Dict[str, str]],
                             epsg_code: int,
                             working_dir: str,
                             logger=logger) -> None:
    """
    """
    from iota2.POC.rasterUtils import merge_rasters

    for element in rasters_to_merge_dic:
        logger.info("creating : {}".format(element["merge_path"]))
        merge_rasters(element["rasters_list"],
                      element["merge_path"],
                      epsg_code,
                      working_dir)


def sk_classifications_to_merge(iota2_classif_directory: str) -> List[Dict[str, List[str]]]:
    """feed function

    Parameters
    ----------
    iota2_classif_directory : str
        iota2's classification directory

    TODO : manage probability map
    """
    import os
    from iota2.Common.FileUtils import FileSearch_AND
    from iota2.Common.FileUtils import sortByFirstElem

    model_pos_classif = 3
    seed_pos_classif = 5
    tile_pos_classif = 1

    model_pos_confidence = 2
    seed_pos_confidence = 5
    tile_pos_confidence = 0

    rasters_to_merge = []

    classifications = FileSearch_AND(iota2_classif_directory,
                                     True,
                                     "Classif", "_model_", "_seed_", "_SUBREGION_", ".tif")
    classif_to_merge = []
    for classification in classifications:
        model = os.path.basename(classification).split("_")[model_pos_classif]
        seed = os.path.basename(classification).split("_")[seed_pos_classif]
        tile_name = os.path.basename(classification).split("_")[tile_pos_classif]
        classif_to_merge.append(((model, seed, tile_name), classification))
    classif_to_merge = sortByFirstElem(classif_to_merge)

    confidences = FileSearch_AND(iota2_classif_directory,
                                 True,
                                 "_model_", "confidence", "_seed_", "_SUBREGION_", ".tif")
    confidences_to_merge = []
    for confidence in confidences:
        model = os.path.basename(confidence).split("_")[model_pos_confidence]
        seed = os.path.basename(confidence).split("_")[seed_pos_confidence]
        tile_name = os.path.basename(confidence).split("_")[tile_pos_confidence]
        confidences_to_merge.append(((model, seed, tile_name), confidence))
    confidences_to_merge = sortByFirstElem(confidences_to_merge)

    if not len(classif_to_merge) == len(confidences_to_merge):
        raise ValueError("number of classification to merge : {} is different than number of confidence to merge : {}".format(len(classif_to_merge), len(confidences_to_merge)))
    for (model_name, seed_num, tile_name), classif_list in classif_to_merge:
        output_dir, _ = os.path.split(classif_list[0])
        classif_name = "_".join(["Classif", tile_name, "model", model_name, "seed", seed_num]) + ".tif"
        rasters_to_merge.append({"rasters_list": classif_list,
                                 "merge_path": os.path.join(output_dir, classif_name)})
    for (model_name, seed_num, tile_name), confidence_list in confidences_to_merge:
        output_dir, _ = os.path.split(confidence_list[0])
        confidence_name = "_".join([tile_name, "model", model_name, "confidence", "seed", seed_num]) + ".tif"
        rasters_to_merge.append({"rasters_list": confidence_list,
                                 "merge_path": os.path.join(output_dir, confidence_name)})
    return rasters_to_merge


def do_predict(array, model, dtype="float"):
    """
    """
    array_reshaped = array.reshape((array.shape[0] * array.shape[1]), array.shape[2])
    predicted_array = model.predict_proba(array_reshaped)
    predicted_array = predicted_array.reshape(array.shape[0],
                                              array.shape[1],
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
                   transform,
                   epsg_code: int,
                   mask_arr: Optional[np.ndarray] = None) -> np.ndarray:
    """
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
                               transform,
                               epsg_code: int,
                               out_max_confidence: str) -> np.ndarray:
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
            number_of_chunks: Optional[int] = None, targeted_chunk: Optional[int] = None,
            ram: Optional[int] = 128, logger=logger) -> None:
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

    # ~ if hasattr(model, "n_jobs"):
        # ~ model.n_jobs = -1

    if number_of_chunks and targeted_chunk:
        if targeted_chunk > number_of_chunks - 1:
            raise ValueError("targeted_chunk must be inferior to the number of chunks")

    function_partial = partial(do_predict, model=model)

    cfg = serviceConf.serviceConfigFile(configuration_file)
    tile_name = findCurrentTileInString(mask, cfg.getParam("chain", "listTile").split(" "))
    classification_dir = os.path.join(cfg.getParam("chain", "outputPath"), "classif")
    feat_stack, feat_labels, _ = generateFeatures(working_dir, tile_name, cfg)

    logger.info("producing {}".format(out_classif))

    # ~ sk-learn provide only methods 'predict' and 'predict_proba', no proba_max.
    # ~ Then we have to compute the full probability vector to get the maximum
    # ~ confidence and generate the confidence map

    predicted_proba, _, transform, epsg, masks = rasterU.apply_function(feat_stack,
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

    # ~ print("predicted_proba.shape : {}".format(predicted_proba))
    if targeted_chunk is not None:
        out_classif = out_classif.replace(".tif", "_SUBREGION_{}.tif".format(targeted_chunk))
        out_confidence = out_confidence.replace(".tif", "_SUBREGION_{}.tif".format(targeted_chunk))

    proba_to_label(predicted_proba, out_classif,
                   model.classes_, transform,
                   epsg, masks[0])
    probabilities_to_max_proba(predicted_proba, transform, epsg, out_confidence)

    if working_dir:
        shutil.copy(out_classif, classification_dir)
        shutil.copy(out_confidence, classification_dir)
        os.remove(out_classif)
        os.remove(out_confidence)
        if out_proba:
            shutil.copy(out_proba, classification_dir)
            os.remove(out_proba)
