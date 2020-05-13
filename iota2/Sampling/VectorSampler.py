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
"""
The Vector Sampler Module
"""
import argparse
import time
import os
import logging
from logging import Logger
import multiprocessing as mp
import shutil
import sqlite3 as lite
from typing import List, Optional, Dict, Union, Tuple, TypeVar
from osgeo import ogr
import otbApplication as otb

from iota2.Common import FileUtils as fu
from iota2.Sampling.VectorFormatting import split_vector_by_region
from iota2.Common.OtbAppBank import executeApp
from iota2.Common.customNumpyFeatures import compute_custom_features

LOGGER = logging.getLogger(__name__)
otb_app_type = TypeVar('otbApplication')
# in order to avoid issue 'No handlers could be found for logger...'
LOGGER.addHandler(logging.NullHandler())
sensors_params_type = Dict[str, Union[str, List[str], int]]


def get_vectors_to_sample(iota2_formatting_dir: str,
                          ds_fusion_sar_opt: Optional[bool] = False
                          ) -> List[Dict[str, str]]:
    """
    get vectors to sample
    IN :
        iota2_formatting_dir : str
            path to shapefiles
        ds_fusion_sar_opt : bool
            activate sar mode
    OUT:
        List of dictionary containing all shapefiles
    """
    formatting_tiles = fu.FileSearch_AND(iota2_formatting_dir, True, ".shp")

    #  parameters generation
    tiles_vectors = [{"usually": vector} for vector in formatting_tiles]

    # parameters dedicated to SAR
    tiles_vectors_sar = [{"SAR": vector} for vector in formatting_tiles]

    tiles_vectors_to_sample = tiles_vectors

    # if we want to have SAR classification and Optical classification belong
    # we have to double the number of parameters in generateSamples
    if ds_fusion_sar_opt:
        tiles_vectors_to_sample = tiles_vectors + tiles_vectors_sar

    return tiles_vectors_to_sample


def get_points_coord_in_shape(in_shape: str, gdal_driver: str) -> List[Tuple]:
    """

    IN:
    in_shape [string] : path to the vector shape containing points
    gdal_driver [string] : gdalDriver of inShape

    OUT:
    allCoord [list of tuple] : coord X and Y of points
    """
    driver = ogr.GetDriverByName(gdal_driver)
    data_source = driver.Open(in_shape, 0)
    layer = data_source.GetLayer()

    all_coord = []
    for feature in layer:
        geom = feature.GetGeometryRef()
        all_coord.append((geom.GetX(), geom.GetY()))
    return all_coord


def get_features_application(train_shape: str,
                             working_directory: str,
                             samples: str,
                             data_field: str,
                             output_path: str,
                             sar_optical_post_fusion: bool,
                             sensors_parameters: sensors_params_type,
                             ram: Optional[int] = 128,
                             mode: Optional[str] = "usually",
                             only_mask_comm: Optional[bool] = False,
                             only_sensors_masks: Optional[bool] = False,
                             custom_features: Optional[bool] = False,
                             module_path: Optional[str] = None,
                             list_functions: Optional[List[str]] = None,
                             force_standard_labels: Optional[bool] = False,
                             number_of_chunks: Optional[int] = 50,
                             targeted_chunk: Optional[int] = None,
                             chunk_size_mode: Optional[str] = "split_number",
                             chunk_size_x: Optional[int] = None,
                             chunk_size_y: Optional[int] = None,
                             concat_mode: Optional[bool] = True,
                             logger: Optional[Logger] = LOGGER
                             ) -> Tuple[otb_app_type, List[otb_app_type]]:
    """
    usage : compute from a stack of data -> gapFilling -> features computation
            -> sampleExtractions
    thanks to OTB's applications'

    IN:
        trainShape [string] : path to a vector shape containing points
        workingDirectory [string] : working directory path
        samples [string] : output sqlite file
        dataField [string] : data's field in trainShape
        tile [string] : actual tile to compute. (ex : T31TCJ)
        output_path [string] : output_path
        onlyMaskComm [bool] :  flag to stop the script after common Mask
                               computation
        onlySensorsMasks [bool] : compute only masks
        customFeatures [bool] : compute custom features
    OUT:
        sampleExtr [SampleExtraction OTB's object]:
    """
    # const
    # seed_position = -1
    from iota2.Common import GenerateFeatures as genFeatures
    from iota2.Sensors.ProcessLauncher import commonMasks

    tile = train_shape.split("/")[-1].split(".")[0].split("_")[0]

    working_directory_features = os.path.join(working_directory, tile)
    c_mask_directory = os.path.join(output_path, "features", tile, "tmp")

    if not os.path.exists(working_directory_features):
        try:
            os.mkdir(working_directory_features)
        except OSError:
            logger.warning(f"{working_directory_features} allready exists")

    (all_features, feat_labels, dep_features) = genFeatures.generate_features(
        working_directory_features,
        tile,
        sar_optical_post_fusion,
        output_path,
        sensors_parameters,
        mode=mode,
        force_standard_labels=force_standard_labels)

    if only_sensors_masks:
        # return AllRefl,AllMask,datesInterp,realDates
        return dep_features[1], dep_features[2], dep_features[3], dep_features[
            4]

    all_features.Execute()
    ref = fu.FileSearch_AND(c_mask_directory, True, "MaskCommunSL.tif")

    if not ref:
        commonMasks(tile, output_path, sensors_parameters)
    ref = fu.FileSearch_AND(c_mask_directory, True, "MaskCommunSL.tif")[0]

    if only_mask_comm:
        return ref

    sample_extr = otb.Registry.CreateApplication("SampleExtraction")
    sample_extr.SetParameterString("ram", str(0.7 * ram))
    sample_extr.SetParameterString("vec", train_shape)
    if not custom_features:
        sample_extr.SetParameterInputImage(
            "in", all_features.GetParameterOutputImage("out"))
    else:
        otbimage, feat_labels = compute_custom_features(
            tile=tile,
            output_path=output_path,
            sensors_parameters=sensors_parameters,
            module_path=module_path,
            list_functions=list_functions,
            otb_pipeline=all_features,
            feat_labels=feat_labels,
            path_wd=working_directory_features,
            targeted_chunk=targeted_chunk,
            number_of_chunks=number_of_chunks,
            chunk_size_x=chunk_size_x,
            chunk_size_y=chunk_size_y,
            chunk_size_mode=chunk_size_mode,
            concat_mode=concat_mode)
        sample_extr.ImportVectorImage("in", otbimage)
    sample_extr.SetParameterString("out", samples)
    sample_extr.SetParameterString("outfield", "list")
    sample_extr.SetParameterStringList("outfield.list.names", feat_labels)
    sample_extr.UpdateParameters()
    sample_extr.SetParameterStringList("field", [data_field.lower()])

    all_dep = [all_features] + dep_features
    return sample_extr, all_dep


