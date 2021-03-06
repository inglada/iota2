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
This is the sentinel 2 sen2cor class definition
"""
import logging

LOGGER = logging.getLogger(__name__)

# in order to avoid issue 'No handlers could be found for logger...'
LOGGER.addHandler(logging.NullHandler())


class sentinel_2_s2c():
    """
    Sensor class for sentinel 2 Sen2cor images
    """
    name = 'Sentinel2S2C'

    def __init__(self, tile_name, target_proj, all_tiles, image_directory,
                 write_dates_stack, extract_bands_flag, output_target_dir,
                 keep_bands, i2_output_path, temporal_res, auto_date_flag,
                 date_interp_min_user, date_interp_max_user,
                 write_outputs_flag, features, enable_gapfilling,
                 hand_features_flag, hand_features, copy_input, rel_refl,
                 keep_dupl, acorfeat, vhr_path, **kwargs):
        """
        Construct the sentinel_2_s2c class
        """
        import os
        from iota2.Common import ServiceConfigFile as SCF
        from iota2.Common.FileUtils import get_iota2_project_dir

        self.tile_name = tile_name
        # self.cfg_iota2 = SCF.serviceConfigFile(config_path)
        cfg_sensors = os.path.join(get_iota2_project_dir(), "iota2", "Sensors",
                                   "sensors.cfg")
        cfg_sensors = SCF.serviceConfigFile(cfg_sensors, iota_config=False)

        # running attributes
        self.copy_input = copy_input
        self.rel_refl = rel_refl
        self.i2_output_path = i2_output_path
        self.keep_dupl = keep_dupl
        self.acorfeat = acorfeat
        self.features = features
        self.enable_gapfilling = enable_gapfilling
        self.hand_features_flag = hand_features_flag
        self.hand_features = hand_features
        self.auto_date_flag = auto_date_flag
        self.date_interp_min_user = date_interp_min_user
        self.date_interp_max_user = date_interp_max_user
        self.target_proj = target_proj
        self.all_tiles = all_tiles
        self.s2_s2c_data = image_directory
        self.tile_directory = os.path.join(self.s2_s2c_data, tile_name)
        self.struct_path_masks = cfg_sensors.getParam("Sentinel_2_S2C",
                                                      "arbomask")
        self.write_dates_stack = write_dates_stack
        self.features_dir = os.path.join(self.i2_output_path, "features",
                                         tile_name)
        self.write_outputs_flag = write_outputs_flag

        if output_target_dir:
            self.output_preprocess_directory = os.path.join(
                output_target_dir, tile_name)
            if not os.path.exists(self.output_preprocess_directory):
                try:
                    os.mkdir(self.output_preprocess_directory)
                except Exception:
                    print(f"Unable to create directory"
                          "{self.output_preprocess_directory}")
        else:
            #  self.output_preprocess_directory = self.tile_directory
            self.output_preprocess_directory = None

        # sensors attributes
        self.suffix = "STACK"
        self.masks_date_suffix = "BINARY_MASK"
        self.scene_classif = "SCL_20m.jp2"
        self.invalid_flags = [0, 1, 3, 8, 9, 10]
        self.nodata_flag = 0
        self.date_position = 2  # if date's name split by "_"
        self.features_names_list = ["NDVI", "NDWI", "Brightness"]

        # define bands to get and their order
        self.stack_band_position = [
            "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11",
            "B12"
        ]
        self.extracted_bands = None
        if extract_bands_flag:
            # TODO check every mandatory bands still selected
            # -> def check_mandatory bands() return True/False
            self.extracted_bands = [(band_name, band_position + 1)
                                    for band_position, band_name in enumerate(
                                        self.stack_band_position)
                                    if band_name in keep_bands]

        # output's names
        self.footprint_name = "{}_{}_footprint.tif".format(
            self.__class__.name, tile_name)
        ref_image_name = "{}_{}_reference.tif".format(self.__class__.name,
                                                      tile_name)
        self.ref_image = os.path.join(i2_output_path, "features", tile_name,
                                      "tmp", ref_image_name)

        self.time_series_name = "{}_{}_TS.tif".format(self.__class__.name,
                                                      tile_name)
        self.time_series_masks_name = "{}_{}_MASKS.tif".format(
            self.__class__.name, tile_name)
        self.time_series_gapfilling_name = "{}_{}_TSG.tif".format(
            self.__class__.name, tile_name)
        self.features_names = "{}_{}_Features.tif".format(
            self.__class__.name, tile_name)
        # about gapFilling interpolations
        self.temporal_res = temporal_res
        self.input_dates = "{}_{}_input_dates.txt".format(
            self.__class__.name, tile_name)
        self.interpolated_dates = "{}_{}_interpolation_dates.txt".format(
            self.__class__.name, tile_name)
        self.vhr_path = vhr_path
        self.working_resolution = kwargs["working_resolution"]

    def sort_dates_directories(self, dates_directories):
        """
        sort date directories
        """
        import os
        return sorted(dates_directories,
                      key=lambda x: int(
                          os.path.basename(x).split("_")[self.date_position].
                          split("T")[0]))

    def get_date_from_name(self, product_name):
        """
        return the date from image name
        """
        return product_name.split("_")[self.date_position].split("T")[0]

    def get_date_dir(self, date_dir, size):
        """
        get date dir
        """
        import os
        from iota2.Common.FileUtils import FileSearch_AND
        if size == 10:
            target_dir, _ = os.path.split(
                FileSearch_AND(date_dir, True, "10m.jp2")[0])
        elif size == 20:
            target_dir, _ = os.path.split(
                FileSearch_AND(date_dir, True, "B02_20m.jp2")[0])
        else:
            raise Exception("size not in [10, 20]")
        return target_dir

    def build_date_name(self, date_dir, suffix):
        """
        build date name
        """
        import os
        from iota2.Common.FileUtils import FileSearch_AND
        _, b2_name = os.path.split(
            FileSearch_AND(date_dir, True, "B02_10m.jp2")[0])
        return b2_name.replace("B02_10m.jp2", "{}.tif".format(suffix))

    def preprocess_date(self,
                        date_dir,
                        out_prepro,
                        working_dir=None,
                        ram=128,
                        logger=LOGGER):
        """
        preprocess date
        """
        import os
        import shutil
        from collections import OrderedDict
        from gdal import Warp
        from osgeo.gdalconst import GDT_Byte
        import multiprocessing as mp
        from iota2.Common.FileUtils import ensure_dir
        from iota2.Common.FileUtils import FileSearch_AND
        from iota2.Common.FileUtils import getRasterProjectionEPSG
        from iota2.Common.OtbAppBank import CreateConcatenateImagesApplication
        from iota2.Common.OtbAppBank import CreateSuperimposeApplication
        from iota2.Common.OtbAppBank import executeApp
        from iota2.Common.FileUtils import getRasterResolution

        # manage directories
        date_stack_name = self.build_date_name(date_dir, self.suffix)
        logger.debug(f"preprocessing {date_dir}")
        r10_dir = self.get_date_dir(date_dir, 10)

        out_stack = os.path.join(r10_dir, date_stack_name)
        if out_prepro:
            out_dir = r10_dir.replace(date_dir, out_prepro)
            ensure_dir(out_dir, raise_exe=False)
            out_stack = os.path.join(out_dir, date_stack_name)
        out_stack_processing = out_stack
        if working_dir:
            out_stack_processing = os.path.join(working_dir, date_stack_name)

        # get bands
        date_bands = []
        for band in self.stack_band_position:
            if band in ["B02", "B03", "B04", "B08"]:
                date_bands.append(
                    FileSearch_AND(date_dir, True,
                                   "{}_".format(self.tile_name),
                                   "{}_10m.jp2".format(band))[0])
            elif band in ["B05", "B06", "B07", "B8A", "B11", "B12"]:
                date_bands.append(
                    FileSearch_AND(date_dir, True,
                                   "{}_".format(self.tile_name),
                                   "{}_20m.jp2".format(band))[0])
        # tile reference image generation
        base_ref = date_bands[0]
        logger.info(f"reference image generation {self.ref_image}"
                    f" from {base_ref}")
        ensure_dir(os.path.dirname(self.ref_image), raise_exe=False)
        base_ref_projection = getRasterProjectionEPSG(base_ref)
        base_ref_res_x, base_ref_res_y = getRasterResolution(base_ref)
        if self.working_resolution:
            base_ref_res_x = self.working_resolution[0]
            base_ref_res_y = self.working_resolution[1]

        if not os.path.exists(self.ref_image):
            Warp(self.ref_image,
                 base_ref,
                 multithread=True,
                 format="GTiff",
                 xRes=base_ref_res_x,
                 yRes=base_ref_res_y,
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
            same_res = True
            if os.path.exists(out_stack):
                same_proj = int(getRasterProjectionEPSG(out_stack)) == int(
                    self.target_proj)
                same_res = getRasterResolution(
                    out_stack) == getRasterResolution(self.ref_image)
            if not os.path.exists(
                    out_stack) or same_proj is False or not same_res:
                # date_stack.ExecuteAndWriteOutput()
                multi_proc = mp.Process(target=executeApp, args=[date_stack])
                multi_proc.start()
                multi_proc.join()
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
        preprocess date masks
        """
        import shutil
        import os
        import multiprocessing as mp
        from iota2.Common.FileUtils import FileSearch_AND
        from iota2.Common.FileUtils import ensure_dir
        from iota2.Common.OtbAppBank import CreateBandMathApplication
        from iota2.Common.OtbAppBank import CreateSuperimposeApplication
        from iota2.Common.FileUtils import getRasterProjectionEPSG
        from iota2.Common.OtbAppBank import executeApp
        # manage directories
        date_mask_name = self.build_date_name(date_dir, self.masks_date_suffix)
        logger.debug(f"preprocessing {date_dir}")
        r10_dir = self.get_date_dir(date_dir, 10)
        out_mask = os.path.join(r10_dir, date_mask_name)
        if out_prepro:
            out_dir = r10_dir.replace(date_dir, out_prepro)
            ensure_dir(out_dir, raise_exe=False)
            out_mask = os.path.join(out_dir, date_mask_name)
        out_mask_processing = out_mask
        if working_dir:
            out_mask_processing = os.path.join(working_dir, date_mask_name)

        r20m_dir = self.get_date_dir(date_dir, 20)
        scl = FileSearch_AND(r20m_dir, True, self.scene_classif)[0]
        invalid_expr = " or ".join(
            ["im1b1=={}".format(flag) for flag in self.invalid_flags])
        binary_mask = CreateBandMathApplication({
            "il":
            scl,
            "exp":
            "{}?1:0".format(invalid_expr),
            "pixType":
            "uint8"
        })
        binary_mask.Execute()
        app_dep = [binary_mask]

        superimp, _ = CreateSuperimposeApplication({
            "inr": self.ref_image,
            "inm": binary_mask,
            "interpolator": "nn",
            "out": out_mask_processing,
            "pixType": "uint8",
            "ram": str(ram)
        })
        if self.write_dates_stack:
            same_proj = False
            same_res = True
            if os.path.exists(out_mask):
                same_proj = int(getRasterProjectionEPSG(out_mask)) == int(
                    self.target_proj)
                same_res = getRasterProjectionEPSG(
                    out_mask) == getRasterProjectionEPSG(self.ref_image)

            if not os.path.exists(
                    out_mask) or same_proj is False or not same_res:
                # superimp.ExecuteAndWriteOutput()
                multi_proc = mp.Process(target=executeApp, args=[superimp])
                multi_proc.start()
                multi_proc.join()
                if working_dir:
                    shutil.copy(out_mask_processing, out_mask)
                    os.remove(out_mask_processing)

        return superimp, app_dep

    def preprocess(self, working_dir=None, ram=128):
        """
        preprocess
        """
        import os
        from collections import OrderedDict
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
        compute footprint of images
        """
        import os
        from iota2.Common.OtbAppBank import CreateSuperimposeApplication
        from iota2.Common.OtbAppBank import CreateBandMathApplication
        from iota2.Common.FileUtils import ensure_dir
        from iota2.Common.FileUtils import FileSearch_AND

        footprint_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(footprint_dir, raise_exe=False)
        footprint_out = os.path.join(footprint_dir, self.footprint_name)

        input_dates = [
            os.path.join(self.tile_directory, cdir)
            for cdir in os.listdir(self.tile_directory)
        ]
        input_dates = self.sort_dates_directories(input_dates)
        all_scl = []
        for date_dir in input_dates:
            r20m_dir = self.get_date_dir(date_dir, 20)
            scl = FileSearch_AND(r20m_dir, True, self.scene_classif)[0]
            all_scl.append(scl)
        sum_scl = "+".join(
            ["im{}b1".format(i + 1) for i in range(len(all_scl))])
        edge = CreateBandMathApplication({
            "il": all_scl,
            "exp": "{}==0?0:1".format(sum_scl)
        })
        edge.Execute()
        app_dep = [edge]

        # superimpose footprint
        reference_raster = self.ref_image
        if self.vhr_path.lower() != "none":
            reference_raster = self.get_available_dates()[0]
        superimp, _ = CreateSuperimposeApplication({
            "inr": reference_raster,
            "inm": edge,
            "out": footprint_out,
            "pixType": "uint8",
            "ram": str(ram)
        })
        # needed to travel throught iota2's library
        app_dep.append(_)

        return superimp, app_dep

    def get_available_dates(self):
        """
        return sorted available dates
        """
        import os
        from iota2.Common.FileUtils import FileSearch_AND
        target_folder = self.tile_directory
        if self.output_preprocess_directory:
            target_folder = self.output_preprocess_directory

        pattern = "{}.tif".format(self.suffix)
        if self.vhr_path.lower() != "none":
            pattern = "{}_COREG.tif".format(self.suffix)

        stacks = sorted(FileSearch_AND(target_folder, True, pattern),
                        key=lambda x: os.path.basename(x).split("_")[
                            self.date_position].split("T")[0])
        return stacks

    def get_available_dates_masks(self):
        """
        return sorted available masks
        """
        import os
        from iota2.Common.FileUtils import FileSearch_AND
        target_folder = self.tile_directory
        if self.output_preprocess_directory:
            target_folder = self.output_preprocess_directory

        pattern = "{}.tif".format(self.masks_date_suffix)
        if self.vhr_path.lower() != "none":
            pattern = "{}_COREG.tif".format(self.masks_date_suffix)

        masks = sorted(FileSearch_AND(target_folder, True, pattern),
                       key=lambda x: os.path.basename(x).split("_")[
                           self.date_position].split("T")[0])
        return masks

    def write_interpolation_dates_file(self, write=True):
        """
        TODO : mv to base-class
        """
        import os
        from iota2.Common.FileUtils import getDateS2_S2C
        from iota2.Common.FileUtils import ensure_dir
        from iota2.Common.FileUtils import dateInterval

        interp_date_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(interp_date_dir, raise_exe=False)
        interp_date_file = os.path.join(interp_date_dir,
                                        self.interpolated_dates)
        # get dates in the whole S2 data-set
        date_interp_min, date_interp_max = getDateS2_S2C(
            self.s2_s2c_data, self.all_tiles.split(" "))
        # force dates
        if not self.auto_date_flag:
            date_interp_min = self.date_interp_min_user
            date_interp_max = self.date_interp_max_user

        dates = [
            str(date).replace("-", "") for date in dateInterval(
                date_interp_min, date_interp_max, self.temporal_res)
        ]
        if not os.path.exists(interp_date_file) and write:
            with open(interp_date_file, "w") as interpolation_date_file:
                interpolation_date_file.write("\n".join(dates))
        return interp_date_file, dates

    def write_dates_file(self):
        """
        write date file
        """
        import os
        input_dates_dir = [
            os.path.join(self.tile_directory, cdir)
            for cdir in os.listdir(self.tile_directory)
        ]
        date_file = os.path.join(self.features_dir, "tmp", self.input_dates)
        all_available_dates = [
            int(
                os.path.basename(date).split("_")[self.date_position].split(
                    "T")[0]) for date in input_dates_dir
        ]
        all_available_dates = sorted(all_available_dates)
        # sort requires int but input_date_file requires str
        all_available_dates = [str(x) for x in all_available_dates]
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
        import os
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
        # time_series_out = dates_time_series.GetParameterString("out")
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
        TODO : be able of using a date interval
        Return
        ------
            list
                [(otb_Application, some otb's objects), time_series_labels]
                Functions dealing with otb's application instance has to 
                returns every objects in the pipeline
        """
        import os
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

    def get_time_series_gapfilling(self, ram=128):
        """
        get time series after gapfilling
        """
        import os
        import multiprocessing as mp
        from iota2.Common.OtbAppBank import CreateImageTimeSeriesGapFillingApplication
        from iota2.Common.FileUtils import ensure_dir
        from iota2.Common.OtbAppBank import getInputParameterOutput
        from iota2.Common.OtbAppBank import executeApp
        gap_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(gap_dir, raise_exe=False)
        gap_out = os.path.join(gap_dir, self.time_series_gapfilling_name)

        dates_interp_file, dates_interp = self.write_interpolation_dates_file()
        dates_in_file, _ = self.write_dates_file()

        masks, masks_dep, _ = self.get_time_series_masks()
        (time_series, time_series_dep), _ = self.get_time_series()

        # time_series.Execute()
        # masks.Execute()
        # inputs
        if self.write_outputs_flag is False:
            time_series.Execute()
            masks.Execute()
        else:
            time_series_raster = time_series.GetParameterValue(
                getInputParameterOutput(time_series))
            masks_raster = masks.GetParameterValue(
                getInputParameterOutput(masks))
            if not os.path.exists(masks_raster):
                multi_proc = mp.Process(target=executeApp, args=[masks])
                multi_proc.start()
                multi_proc.join()
            if not os.path.exists(time_series_raster):
                # time_series.ExecuteAndWriteOutput()
                multi_proc = mp.Process(target=executeApp, args=[time_series])
                multi_proc.start()
                multi_proc.join()
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
        return the feature labels
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
        Get features
        """
        import os
        from iota2.Common.OtbAppBank import CreateConcatenateImagesApplication
        from iota2.Common.OtbAppBank import computeUserFeatures
        from iota2.Common.OtbAppBank import CreateIota2FeatureExtractionApplication
        from iota2.Common.FileUtils import ensure_dir

        features_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(features_dir, raise_exe=False)
        features_out = os.path.join(features_dir, self.features_names)

        features = self.features
        enable_gapfilling = self.enable_gapfilling
        hand_features_flag = self.hand_features_flag

        (in_stack, in_stack_dep
         ), in_stack_features_labels = self.get_time_series_gapfilling()
        _, dates_enabled = self.write_interpolation_dates_file()

        if not enable_gapfilling:
            (in_stack,
             in_stack_dep), in_stack_features_labels = self.get_time_series()
            _, dates_enabled = self.write_dates_file()

        in_stack.Execute()

        app_dep = []
        if hand_features_flag:
            hand_features = self.hand_features
            comp = len(
                self.stack_band_position) if not self.extracted_bands else len(
                    self.extracted_bands)
            user_date_features, fields_userfeat, user_feat_date, stack = (
                computeUserFeatures(in_stack, dates_enabled, comp,
                                    hand_features.split(",")))
            user_date_features.Execute()
            app_dep.append([user_date_features, user_feat_date, stack])

        if features:
            bands_avail = self.stack_band_position
            if self.extracted_bands:
                bands_avail = [
                    band_name for band_name, _ in self.extracted_bands
                ]
                # check mandatory bands
                if "B04" not in bands_avail:
                    raise Exception(
                        "red band (B04) is needed to compute features")
                if "B08" not in bands_avail:
                    raise Exception(
                        "nir band (B08) is needed to compute features")
                if "B11" not in bands_avail:
                    raise Exception(
                        "swir band (B11) is needed to compute features")
            feat_parameters = {
                "in": in_stack,
                "out": features_out,
                "comp": len(bands_avail),
                "red": bands_avail.index("B04") + 1,
                "nir": bands_avail.index("B08") + 1,
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
            features_labels = (
                in_stack_features_labels +
                self.get_features_labels(dates_enabled, self.rel_refl,
                                         self.keep_dupl, self.copy_input))
        else:
            features_app = in_stack
            features_labels = in_stack_features_labels

        app_dep.append([in_stack, in_stack_dep])

        if hand_features_flag:
            features_app.Execute()
            app_dep.append(features_app)
            features_app = CreateConcatenateImagesApplication({
                "il": [features_app, user_date_features],
                "out":
                features_out,
                "ram":
                str(ram)
            })
            features_labels += fields_userfeat
        return (features_app, app_dep), features_labels
