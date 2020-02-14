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
The landsat 8 sensor class
"""
import logging

# from collections import OrderedDict
# import multiprocessing as mp
# import glob
# import os

# from iota2.Common.OtbAppBank import executeApp

LOGGER = logging.getLogger(__name__)

# in order to avoid issue 'No handlers could be found for logger...'
LOGGER.addHandler(logging.NullHandler())


class landsat_8():
    """
    Landsat 8 sensor
    """
    name = "Landsat8"

    def __init__(self, tile_name, target_proj, all_tiles, image_directory,
                 write_dates_stack, extract_bands_flag, output_target_dir,
                 keep_bands, i2_output_path, temporal_res, auto_date_flag,
                 date_interp_min_user, date_interp_max_user,
                 write_outputs_flag, features, enable_gapfilling,
                 hand_features_flag, hand_features, copy_input, rel_refl,
                 keep_dupl, acorfeat, vhr_path, **kwargs):
        """
        initialize the class landsat_8
        """
        import os
        from collections import OrderedDict
        from iota2.Common import ServiceConfigFile as SCF
        from iota2.Common.FileUtils import get_iota2_project_dir

        self.tile_name = tile_name

        cfg_sensors = os.path.join(get_iota2_project_dir(), "iota2", "Sensors",
                                   "sensors.cfg")
        cfg_sensors = SCF.serviceConfigFile(cfg_sensors, iota_config=False)

        # running attributes

        self.target_proj = target_proj
        self.all_tiles = all_tiles
        self.l8_data = image_directory
        self.tile_directory = os.path.join(self.l8_data, tile_name)
        self.write_dates_stack = write_dates_stack
        self.extract_bands_flag = extract_bands_flag
        self.keep_bands = keep_bands
        self.i2_output_path = i2_output_path
        self.temporal_res = temporal_res
        self.auto_date_flag = auto_date_flag
        self.date_interp_min_user = date_interp_min_user
        self.date_interp_max_user = date_interp_max_user
        self.write_outputs_flag = write_outputs_flag
        self.features = features
        self.enable_gapfilling = enable_gapfilling
        self.hand_features_flag = hand_features_flag
        self.hand_features = hand_features
        self.copy_input = copy_input
        self.rel_refl = rel_refl
        self.keep_dupl = keep_dupl
        self.acorfeat = acorfeat
        self.vhr_path = vhr_path
        self.features_dir = os.path.join(self.i2_output_path, "features",
                                         tile_name)

        if output_target_dir:
            self.output_preprocess_directory = os.path.join(
                output_target_dir, tile_name)
            if not os.path.exists(self.output_preprocess_directory):
                try:
                    os.mkdir(self.output_preprocess_directory)
                except OSError:
                    print(f"Impossible to create directory :"
                          " {self.output_preprocess_directory}")
        else:
            self.output_preprocess_directory = self.tile_directory

        self.struct_path_masks = cfg_sensors.getParam("Landsat8", "arbomask")

        # sensors attributes
        self.native_res = 30
        self.data_type = "FRE"
        self.suffix = "STACK"
        self.masks_date_suffix = "BINARY_MASK"
        self.date_position = 1  # if date's name split by "_"
        self.nodata_value = -10000
        self.masks_rules = OrderedDict([("CLM_XS.tif", 0), ("SAT_XS.tif", 0),
                                        ("EDG_XS.tif", 0)
                                        ])  # 0 mean data, else noData
        self.border_pos = 2
        self.features_names_list = ["NDVI", "NDWI", "Brightness"]

        # define bands to get and their order
        self.stack_band_position = ["B1", "B2", "B3", "B4", "B5", "B6", "B7"]
        self.extracted_bands = None
        if extract_bands_flag:
            # TODO check every mandatory bands still selected
            # -> def check_mandatory bands() return True/False
            self.extracted_bands = [(band_name, band_position + 1)
                                    for band_position, band_name in enumerate(
                                        self.stack_band_position)
                                    if band_name in self.keep_bands]

        # output's names
        self.footprint_name = (f"{self.__class__.name}_{tile_name}_"
                               "footprint.tif")
        ref_image_name = f"{self.__class__.name}_{tile_name}_reference.tif"
        self.ref_image = os.path.join(self.i2_output_path, "features",
                                      tile_name, "tmp", ref_image_name)
        self.time_series_name = f"{self.__class__.name}_{tile_name}_TS.tif"
        self.time_series_masks_name = (f"{self.__class__.name}_{tile_name}"
                                       "_MASKS.tif")
        self.time_series_gapfilling_name = (f"{self.__class__.name}_"
                                            "{tile_name}_TSG.tif")
        self.features_names = f"{self.__class__.name}_{tile_name}_Features.tif"
        # about gapFilling interpolations
        self.input_dates = f"{self.__class__.name}_{tile_name}_input_dates.txt"
        self.interpolated_dates = (f"{self.__class__.name}_{tile_name}"
                                   "_interpolation_dates.txt")

    def get_date_from_name(self, product_name):
        """
        return the date from the name
        """
        return product_name.split("_")[self.date_position].split("-")[0]

    def sort_dates_directories(self, dates_directories):
        """
        sort the dates
        """
        import os
        return sorted(
            dates_directories,
            key=lambda x: int(
                os.path.basename(x).split("_")[self.date_position].split("-")[
                    0]),
        )

    def get_available_dates(self):
        """
        return sorted available dates
        """
        import os
        from iota2.Common.FileUtils import FileSearch_AND

        stacks = sorted(
            FileSearch_AND(self.output_preprocess_directory, True,
                           "{}.tif".format(self.suffix)),
            key=lambda x: int(
                os.path.basename(x).split("_")[self.date_position].split("-")[
                    0]),
        )
        return stacks

    def get_available_dates_masks(self):
        """
        return sorted available masks
        """
        import os
        from iota2.Common.FileUtils import FileSearch_AND

        masks = sorted(FileSearch_AND(self.output_preprocess_directory, True,
                                      f"{self.masks_date_suffix}.tif"),
                       key=lambda x: int(
                           os.path.basename(x).split("_")[self.date_position].
                           split("-")[0]))
        return masks

    def build_stack_date_name(self, date_dir):
        """
        build the stack date name
        """
        import os
        from iota2.Common.FileUtils import FileSearch_AND

        _, b2_name = os.path.split(
            FileSearch_AND(date_dir, True, f"{self.data_type}_B2.tif")[0])
        return b2_name.replace(f"{self.data_type}_B2.tif",
                               f"{self.data_type}_{self.suffix}.tif")

    def preprocess_date(self,
                        date_dir,
                        out_prepro,
                        working_dir=None,
                        ram=128,
                        logger=LOGGER):
        """
        Preprocess each date
        """
        import os
        import shutil
        from gdal import Warp
        import multiprocessing as mp
        from osgeo.gdalconst import GDT_Byte
        from collections import OrderedDict
        from iota2.Common.FileUtils import ensure_dir
        from iota2.Common.FileUtils import getRasterProjectionEPSG
        from iota2.Common.FileUtils import FileSearch_AND
        from iota2.Common.OtbAppBank import CreateConcatenateImagesApplication
        from iota2.Common.OtbAppBank import CreateSuperimposeApplication
        from iota2.Common.OtbAppBank import executeApp
        # manage directories
        date_stack_name = self.build_stack_date_name(date_dir)
        logger.debug(f"preprocessing {date_dir}")
        out_stack = os.path.join(date_dir, date_stack_name)
        if out_prepro:
            _, date_dir_name = os.path.split(date_dir)
            out_dir = os.path.join(out_prepro, date_dir_name)
            if not os.path.exists(out_dir):
                try:
                    os.mkdir(out_dir)
                except OSError:
                    logger.warning(f"{out_dir} already exists")
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
        ensure_dir(os.path.dirname(self.ref_image), raise_exe=False)
        base_ref_projection = getRasterProjectionEPSG(base_ref)

        if not os.path.exists(self.ref_image):
            logger.info(
                f"reference image generation {self.ref_image} from {base_ref}")
            Warp(self.ref_image,
                 base_ref,
                 multithread=True,
                 format="GTiff",
                 xRes=self.native_res,
                 yRes=self.native_res,
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
                # ~ date_stack.ExecuteAndWriteOutput()
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
        preprocess date mask
        """
        import os
        import shutil
        import glob
        import multiprocessing as mp
        from iota2.Common.FileUtils import ensure_dir
        from iota2.Common.OtbAppBank import CreateBandMathApplication
        from iota2.Common.OtbAppBank import CreateSuperimposeApplication
        from iota2.Common.FileUtils import getRasterProjectionEPSG
        from iota2.Common.OtbAppBank import executeApp
        # TODO : throw Exception if no masks are found
        date_mask = []
        for mask_name, _ in list(self.masks_rules.items()):
            date_mask.append(
                glob.glob(
                    os.path.join(date_dir,
                                 f"{self.struct_path_masks}{mask_name}"))[0])

        # manage directories
        mask_dir = os.path.dirname(date_mask[0])
        logger.debug(f"preprocessing {mask_dir} masks")
        mask_name = os.path.basename(date_mask[0]).replace(
            list(self.masks_rules.items())[0][0],
            "{}.tif".format(self.masks_date_suffix),
        )
        out_mask = os.path.join(mask_dir, mask_name)
        if out_prepro:
            out_mask_dir = mask_dir.replace(
                os.path.join(self.l8_data, self.tile_name), out_prepro)
            ensure_dir(out_mask_dir, raise_exe=False)
            out_mask = os.path.join(out_mask_dir, mask_name)

        out_mask_processing = out_mask
        if working_dir:
            out_mask_processing = os.path.join(working_dir, mask_name)

        # build binary mask
        expr = "+".join([f"im{cpt+1}b1" for cpt in range(len(date_mask))])
        expr = f"({expr})==0?0:1"
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
                # ~ superimp.ExecuteAndWriteOutput()
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
            # TODO check if current_date already exists
            preprocessed_dates[current_date] = {
                "data": data_prepro,
                "mask": data_mask
            }
        return preprocessed_dates

    def footprint(self, ram=128):
        """
        compute the footprint
        """
        import os
        import glob
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

        # get date's footprint
        date_edge = []
        for date_dir in input_dates:
            date_edge.append(
                glob.glob(
                    os.path.join(
                        date_dir,
                        "{}{}".format(
                            self.struct_path_masks,
                            list(self.masks_rules.keys())[self.border_pos],
                        ),
                    ))[0])

        expr = " || ".join("1 - im{}b1".format(i + 1)
                           for i in range(len(date_edge)))
        l8_border = CreateBandMathApplication({
            "il": date_edge,
            "exp": expr,
            "ram": str(ram)
        })
        l8_border.Execute()

        reference_raster = self.ref_image
        if self.vhr_path is not None:
            reference_raster = FileSearch_AND(input_dates[0], True,
                                              self.data_type, "COREG",
                                              ".TIF")[0]

        # superimpose footprint
        superimp, _ = CreateSuperimposeApplication({
            "inr": reference_raster,
            "inm": l8_border,
            "out": footprint_out,
            "pixType": "uint8",
            "ram": str(ram),
        })

        # needed to travel throught iota2's library
        app_dep = [l8_border, _]

        return superimp, app_dep

    def write_dates_file(self):
        """
        write dates file
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
                    "-")[0]) for date in input_dates_dir
        ]
        all_available_dates = sorted(all_available_dates)
        all_available_dates = [str(x) for x in all_available_dates]
        if not os.path.exists(date_file):
            with open(date_file, "w") as input_date_file:
                input_date_file.write("\n".join(all_available_dates))
        return date_file, all_available_dates

    def write_interpolation_dates_file(self):
        """
        TODO : mv to base-class
        """
        import os
        from iota2.Common.FileUtils import getDateS2
        from iota2.Common.FileUtils import ensure_dir
        from iota2.Common.FileUtils import dateInterval

        interp_date_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(interp_date_dir, raise_exe=False)
        interp_date_file = os.path.join(interp_date_dir,
                                        self.interpolated_dates)
        # get dates in the whole L8 data-set (getDateS2 -> avail to L8)
        date_interp_min, date_interp_max = getDateS2(self.l8_data,
                                                     self.all_tiles.split(" "))
        # force dates
        if not self.auto_date_flag:
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
            "ram": str(ram),
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
                 dates_time_series,
                 dates_in,
                 len(self.stack_band_position),
                 self.extracted_bands,
                 ram,
             )
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
        get time series gapfilling
        """
        import os
        from iota2.Common.OtbAppBank import CreateImageTimeSeriesGapFillingApplication
        from iota2.Common.FileUtils import ensure_dir

        gap_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(gap_dir, raise_exe=False)
        gap_out = os.path.join(gap_dir, self.time_series_gapfilling_name)

        dates_interp_file, dates_interp = self.write_interpolation_dates_file()
        dates_in_file, _ = self.write_dates_file()

        masks, masks_dep, _ = self.get_time_series_masks()
        (time_series, time_series_dep), _ = self.get_time_series()

        time_series.Execute()
        masks.Execute()

        comp = (len(self.stack_band_position)
                if not self.extracted_bands else len(self.extracted_bands))

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
            f"{self.__class__.name}_{band_name}_{date}"
            for date in dates_interp for band_name in bands
        ]
        return (gap, app_dep), features_labels

    def get_features_labels(self, dates, rel_refl, keep_dupl, copy_in):
        """
        get features labels
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
        get features
        """
        import os
        from iota2.Common.OtbAppBank import CreateConcatenateImagesApplication
        from iota2.Common.OtbAppBank import computeUserFeatures
        from iota2.Common.OtbAppBank import CreateIota2FeatureExtractionApplication
        from iota2.Common.FileUtils import ensure_dir

        features_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(features_dir, raise_exe=False)
        features_out = os.path.join(features_dir, self.features_names)

        ((in_stack, in_stack_dep),
         in_stack_features_labels) = self.get_time_series_gapfilling()
        _, dates_enabled = self.write_interpolation_dates_file()

        if not self.enable_gapfilling:
            (in_stack,
             in_stack_dep), in_stack_features_labels = self.get_time_series()
            _, dates_enabled = self.write_dates_file()

        in_stack.Execute()
        app_dep = []
        if self.hand_features_flag:
            hand_features = self.hand_features
            comp = (len(self.stack_band_position)
                    if not self.extracted_bands else len(self.extracted_bands))
            (user_date_features, fields_userfeat, user_feat_date,
             stack) = computeUserFeatures(in_stack, dates_enabled, comp,
                                          hand_features.split(","))
            user_date_features.Execute()
            app_dep.append([user_date_features, user_feat_date, stack])

        if self.features:
            bands_avail = self.stack_band_position
            if self.extracted_bands:
                bands_avail = [
                    band_name for band_name, _ in self.extracted_bands
                ]
                # check mandatory bands
                if "B4" not in bands_avail:
                    raise Exception(
                        "red band (B4) is needed to compute features")
                if "B5" not in bands_avail:
                    raise Exception(
                        "nir band (B5) is needed to compute features")
                if "B6" not in bands_avail:
                    raise Exception(
                        "swir band (B6) is needed to compute features")
            feat_parameters = {
                "in": in_stack,
                "out": features_out,
                "comp": len(bands_avail),
                "red": bands_avail.index("B4") + 1,
                "nir": bands_avail.index("B5") + 1,
                "swir": bands_avail.index("B6") + 1,
                "copyinput": self.copy_input,
                "relrefl": self.rel_refl,
                "keepduplicates": self.keep_dupl,
                "acorfeat": self.acorfeat,
                "pixType": "int16",
                "ram": str(ram),
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

        if self.hand_features_flag:
            features_app.Execute()
            app_dep.append(features_app)
            features_app = CreateConcatenateImagesApplication({
                "il": [features_app, user_date_features],
                "out":
                features_out,
                "ram":
                str(ram),
            })
            features_labels += fields_userfeat
        return (features_app, app_dep), features_labels