def generate_samples_simple(folder_sample: str,
                            working_directory: str,
                            train_shape: str,
                            path_wd: str,
                            data_field: str,
                            region_field: str,
                            output_path: str,
                            runs: int,
                            proj: int,
                            enable_cross_validation: bool,
                            sensors_parameters: sensors_params_type,
                            sar_optical_post_fusion: bool,
                            ram: Optional[int] = 128,
                            w_mode: Optional[bool] = False,
                            folder_features: Optional[str] = None,
                            sample_sel=None,
                            mode: Optional[str] = "usually",
                            custom_features: Optional[bool] = False,
                            module_path: Optional[str] = None,
                            list_functions: Optional[List[str]] = None,
                            force_standard_labels: Optional[bool] = False,
                            number_of_chunks: Optional[int] = 50,
                            targeted_chunk: Optional[int] = None,
                            chunk_size_x: Optional[int] = None,
                            chunk_size_y: Optional[int] = None,
                            chunk_size_mode: Optional[str] = "split_number",
                            concat_mode: Optional[bool] = True,
                            logger: Optional[Logger] = LOGGER) -> None:
    """
    usage : from a strack of data generate samples containing points with
    features


    IN:
    folderSample [string] : output folder
    workingDirectory [string] : computation folder
    trainShape [string] : vector shape (polygons) to sample
    pathWd [string] : working Directory, if different from None
                      enable HPC mode (copy at ending)
    featuresPath [string] : path to all stack
    cfg [string] : configuration file class
    dataField [string] : data's field into vector shape
    testMode [bool] : enable testMode -> iota2tests.py
    testFeatures [string] : path to features allready compute (refl + NDVI ...)
    testFeaturePath [string] : path to the stack of data, without features
    mode : string
        define if we only use SAR data
    OUT:
    samples [string] : vector shape containing points
    """
    from iota2.Sampling.SamplesSelection import prepare_selection
    tile = train_shape.split("/")[-1].split(".")[0].split("_")[0]

    if enable_cross_validation:
        runs = runs - 1
    sample_sel_directory = os.path.join(output_path, "samplesSelection")

    if custom_features:

        samples = os.path.join(
            working_directory,
            train_shape.split("/")[-1].replace(
                ".shp", f"_Samples_{targeted_chunk}.sqlite"))

    else:
        samples = os.path.join(
            working_directory,
            train_shape.split("/")[-1].replace(".shp", "_Samples.sqlite"))
    if mode == "SAR":
        samples = os.path.join(
            working_directory,
            train_shape.split("/")[-1].replace(".shp", "_Samples_SAR.sqlite"))

    if sample_sel:
        sample_selection = sample_sel
    else:
        sample_selection = prepare_selection(sample_sel_directory,
                                             tile,
                                             workingDirectory=None)

    sample_extr, dep_gapsample = get_features_application(
        sample_selection,
        working_directory,
        samples,
        data_field,
        output_path,
        sar_optical_post_fusion,
        sensors_parameters,
        ram,
        mode,
        custom_features=custom_features,
        module_path=module_path,
        list_functions=list_functions,
        force_standard_labels=force_standard_labels,
        number_of_chunks=number_of_chunks,
        targeted_chunk=targeted_chunk,
        chunk_size_mode=chunk_size_mode,
        chunk_size_x=chunk_size_x,
        chunk_size_y=chunk_size_y,
        concat_mode=concat_mode)

    sample_extraction_output = os.path.join(
        folder_sample, os.path.basename(sample_extr.GetParameterValue("out")))
    if not os.path.exists(sample_extraction_output):
        logger.info("--------> Start Sample Extraction <--------")
        logger.info(f"RAM before features extraction :"
                    f" {fu.memory_usage_psutil()} MB")
        print("RAM before features extraction : "
              f"{fu.memory_usage_psutil()} MB")

        multi_proc = mp.Process(target=executeApp, args=[sample_extr])
        multi_proc.start()
        multi_proc.join()
        print("RAM after features extraction :"
              f" {fu.memory_usage_psutil()} MB")
        logger.info("RAM after features extraction :"
                    f" {fu.memory_usage_psutil()} MB")
        logger.info("--------> END Sample Extraction <--------")

        split_vec_directory = os.path.join(output_path, "learningSamples")
        if working_directory:
            split_vec_directory = working_directory
        # split vectors by there regions
        split_vectors = split_vector_by_region(
            in_vect=sample_extr.GetParameterValue("out"),
            output_dir=split_vec_directory,
            region_field=region_field,
            runs=int(runs),
            driver="SQLite",
            proj_in=proj,
            proj_out=proj,
            mode=mode,
            targeted_chunk=targeted_chunk)

        os.remove(sample_extr.GetParameterValue("out"))

    if path_wd:
        for sample in split_vectors:
            shutil.copy(sample, folder_sample)
    if w_mode:
        working_directory_features = os.path.join(folder_features, tile, "tmp")
        if not os.path.exists(working_directory_features):
            try:
                os.makedirs(working_directory_features)
            except OSError:
                logger.warning(f"{working_directory_features} allready exists")


