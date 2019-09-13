#!/usr/bin/env python3
#-*- coding: utf-8 -*-

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

import os
import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def train_autoContext_parameters(iota2_directory, regionField):
    """
    Parameters
    ----------
    iota2_directory : string
        path to iota²'s running directory
    regionField : string
        region's field
    Return
    ------
    parameters : list
    """
    from Common.FileUtils import FileSearch_AND
    from Common.FileUtils import sortByFirstElem
    from Learning.TrainingCmd import config_model

    pathToModelConfig = os.path.join(iota2_directory, "config_model", "configModel.cfg")
    configModel = config_model(iota2_directory, regionField)
    if not os.path.exists(pathToModelConfig):
        with open(pathToModelConfig, "w") as configFile:
            configFile.write(configModel)

    sample_selection_directory = os.path.join(iota2_directory, "samplesSelection")

    tile_position = 0
    model_position = 3
    seed_position = 5

    parameters = []

    sample_sel_content = FileSearch_AND(sample_selection_directory, False, "_samples_region_", "selection.sqlite")
    selection_models = [((c_file.split("_")[model_position],
                          int(c_file.split("_")[seed_position])),
                          c_file) for c_file in sample_sel_content]
    selection_models = sortByFirstElem(selection_models)

    for (model_name, seed_num), selection_files in selection_models:
        tiles = [selection_file.split("_")[tile_position] for selection_file in selection_files]

        assert len(set(tiles)) == len(selection_files)

        tiles_slic = []
        for tile in tiles :
            tiles_slic.append(FileSearch_AND(os.path.join(iota2_directory,
                                             "features", tile, "tmp"),
                                             True, "SLIC", ".tif")[0])
        parameters.append({"model_name": model_name,
                           "seed": seed_num,
                           "list_selection": ["{}.sqlite".format(os.path.join(sample_selection_directory, selection_file)) for selection_file in selection_files],
                           "list_tiles": tiles,
                           "list_slic":tiles_slic})
    return parameters


def choosable_annual_pixels(classification_raster, validity_raster, region_mask, validity_threshold):
    """mask pixels in order to choose annual ones according to clouds, region...

    Parameters
    ----------
    classification_raster : string
        path to classification raster
    validity_raster : string
        path to vilidity raster
    region_mask : string
        path to region mask raster
    validity_threshold : int
        cloud threashold to pick up samples

    Return
    ------
    tuple (mask, (Ox, Oy, spx, spy))
        mask : numpy.array
            numpy array where non 0 are choosable pixels
        Ox : float
            x origin
        Oy : float
            y origin
        spx : float
            x spacing
        spy : float
            y spacing
    """
    from Common.OtbAppBank import CreateClassificationMapRegularization
    from Common.OtbAppBank import CreateBandMathApplication
    from Common.OtbAppBank import CreateSuperimposeApplication

    roi_classif, _ = CreateSuperimposeApplication({"inr": region_mask,
                                                "inm": classification_raster,
                                                "interpolator": "nn"})
    roi_classif.Execute()
    roi_validity, _ = CreateSuperimposeApplication({"inr": region_mask,
                                                 "inm": validity_raster,
                                                 "interpolator": "nn"})
    roi_validity.Execute()
    classif_reg = CreateClassificationMapRegularization({"io.in": roi_classif,
                                                         "ip.undecidedlabel": 0})
    classif_reg.Execute()
    mask_dummy = CreateBandMathApplication({"il": [region_mask],
                                            "exp": "im1b1"})
    mask_dummy.Execute()
    valid = CreateBandMathApplication({"il": [roi_validity, classif_reg],
                                       "exp": "im1b1>{}?im2b1:0".format(validity_threshold)})
    valid.Execute()
    choosable = CreateBandMathApplication({"il": [valid, mask_dummy],
                                           "out" : "/work/OT/theia/oso/arthur/TMP/val_mask.tif",
                                           "exp": "im1b1*(im2b1>=1?1:0)"})
    choosable.Execute()
    choosable.ExecuteAndWriteOutput()
    oy, ox = choosable.GetImageOrigin("out")
    spx, spy = choosable.GetImageSpacing("out")
    return choosable.GetImageAsNumpyArray("out"), (ox, oy, spx, spy)


def move_annual_samples_from_array(samples_position, target_label, dataField,
                                   samples_number, array, ox, oy, spx, spy):
    """
    """
    import numpy as np
    import random
    from osgeo import ogr

    x_coords, y_coords = np.where(array==target_label)
    samples_number = samples_number if len(y_coords) > samples_number else len(y_coords)

    geo_coordinates = []
    for y_coord, x_coord in zip(y_coords, x_coords):
        x_geo = (ox + spx) - spx * (x_coord + 1)
        y_geo = (oy + spy) - spy * (y_coord + 1)

        geo_coordinates.append((x_geo, y_geo))

    random_coords = random.sample(geo_coordinates, samples_number)

    #seek and destroy samples
    driver = ogr.GetDriverByName("SQLite")
    dataSource = driver.Open(samples_position, 1)
    layer = dataSource.GetLayer()
    for feature in layer:
        if feature.GetField(dataField) == target_label:
            layer.DeleteFeature(feature.GetFID())
    # add new samples according to random_coords
    for x_geo, y_geo in random_coords:
        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetField(dataField, int(target_label))
        point = ogr.CreateGeometryFromWkt("POINT({} {})".format(y_geo, x_geo))
        feature.SetGeometry(point)
        layer.CreateFeature(feature)
        feature = None
    dataSource = None


