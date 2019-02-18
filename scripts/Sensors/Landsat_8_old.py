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

from config import Config
import logging
import glob
import os

from GenSensors import Sensor
from collections import OrderedDict

logger = logging.getLogger(__name__)

#in order to avoid issue 'No handlers could be found for logger...'
logger.addHandler(logging.NullHandler())

class Landsat_8_old(Sensor):

    name = 'Landsat8Old'

    def __init__(self, config_path, tile_name):
        from Common import ServiceConfigFile as SCF
        Sensor.__init__(self)

        if not os.path.exists(config_path):
            return

        self.tile_name = tile_name
        self.cfg_IOTA2 = SCF.serviceConfigFile(config_path)
        cfg_sensors = os.path.join(os.environ.get('IOTA2DIR'), "config", "sensors.cfg")
        cfg_sensors = SCF.serviceConfigFile(cfg_sensors, iota_config=False)

        # running attributes
        self.target_proj = int(self.cfg_IOTA2.getParam("GlobChain", "proj").lower().replace(" ","").replace("epsg:",""))
        self.all_tiles = self.cfg_IOTA2.getParam("chain", "listTile")
        self.struct_path_masks = cfg_sensors.getParam("Landsat8_old", "arbomask")
        self.l8_old_data = self.cfg_IOTA2.getParam("chain", "L8Path_old")
        self.tile_directory = os.path.join(self.l8_old_data, tile_name)
        self.features_dir = os.path.join(self.cfg_IOTA2.getParam("chain", "outputPath"),
                                         "features", tile_name)
        extract_bands = self.cfg_IOTA2.getParam("Landsat8_old", "keepBands")
        extract_bands_flag = self.cfg_IOTA2.getParam("iota2FeatureExtraction", "extractBands")
        output_target_dir = self.cfg_IOTA2.getParam("chain", "L8_old_output_path")
        if output_target_dir:
            self.output_preprocess_directory = os.path.join(output_target_dir, tile_name)
            if not os.path.exists(self.output_preprocess_directory):
                try:
                    os.mkdir(self.output_preprocess_directory)
                except:
                    pass
        else :
            self.output_preprocess_directory = self.tile_directory

        # sensors attributes
        self.native_res = 30
        self.data_type = "CORR_PENTE"
        self.date_position = 3# if date's name split by "_"
        #~ self.NODATA_VALUE = -10000
        self.masks_rules = OrderedDict([("_DIV.TIF", 1), ("_NUA.TIF", 0), ("_SAT.TIF", 0)])
        self.border_pos = 0
        self.cloud_pos = 1
        self.sat_pos = 2
        self.features_names_list = ["NDVI", "NDWI", "Brightness"]

        # define bands to get and their order
        self.stack_band_position = ["B1", "B2", "B3", "B4", "B5", "B6", "B7"]
        self.extracted_bands = None
        if extract_bands_flag:
            self.extracted_bands = [(band_name, band_position + 1) for band_position, band_name in enumerate(self.stack_band_position) if band_name in self.cfg_IOTA2.getParam("Landsat8_old", "keepBands")]

        # output's names
        self.footprint_name = "{}_{}_footprint.tif".format(self.__class__.name,
                                                           tile_name)
        ref_image_name = "{}_{}_reference.tif".format(self.__class__.name,
                                                           tile_name)
        self.ref_image = os.path.join(self.cfg_IOTA2.getParam("chain", "outputPath"),
                                      "features",
                                      tile_name,
                                      "tmp",
                                      ref_image_name)
        self.time_series_name = "{}_{}_TS.tif".format(self.__class__.name,
                                                      tile_name)
        self.time_series_masks_name = "{}_{}_MASKS.tif".format(self.__class__.name,
                                                               tile_name)
        self.time_series_gapfilling_name = "{}_{}_TSG.tif".format(self.__class__.name,
                                                                  tile_name)
        self.features_names = "{}_{}_Features.tif".format(self.__class__.name,
                                                          tile_name)
        # about gapFilling interpolations
        self.temporal_res = self.cfg_IOTA2.getParam("Landsat8", "temporalResolution")
        self.input_dates = "{}_{}_input_dates.txt".format(self.__class__.name,
                                                           tile_name)
        self.interpolated_dates = "{}_{}_interpolation_dates.txt".format(self.__class__.name,
                                                                         tile_name)

    def get_date_from_name(self, product_name):
        """
        """
        return product_name.split("_")[self.date_position]

    def sort_dates_directories(self, dates_directories):
        """
        """
        return sorted(dates_directories,
                      key=lambda x : int(os.path.basename(x).split("_")[self.date_position]))

    def generate_raster_ref(self, base_ref):
        """
        """
        from gdal import Warp
        from osgeo.gdalconst import  GDT_Byte
        from Common.FileUtils import ensure_dir
        from Common.FileUtils import getRasterProjectionEPSG

        ensure_dir(os.path.dirname(self.ref_image), raise_exe=False)
        base_ref_projection = getRasterProjectionEPSG(base_ref)

        if not os.path.exists(self.ref_image):
            logger.info("reference image generation {} from {}".format(self.ref_image, base_ref))
            ds = Warp(self.ref_image, base_ref, multithread=True,
                      format="GTiff", xRes=self.native_res, yRes=self.native_res,
                      outputType=GDT_Byte, srcSRS="EPSG:{}".format(base_ref_projection),
                      dstSRS="EPSG:{}".format(self.target_proj))

    def footprint(self, ram=128):
        """
        """
        from Common.OtbAppBank import CreateSuperimposeApplication
        from Common.OtbAppBank import CreateBandMathApplication
        from Common.FileUtils import ensure_dir

        footprint_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(footprint_dir,raise_exe=False)
        footprint_out = os.path.join(footprint_dir, self.footprint_name)

        input_dates = [os.path.join(self.tile_directory, cdir) for cdir in os.listdir(self.tile_directory)]
        input_dates = self.sort_dates_directories(input_dates)

        # get date's footprint
        date_edge = []
        for date_dir in input_dates:
            date_edge.append(glob.glob(os.path.join(date_dir, "{}{}".format(self.struct_path_masks, self.masks_rules.keys()[self.border_pos])))[0])

        self.generate_raster_ref(date_edge[0])

        # seek odd values, then sum it
        expr = ["(im{0}b1/2==rint(im{0}b1/2))".format(i + 1) for i in range(len(date_edge))]
        expr = "{}>0?1:0".format("+".join(expr))
        masks_rules = CreateBandMathApplication({"il": date_edge,
                                                 "ram": str(ram),
                                                 "exp": expr})
        masks_rules.Execute()
        app_dep= [masks_rules]
        superimp, _ = CreateSuperimposeApplication({"inr": self.ref_image,
                                                    "inm": masks_rules,
                                                    "out": footprint_out,
                                                    "pixType":"uint8",
                                                    "ram": str(ram)})
        return superimp, app_dep

    def write_dates_file(self):
        """
        """
        from Common.FileUtils import ensure_dir
        input_dates_dir = [os.path.join(self.tile_directory, cdir) for cdir in os.listdir(self.tile_directory)]
        date_file = os.path.join(self.features_dir, "tmp", self.input_dates)
        all_available_dates = [os.path.basename(date).split("_")[self.date_position] for date in input_dates_dir]
        all_available_dates = sorted(all_available_dates, key=lambda x:int(x))
        if not os.path.exists(date_file):
            with open(date_file, "w") as input_date_file:
                input_date_file.write("\n".join(all_available_dates))
        return date_file, all_available_dates

    def write_interpolation_dates_file(self):
        """
        TODO : mv to base-class
        """
        from Common.FileUtils import getDateLandsat
        from Common.FileUtils import ensure_dir
        from Common.FileUtils import dateInterval
        
        interp_date_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(interp_date_dir, raise_exe=False)
        interp_date_file = os.path.join(interp_date_dir, self.interpolated_dates)
        date_interp_min, date_interp_max = getDateLandsat(self.l8_old_data, self.all_tiles.split(" "))
        # force dates
        if not self.cfg_IOTA2.getParam("GlobChain", "autoDate"):
            date_interp_min = self.cfg_IOTA2.getParam("Landsat8_old", "startDate")
            date_interp_max = self.cfg_IOTA2.getParam("Landsat8_old", "endDate")

        dates = [str(date).replace("-","") for date in dateInterval(date_interp_min, date_interp_max, self.temporal_res)]

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
        from Common.OtbAppBank import CreateConcatenateImagesApplication
        from Common.OtbAppBank import CreateSuperimposeApplication
        from Common.FileUtils import ensure_dir
        from Common.FileUtils import getRasterProjectionEPSG
        from Common.FileUtils import FileSearch_AND

        # needed to travel throught iota2's library
        app_dep = []

        input_dates = [os.path.join(self.tile_directory, cdir) for cdir in os.listdir(self.tile_directory)]
        input_dates = self.sort_dates_directories(input_dates)

        # get date's data
        date_data = []
        for date_dir in input_dates:
            date_data.append(FileSearch_AND(date_dir, True, self.data_type, ".TIF")[0])

        time_series_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(time_series_dir, raise_exe=False)
        times_series_raster = os.path.join(time_series_dir, self.time_series_name)
        dates_time_series = CreateConcatenateImagesApplication({"il": date_data,
                                                                "out": times_series_raster,
                                                                "ram": str(ram)})
        dates_in_file, dates_in = self.write_dates_file()

        # build labels
        features_labels = ["{}_{}_{}".format(self.__class__.name, band_name, date) for date in dates_in for band_name in self.stack_band_position]

        # if not all bands must be used
        if self.extracted_bands:
            app_dep.append(dates_time_series)
            (dates_time_series,
             features_labels) = self.extract_bands_time_series(dates_time_series,
                                                               dates_in,
                                                               len(self.stack_band_position),
                                                               self.extracted_bands,
                                                               ram)
        origin_proj = getRasterProjectionEPSG(date_data[0])
        if int(origin_proj) != int(self.target_proj):
            dates_time_series.Execute()
            app_dep.append(dates_time_series)
            self.generate_raster_ref(date_data[0])
            dates_time_series, _ = CreateSuperimposeApplication({"inr": self.ref_image,
                                                                 "inm": masks_rules,
                                                                 "out": times_series_raster,
                                                                 "ram": str(ram)})
        return (dates_time_series, app_dep), features_labels

    def extract_bands_time_series(self, dates_time_series,
                                  dates_in,
                                  comp,
                                  extract_bands,
                                  ram):
        """
        TODO : mv to base class ?
        extract_bands : list
             [('bandName', band_position), ...]
        comp : number of bands in original stack
        """
        from Common.OtbAppBank import CreateExtractROIApplication

        nb_dates = len(dates_in)
        channels_interest = []
        for date_number in range(nb_dates):
            for band_name, band_position in extract_bands:
                channels_interest.append(band_position + int(date_number * comp))

        features_labels = ["{}_{}_{}".format(self.__class__.name, band_name, date) for date in dates_in for band_name, band_pos in extract_bands]
        channels_list = ["Channel{}".format(channel) for channel in channels_interest]
        time_series_out = dates_time_series.GetParameterString("out")
        dates_time_series.Execute()
        extract = CreateExtractROIApplication({"in":dates_time_series,
                                               "cl":channels_list,
                                               "ram":str(ram),
                                               "out":dates_time_series.GetParameterString("out")})
        return extract, features_labels

    def get_time_series_masks(self, ram=128, logger=logger):
        """
        """
        from Common.OtbAppBank import CreateConcatenateImagesApplication
        from Common.OtbAppBank import CreateSuperimposeApplication
        from Common.OtbAppBank import CreateBandMathApplication
        from Common.FileUtils import ensure_dir
        from Common.FileUtils import getRasterProjectionEPSG
        
        time_series_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(time_series_dir, raise_exe=False)
        times_series_mask = os.path.join(time_series_dir, self.time_series_masks_name)
        
        # needed to travel throught iota2's library
        app_dep = []

        input_dates = [os.path.join(self.tile_directory, cdir) for cdir in os.listdir(self.tile_directory)]
        input_dates = self.sort_dates_directories(input_dates)

        # get date's data
        date_data = []
        dates_masks = []
        for date_dir in input_dates:
            div_mask = glob.glob(os.path.join(date_dir, "{}{}".format(self.struct_path_masks, self.masks_rules.keys()[self.border_pos])))[0]
            cloud_mask = glob.glob(os.path.join(date_dir, "{}{}".format(self.struct_path_masks, self.masks_rules.keys()[self.cloud_pos])))[0]
            sat_mask = glob.glob(os.path.join(date_dir, "{}{}".format(self.struct_path_masks, self.masks_rules.keys()[self.sat_pos])))[0]
            # im1 = div, im2 = cloud, im3 = sat
            div_expr = "(1-(im1b1/2==rint(im1b1/2)))"
            cloud_expr = "im2b1"
            sat_expr = "im3b1"
            #~ expr = "*".join([div_expr, cloud_expr, sat_expr])
            expr = "({} + {} + {})==0?0:1".format(div_expr, cloud_expr, sat_expr)
            date_binary_mask = CreateBandMathApplication({"il": [div_mask, cloud_mask, sat_mask],
                                                          "exp": expr})
            date_binary_mask.Execute()
            date_data.append(date_binary_mask)
            app_dep.append(date_binary_mask)
        dates_time_series_mask = CreateConcatenateImagesApplication({"il": date_data,
                                                                     "ram": str(ram),
                                                                     "out": times_series_mask})

        origin_proj = getRasterProjectionEPSG(sat_mask)
        if int(origin_proj) != int(self.target_proj):
            dates_time_series_mask.Execute()
            app_dep.append(dates_time_series_mask)
            self.generate_raster_ref(sat_mask)
            dates_time_series_mask, _ = CreateSuperimposeApplication({"inr": self.ref_image,
                                                                      "inm": dates_time_series_mask,
                                                                      "out": times_series_mask,
                                                                      "ram": str(ram)})

        return dates_time_series_mask, app_dep, len(date_data)

    def get_time_series_gapFilling(self, ram=128):
        """
        """
        from Common.OtbAppBank import CreateImageTimeSeriesGapFillingApplication
        from Common.FileUtils import ensure_dir

        gap_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(gap_dir, raise_exe=False)
        gap_out = os.path.join(gap_dir, self.time_series_gapfilling_name)

        dates_interp_file, dates_interp = self.write_interpolation_dates_file()
        dates_in_file, _ = self.write_dates_file()

        masks, masks_dep, _ = self.get_time_series_masks()
        (time_series, time_series_dep), _ = self.get_time_series()

        time_series.Execute()
        masks.Execute()
        
        comp = len(self.stack_band_position) if not self.extracted_bands else len(self.extracted_bands)

        gap = CreateImageTimeSeriesGapFillingApplication({"in": time_series,
                                                          "mask": masks,
                                                          "comp": str(comp),
                                                          "it": "linear",
                                                          "id": dates_in_file,
                                                          "od": dates_interp_file,
                                                          "out": gap_out,
                                                          "ram": str(ram),
                                                          "pixType": "int16"})
        app_dep = [time_series, masks, masks_dep, time_series_dep]

        bands = self.stack_band_position
        if self.extracted_bands:
            bands = [band_name for band_name, band_pos in self.extracted_bands]

        features_labels = ["{}_{}_{}".format(self.__class__.name, band_name, date) for date in dates_interp for band_name in bands]
        return (gap, app_dep), features_labels

    def get_features_labels(self, dates,
                            rel_refl, keep_dupl, copy_in):
        """
        """
        if rel_refl and keep_dupl is False and copy_in is True:
            self.features_names_list = ["NDWI", "Brightness"]
        out_labels = []

        for feature in self.features_names_list:
            for date in dates:
                out_labels.append("{}_{}_{}".format(self.__class__.name, feature, date))
        return out_labels

    def get_features(self, ram=128, logger=logger):
        """
        """
        from Common.OtbAppBank import CreateConcatenateImagesApplication
        from Common.OtbAppBank import CreateIota2FeatureExtractionApplication
        from Common.OtbAppBank import computeUserFeatures
        from Common.FileUtils import ensure_dir

        features_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(features_dir, raise_exe=False)
        features_out = os.path.join(features_dir, self.features_names)

        features = self.cfg_IOTA2.getParam("GlobChain", "features")
        enable_gapFilling = self.cfg_IOTA2.getParam("GlobChain", "useGapFilling")
        hand_features_flag = self.cfg_IOTA2.getParam('GlobChain', 'useAdditionalFeatures')

        (in_stack, in_stack_dep), in_stack_features_labels = self.get_time_series_gapFilling()
        _, dates_enabled = self.write_interpolation_dates_file()

        if not enable_gapFilling:
            (in_stack, in_stack_dep), in_stack_features_labels = self.get_time_series()
            _, dates_enabled = self.write_dates_file()

        in_stack.Execute()

        app_dep = []
        if hand_features_flag:
            hand_features = self.cfg_IOTA2.getParam("Landsat8_old", "additionalFeatures")
            comp = len(self.stack_band_position) if not self.extracted_bands else len(self.extracted_bands)
            userDateFeatures, fields_userFeat, a, b = computeUserFeatures(in_stack,
                                                                          dates_enabled,
                                                                          comp,
                                                                          hand_features.split(","))
            userDateFeatures.Execute()
            app_dep.append([userDateFeatures, a, b])

        if features:
            bands_avail = self.stack_band_position
            if self.extracted_bands:
                bands_avail = [band_name for band_name, _ in self.extracted_bands]
                # check mandatory bands
                if not "B4" in bands_avail:
                    raise Exception("red band (B4) is needed to compute features")
                if not "B5" in bands_avail:
                    raise Exception("nir band (B5) is needed to compute features")
                if not "B6" in bands_avail:
                    raise Exception("swir band (B6) is needed to compute features")
            feat_parameters = {"in": in_stack,
                               "out": features_out,
                               "comp": len(bands_avail),
                               "red": bands_avail.index("B4") + 1,
                               "nir": bands_avail.index("B5") + 1,
                               "swir": bands_avail.index("B6") + 1,
                               "copyinput": self.cfg_IOTA2.getParam('iota2FeatureExtraction', 'copyinput'),
                               "pixType": "int16",
                               "ram": str(ram)}
            copyinput = self.cfg_IOTA2.getParam('iota2FeatureExtraction', 'copyinput')
            rel_refl = self.cfg_IOTA2.getParam('iota2FeatureExtraction', 'relrefl')
            keep_dupl = self.cfg_IOTA2.getParam('iota2FeatureExtraction', 'keepduplicates')
            acorfeat = self.cfg_IOTA2.getParam('iota2FeatureExtraction', 'acorfeat')

            if rel_refl:
                feat_parameters["relrefl"] = True
            if keep_dupl:
                feat_parameters["keepduplicates"] = True
            if acorfeat:
                feat_parameters["acorfeat"] = True
            features_app = CreateIota2FeatureExtractionApplication(feat_parameters)
            if copyinput is False:
                in_stack_features_labels = []
            features_labels = in_stack_features_labels + self.get_features_labels(dates_enabled,
                                                                                  rel_refl,
                                                                                  keep_dupl,
                                                                                  copyinput)
        else:
            features_app = in_stack
            features_labels = in_stack_features_labels

        app_dep.append([in_stack, in_stack_dep])
        
        if hand_features_flag:
            features_app.Execute()
            app_dep.append(features_app)
            features_app = CreateConcatenateImagesApplication({"il": [features_app, userDateFeatures],
                                                               "out": features_out,
                                                               "ram": str(ram)})
            features_labels += fields_userFeat
        return (features_app, app_dep), features_labels