def extract_class(vec_in: str, vec_out: str, target_class: List[str],
                  data_field: str) -> int:
    """
    Extract class
    IN:
        vec_in: str
        vec_out: str
        target_class:List[str]
        data_field: str
    """
    from iota2.Common.Utils import run

    if type(target_class) != type(list()):
        target_class = target_class.data

    where = " OR ".join(
        ["{}={}".format(data_field.lower(), klass) for klass in target_class])
    cmd = (f"ogr2ogr -f 'SQLite' -nln output -where '{where}' "
           f"{vec_out} {vec_in}")
    run(cmd)

    return len(
        fu.getFieldElement(vec_out,
                           driverName="SQLite",
                           field=data_field.lower(),
                           mode="all",
                           elemType="int"))


# def generateSamples_cropMix(folder_sample: str,
def generate_samples_crop_mix(folder_sample: str,
                              working_directory: str,
                              output_path: str,
                              output_path_annual: str,
                              train_shape: str,
                              path_wd: str,
                              annual_crop: List[Union[str, int]],
                              all_class: List[Union[str, int]],
                              data_field: str,
                              folder_feature: str,
                              folder_features_annual: str,
                              enable_cross_validation: bool,
                              runs: int,
                              region_field: str,
                              proj: str,
                              sar_optical_post_fusion: bool,
                              sensors_params: sensors_params_type,
                              ram: Optional[int] = 128,
                              w_mode: Optional[bool] = False,
                              test_mode: Optional[bool] = False,
                              sample_sel: Optional[str] = None,
                              mode: Optional[str] = "usually",
                              year_a: Optional[str] = '2017',
                              year_na: Optional[str] = '2016',
                              custom_features: Optional[bool] = False,
                              module_path: Optional[str] = None,
                              list_functions: Optional[List[str]] = None,
                              force_standard_labels: Optional[bool] = False,
                              number_of_chunks: Optional[int] = 50,
                              targeted_chunk: Optional[int] = None,
                              chunk_size_mode: Optional[str] = "split_number",
                              chunk_size_x: Optional[int] = None,
                              chunk_size_y: Optional[int] = None,
                              logger=LOGGER) -> Union[None, List[str]]:
    """
    usage : from stracks A and B, generate samples containing points
            where annual crop are compute with A
            and non annual crop with B.

    IN:
    folder_sample [string] : output folder
    working_directory [string] : computation folder
    train_shape [string] : vector shape (polygons) to sample
    path_wd [string] : if different from None, enable HPC mode (copy at ending)
    annual_crop [list of string/int] : list containing annual crops
                                       ex : [11,12]
    all_class [list of string/int] : list containing permanant classes
                                     in vector shape ex : [51..]
    data_field [string] : data's field into vector shape
    folder_feature [str] : path to current year features,
    folder_features_annual [str] : path to past year features,
    enable_cross_validation [bool] : enable cross validation,
    runs [int] : number of runs,
    region_field [str] : the region field,
    ram [int] : choose the amount of ram to be used by OTB,
    w_mode [bool] : if true write all temporary files,
    test_mode [bool] : enable testMode -> iota2tests.py,
    sample_sel [str] : provide a shapefile containing points and skip sample
                       selection step,
    mode [str] : choose between "usually" or "SAR"
    year_a [str] : the current year,
    year_na [str] : the past year

    OUT:
    samples [string] : vector shape containing points
    """

    from iota2.Sampling.SamplesSelection import prepare_selection
    if os.path.exists(
            folder_sample + "/" +
            train_shape.split("/")[-1].replace(".shp", "_Samples.sqlite")):
        return None

    data_field = data_field.lower()

    if enable_cross_validation:
        runs = runs - 1

    sample_sel_directory = os.path.join(output_path, "samplesSelection")
    current_tile = (os.path.splitext(os.path.basename(train_shape))[0])

    # filter vector file
    work_dir = sample_sel_directory
    if working_directory:
        work_dir = working_directory

    if sample_sel:
        sample_selection = sample_sel
    else:

        sample_selection = prepare_selection(sample_sel_directory,
                                             current_tile,
                                             workingDirectory=None)

    nonannual_vector_sel = os.path.join(
        work_dir, "{}_nonAnnual_selection.sqlite".format(current_tile))
    annual_vector_sel = os.path.join(
        work_dir, "{}_annual_selection.sqlite".format(current_tile))
    nb_feat_nannu = extract_class(sample_selection, nonannual_vector_sel,
                                  all_class, data_field)
    nb_feat_annu = extract_class(sample_selection, annual_vector_sel,
                                 annual_crop, data_field)

    sample_extr_na = os.path.join(
        work_dir, "{}_nonAnnual_extraction.sqlite".format(current_tile))
    sample_extr_a = os.path.join(
        work_dir, "{}_annual_extraction.sqlite".format(current_tile))

    start_extraction = time.time()
    if nb_feat_nannu > 0:
        na_working_directory = os.path.join(working_directory,
                                            current_tile + "_nonAnnual")
        if not os.path.exists(na_working_directory):
            try:
                os.mkdir(na_working_directory)
            except OSError:

                logger.warning(f"{na_working_directory} allready exists")

        sample_extr_na_app, dep_gapsample_na = get_features_application(
            nonannual_vector_sel,
            na_working_directory,
            sample_extr_na,
            data_field,
            output_path,
            sar_optical_post_fusion,
            sensors_params,
            ram,
            mode,
            custom_features=custom_features,
            module_path=module_path,
            list_functions=list_functions,
            force_standard_labels=force_standard_labels,
            number_of_chunks=number_of_chunks,
            targeted_chunk=targeted_chunk,
            chunk_size_mode=chunk_size_mode,
            chunk_size_x=chunk_size_x,
            chunk_size_y=chunk_size_y)

        multi_proc = mp.Process(target=executeApp, args=[sample_extr_na_app])
        multi_proc.start()
        multi_proc.join()

    if nb_feat_annu > 0:
        a_working_directory = os.path.join(working_directory,
                                           current_tile + "_annual")
        if not os.path.exists(a_working_directory):
            try:
                os.mkdir(a_working_directory)
            except OSError:
                logger.warning(f"{a_working_directory} allready exists")
        sample_extr_a_app, dep_gapsample_a = get_features_application(
            annual_vector_sel,
            a_working_directory,
            sample_extr_a,
            data_field,
            output_path_annual,
            sar_optical_post_fusion,
            sensors_params,
            mode=mode,
            custom_features=custom_features,
            module_path=module_path,
            list_functions=list_functions,
            force_standard_labels=force_standard_labels,
            number_of_chunks=number_of_chunks,
            targeted_chunk=targeted_chunk,
            chunk_size_mode=chunk_size_mode,
            chunk_size_x=chunk_size_x,
            chunk_size_y=chunk_size_y)

        multi_proc = mp.Process(target=executeApp, args=[sample_extr_a_app])
        multi_proc.start()
        multi_proc.join()

    end_extraction = time.time()
    logger.debug(f"Samples Extraction time : "
                 f"{end_extraction - start_extraction} seconds")
    # rename annual fields in order to fit non annual dates
    if os.path.exists(sample_extr_a):
        annual_fields = fu.get_all_fields_in_shape(sample_extr_a, "SQLite")
    if os.path.exists(sample_extr_na):
        non_annual_fields = fu.get_all_fields_in_shape(sample_extr_na,
                                                       "SQLite")
    if os.path.exists(sample_extr_na) and os.path.exists(sample_extr_a):
        if len(annual_fields) != len(non_annual_fields):
            raise Exception(
                "annual data's fields and non annual data's fields can"
                "not fitted")

    if os.path.exists(sample_extr_a):
        driver = ogr.GetDriverByName("SQLite")
        data_source = driver.Open(sample_extr_a, 1)
        if data_source is None:
            raise Exception(f"Could not open {sample_extr_a}")
        layer = data_source.GetLayer()

        # Connection to shapefile sqlite database
        conn = lite.connect(sample_extr_a)

        # Create cursor
        cursor = conn.cursor()

        cursor.execute("PRAGMA writable_schema=1")

        if not os.path.exists(sample_extr_na):
            non_annual_fields = [
                x.replace(year_na, year_a) for x in annual_fields
            ]

        for field_non_a, field_a in zip(non_annual_fields, annual_fields):
            cursor.execute("UPDATE sqlite_master SET SQL=REPLACE(SQL, '" +
                           field_a + "', '" + field_non_a + "') WHERE name='" +
                           layer.GetName() + "'")
        cursor.execute("PRAGMA writable_schema=0")
        conn.commit()
        conn.close()

    # Merge samples
    merge_name = train_shape.split("/")[-1].replace(".shp", "_Samples")

    if (nb_feat_nannu > 0) and (nb_feat_annu > 0):
        fu.mergeSQLite(merge_name, working_directory,
                       [sample_extr_na, sample_extr_a])
    elif nb_feat_nannu > 0 and not nb_feat_annu > 0:
        shutil.copyfile(
            sample_extr_na,
            os.path.join(working_directory, merge_name + ".sqlite"))
    elif not (nb_feat_nannu > 0) and (nb_feat_annu > 0):
        shutil.copyfile(
            sample_extr_a,
            os.path.join(working_directory, merge_name + ".sqlite"))

    if custom_features:
        samples = os.path.join(working_directory,
                               train_shape).split("/")[-1].replace(
                                   ".shp", f"_Samples_{targeted_chunk}.sqlite")
    else:
        samples = os.path.join(
            working_directory,
            train_shape.split("/")[-1].replace(".shp", "_Samples.sqlite"))

    if nb_feat_nannu > 0:
        os.remove(sample_extr_na)
        os.remove(nonannual_vector_sel)

    if nb_feat_annu > 0:
        os.remove(sample_extr_a)
        os.remove(annual_vector_sel)

    if w_mode:
        target_directory = os.path.join(folder_feature, current_tile)
        if not os.path.exists(target_directory):
            try:
                os.mkdir(target_directory)
            except OSError:
                logger.warning(f"{target_directory} allready exists")
            try:
                os.mkdir(os.path.join(target_directory, "tmp"))
            except OSError:
                logger.warning(f"{target_directory}/tmp allready exists")

        from_dir = os.path.join(working_directory, current_tile + "_nonAnnual",
                                current_tile, "tmp")
        to_dir = target_directory + "/tmp"
        if os.path.exists(from_dir):
            fu.updateDirectory(from_dir, to_dir)

        target_directory = folder_features_annual + "/" + current_tile
        if not os.path.exists(target_directory):
            try:
                os.mkdir(target_directory)
            except OSError:
                logger.warning(f"{target_directory} allready exists")
            try:
                os.mkdir(os.path.join(target_directory, "tmp"))
            except OSError:
                logger.warning(f"{target_directory}/tmp allready exists")

        from_dir = os.path.join(working_directory, current_tile + "_annual",
                                current_tile, "tmp")
        to_dir = target_directory + "/tmp"
        if os.path.exists(from_dir):
            fu.updateDirectory(from_dir, to_dir)

    # split vectors by there regions
    split_vec_directory = os.path.join(output_path, "learningSamples")
    if working_directory:
        split_vec_directory = working_directory

    split_vectors = split_vector_by_region(in_vect=samples,
                                           output_dir=split_vec_directory,
                                           region_field=region_field.lower(),
                                           runs=int(runs),
                                           driver="SQLite",
                                           proj_in=proj,
                                           proj_out=proj,
                                           targeted_chunk=targeted_chunk)

    if test_mode:
        return split_vectors
    if path_wd and os.path.exists(samples):
        for sample in split_vectors:
            shutil.copy(sample, folder_sample)
    os.remove(samples)


