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
"""Sentinel-2 class definition
"""

import multiprocessing as mp

import logging
import glob
import os

from collections import OrderedDict
from iota2.Common.OtbAppBank import executeApp

LOGGER = logging.getLogger(__name__)

#in order to avoid issue 'No handlers could be found for logger...'
LOGGER.addHandler(logging.NullHandler())


class sentinel_2():
    """Sentinel-2 class definition
    """

    name = 'Sentinel2'

    def __init__(self, tile_name, target_proj, all_tiles, s2_data,
                 write_dates_stack, extract_bands_flag, output_target_dir,
                 keep_bands, i2_output_path, temporal_res, auto_date_flag,
                 date_interp_min_user, date_interp_max_user,
                 write_outputs_flag, features, enable_gapfilling,
                 hand_features_flag, hand_features, copy_input, rel_refl,
                 keep_dupl, acorfeat, vhr_path, **kwargs):
        """
        """
        from iota2.Common import ServiceConfigFile as SCF
        from iota2.Common.FileUtils import get_iota2_project_dir

        self.tile_name = tile_name
        self.target_proj = target_proj
        self.all_tiles = all_tiles
        self.s2_data = s2_data
        self.write_dates_stack = write_dates_stack
        self.extract_bands_flag = extract_bands_flag
        self.output_target_dir = output_target_dir
        self.keep_bands = keep_bands
        self.i2_output_path = i2_output_path
        self.temporal_res = temporal_res
        self.auto_date_flag = auto_date_flag
        self.date_interp_min_user = date_interp_min_user
        self.date_interp_max_user = date_interp_max_user
        self.write_outputs_flag = write_outputs_flag
        self.features = features
        self.enable_gapFilling = enable_gapfilling
        self.hand_features_flag = hand_features_flag
        self.hand_features = hand_features
        self.copy_input = copy_input
        self.rel_refl = rel_refl
        self.keep_dupl = keep_dupl
        self.acorfeat = acorfeat
        self.VHRPath = vhr_path

        cfg_sensors = os.path.join(get_iota2_project_dir(), "iota2", "Sensors",
                                   "sensors.cfg")
        cfg_sensors = SCF.serviceConfigFile(cfg_sensors, iota_config=False)

        self.tile_directory = os.path.join(self.s2_data, tile_name)
        self.struct_path_masks = cfg_sensors.getParam("Sentinel_2", "arbomask")
        # ~ self.write_dates_stack = self.cfg_IOTA2.getParam(
        # ~ "Sentinel_2", "write_reproject_resampled_input_dates_stack")
        self.features_dir = os.path.join(self.i2_output_path, "features",
                                         tile_name)

        # ~ extract_bands_flag = self.cfg_IOTA2.getParam("iota2FeatureExtraction",
        # ~ "extractBands")
        # ~ output_target_dir = self.cfg_IOTA2.getParam("chain", "S2_output_path")
        if output_target_dir:
            self.output_preprocess_directory = os.path.join(
                output_target_dir, tile_name)
            if not os.path.exists(self.output_preprocess_directory):
                try:
                    os.mkdir(self.output_preprocess_directory)
                except Exception:
                    pass
        else:
            self.output_preprocess_directory = self.tile_directory

        # sensors attributes
        self.data_type = "FRE"
        self.suffix = "STACK"
        self.masks_date_suffix = "BINARY_MASK"
        self.date_position = 1  # if date's name split by "_"
        self.NODATA_VALUE = -10000
        self.masks_rules = OrderedDict({
            "CLM_R1.tif": 0,
            "SAT_R1.tif": 0,
            "EDG_R1.tif": 0
        })  # 0 mean data, else noData
        self.border_pos = 2
        self.features_names_list = ["NDVI", "NDWI", "Brightness"]

        # define bands to get and their order
        self.stack_band_position = [
            "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"
        ]
        self.extracted_bands = None
        if extract_bands_flag:
            # ~ keep_bands = self.cfg_IOTA2.getParam("Sentinel_2", "keepBands")
            self.extracted_bands = [(band_name, band_position + 1)
                                    for band_position, band_name in enumerate(
                                        self.stack_band_position)
                                    if band_name in keep_bands]

        # output's names
        self.footprint_name = "{}_{}_footprint.tif".format(
            self.__class__.name, tile_name)
        ref_image_name = "{}_{}_reference.tif".format(self.__class__.name,
                                                      tile_name)
        self.ref_image = os.path.join(self.i2_output_path, "features",
                                      tile_name, "tmp", ref_image_name)
        self.time_series_name = "{}_{}_TS.tif".format(self.__class__.name,
                                                      tile_name)
        self.time_series_masks_name = "{}_{}_MASKS.tif".format(
            self.__class__.name, tile_name)
        self.time_series_gapfilling_name = "{}_{}_TSG.tif".format(
            self.__class__.name, tile_name)
        self.features_names = "{}_{}_Features.tif".format(
            self.__class__.name, tile_name)
        # about gapFilling interpolations
        # ~ self.temporal_res = self.cfg_IOTA2.getParam("Sentinel_2",
        # ~ "temporalResolution")
        self.input_dates = "{}_{}_input_dates.txt".format(
            self.__class__.name, tile_name)
        self.interpolated_dates = "{}_{}_interpolation_dates.txt".format(
            self.__class__.name, tile_name)

    def sort_dates_directories(self, dates_directories):
        """sort dates directories
        """
        return sorted(dates_directories,
                      key=lambda x: os.path.basename(x).split("_")[
                          self.date_position].split("-")[0])

    def get_available_dates(self):
        """
        return sorted available dates
        """
        from iota2.Common.FileUtils import FileSearch_AND

        pattern = "{}.tif".format(self.suffix)
        if not "none" in self.VHRPath.lower():
            pattern = "{}_COREG.tif".format(self.suffix)

        stacks = sorted(FileSearch_AND(self.output_preprocess_directory, True,
                                       "{}".format(pattern)),
                        key=lambda x: os.path.basename(x).split("_")[
                            self.date_position].split("-")[0])
        return stacks

    def get_available_dates_masks(self):
        """
        return sorted available masks
        """
        from iota2.Common.FileUtils import FileSearch_AND
        pattern = "{}.tif".format(self.masks_date_suffix)
        if not "none" in self.VHRPath.lower():
            pattern = "{}_COREG.tif".format(self.suffix)
        masks = sorted(FileSearch_AND(self.output_preprocess_directory, True,
                                      "{}".format(pattern)),
                       key=lambda x: os.path.basename(x).split("_")[
                           self.date_position].split("-")[0])
        return masks

    def build_stack_date_name(self, date_dir):
        """build stack date name
        """
        from iota2.Common.FileUtils import FileSearch_AND
        _, b2_name = os.path.split(
            FileSearch_AND(date_dir, True, "FRE_B2.tif")[0])
        return b2_name.replace("{}_B2.tif".format(self.data_type),
                               "{}_{}.tif".format(self.data_type, self.suffix))

    def preprocess_date(self,
                        date_dir,
                        out_prepro,
                        working_dir=None,
                        ram=128,
                        logger=LOGGER):
        """
        """
        import os
        import shutil
        from gdal import Warp
        from osgeo.gdalconst import GDT_Byte

        from iota2.Common.FileUtils import ensure_dir
        from iota2.Common.FileUtils import getRasterProjectionEPSG
        from iota2.Common.FileUtils import FileSearch_AND
        from iota2.Common.OtbAppBank import CreateConcatenateImagesApplication
        from iota2.Common.OtbAppBank import CreateSuperimposeApplication

        # manage directories
        date_stack_name = self.build_stack_date_name(date_dir)
        logger.debug("preprocessing {}".format(date_dir))
        out_stack = os.path.join(date_dir, date_stack_name)
        if out_prepro:
            _, date_dir_name = os.path.split(date_dir)
            out_dir = os.path.join(out_prepro, date_dir_name)
            if not os.path.exists(out_dir):
                try:
                    os.mkdir(out_dir)
                except:
                    logger.warning("{} already exists".format(out_dir))
            out_stack = os.path.join(out_dir, date_stack_name)

        out_stack_processing = out_stack
        if working_dir:
            out_stack_processing = os.path.join(working_dir, date_stack_name)

        # get bands
        date_bands = [
            FileSearch_AND(date_dir, True,
                           "{}_{}.tif".format(self.data_type, bands_name))[0]
            for bands_name in self.stack_band_position
        ]

        # tile reference image generation
        base_ref = date_bands[0]
        logger.info("reference image generation {} from {}".format(
            self.ref_image, base_ref))
        ensure_dir(os.path.dirname(self.ref_image), raise_exe=False)
        base_ref_projection = getRasterProjectionEPSG(base_ref)
        if not os.path.exists(self.ref_image):
            Warp(self.ref_image,
                 base_ref,
                 multithread=True,
                 format="GTiff",
                 xRes=10,
                 yRes=10,
                 outputType=GDT_Byte,
                 srcSRS="EPSG:{}".format(base_ref_projection),
                 dstSRS="EPSG:{}".format(self.target_proj))

        # reproject / resample
        bands_proj = OrderedDict()
        all_reproj = []
        for band, band_name in zip(date_bands, self.stack_band_position):
            superimp, _ = CreateSuperimposeApplication({
                "inr": self.ref_image,
                "inm": band,
                "ram": str(ram)
            })
            bands_proj[band_name] = superimp
            all_reproj.append(superimp)

        if self.write_dates_stack:
            for reproj in all_reproj:
                reproj.Execute()
            date_stack = CreateConcatenateImagesApplication({
                "il":
                all_reproj,
                "ram":
                str(ram),
                "pixType":
                "int16",
                "out":
                out_stack_processing
            })
            same_proj = False
            if os.path.exists(out_stack):
                same_proj = int(getRasterProjectionEPSG(out_stack)) == int(
                    self.target_proj)

            if not os.path.exists(out_stack) or same_proj is False:
                #~ date_stack.ExecuteAndWriteOutput()
                p = mp.Process(target=executeApp, args=[date_stack])
                p.start()
                p.join()
                if working_dir:
                    shutil.copy(out_stack_processing, out_stack)
                    os.remove(out_stack_processing)
        return bands_proj if self.write_dates_stack is False else out_stack

    def preprocess_date_masks(self,
                              date_dir,
                              out_prepro,
                              working_dir=None,
                              ram=128,
                              logger=LOGGER):
        """
        """
        import shutil
        from iota2.Common.FileUtils import ensure_dir
        from iota2.Common.OtbAppBank import CreateBandMathApplication
        from iota2.Common.OtbAppBank import CreateSuperimposeApplication
        from iota2.Common.FileUtils import getRasterProjectionEPSG

        # TODO : throw Exception if no masks are found
        date_mask = []
        for mask_name, _ in list(self.masks_rules.items()):
            date_mask.append(
                glob.glob(
                    os.path.join(
                        date_dir, "{}{}".format(self.struct_path_masks,
                                                mask_name)))[0])

        # manage directories
        mask_dir = os.path.dirname(date_mask[0])
        logger.debug("preprocessing {} masks".format(mask_dir))
        mask_name = os.path.basename(date_mask[0]).replace(
            list(self.masks_rules.items())[0][0],
            "{}.tif".format(self.masks_date_suffix))
        out_mask = os.path.join(mask_dir, mask_name)
        if out_prepro:
            out_mask_dir = mask_dir.replace(
                os.path.join(self.s2_data, self.tile_name), out_prepro)
            ensure_dir(out_mask_dir, raise_exe=False)
            out_mask = os.path.join(out_mask_dir, mask_name)

        out_mask_processing = out_mask
        if working_dir:
            out_mask_processing = os.path.join(working_dir, mask_name)

        # build binary mask
        expr = "+".join(
            ["im{}b1".format(cpt + 1) for cpt in range(len(date_mask))])
        expr = "({})==0?0:1".format(expr)
        binary_mask_rule = CreateBandMathApplication({
            "il": date_mask,
            "exp": expr
        })
        binary_mask_rule.Execute()
        # reproject using reference image
        superimp, _ = CreateSuperimposeApplication({
            "inr": self.ref_image,
            "inm": binary_mask_rule,
            "interpolator": "nn",
            "out": out_mask_processing,
            "pixType": "uint8",
            "ram": str(ram)
        })

        # needed to travel throught iota2's library
        app_dep = [binary_mask_rule]

        if self.write_dates_stack:
            same_proj = False
            if os.path.exists(out_mask):
                same_proj = int(getRasterProjectionEPSG(out_mask)) == int(
                    self.target_proj)

            if not os.path.exists(out_mask) or same_proj is False:
                #~ superimp.ExecuteAndWriteOutput()
                p = mp.Process(target=executeApp, args=[superimp])
                p.start()
                p.join()
                if working_dir:
                    shutil.copy(out_mask_processing, out_mask)
                    os.remove(out_mask_processing)

        return superimp, app_dep

    def get_date_from_name(self, product_name):
        """
        """
        return product_name.split("_")[self.date_position].split("-")[0]

    def preprocess(self, working_dir=None, ram=128):
        """
        """
        input_dates = [
            os.path.join(self.tile_directory, cdir)
            for cdir in os.listdir(self.tile_directory)
        ]
        input_dates = self.sort_dates_directories(input_dates)

        preprocessed_dates = OrderedDict()
        for date in input_dates:
            data_prepro = self.preprocess_date(
                date, self.output_preprocess_directory, working_dir, ram)
            data_mask = self.preprocess_date_masks(
                date, self.output_preprocess_directory, working_dir, ram)
            current_date = self.get_date_from_name(os.path.basename(date))
            # manage date dupplicate
            if current_date in preprocessed_dates:
                current_date = "{}.1".format(current_date)
            preprocessed_dates[current_date] = {
                "data": data_prepro,
                "mask": data_mask
            }
        return preprocessed_dates

    def footprint(self, ram=128):
        """
        """
        from iota2.Common.OtbAppBank import CreateSuperimposeApplication
        from iota2.Common.OtbAppBank import CreateBandMathApplication
        from iota2.Common.FileUtils import ensure_dir

        footprint_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(footprint_dir, raise_exe=False)
        footprint_out = os.path.join(footprint_dir, self.footprint_name)

        input_dates = [
            os.path.join(self.tile_directory, cdir)
            for cdir in os.listdir(self.tile_directory)
        ]
        input_dates = self.sort_dates_directories(input_dates)

        # get date's footprint
        date_edge = []
        for date_dir in input_dates:
            date_edge.append(
                glob.glob(
                    os.path.join(
                        date_dir, "{}{}".format(
                            self.struct_path_masks,
                            list(self.masks_rules.keys())[self.border_pos])))
                [0])

        expr = " || ".join("1 - im{}b1".format(i + 1)
                           for i in range(len(date_edge)))
        s2_border = CreateBandMathApplication({
            "il": date_edge,
            "exp": expr,
            "ram": str(ram)
        })
        s2_border.Execute()

        reference_raster = self.ref_image
        if not "none" in self.cfg_IOTA2.getParam('coregistration',
                                                 'VHRPath').lower():
            reference_raster = self.get_available_dates()[0]

        # superimpose footprint
        superimp, _ = CreateSuperimposeApplication({
            "inr": reference_raster,
            "inm": s2_border,
            "out": footprint_out,
            "pixType": "uint8",
            "ram": str(ram)
        })

        # needed to travel throught iota2's library
        app_dep = [s2_border, _]

        return superimp, app_dep

    def write_interpolation_dates_file(self):
        """
        TODO : mv to base-class
        """
        from iota2.Common.FileUtils import getDateS2
        from iota2.Common.FileUtils import ensure_dir
        from iota2.Common.FileUtils import dateInterval

        interp_date_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(interp_date_dir, raise_exe=False)
        interp_date_file = os.path.join(interp_date_dir,
                                        self.interpolated_dates)
        # get dates in the whole S2 data-set
        date_interp_min, date_interp_max = getDateS2(self.s2_data,
                                                     self.all_tiles.split(" "))

        # force dates
        # ~ auto_date_flag = self.cfg_IOTA2.getParam("GlobChain", "autoDate")
        if not self.auto_date_flag:
            # ~ date_interp_min = self.cfg_IOTA2.getParam("Sentinel_2",
            # ~ "startDate")
            # ~ date_interp_max = self.cfg_IOTA2.getParam("Sentinel_2", "endDate")
            date_interp_min = self.date_interp_min_user
            date_interp_max = self.date_interp_max_user
        dates = [
            str(date).replace("-", "") for date in dateInterval(
                date_interp_min, date_interp_max, self.temporal_res)
        ]
        if not os.path.exists(interp_date_file):
            with open(interp_date_file, "w") as interpolation_date_file:
                interpolation_date_file.write("\n".join(dates))
        return interp_date_file, dates

    def write_dates_file(self):
        """
        """

        input_dates_dir = [
            os.path.join(self.tile_directory, cdir)
            for cdir in os.listdir(self.tile_directory)
        ]
        date_file = os.path.join(self.features_dir, "tmp", self.input_dates)
        all_available_dates = [
            os.path.basename(date).split("_")[self.date_position].split("-")[0]
            for date in input_dates_dir
        ]
        all_available_dates = sorted(all_available_dates, key=lambda x: int(x))
        if not os.path.exists(date_file):
            with open(date_file, "w") as input_date_file:
                input_date_file.write("\n".join(all_available_dates))
        return date_file, all_available_dates

    def get_time_series(self, ram=128):
        """
        TODO : be able of using a date interval
        Return
        ------
            list
                [(otb_Application, some otb's objects), time_series_labels]
                Functions dealing with otb's application instance has to
                returns every objects in the pipeline
        """
        from iota2.Common.OtbAppBank import CreateConcatenateImagesApplication
        from iota2.Common.FileUtils import ensure_dir

        # needed to travel throught iota2's library
        app_dep = []

        preprocessed_dates = self.preprocess(working_dir=None, ram=str(ram))

        if self.write_dates_stack is False:
            dates_concatenation = []
            for _, dico_date in list(preprocessed_dates.items()):
                for _, reproj_date in list(dico_date["data"].items()):
                    dates_concatenation.append(reproj_date)
                    reproj_date.Execute()
                    app_dep.append(reproj_date)
        else:
            dates_concatenation = self.get_available_dates()

        time_series_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(time_series_dir, raise_exe=False)
        times_series_raster = os.path.join(time_series_dir,
                                           self.time_series_name)

        dates_time_series = CreateConcatenateImagesApplication({
            "il": dates_concatenation,
            "out": times_series_raster,
            "pixType": "int16",
            "ram": str(ram)
        })
        _, dates_in = self.write_dates_file()

        # build labels
        features_labels = [
            "{}_{}_{}".format(self.__class__.name, band_name, date)
            for date in dates_in for band_name in self.stack_band_position
        ]

        # if not all bands must be used
        if self.extracted_bands:
            app_dep.append(dates_time_series)
            (dates_time_series,
             features_labels) = self.extract_bands_time_series(
                 dates_time_series, dates_in, len(self.stack_band_position),
                 self.extracted_bands, ram)
        return (dates_time_series, app_dep), features_labels

    def extract_bands_time_series(self, dates_time_series, dates_in, comp,
                                  extract_bands, ram):
        """
        TODO : mv to base class ?
        extract_bands : list
             [('bandName', band_position), ...]
        comp : number of bands in original stack
        """
        from iota2.Common.OtbAppBank import CreateExtractROIApplication

        nb_dates = len(dates_in)
        channels_interest = []
        for date_number in range(nb_dates):
            for _, band_position in extract_bands:
                channels_interest.append(band_position +
                                         int(date_number * comp))

        features_labels = [
            "{}_{}_{}".format(self.__class__.name, band_name, date)
            for date in dates_in for band_name, band_pos in extract_bands
        ]
        channels_list = [
            "Channel{}".format(channel) for channel in channels_interest
        ]
        dates_time_series.Execute()
        extract = CreateExtractROIApplication({
            "in":
            dates_time_series,
            "cl":
            channels_list,
            "ram":
            str(ram),
            "out":
            dates_time_series.GetParameterString("out")
        })
        return extract, features_labels

    def get_time_series_masks(self, ram=128):
        """
        """
        """
        TODO : be able of using a date interval
        Return
        ------
            list
                [(otb_Application, some otb's objects), time_series_labels]
                Functions dealing with otb's application instance has to
                returns every objects in the pipeline
        """
        from iota2.Common.OtbAppBank import CreateConcatenateImagesApplication
        from iota2.Common.FileUtils import ensure_dir

        # needed to travel throught iota2's library
        app_dep = []

        preprocessed_dates = self.preprocess(working_dir=None, ram=str(ram))

        dates_masks = []
        if self.write_dates_stack is False:
            for _, dico_date in list(preprocessed_dates.items()):
                mask_app, mask_app_dep = dico_date["mask"]
                mask_app.Execute()
                dates_masks.append(mask_app)
                app_dep.append(mask_app)
                app_dep.append(mask_app_dep)
        else:
            dates_masks = self.get_available_dates_masks()

        time_series_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(time_series_dir, raise_exe=False)
        times_series_mask = os.path.join(time_series_dir,
                                         self.time_series_masks_name)
        dates_time_series_mask = CreateConcatenateImagesApplication({
            "il":
            dates_masks,
            "out":
            times_series_mask,
            "pixType":
            "uint8",
            "ram":
            str(ram)
        })
        return dates_time_series_mask, app_dep, len(dates_masks)

    def get_time_series_gapFilling(self, ram=128):
        """
        """
        from iota2.Common.OtbAppBank import CreateImageTimeSeriesGapFillingApplication
        from iota2.Common.OtbAppBank import getInputParameterOutput
        from iota2.Common.FileUtils import ensure_dir

        gap_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(gap_dir, raise_exe=False)
        gap_out = os.path.join(gap_dir, self.time_series_gapfilling_name)

        dates_interp_file, dates_interp = self.write_interpolation_dates_file()
        dates_in_file, _ = self.write_dates_file()

        masks, masks_dep, _ = self.get_time_series_masks()
        (time_series, time_series_dep), _ = self.get_time_series()

        # inputs
        # ~ write_outputs_flag = self.cfg_IOTA2.getParam('GlobChain', 'writeOutputs')
        if self.write_outputs_flag is False:
            time_series.Execute()
            masks.Execute()
        else:
            time_series_raster = time_series.GetParameterValue(
                getInputParameterOutput(time_series))
            masks_raster = masks.GetParameterValue(
                getInputParameterOutput(masks))
            if not os.path.exists(masks_raster):
                p = mp.Process(target=executeApp, args=[masks])
                p.start()
                p.join()
            if not os.path.exists(time_series_raster):
                #~ time_series.ExecuteAndWriteOutput()
                p = mp.Process(target=executeApp, args=[time_series])
                p.start()
                p.join()
            if os.path.exists(masks_raster):
                masks = masks_raster
            if os.path.exists(time_series_raster):
                time_series = time_series_raster

        comp = len(
            self.stack_band_position) if not self.extracted_bands else len(
                self.extracted_bands)

        gap = CreateImageTimeSeriesGapFillingApplication({
            "in": time_series,
            "mask": masks,
            "comp": str(comp),
            "it": "linear",
            "id": dates_in_file,
            "od": dates_interp_file,
            "out": gap_out,
            "ram": str(ram),
            "pixType": "int16"
        })
        app_dep = [time_series, masks, masks_dep, time_series_dep]

        bands = self.stack_band_position
        if self.extracted_bands:
            bands = [band_name for band_name, band_pos in self.extracted_bands]

        features_labels = [
            "{}_{}_{}".format(self.__class__.name, band_name, date)
            for date in dates_interp for band_name in bands
        ]
        return (gap, app_dep), features_labels

    def get_features_labels(self, dates, rel_refl, keep_dupl, copy_in):
        """
        """
        if rel_refl and keep_dupl is False and copy_in is True:
            self.features_names_list = ["NDWI", "Brightness"]
        out_labels = []

        for feature in self.features_names_list:
            for date in dates:
                out_labels.append("{}_{}_{}".format(self.__class__.name,
                                                    feature, date))
        return out_labels

    def get_features(self, ram=128):
        """
        """
        from iota2.Common.OtbAppBank import CreateConcatenateImagesApplication
        from iota2.Common.OtbAppBank import computeUserFeatures
        from iota2.Common.OtbAppBank import CreateIota2FeatureExtractionApplication
        from iota2.Common.OtbAppBank import getInputParameterOutput
        from iota2.Common.FileUtils import ensure_dir

        features_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(features_dir, raise_exe=False)
        features_out = os.path.join(features_dir, self.features_names)

        # ~ features = self.cfg_IOTA2.getParam("GlobChain", "features")
        # ~ enable_gapFilling = self.cfg_IOTA2.getParam("GlobChain",
        # ~ "useGapFilling")
        # ~ hand_features_flag = self.cfg_IOTA2.getParam('GlobChain',
        # ~ 'useAdditionalFeatures')

        # input
        (in_stack, in_stack_dep
         ), in_stack_features_labels = self.get_time_series_gapFilling()
        _, dates_enabled = self.write_interpolation_dates_file()

        if not self.enable_gapFilling:
            (in_stack,
             in_stack_dep), in_stack_features_labels = self.get_time_series()
            _, dates_enabled = self.write_dates_file()

        if self.write_outputs_flag is False:
            in_stack.Execute()
        else:
            in_stack_raster = in_stack.GetParameterValue(
                getInputParameterOutput(in_stack))
            if not os.path.exists(in_stack_raster):
                #~ in_stack.ExecuteAndWriteOutput()
                p = mp.Process(target=executeApp, args=[in_stack])
                p.start()
                p.join()
            if os.path.exists(in_stack_raster):
                in_stack = in_stack_raster
        # output
        app_dep = []
        if self.hand_features_flag:
            # ~ hand_features = self.cfg_IOTA2.getParam("Sentinel_2",
            # ~ "additionalFeatures")
            comp = len(
                self.stack_band_position) if not self.extracted_bands else len(
                    self.extracted_bands)
            userDateFeatures, fields_userFeat, a, b = computeUserFeatures(
                in_stack, dates_enabled, comp, hand_features.split(","))
            userDateFeatures.Execute()
            app_dep.append([userDateFeatures, a, b])

        if self.features:
            bands_avail = self.stack_band_position
            if self.extracted_bands:
                bands_avail = [
                    band_name for band_name, _ in self.extracted_bands
                ]
                # check mandatory bands
                if not "B4" in bands_avail:
                    raise Exception(
                        "red band (B4) is needed to compute features")
                if not "B8" in bands_avail:
                    raise Exception(
                        "nir band (B8) is needed to compute features")
                if not "B11" in bands_avail:
                    raise Exception(
                        "swir band (B11) is needed to compute features")

            # ~ copyinput = self.cfg_IOTA2.getParam('iota2FeatureExtraction',
            # ~ 'copyinput')
            # ~ rel_refl = self.cfg_IOTA2.getParam('iota2FeatureExtraction',
            # ~ 'relrefl')
            # ~ keep_dupl = self.cfg_IOTA2.getParam('iota2FeatureExtraction',
            # ~ 'keepduplicates')
            # ~ acorfeat = self.cfg_IOTA2.getParam('iota2FeatureExtraction', 'acorfeat')
            feat_parameters = {
                "in": in_stack,
                "out": features_out,
                "comp": len(bands_avail),
                "red": bands_avail.index("B4") + 1,
                "nir": bands_avail.index("B8") + 1,
                "swir": bands_avail.index("B11") + 1,
                "copyinput": self.copy_input,
                "relrefl": self.rel_refl,
                "keepduplicates": self.keep_dupl,
                "acorfeat": self.acorfeat,
                "pixType": "int16",
                "ram": str(ram)
            }

            features_app = CreateIota2FeatureExtractionApplication(
                feat_parameters)
            if self.copy_input is False:
                in_stack_features_labels = []
            features_labels = in_stack_features_labels + self.get_features_labels(
                dates_enabled, self.rel_refl, self.keep_dupl, self.copy_input)
        else:
            features_app = in_stack
            features_labels = in_stack_features_labels

        app_dep.append([in_stack, in_stack_dep])

        if self.hand_features_flag:
            features_app.Execute()
            app_dep.append(features_app)
            features_app = CreateConcatenateImagesApplication({
                "il": [features_app, userDateFeatures],
                "out":
                features_out,
                "ram":
                str(ram)
            })
            features_labels += fields_userFeat
        return (features_app, app_dep), features_labels
