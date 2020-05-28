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
"""
Landsat 8 old module
"""
import logging

LOGGER = logging.getLogger(__name__)

# in order to avoid issue 'No handlers could be found for logger...'
LOGGER.addHandler(logging.NullHandler())


class landsat_8_old():
    """
    Landsat 8 old class
    """
    name = 'Landsat8Old'

    def __init__(self, tile_name, target_proj, all_tiles, image_directory,
                 write_dates_stack, extract_bands_flag, output_target_dir,
                 keep_bands, i2_output_path, temporal_res, auto_date_flag,
                 date_interp_min_user, date_interp_max_user,
                 write_outputs_flag, features, enable_gapfilling,
                 hand_features_flag, hand_features, copy_input, rel_refl,
                 keep_dupl, acorfeat, vhr_path, **kwargs):
        import os
        from collections import OrderedDict
        from iota2.Common import ServiceConfigFile as SCF
        from iota2.Common.FileUtils import get_iota2_project_dir

        cfg_sensors = os.path.join(get_iota2_project_dir(), "iota2", "Sensors",
                                   "sensors.cfg")
        cfg_sensors = SCF.serviceConfigFile(cfg_sensors, iota_config=False)
        self.struct_path_masks = cfg_sensors.getParam("Landsat8_old",
                                                      "arbomask")

        # running attributes
        self.tile_name = tile_name
        self.target_proj = target_proj
        self.all_tiles = all_tiles
        self.l8_old_data = image_directory
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
        self.enable_gapfilling = enable_gapfilling
        self.hand_features_flag = hand_features_flag
        self.hand_features = hand_features
        self.copy_input = copy_input
        self.rel_refl = rel_refl
        self.keep_dupl = keep_dupl
        self.acorfeat = acorfeat
        self.vhr_path = vhr_path

        self.tile_directory = os.path.join(self.l8_old_data, tile_name)
        self.features_dir = os.path.join(self.i2_output_path, "features",
                                         tile_name)
        if output_target_dir:
            self.output_preprocess_directory = os.path.join(
                output_target_dir, tile_name)
            if not os.path.exists(self.output_preprocess_directory):
                try:
                    os.mkdir(self.output_preprocess_directory)
                except OSError:
                    LOGGER.warning(f"Unable to create directory"
                                   f"{self.output_preprocess_directory}")
        else:
            self.output_preprocess_directory = self.tile_directory

        # sensors attributes
        self.native_res = 30
        self.data_type = "CORR_PENTE"
        self.date_position = 3  # if date's name split by "_"
        self.nodata_value = -10000
        self.masks_rules = OrderedDict([("_DIV.TIF", 1), ("_NUA.TIF", 0),
                                        ("_SAT.TIF", 0)])
        self.border_pos = 0
        self.cloud_pos = 1
        self.sat_pos = 2
        self.features_names_list = ["NDVI", "NDWI", "Brightness"]

        # define bands to get and their order
        self.stack_band_position = ["B1", "B2", "B3", "B4", "B5", "B6", "B7"]
        self.extracted_bands = None
        if extract_bands_flag:
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
        self.time_series_gapfilling_name = (f"{self.__class__.name}"
                                            f"_{tile_name}_TSG.tif")
        self.features_names = "{}_{}_Features.tif".format(
            self.__class__.name, tile_name)
        # about gapFilling interpolations

        self.input_dates = f"{self.__class__.name}_{tile_name}_input_dates.txt"
        self.interpolated_dates = (f"{self.__class__.name}_{tile_name}_"
                                   "interpolation_dates.txt")
        self.working_resolution = kwargs["working_resolution"]

    def get_date_from_name(self, product_name):
        """
        get date from name
        """
        return product_name.split("_")[self.date_position]

    def sort_dates_directories(self, dates_directories):
        """
        sort date directories
        """
        import os
        return sorted(dates_directories,
                      key=lambda x: int(
                          os.path.basename(x).split("_")[self.date_position]))

    def generate_raster_ref(self, base_ref, logger=LOGGER):
        """
        generate raster ref
        """
        import os
        from gdal import Warp
        from osgeo.gdalconst import GDT_Byte
        from iota2.Common.FileUtils import ensure_dir
        from iota2.Common.FileUtils import getRasterProjectionEPSG
        from iota2.Common.FileUtils import getRasterResolution

        ensure_dir(os.path.dirname(self.ref_image), raise_exe=False)
        base_ref_projection = getRasterProjectionEPSG(base_ref)
        base_ref_res_x, base_ref_res_y = getRasterResolution(base_ref)
        if self.working_resolution:
            base_ref_res_x = self.working_resolution[0]
            base_ref_res_y = self.working_resolution[1]

        if not os.path.exists(self.ref_image):
            logger.info(f"reference image generation {self.ref_image} "
                        f"from {base_ref}")
            Warp(self.ref_image,
                 base_ref,
                 multithread=True,
                 format="GTiff",
                 xRes=base_ref_res_x,
                 yRes=base_ref_res_y,
                 outputType=GDT_Byte,
                 srcSRS=f"EPSG:{base_ref_projection}",
                 dstSRS=f"EPSG:{self.target_proj}")

    def footprint(self, ram=128):
        """
        footprint
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
                        date_dir, f"{self.struct_path_masks}"
                        f"{list(self.masks_rules.keys())[self.border_pos]}"))
                [0])

        self.generate_raster_ref(date_edge[0])

        # seek odd values, then sum it
        expr = [
            f"(im{i+1}b1/2==rint(im{i+1}b1/2))" for i in range(len(date_edge))
        ]
        expr = f"{'+'.join(expr)}>0?1:0"
        masks_rules = CreateBandMathApplication({
            "il": date_edge,
            "ram": str(ram),
            "exp": expr
        })
        masks_rules.Execute()
        app_dep = [masks_rules]

        reference_raster = self.ref_image
        if self.vhr_path.lower() != "none":
            reference_raster = FileSearch_AND(input_dates[0], True,
                                              self.data_type, "COREG",
                                              ".TIF")[0]

        superimp, _ = CreateSuperimposeApplication({
            "inr": reference_raster,
            "inm": masks_rules,
            "out": footprint_out,
            "pixType": "uint8",
            "ram": str(ram)
        })
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
            int(os.path.basename(date).split("_")[self.date_position])
            for date in input_dates_dir
        ]
        all_available_dates = sorted(all_available_dates)
        all_available_dates = [str(x) for x in all_available_dates]
        if not os.path.exists(date_file):
            with open(date_file, "w") as input_date_file:
                input_date_file.write("\n".join(all_available_dates))
        return date_file, all_available_dates

    def write_interpolation_dates_file(self, write=True):
        """
        TODO : mv to base-class
        """
        import os
        from iota2.Common.FileUtils import getDateLandsat
        from iota2.Common.FileUtils import ensure_dir
        from iota2.Common.FileUtils import dateInterval

        interp_date_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(interp_date_dir, raise_exe=False)
        interp_date_file = os.path.join(interp_date_dir,
                                        self.interpolated_dates)
        date_interp_min, date_interp_max = getDateLandsat(
            self.l8_old_data, self.all_tiles.split(" "))
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
        from iota2.Common.OtbAppBank import CreateSuperimposeApplication
        from iota2.Common.FileUtils import ensure_dir
        from iota2.Common.FileUtils import getRasterProjectionEPSG
        from iota2.Common.FileUtils import FileSearch_AND
        from iota2.Common.FileUtils import getRasterResolution

        # needed to travel throught iota2's library
        app_dep = []

        input_dates = [
            os.path.join(self.tile_directory, cdir)
            for cdir in os.listdir(self.tile_directory)
        ]
        input_dates = self.sort_dates_directories(input_dates)

        # get date's data
        date_data = []
        for date_dir in input_dates:
            l8_old_date = FileSearch_AND(date_dir, True, self.data_type,
                                         ".TIF")[0]
            if self.vhr_path.lower() != "none":
                l8_old_date = FileSearch_AND(date_dir, True, self.data_type,
                                             "COREG", ".TIF")[0]
            date_data.append(l8_old_date)

        time_series_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(time_series_dir, raise_exe=False)
        times_series_raster = os.path.join(time_series_dir,
                                           self.time_series_name)
        dates_time_series = CreateConcatenateImagesApplication({
            "il": date_data,
            "out": times_series_raster,
            "ram": str(ram)
        })
        _, dates_in = self.write_dates_file()

        # build labels
        features_labels = [
            f"{self.__class__.name}_{band_name}_{date}" for date in dates_in
            for band_name in self.stack_band_position
        ]

        # if not all bands must be used
        if self.extracted_bands:
            app_dep.append(dates_time_series)
            (dates_time_series,
             features_labels) = self.extract_bands_time_series(
                 dates_time_series, dates_in, len(self.stack_band_position),
                 self.extracted_bands, ram)
        origin_proj = getRasterProjectionEPSG(date_data[0])
        same_res = getRasterResolution(date_data[0]) == getRasterResolution(
            self.ref_image)
        if int(origin_proj) != int(self.target_proj) or not same_res:
            dates_time_series.Execute()
            app_dep.append(dates_time_series)
            self.generate_raster_ref(date_data[0])
            dates_time_series, _ = CreateSuperimposeApplication({
                "inr": self.ref_image,
                "inm": self.masks_rules,
                "out": times_series_raster,
                "ram": str(ram)
            })
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
            "{self.__class__.name}_{band_name}_{date}" for date in dates_in
            for band_name, band_pos in extract_bands
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
        get time series masks
        """
        import os
        import glob
        from iota2.Common.OtbAppBank import CreateConcatenateImagesApplication
        from iota2.Common.OtbAppBank import CreateSuperimposeApplication
        from iota2.Common.OtbAppBank import CreateBandMathApplication
        from iota2.Common.FileUtils import ensure_dir
        from iota2.Common.FileUtils import getRasterProjectionEPSG
        from iota2.Common.FileUtils import getRasterResolution

        time_series_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(time_series_dir, raise_exe=False)
        times_series_mask = os.path.join(time_series_dir,
                                         self.time_series_masks_name)

        # needed to travel throught iota2's library
        app_dep = []

        input_dates = [
            os.path.join(self.tile_directory, cdir)
            for cdir in os.listdir(self.tile_directory)
        ]
        input_dates = self.sort_dates_directories(input_dates)

        # get date's data
        date_data = []

        div_mask_patter = list(self.masks_rules.keys())[self.border_pos]
        cloud_mask_patter = list(self.masks_rules.keys())[self.cloud_pos]
        sat_mask_patter = list(self.masks_rules.keys())[self.sat_pos]
        if self.vhr_path.lower() != "none":
            div_mask_patter = div_mask_patter.replace(".TIF", "_COREG.TIF")
            cloud_mask_patter = div_mask_patter.replace(".TIF", "_COREG.TIF")
            sat_mask_patter = div_mask_patter.replace(".TIF", "_COREG.TIF")

        for date_dir in input_dates:
            div_mask = glob.glob(
                os.path.join(
                    date_dir, "{}{}".format(self.struct_path_masks,
                                            div_mask_patter)))[0]
            cloud_mask = glob.glob(
                os.path.join(
                    date_dir, "{}{}".format(self.struct_path_masks,
                                            cloud_mask_patter)))[0]
            sat_mask = glob.glob(
                os.path.join(
                    date_dir, "{}{}".format(self.struct_path_masks,
                                            sat_mask_patter)))[0]
            # im1 = div, im2 = cloud, im3 = sat
            div_expr = "(1-(im1b1/2==rint(im1b1/2)))"
            cloud_expr = "im2b1"
            sat_expr = "im3b1"
            #~ expr = "*".join([div_expr, cloud_expr, sat_expr])
            expr = "({} + {} + {})==0?0:1".format(div_expr, cloud_expr,
                                                  sat_expr)
            date_binary_mask = CreateBandMathApplication({
                "il": [div_mask, cloud_mask, sat_mask],
                "exp":
                expr
            })
            date_binary_mask.Execute()
            date_data.append(date_binary_mask)
            app_dep.append(date_binary_mask)
        dates_time_series_mask = CreateConcatenateImagesApplication({
            "il":
            date_data,
            "ram":
            str(ram),
            "out":
            times_series_mask
        })

        origin_proj = getRasterProjectionEPSG(sat_mask)
        same_res = getRasterResolution(sat_mask) == getRasterResolution(
            self.ref_image)
        if int(origin_proj) != int(self.target_proj) or not same_res:
            dates_time_series_mask.Execute()
            app_dep.append(dates_time_series_mask)
            self.generate_raster_ref(sat_mask)
            dates_time_series_mask, _ = CreateSuperimposeApplication({
                "inr":
                self.ref_image,
                "inm":
                dates_time_series_mask,
                "interpolator":
                "nn",
                "out":
                times_series_mask,
                "ram":
                str(ram)
            })

        return dates_time_series_mask, app_dep, len(date_data)

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
        get features labels
        """
        if rel_refl and keep_dupl is False and copy_in is True:
            self.features_names_list = ["NDWI", "Brightness"]
        out_labels = []

        for feature in self.features_names_list:
            for date in dates:
                out_labels.append(f"{self.__class__.name}_{feature}"
                                  f"_{date}")
        return out_labels

    def get_features(self, ram=128):
        """
        get features
        """
        import os
        from iota2.Common.OtbAppBank import CreateConcatenateImagesApplication
        from iota2.Common.OtbAppBank import CreateIota2FeatureExtractionApplication
        from iota2.Common.OtbAppBank import computeUserFeatures
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
            comp = len(
                self.stack_band_position) if not self.extracted_bands else len(
                    self.extracted_bands)
            (user_date_features, fields_userfeat, user_feat_date,
             stack) = computeUserFeatures(in_stack, dates_enabled, comp,
                                          self.hand_features.split(","))
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

        if self.hand_features_flag:
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