# def extractROI(raster,
def extract_roi(raster: str,
                current_tile: str,
                path_wd: str,
                output_path: str,
                name: str,
                ref: str,
                test_mode: Optional[bool] = None,
                test_output: Optional[str] = None) -> str:
    """
    usage : extract ROI in raster

    IN:
    raster [string] : path to the input raster
    currentTile [string] : current tile to compute
    output_path [string] : the output path
    path_wd [string] : path to the working directory
    name [string] : output name
    ref [strin] : raster reference use to get it's extent
    test_mode [bool] : activate test mode
    test_output [str] : path to test output data
    OUT:
    raterROI [string] : path to the extracted raster.
    """
    from iota2.Common.Utils import run
    working_directory = output_path + "/learningSamples/"
    if path_wd:
        working_directory = path_wd
    if test_mode:
        working_directory = test_output
    current_tile_raster = ref
    min_x, max_x, min_y, max_y = fu.getRasterExtent(current_tile_raster)
    raster_roi = os.path.join(working_directory,
                              current_tile + "_" + name + ".tif")
    cmd = (f"gdalwarp -of GTiff -te {min_x} {min_y} {max_x} {max_y} "
           f"-ot Byte {raster} {raster_roi}")
    run(cmd)
    return raster_roi


def get_region_model_in_tile(current_tile: str, current_region: str,
                             output_path: str, path_wd: str, ref_img: str,
                             field_region: str, test_mode: bool,
                             test_path: str, test_output_folder: str) -> str:
    """
    usage : rasterize region shape.
    IN:
        currentTile [string] : tile to compute
        currentRegion [string] : current region in tile
        output_path [str] : output path
        pathWd [string] : working directory
        refImg [string] : reference image
        testMode [bool] : flag to enable test mode
        testPath [string] : path to the vector shape
        testOutputFolder [string] : path to the output folder

    OUT:
        rasterMask [string] : path to the output raster
    """
    from iota2.Common.Utils import run
    working_directory = os.path.join(output_path, "learningSamples")
    if path_wd:
        working_directory = path_wd
    name_out = f"Mask_region_{current_region}_{current_tile}.tif"

    if test_mode:
        mask_shp = test_path
        working_directory = test_output_folder
    else:
        mask_shp = fu.FileSearch_AND(output_path + "/shapeRegion/", True,
                                     current_tile,
                                     f"region_{current_region.split('f')[0]}",
                                     ".shp")[0]

    raster_mask = os.path.join(working_directory, name_out)
    cmd_raster = (f"otbcli_Rasterization -in {mask_shp} -mode attribute "
                  f"-mode.attribute.field {field_region} -im {ref_img} "
                  f"-out {raster_mask}")
    run(cmd_raster)
    return raster_mask