def move_annual_samples_position(samples_position, dataField, annual_labels,
                                 classification_raster, validity_raster,
                                 region_mask, validity_threshold):
    """
    Parameters
    ----------
    samples_position : string
        path to a vector file containing points, representing samples' positions
    dataField : string
        data field in vector
    annual_labels : list
        list of annual labels
    classification_raster : string
        path to classification raster
    validity_raster : string
        path to vilidity raster
    region_mask : string
        path to region mask raster
    validity_threshold : int
        cloud threshold to pick up samples
    """
    import collections
    from Common.FileUtils import getFieldElement

    annual_labels = map(int, annual_labels)
    class_repartition = getFieldElement(samples_position, driverName="SQLite",
                                        field=dataField, mode="all", elemType="int")
    class_repartition = collections.Counter(class_repartition)

    mask_array, (ox, oy, spx, spy) = choosable_annual_pixels(classification_raster,
                                                             validity_raster, region_mask,
                                                             validity_threshold)
    for annual_label in annual_labels:
        if annual_label in class_repartition:
            samples_number = class_repartition[annual_label]
            move_annual_samples_from_array(samples_position, annual_label,
                                           dataField, samples_number, mask_array,
                                           ox, oy, spx, spy)
        else:
            continue

def train_autoContext(parameter_dict, config_path, RAM=128, WORKING_DIR=None, LOGGER=logger):
    """launch autoContext training

    Parameters
    ----------
    parameter_dict : dict
        dictionnary containing autoContext's input parameters
        {"model_name": string,
         "seed": integer,
         "list_selection": list,
         "list_tiles": list,
         "list_slic": list}
    config_path : string
        path to the configuration file
    RAM : integer
        available ram
    WORKING_DIR : string
        path to store temporary data
    LOGGER : logging
        root logger
    """
    import shutil
    from Sampling import GenAnnualSamples
    from Common.GenerateFeatures import generateFeatures
    from Common import ServiceConfigFile as SCF
    from Common.OtbAppBank import CreateTrainAutoContext
    from Common.FileUtils import ensure_dir
    from Common.FileUtils import FileSearch_AND

    cfg = SCF.serviceConfigFile(config_path)

    tiles = parameter_dict["list_tiles"]
    model_name = parameter_dict["model_name"]
    seed_num = parameter_dict["seed"]
    slic = parameter_dict["list_slic"]
    data_ref = parameter_dict["list_selection"]
    field = cfg.getParam("chain", "dataField").lower()
    iota2_run = cfg.getParam("chain", "outputPath")

    dataField = cfg.getParam("chain", "dataField")
    annual_labels = cfg.getParam("argTrain", "annualCrop")

    features = []
    dependencies = []
    for tile in tiles :
       features_tile, feat_labels, dep = generateFeatures(WORKING_DIR, tile, cfg)
       features_tile.Execute()
       features.append(features_tile)
       dependencies.append(dep)

    models_path = os.path.join(iota2_run, "model")
    model_path = os.path.join(models_path, "model_{}_seed_{}".format(model_name, seed_num))
    ensure_dir(model_path)

    if WORKING_DIR is None:
        tmp_dir = os.path.join(model_path, "tmp")
    else :
        tmp_dir = os.path.join(WORKING_DIR, "model_{}_seed_{}_tmp".format(model_name, seed_num))
    ensure_dir(tmp_dir)

    #~ cropMix sampling
    if cfg.getParam("argTrain", "cropMix") and cfg.getParam("argTrain", "samplesClassifMix"):
        source_dir = cfg.getParam("argTrain", "annualClassesExtractionSource")
        val_threshold = cfg.getParam("argTrain", "validityThreshold")
        classification_raster = FileSearch_AND(os.path.join(source_dir, "final"),
                                                   True, "Classif_Seed_0.tif")[0]
        validity_raster = FileSearch_AND(os.path.join(source_dir, "final"),
                                         True, "PixelsValidity.tif")[0]
        for tile, ref in zip(tiles, data_ref):
            region_mask = FileSearch_AND(os.path.join(iota2_run, "shapeRegion"),
                                         True, "region_{}_{}.tif".format(model_name.split("f")[0], tile))[0]
            move_annual_samples_position(ref, dataField, annual_labels,
                                         classification_raster, validity_raster,
                                         region_mask, val_threshold)

    train_autoContext = CreateTrainAutoContext({"il" : features,
                                                "inseg": slic,
                                                "tmpdir": "{}/".format(tmp_dir),
                                                "refdata": data_ref,
                                                "field": field,
                                                "out": "{}/".format(model_path),
                                                "ram": str(0.1 * RAM)})
    LOGGER.info("Start training autoContext, produce model {}, seed {}".format(model_name, seed_num))
    train_autoContext.ExecuteAndWriteOutput()
    LOGGER.info("training autoContext DONE")
    shutil.rmtree(tmp_dir)