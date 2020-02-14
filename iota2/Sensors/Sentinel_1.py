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
"""sentinel_1 class definition"""

import os
import logging
from collections import OrderedDict

LOGGER = logging.getLogger(__name__)

#in order to avoid issue 'No handlers could be found for logger...'
LOGGER.addHandler(logging.NullHandler())


class sentinel_1():
    """sentinel_1 class definition"""
    name = 'Sentinel1'

    def __init__(self, tile_name: str, image_directory: str, all_tiles: str,
                 i2_output_path: str, enable_gapfilling: bool,
                 write_outputs_flag: bool, **kwargs):
        """
        """
        import configparser

        self.tile_name = tile_name

        config_parser = configparser.ConfigParser()

        # running attributes
        self.s1_cfg = image_directory
        self.write_outputs_flag = write_outputs_flag
        config_parser.read(self.s1_cfg)
        s1_output_processing = config_parser.get('Paths', 'output')
        self.all_tiles = all_tiles
        self.output_processing = os.path.join(s1_output_processing,
                                              tile_name[1:])
        self.i2_output_path = i2_output_path
        self.features_dir = os.path.join(self.i2_output_path, "features",
                                         tile_name)
        self.use_gapfilling = enable_gapfilling
        # sensors attributes
        self.mask_pattern = "BorderMask.tif"
        # output's names
        self.mask_orbit_pol_name = "{}_{}_MASK".format(self.__class__.name,
                                                       tile_name)
        self.gapfilling_orbit_pol_name = "{}_{}_TSG".format(
            self.__class__.name, tile_name)
        self.gapfilling_orbit_pol_name_mask = "{}_{}_MASK".format(
            self.__class__.name, tile_name)
        self.sar_features_name = "{}_{}_Features.tif".format(
            self.__class__.name, tile_name)
        self.user_sar_features_name = "{}_{}_USER_Features.tif".format(
            self.__class__.name, tile_name)
        self.footprint_name = "{}_{}_footprint.tif".format(
            self.__class__.name, tile_name)

    def get_available_dates(self):
        """
        return sorted available dates
        """
    def get_available_dates_masks(self):
        """
        return sorted available masks
        """
    def preprocess(self, working_dir=None, ram=128, logger=LOGGER):
        """sentinel_1 preprocessing
        """
        from .SAR.S1Processor import S1PreProcess
        S1PreProcess(self.s1_cfg, self.tile_name, working_dir)

    def footprint(self, ram=128):
        """get sentinel_1 footprint
        """
        from iota2.Common.OtbAppBank import CreateBandMathApplication
        from iota2.Common.FileUtils import FileSearch_AND
        s1_border_masks = FileSearch_AND(self.output_processing, True,
                                         self.mask_pattern)

        sum_mask = "+".join(
            ["im{}b1".format(i + 1) for i in range(len(s1_border_masks))])
        expression = "{}=={}?0:1".format(sum_mask, len(s1_border_masks))
        raster_footprint = os.path.join(self.features_dir, "tmp",
                                        self.footprint_name)
        footprint_app = CreateBandMathApplication({
            "il": s1_border_masks,
            "out": raster_footprint,
            "exp": expression,
            "ram": str(ram)
        })
        footprint_app_dep = []
        return footprint_app, footprint_app_dep

    def get_time_series(self, ram=128):
        """
        Due to the SAR data, time series must be split by polarisation
        and orbit (ascending / descending)
        """
        from iota2.Common.OtbAppBank import getSARstack
        from iota2.Common.FileUtils import getNbDateInTile
        (all_filtered, all_masks, interp_date_files,
         input_date_files) = getSARstack(self.s1_cfg,
                                         self.tile_name,
                                         self.all_tiles.split(" "),
                                         os.path.join(self.i2_output_path,
                                                      "features"),
                                         workingDirectory=None)
        # to be clearer
        s1_data = OrderedDict()
        s1_labels = OrderedDict()

        for filtered, _, _, in_dates in zip(all_filtered, all_masks,
                                            interp_date_files,
                                            input_date_files):
            sar_mode = os.path.basename(
                filtered.GetParameterValue("outputstack"))
            sar_mode = "_".join(os.path.splitext(sar_mode)[0].split("_")[0:-1])
            polarisation = sar_mode.split("_")[1]
            orbit = sar_mode.split("_")[2]

            s1_data[sar_mode] = filtered
            sar_dates = sorted(getNbDateInTile(in_dates,
                                               display=False,
                                               raw_dates=True),
                               key=lambda x: int(x))
            labels = [
                "{}_{}_{}_{}".format(self.__class__.name, orbit, polarisation,
                                     date).lower() for date in sar_dates
            ]
            s1_labels[sar_mode] = labels
        dependancies = []
        return (s1_data, dependancies), s1_labels

    def get_time_series_masks(self, ram=128, logger=LOGGER):
        """
        Due to the SAR data, masks series must be split by polarisation
        and orbit (ascending / descending)
        """
        from iota2.Common.OtbAppBank import getSARstack
        from iota2.Common.OtbAppBank import CreateConcatenateImagesApplication
        (all_filtered, all_masks, interp_date_files,
         input_date_files) = getSARstack(self.s1_cfg,
                                         self.tile_name,
                                         self.all_tiles.split(" "),
                                         os.path.join(self.i2_output_path,
                                                      "features"),
                                         workingDirectory=None)
        # to be clearer
        s1_masks = OrderedDict()
        nb_avail_masks = 0
        for filtered, masks, _, _ in zip(all_filtered, all_masks,
                                         interp_date_files, input_date_files):
            sar_mode = os.path.basename(
                filtered.GetParameterValue("outputstack"))
            sar_mode = "_".join(os.path.splitext(sar_mode)[0].split("_")[0:-1])
            polarisation = sar_mode.split("_")[1]
            orbit = sar_mode.split("_")[2]
            mask_orbit_pol_name = f"{self.mask_orbit_pol_name}_{orbit}_{polarisation}.tif"

            mask_orbit_pol = os.path.join(self.features_dir, "tmp",
                                          mask_orbit_pol_name)
            masks_app = CreateConcatenateImagesApplication({
                "il":
                masks,
                "out":
                mask_orbit_pol,
                "pixType":
                "uint8" if len(masks) > 255 else "uint16",
                "ram":
                str(ram)
            })
            s1_masks[sar_mode] = masks_app
            nb_avail_masks += len(masks)

        dependancies = []
        return s1_masks, dependancies, nb_avail_masks

    def get_time_series_gapFilling(self, ram=128):
        """
        Due to the SAR data, time series must be split by polarisation
        and orbit (ascending / descending)
        """
        import configparser

        from iota2.Common.FileUtils import getNbDateInTile
        from iota2.Common.OtbAppBank import getSARstack
        from iota2.Common.OtbAppBank import CreateConcatenateImagesApplication
        from iota2.Common.OtbAppBank import CreateImageTimeSeriesGapFillingApplication
        from iota2.Common.OtbAppBank import getInputParameterOutput

        (all_filtered, all_masks, interp_date_files,
         input_date_files) = getSARstack(self.s1_cfg,
                                         self.tile_name,
                                         self.all_tiles.split(" "),
                                         os.path.join(self.i2_output_path,
                                                      "features"),
                                         workingDirectory=None)
        # to be clearer
        s1_data = OrderedDict()
        s1_labels = OrderedDict()

        config = configparser.ConfigParser()
        config.read(self.s1_cfg)

        interpolation_method = "linear"
        if config.has_option("Processing", "gapFilling_interpolation"):
            interpolation_method = config.get("Processing",
                                              "gapFilling_interpolation")
        dependancies = []

        for filtered, masks, interp_dates, in_dates in zip(
                all_filtered, all_masks, interp_date_files, input_date_files):
            sar_mode = os.path.basename(
                filtered.GetParameterValue("outputstack"))
            sar_mode = "_".join(os.path.splitext(sar_mode)[0].split("_")[0:-1])
            polarisation = sar_mode.split("_")[1]
            orbit = sar_mode.split("_")[2]

            gapfilling_orbit_pol_name_masks = f"{self.gapfilling_orbit_pol_name_mask}_{orbit}_{polarisation}.tif"
            gapfilling_raster_mask = os.path.join(
                self.features_dir, "tmp", gapfilling_orbit_pol_name_masks)

            masks_stack = CreateConcatenateImagesApplication({
                "il": masks,
                "out": gapfilling_raster_mask,
                "ram": str(ram)
            })

            if self.write_outputs_flag is False:
                filtered.Execute()
                masks_stack.Execute()
            else:
                filtered_raster = filtered.GetParameterValue(
                    getInputParameterOutput(filtered))
                masks_stack_raster = masks_stack.GetParameterValue(
                    getInputParameterOutput(masks_stack))
                if not os.path.exists(masks_stack_raster):
                    masks_stack.ExecuteAndWriteOutput()
                if not os.path.exists(filtered_raster):
                    filtered.ExecuteAndWriteOutput()
                if os.path.exists(masks_stack_raster):
                    masks_stack = masks_stack_raster
                if os.path.exists(filtered_raster):
                    filtered = filtered_raster
            dependancies.append((filtered, masks_stack))
            gapfilling_orbit_pol_name = f"{self.gapfilling_orbit_pol_name}_{orbit}_{polarisation}.tif"
            gapfilling_raster = os.path.join(self.features_dir, "tmp",
                                             gapfilling_orbit_pol_name)

            gap_app = CreateImageTimeSeriesGapFillingApplication({
                "in":
                filtered,
                "mask":
                masks_stack,
                "it":
                interpolation_method,
                "id":
                in_dates,
                "od":
                interp_dates,
                "comp":
                str(1),
                "out":
                gapfilling_raster
            })
            s1_data[sar_mode] = gap_app

            sar_dates = sorted(getNbDateInTile(interp_dates,
                                               display=False,
                                               raw_dates=True),
                               key=lambda x: int(x))
            labels = [
                "{}_{}_{}_{}".format(self.__class__.name, orbit, polarisation,
                                     date).lower() for date in sar_dates
            ]
            s1_labels[sar_mode] = labels
        return (s1_data, dependancies), s1_labels

    def get_features(self, ram=128, logger=LOGGER):
        """get sar features
        """
        import configparser
        from iota2.Common.FileUtils import getNbDateInTile, FileSearch_AND
        from iota2.Common.OtbAppBank import CreateConcatenateImagesApplication
        from iota2.Common.OtbAppBank import generateSARFeat_dates
        from iota2.Common.OtbAppBank import getInputParameterOutput

        if self.use_gapfilling:
            (s1_data,
             dependancies), s1_labels = self.get_time_series_gapFilling(ram)
        else:
            (s1_data, dependancies), s1_labels = self.get_time_series(ram)
        config = configparser.ConfigParser()
        config.read(self.s1_cfg)

        sar_features_expr = None
        if config.has_option("Features", "expression"):
            sar_features_expr_cfg = config.get("Features", "expression")
            if not "none" in sar_features_expr_cfg.lower():
                sar_features_expr = sar_features_expr_cfg.split(",")

        dependancies = [dependancies]
        s1_features = []
        sar_time_series = {
            "asc": {
                "vv": {
                    "App": None,
                    "availDates": None
                },
                "vh": {
                    "App": None,
                    "availDates": None
                }
            },
            "des": {
                "vv": {
                    "App": None,
                    "availDates": None
                },
                "vh": {
                    "App": None,
                    "availDates": None
                }
            }
        }
        for sensor_mode, time_series_app in list(s1_data.items()):
            _, polarisation, orbit = sensor_mode.split("_")
            # inputs
            if self.write_outputs_flag is False:
                time_series_app.Execute()
            else:
                time_series_raster = time_series_app.GetParameterValue(
                    getInputParameterOutput(time_series_app))
                if not os.path.exists(time_series_raster):
                    time_series_app.ExecuteAndWriteOutput()
                if os.path.exists(time_series_raster):
                    time_series_app = time_series_raster

            sar_time_series[orbit.lower()][
                polarisation.lower()]["App"] = time_series_app

            s1_features.append(time_series_app)
            dependancies.append(time_series_app)
            if self.use_gapfilling:
                date_file = FileSearch_AND(
                    self.features_dir, True,
                    "{}_{}_dates_interpolation.txt".format(
                        polarisation.lower(), orbit.upper()))[0]
            else:
                tar_dir = os.path.join(config.get("Paths", "output"),
                                       self.tile_name[1:])
                date_file = FileSearch_AND(
                    tar_dir, True,
                    "{}_{}_dates_input.txt".format(polarisation.lower(),
                                                   orbit.upper()))[0]
            sar_time_series[orbit.lower()][
                polarisation.lower()]["availDates"] = getNbDateInTile(
                    date_file, display=False, raw_dates=True)
        features_labels = []
        for sensor_mode, features in list(s1_labels.items()):
            features_labels += features
        if sar_features_expr:
            sar_user_features_raster = os.path.join(
                self.features_dir, "tmp", self.user_sar_features_name)
            user_sar_features, user_sar_features_lab = generateSARFeat_dates(
                sar_features_expr, sar_time_series, sar_user_features_raster)
            if self.write_outputs_flag is False:
                user_sar_features.Execute()
            else:
                if not os.path.exists(sar_user_features_raster):
                    user_sar_features.ExecuteAndWriteOutput()
                if os.path.exists(sar_user_features_raster):
                    user_sar_features = sar_user_features_raster
            dependancies.append(user_sar_features)
            s1_features.append(user_sar_features)
            features_labels += user_sar_features_lab
        sar_features_raster = os.path.join(self.features_dir, "tmp",
                                           self.sar_features_name)
        sar_features = CreateConcatenateImagesApplication({
            "il": s1_features,
            "out": sar_features_raster,
            "ram": str(ram)
        })
        return (sar_features, dependancies), features_labels