def get_repartition(vec: str, labels: List[str], data_field: str,
                    region_field: str, regions, runs: Union[str, int]):
    """
    usage : count label apparition in vector
    IN
    vec [string] path to a sqlite file
    labels [list of string]
    data_field [string] data field name
    region_field [string] :
    regions [list of string] : the list of different region
    runs [string or int] : the number of runs
    """

    conn = lite.connect(vec)
    cursor = conn.cursor()

    repartition = {}
    for label in labels.data:
        repartition[label] = {}
        for region in regions:
            repartition[label][region] = {}
            for run in range(runs):
                sql_clause = (
                    f"SELECT * FROM output WHERE {data_field}={label}"
                    f" AND {region_field}='{region}' "
                    f"AND seed_{run}='learn'")
                cursor.execute(sql_clause)
                results = cursor.fetchall()
                repartition[label][region][run] = len(results)

    return repartition


def get_number_annual_sample(annu_repartition):
    """
    usage : use to flatten annu_repartition to compute number
    of annual samples
    """
    nb_feat_annu = 0
    for _, vac in list(annu_repartition.items()):
        for _, var in list(vac.items()):
            for _, vas in list(var.items()):
                nb_feat_annu += vas

    return nb_feat_annu


def generate_samples_classif_mix(
        folder_sample: str,
        working_directory: str,
        train_shape: str,
        path_wd: str,
        output_path: str,
        annual_crop: List[Union[str, int]],
        all_class: List[Union[str, int]],
        data_field: str,
        previous_classif_path: str,
        proj: int,
        runs: Union[str, int],
        enable_cross_validation: bool,
        region_field: str,
        validity_threshold: int,
        target_resolution: int,
        sar_optical_post_fusion: bool,
        sensors_parameters: sensors_params_type,
        folder_features: Optional[str] = None,
        ram: Optional[int] = 128,
        w_mode: Optional[bool] = False,
        test_mode: Optional[bool] = False,
        test_shape_region: Optional[str] = None,
        sample_sel: Optional[str] = None,
        mode: Optional[str] = "usually",
        custom_features: Optional[bool] = False,
        module_path: Optional[str] = None,
        list_functions: Optional[List[str]] = None,
        force_standard_labels: Optional[bool] = False,
        number_of_chunks: Optional[int] = 50,
        targeted_chunk: Optional[int] = None,
        chunk_size_mode: Optional[str] = "split_number",
        chunk_size_x: Optional[int] = None,
        chunk_size_y: Optional[int] = None,
        logger: Optional[Logger] = LOGGER):
    """
    usage : from one classification, chose randomly annual sample merge
            with non annual sample and extract features.
    IN:
        folderSample [string] : output folder
        workingDirectory [string] : computation folder
        trainShape [string] : vector shape (polygons) to sample
        pathWd [string] : if different from None, enable HPC mode
                          (copy at ending)
        featuresPath [string] : path to all stack
        annualCrop [list of string/int] : list containing annual crops
                                          ex : [11,12]
        AllClass [list of string/int] : list containing all classes in
                                        vector shape ex : [11,12,51..]
        cfg [string] : configuration file class
        previousClassifPath [string] : path to the iota2 output
                                       directory which generate previous
                                       classification
        dataField [string] : data's field into vector shape
        testMode [bool] : enable testMode -> iota2tests.py
        testPrevConfig [string] : path to the configuration file which generate
                                  previous classification
        testShapeRegion [string] : path to the shapefile representing region in
                                   the tile.
        testFeaturePath [string] : path to the stack of data

    OUT:
        samples [string] : vector shape containing points
    """
    from iota2.Sampling.SamplesSelection import prepare_selection
    from iota2.Sampling import GenAnnualSamples as genAS
    if os.path.exists(
            os.path.join(
                folder_sample,
                train_shape.split("/")[-1].replace(".shp",
                                                   "_Samples.sqlite"))):
        return None

    if enable_cross_validation:
        runs = runs - 1
    features_path = os.path.join(output_path, "features")
    sample_sel_directory = os.path.join(output_path, "samplesSelection")

    work_dir = sample_sel_directory
    if working_directory:
        work_dir = working_directory

    data_field = data_field.lower()

    current_tile = (os.path.splitext(os.path.basename(train_shape))[0])

    if sample_sel:
        sample_selection = sample_sel
    else:
        sample_selection = prepare_selection(sample_sel_directory,
                                             current_tile)

    non_annual_shape = os.path.join(
        work_dir, "{}_nonAnnual_selection.sqlite".format(current_tile))
    annual_shape = os.path.join(
        work_dir, "{}_annual_selection.sqlite".format(current_tile))
    # garde toutes les classes pérennes
    nb_feat_nannu = extract_class(sample_selection, non_annual_shape,
                                  all_class, data_field)

    regions = fu.getFieldElement(train_shape,
                                 driverName="ESRI Shapefile",
                                 field=region_field,
                                 mode="unique",
                                 elemType="str")
    # avoir la répartition des classes anuelles par seed et par region
    # -> pouvoir faire annu_repartition[11][R][S]
    annu_repartition = get_repartition(sample_selection, annual_crop,
                                       data_field, region_field, regions, runs)

    nb_feat_annu = get_number_annual_sample(annu_repartition)

    # raster ref (in order to extract ROIs)
    ref = fu.FileSearch_AND(os.path.join(features_path, current_tile), True,
                            "MaskCommunSL.tif")[0]

    if nb_feat_nannu > 0:
        all_coord = get_points_coord_in_shape(non_annual_shape, "SQLite")
    else:
        all_coord = [0]

    classification_raster = extract_roi(os.path.join(previous_classif_path,
                                                     "final",
                                                     "Classif_Seed_0.tif"),
                                        current_tile,
                                        path_wd,
                                        output_path,
                                        f"Classif_{current_tile}",
                                        ref,
                                        test_mode,
                                        test_output=folder_sample)
    validity_raster = extract_roi(os.path.join(previous_classif_path, "final",
                                               "PixelsValidity.tif"),
                                  current_tile,
                                  path_wd,
                                  output_path,
                                  f"Cloud{current_tile}",
                                  ref,
                                  test_mode,
                                  test_output=folder_sample)

    # build regions mask into the tile
    masks = [
        get_region_model_in_tile(current_tile,
                                 current_region,
                                 output_path,
                                 path_wd,
                                 classification_raster,
                                 region_field,
                                 test_mode,
                                 test_shape_region,
                                 test_output_folder=folder_sample)
        for current_region in regions
    ]

    if nb_feat_annu > 0:
        annual_points = genAS.genAnnualShapePoints(
            all_coord, "SQLite", working_directory, target_resolution,
            annual_crop, data_field, current_tile, validity_threshold,
            validity_raster, classification_raster, masks, train_shape,
            annual_shape, proj, region_field, runs, annu_repartition)

    merge_name = train_shape.split("/")[-1].replace(".shp", "_selectionMerge")
    sample_selection = os.path.join(working_directory, f"{merge_name}.sqlite")
    if (nb_feat_nannu > 0) and (nb_feat_annu > 0 and annual_points):
        fu.mergeSQLite(merge_name, working_directory,
                       [non_annual_shape, annual_shape])

    elif (nb_feat_nannu > 0) and not (nb_feat_annu > 0 and annual_points):
        # If not annual samples can be added then annual classes are ignored
        shutil.copy(non_annual_shape, sample_selection)
    elif not (nb_feat_nannu > 0) and (nb_feat_annu > 0 and annual_points):
        # If not non annual samples are found then use all annual samples
        shutil.copy(annual_shape, sample_selection)

    if custom_features:
        samples = os.path.join(working_directory,
                               train_shape).split("/")[-1].replace(
                                   ".shp", f"_Samples_{targeted_chunk}.sqlite")
    else:
        samples = os.path.join(
            working_directory,
            train_shape.split("/")[-1].replace(".shp", "_Samples.sqlite"))

    sample_extr, dep_tmp = get_features_application(
        sample_selection,
        working_directory,
        samples,
        data_field,
        output_path,
        sar_optical_post_fusion,
        sensors_parameters,
        ram,
        mode,
        custom_features=custom_features,
        module_path=module_path,
        list_functions=list_functions,
        force_standard_labels=force_standard_labels,
        number_of_chunks=number_of_chunks,
        targeted_chunk=targeted_chunk,
        chunk_size_mode=chunk_size_mode,
        chunk_size_x=chunk_size_x,
        chunk_size_y=chunk_size_y)

    # sampleExtr.ExecuteAndWriteOutput()
    multi_proc = mp.Process(target=executeApp, args=[sample_extr])
    multi_proc.start()
    multi_proc.join()

    split_vectors = split_vector_by_region(in_vect=samples,
                                           output_dir=working_directory,
                                           region_field=region_field,
                                           runs=int(runs),
                                           driver="SQLite",
                                           proj_in="EPSG:" + str(proj),
                                           proj_out="EPSG:" + str(proj),
                                           targeted_chunk=targeted_chunk)
    if test_mode:
        split_vectors = None

    if path_wd and os.path.exists(samples):
        for sample in split_vectors:
            shutil.copy(sample, folder_sample)

    if os.path.exists(non_annual_shape):
        os.remove(non_annual_shape)
    if os.path.exists(annual_shape):
        os.remove(annual_shape)

    if w_mode:
        target_directory = os.path.join(folder_features, current_tile)
        if not os.path.exists(target_directory):
            try:
                os.mkdir(target_directory)
            except OSError:
                logger.warning(f"{target_directory} allready exists")
            try:
                os.mkdir(os.path.join(target_directory, "tmp"))
            except OSError:
                logger.warning(f"{target_directory}/tmp allready exists")
        from_dir = os.path.join(working_directory, current_tile, "tmp")
        to_dir = os.path.join(target_directory, "tmp")
        if os.path.exists(from_dir):
            fu.updateDirectory(from_dir, to_dir)

    os.remove(samples)
    os.remove(classification_raster)
    os.remove(validity_raster)
    for mask in masks:
        os.remove(mask)
    return split_vectors


def generate_samples(train_shape_dic,
                     path_wd,
                     data_field: str,
                     output_path: str,
                     annual_crop: List[Union[str, int]],
                     crop_mix: bool,
                     auto_context_enable: bool,
                     region_field: str,
                     proj: Union[int, str],
                     enable_cross_validation: bool,
                     runs: int,
                     sensors_parameters: sensors_params_type,
                     sar_optical_post_fusion: bool,
                     samples_classif_mix: Optional[bool] = False,
                     output_path_annual: Optional[str] = None,
                     ram: Optional[int] = 128,
                     w_mode: Optional[int] = False,
                     folder_annual_features: Optional[str] = None,
                     previous_classif_path: Optional[str] = None,
                     validity_threshold: Optional[int] = None,
                     target_resolution: Optional[int] = None,
                     test_mode: Optional[bool] = False,
                     test_shape_region: Optional[str] = None,
                     sample_selection: Optional[str] = None,
                     custom_features: Optional[bool] = False,
                     module_path: Optional[str] = None,
                     list_functions: Optional[List[str]] = None,
                     force_standard_labels: Optional[bool] = False,
                     number_of_chunks: Optional[int] = 50,
                     chunk_size_mode: Optional[str] = "split_number",
                     chunk_size_x: Optional[int] = None,
                     chunk_size_y: Optional[int] = None,
                     targeted_chunk: Optional[int] = None,
                     concat_mode: Optional[bool] = True,
                     logger: Optional[Logger] = LOGGER):
    """
    usage : generation of vector shape of points with features

    IN:
    train_shape_dic [dict] : dictionnary containing a shape file in value
    pathWd [string] : working directory
    data_field [str] : data field name
    output_path [str] : the ouput path
    annual_crop: List[str or int] : the list of annual crop
    crop_mix [bool] : activate the crop mix mode
    auto_context_enable [bool] : activate auto context mode
    region_field [str] : the region field name
    proj [int] : the working projection
    enable_cross_validation [bool] : enable cross validation
    runs: int,
    samples_classif_mix: Optional[bool] = False,
    output_path_annual: Optional[str] = None,
    ram=128,
    w_mode=False,
    folder_annual_features=None,
    previous_classif_path: Optional[str] = None,
    validity_threshold: Optional[int] = None,
    target_resolution: Optional[int] = None,
    testMode [bool] : enable test
    features [string] : path to features allready compute (refl + NDVI ...)
    testFeaturePath [string] : path to stack of data without features
    testAnnualFeaturePath [string] : path to stack of data without features
    testPrevConfig [string] : path to a configuration file
    testShapeRegion [string] : path to a vector shapeFile, representing region
                               in tile

    OUT:
    samples [string] : path to output vector shape
    """
    # mode must be "usally" or "SAR"
    mode = list(train_shape_dic.keys())[0]
    train_shape = train_shape_dic[mode]

    all_class = fu.getFieldElement(train_shape,
                                   "ESRI Shapefile",
                                   data_field,
                                   mode="unique",
                                   elemType="str")

    for current_class in annual_crop.data:
        try:
            all_class.remove(str(current_class))
        except ValueError:
            logger.warning(
                f"Class {current_class} doesn't exist in {train_shape}")

    logger.info(f"All classes: {all_class}")
    logger.info(f"Annual crop: {annual_crop}")

    folder_features = os.path.join(output_path, "features")
    folder_sample = os.path.join(output_path, "learningSamples")
    if not os.path.exists(folder_sample):
        try:
            os.mkdir(folder_sample)
        except OSError:
            logger.warning(f"{folder_sample} allready exists")

    working_directory = folder_sample
    if path_wd:
        working_directory = path_wd

    if crop_mix is False or auto_context_enable:
        samples = generate_samples_simple(
            folder_sample,
            working_directory,
            train_shape,
            path_wd,
            data_field,
            region_field,
            output_path,
            runs,
            proj,
            enable_cross_validation,
            sensors_parameters,
            sar_optical_post_fusion,
            ram,
            w_mode,
            folder_features,
            sample_selection,
            mode,
            custom_features=custom_features,
            module_path=module_path,
            list_functions=list_functions,
            force_standard_labels=force_standard_labels,
            number_of_chunks=number_of_chunks,
            targeted_chunk=targeted_chunk,
            chunk_size_mode=chunk_size_mode,
            chunk_size_x=chunk_size_x,
            chunk_size_y=chunk_size_y,
            concat_mode=concat_mode)

    elif crop_mix is True and samples_classif_mix is False:
        samples = generate_samples_crop_mix(
            folder_sample,
            working_directory,
            output_path,
            output_path_annual,
            train_shape,
            path_wd,
            annual_crop,
            all_class,
            data_field,
            folder_features,
            folder_annual_features,
            enable_cross_validation,
            runs,
            region_field,
            proj,
            sar_optical_post_fusion,
            sensors_parameters,
            ram,
            w_mode,
            test_mode,
            sample_selection,
            mode,
            custom_features=custom_features,
            module_path=module_path,
            list_functions=list_functions,
            force_standard_labels=force_standard_labels,
            number_of_chunks=number_of_chunks,
            targeted_chunk=targeted_chunk,
            chunk_size_mode=chunk_size_mode,
            chunk_size_x=chunk_size_x,
            chunk_size_y=chunk_size_y)

    elif crop_mix is True and samples_classif_mix is True:
        if isinstance(proj, str):
            proj = int(proj.split(":")[-1])
        samples = generate_samples_classif_mix(
            folder_sample,
            working_directory,
            train_shape,
            path_wd,
            output_path,
            annual_crop,
            all_class,
            data_field,
            previous_classif_path,
            proj,
            runs,
            enable_cross_validation,
            region_field,
            validity_threshold,
            target_resolution,
            sar_optical_post_fusion,
            sensors_parameters,
            folder_features,
            ram,
            w_mode,
            test_mode,
            test_shape_region,
            sample_selection,
            mode,
            custom_features=custom_features,
            module_path=module_path,
            list_functions=list_functions,
            force_standard_labels=force_standard_labels,
            number_of_chunks=number_of_chunks,
            targeted_chunk=targeted_chunk,
            chunk_size_mode=chunk_size_mode,
            chunk_size_x=chunk_size_x,
            chunk_size_y=chunk_size_y)
    if test_mode:
        return samples


if __name__ == "__main__":

    PARSER = argparse.ArgumentParser(
        description="This function sample a shapeFile")
    PARSER.add_argument("-shape",
                        dest="shape",
                        help="path to the shapeFile to sampled",
                        default=None,
                        required=True)
    PARSER.add_argument("--wd",
                        dest="pathWd",
                        help="path to the working directory",
                        default=None,
                        required=False)
    PARSER.add_argument("-data_field",
                        help="name of data field in shape (mandatory)",
                        dest="data_field",
                        required=True)
    PARSER.add_argument("-output_path",
                        help="path to output directory (mandatory)",
                        dest="output_path",
                        required=True)
    PARSER.add_argument("-annual_crop",
                        help="path to output directory (mandatory)",
                        dest="annual_crop",
                        required=True)
    PARSER.add_argument("-crop_mix",
                        help="activate crop mix mode (optional)",
                        dest="crop_mix",
                        default=False,
                        required=False)
    PARSER.add_argument("-enable_autoContext",
                        help="activate auto context (optional)",
                        dest="auto_context",
                        default=False,
                        required=False)
    PARSER.add_argument("-region_field",
                        help="name for region field in shape (mandatory)",
                        dest="region_field",
                        required=True)
    PARSER.add_argument("-proj",
                        help="projection (mandatory)",
                        dest="proj",
                        required=True)
    PARSER.add_argument("-enable_crossval",
                        help="activate cross validation (optional)",
                        dest="cross_val",
                        default=False,
                        required=False)
    PARSER.add_argument("-runs",
                        help="number of runs (mandatory)",
                        type=int,
                        dest="runs",
                        required=True)
    PARSER.add_argument("-samples_classif_mix",
                        help="activate classif mix (optional)",
                        dest="samples_classif_mix",
                        default=False,
                        required=False)
    PARSER.add_argument("-annual_path",
                        help="path for annual data (optional)",
                        dest="annual_path",
                        default=None,
                        required=False)
    PARSER.add_argument("-w_mode",
                        help="activate writting of temporary files (optional)",
                        dest="w_mode",
                        default=False,
                        required=False)
    PARSER.add_argument("-ram",
                        help="ram for otbApplications (optional)",
                        type=int,
                        dest="ram",
                        default=128,
                        required=False)
    PARSER.add_argument("-folder_annual_feat",
                        help="path to annual features (optional)",
                        dest="folder_annual_feat",
                        default=None,
                        required=False)
    PARSER.add_argument("-prev_classif_path",
                        help="path to prev features (optional)",
                        dest="prev_classif_path",
                        default=None,
                        required=False)
    PARSER.add_argument("-valid_thres",
                        help=("threshold validation for sample "
                              "selection (optional)"),
                        dest="valid_thres",
                        type=int,
                        default=None,
                        required=False)
    PARSER.add_argument("-target_res",
                        help=("target resolution (optional)"),
                        dest="target_res",
                        type=int,
                        default=None,
                        required=False)
    PARSER.add_argument("-config_file",
                        help=("configuration file for sensors "
                              "parameters (mandatory)"),
                        dest="config_file",
                        required=True)
    PARSER.add_argument("-sar_opt_flag",
                        help=("activate post classification fusion"
                              " between optical and sar images (mandatory)"),
                        dest="sar_opt_flag",
                        default=False,
                        required=False)
    ARGS = PARSER.parse_args()
    from iota2.Common import ServiceConfigFile as SCF
    SENSORS_PARAMS = SCF.iota2_parameters(ARGS.conf_file)

    generate_samples(ARGS.shape, ARGS.pathWd, ARGS.data_field,
                     ARGS.output_path, ARGS.annual_crop, ARGS.crop_mix,
                     ARGS.auto_context, ARGS.region_field, ARGS.proj,
                     ARGS.cross_val, ARGS.runs, SENSORS_PARAMS,
                     ARGS.sar_opt_flag, ARGS.samples_classif_mix,
                     ARGS.annual_path, ARGS.ram, ARGS.w_mode,
                     ARGS.folder_annual_feat, ARGS.prev_classif_path,
                     ARGS.valid_thres, ARGS.target_res)
