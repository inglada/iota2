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
This module provides method for coregister sensors images
"""
import argparse
import os
import sys
import shutil
import logging
import glob
from typing import Optional, List, Dict, Union
from datetime import date
from osgeo import gdal
from osgeo import osr
from iota2.Common import OtbAppBank
from iota2.Common.FileUtils import str2bool

LOGGER = logging.getLogger("CoRegister.py")
STREAMHANDLER = logging.StreamHandler()
STREAMHANDLER.setLevel(logging.DEBUG)
FORMATTER = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
STREAMHANDLER.setFormatter(FORMATTER)

LOGGER.addHandler(STREAMHANDLER)
sensors_params_type = Dict[str, Union[str, List[str], int]]


def get_s2_tile_coverage(ifile: str) -> float:
    """
    Parameters
    ----------
    ifile: string
    Return
    ------
    float: the coverage percent
    """
    file_contain = ''
    with open(ifile) as open_file:
        for line in open_file:
            file_contain += line

    band_str = file_contain.split(
        '<Band_Viewing_Incidence_Angles_Grids_List band_id="B2">')[-1].split(
            '</Band_Viewing_Incidence_Angles_Grids_List>')[0]
    detector_list = []
    for detector in band_str.split('<Values_List>')[1:]:
        detector = detector.split('</Values_List>')[0]
        tab = []
        for line in detector.split('<VALUES>')[1:]:
            line = line.split('</VALUES>')[0]
            tab.append(line.split(' '))
        detector_list.append(tab)

    res_tab = []
    number_of_entry = len(detector_list[0])
    number_of_values = len(detector_list[0][0])
    for i in range(0, number_of_entry):
        for j in range(0, number_of_values):
            res = 0
            for array in detector_list:
                if res == 0 and array[i][j] != 'NaN':
                    res = 1
            res_tab.append(res)
    coverage_percent = float(sum(res_tab)) / float(len(res_tab))
    return coverage_percent


def get_s2_tile_cloud_cover(ifile: str) -> float:
    """
    Parameters
    ----------
    ifile: string
    Return
    ------
    float: the percent of cloud in the tile
    """
    with open(ifile) as open_file:
        for line in open_file:
            if 'name="CloudPercent"' in line:
                cloud = float(line.split("</")[0].split('>')[1])
                percent = 1 - cloud / 100
    return percent


def get_l8_tile_cloud_cover(ifile: str) -> float:
    """
    Parameters
    ----------
    ifile: string
    Return
    ------
    float: the percent of cloud in the tile
    """
    with open(ifile) as open_file:
        for line in open_file:
            if 'CLOUD_COVER ' in line:
                cloud = float(line.split(' = ')[1])
                percent = 1 - cloud / 100
    return percent


def fitness_date_score(date_vhr: str, datadir: str, datatype: str):
    """
    get the date of the best image for the coregistration step

    Parameters
    ----------
    date_vhr : string
        date format YYYYMMDD
    datadir : string
        path to the data directory
    datatype : string
    Return
    ------
    string: the fitted date
    """
    date_vhr = date(int(str(date_vhr)[:4]), int(str(date_vhr)[4:6]),
                    int(str(date_vhr)[6:]))
    fit_date = None
    if datatype in ['L5', 'L8']:
        max_fit_score = None
        for ifile in glob.glob(datadir + os.sep + '*' + os.sep + '*_MTL.txt'):
            in_date = os.path.basename(ifile).split("_")[3]
            year = int(in_date[:4])
            month = int(in_date[4:6])
            day = int(in_date[6:8])
            delta = 1 - min(
                abs((date(year, month, day) - date_vhr).days) / 500, 1)
            percent = get_l8_tile_cloud_cover(ifile)
            fit_score = delta * percent
            if max_fit_score < fit_score or max_fit_score is None:
                max_fit_score = fit_score
                fit_date = in_date

    elif datatype in ['S2', 'S2_S2C']:
        max_fit_score = None
        files = sorted(
            glob.glob(datadir + os.sep + '*' + os.sep + '*_MTD_ALL.xml'))
        for ifile in files:
            in_date = os.path.basename(ifile).split("_")[1].split("-")[0]
            year = int(in_date[:4])
            month = int(in_date[4:6])
            day = int(in_date[6:8])
            delta = 1 - min(
                int(abs((date(year, month, day) - date_vhr).days) / 500), 1)
            percent = get_s2_tile_cloud_cover(ifile)
            cover = get_s2_tile_coverage(ifile)
            fit_score = delta * percent * cover
            if max_fit_score is None or max_fit_score < fit_score:
                max_fit_score = fit_score
                fit_date = in_date
    return fit_date


def launch_coregister(tile: str,
                      working_directory: str,
                      inref: str,
                      bandsrc: str,
                      bandref: str,
                      resample: str,
                      step: str,
                      minstep: str,
                      minsiftpoints: str,
                      iterate: str,
                      prec: str,
                      mode: str,
                      output_path: str,
                      date_vhr: Optional[str] = None,
                      dates_src: Optional[str] = None,
                      list_tiles: Optional[str] = None,
                      ipath_l5: Optional[str] = None,
                      ipath_l8: Optional[str] = None,
                      ipath_s2: Optional[str] = None,
                      ipath_s2_s2c: Optional[str] = None,
                      corregistration_pattern: Optional[str] = None,
                      launch_mask: Optional[bool] = True,
                      sensors_parameters: Optional[sensors_params_type] = None
                      ) -> None:
    """ register an image / a time series on a reference image

    Parameters
    ----------
    tile : string
        tile id
    cfg : serviceConfig obj
        configuration object for parameters
    workingDirectory : string
        path to the working directory
    launch_mask : bool
        boolean to launch common mask
    """
    from iota2.Sensors.ProcessLauncher import commonMasks
    from iota2.Common import ServiceConfigFile as SCF

    LOGGER.info("Source Raster Registration")

    if ipath_l5 is not None and os.path.exists(os.path.join(ipath_l5, tile)):
        datadir = os.path.join(ipath_l5, tile)
        datatype = 'L5'
        pattern = "ORTHO_SURF_CORR_PENTE*.TIF"

    if ipath_l8 != "None" and os.path.exists(os.path.join(ipath_l8, tile)):
        datadir = os.path.join(ipath_l8, tile)
        datatype = 'L8'
        pattern = "ORTHO_SURF_CORR_PENTE*.TIF"

    if ipath_s2 != "None" and os.path.exists(os.path.join(ipath_s2, tile)):
        datadir = os.path.join(ipath_s2, tile)
        datatype = 'S2'
        pattern = "*STACK.tif"

    if ipath_s2_s2c != "None" and os.path.exists(
            os.path.join(ipath_s2_s2c, tile)):
        datadir = os.path.join(ipath_s2_s2c, tile)
        datatype = 'S2_S2C'
        pattern = "*STACK.tif"

    if corregistration_pattern is not None:
        pattern = corregistration_pattern

    # inref = os.path.join(cfg.getParam('coregistration', 'VHRPath'))
    # dates_src = cfg.getParam('coregistration', 'dateSrc')
    if dates_src is not None:
        if list_tiles is not None:
            tiles = list_tiles.split(" ")
        else:
            raise "list_tiles parameters is not set"
        tile_ind = tiles.index(tile)
        date_src = dates_src.split(" ")[tile_ind]
        if date_src is None:

            if date_vhr == 'None':
                LOGGER.warning("date_vhr is not set, please set it")
            else:
                date_src = fitness_date_score(date_vhr, datadir, datatype)
    else:

        if date_vhr is None:
            LOGGER.warning("date_vhr is not set, please set it")
        else:
            date_src = fitness_date_score(date_vhr, datadir, datatype)
    insrc = glob.glob(os.path.join(datadir, f'*{date_src}*', pattern))[0]
    # bandsrc = cfg.getParam('coregistration', 'bandSrc')
    # bandref = cfg.getParam('coregistration', 'bandRef')
    # resample = cfg.getParam('coregistration', 'resample')
    # step = cfg.getParam('coregistration', 'step')
    # minstep = cfg.getParam('coregistration', 'minstep')
    # minsiftpoints = cfg.getParam('coregistration', 'minsiftpoints')
    # iterate = cfg.getParam('coregistration', 'iterate')
    # prec = cfg.getParam('coregistration', 'prec')
    # mode = int(cfg.getParam('coregistration', 'mode'))

    if working_directory is not None:
        working_directory = os.path.join(working_directory, tile)

    coregister(insrc, inref, bandsrc,
               bandref, resample, step, minstep, minsiftpoints, iterate, prec,
               int(mode), datadir, pattern, datatype, False, working_directory)

    if launch_mask:
        commonMasks(tile, output_path, sensors_parameters)


def coregister(in_src,
               inref,
               band,
               bandref,
               resample=1,
               step=256,
               minstep=16,
               minsiftpoints=40,
               iterate=1,
               prec=3,
               mode=2,
               datadir=None,
               pattern='*STACK.tif',
               datatype='S2',
               write_features=False,
               working_directory=None):
    """ register an image / a time series on a reference image

    Parameters
    ----------
    insrc : string
        source raster
    inref : string
        reference raster
    band : int
        band number for the source raster
    bandref : int
        band number for the raster reference raster
    resample : boolean
        resample to reference raster resolution
    step : int
        initial step between the geobins
    minstep : int
        minimal step between the geobins when iterates
    minsiftpoints : int
        minimal number of sift points to perform the registration
    iterate : boolean
        argument to iterate with smaller geobin step to find more sift points
    prec : int
        precision between the source and reference image (in source pixel unit)
    mode : int
        registration mode,
        1 : simple registration ;
        2 : time series registration ;
        3 : time series cascade registration (to do)
    datadir : string
        path to the data directory
    pattern : string
        pattern of the STACK files to register
    write_features : boolean
        argument to keep temporary files

    Note
    ------
    This function use the OTB's application **OrthoRectification** and **SuperImpose**
    more documentation for
    `OrthoRectification <https://www.orfeo-toolbox.org/Applications/OrthoRectification.html>`_
    and
    `SuperImpose <https://www.orfeo-toolbox.org/Applications/Superimpose.html>`_
    """
    from iota2.Common.FileUtils import ensure_dir
    path_wd = os.path.dirname(
        in_src) if not working_directory else working_directory
    if not os.path.exists(path_wd):
        ensure_dir(path_wd)

    src_clip = os.path.join(path_wd, 'tempSrcClip.tif')
    extract_roi_app = OtbAppBank.CreateExtractROIApplication({
        "in":
        in_src,
        "mode":
        "fit",
        "mode.fit.im":
        inref,
        "out":
        src_clip,
        "pixType":
        "uint16"
    })
    extract_roi_app.ExecuteAndWriteOutput()
    # SensorModel generation
    sensor_model = os.path.join(path_wd, 'SensorModel.geom')
    pmcm_app = OtbAppBank.CreatePointMatchCoregistrationModel({
        "in":
        src_clip,
        "band1":
        band,
        "inref":
        inref,
        "bandref":
        bandref,
        "resample":
        resample,
        "precision":
        str(prec),
        "mfilter":
        "1",
        "backmatching":
        "1",
        "outgeom":
        sensor_model,
        "initgeobinstep":
        str(step),
        "mingeobinstep":
        str(minstep),
        "minsiftpoints":
        str(minsiftpoints),
        "iterate":
        iterate
    })
    pmcm_app.ExecuteAndWriteOutput()

    # mode 1 : application on the source image
    if mode in (1, 3):
        out_src = os.path.join(path_wd, 'temp_file.tif')
        io_src = str(src_clip + '?&skipcarto=true&geom=' + sensor_model)
        dataset = gdal.Open(src_clip)
        prj = dataset.GetProjection()
        geo_trans = dataset.GetGeoTransform()
        srs = osr.SpatialReference()
        srs.ImportFromWkt(prj)
        code = srs.GetAuthorityCode(None)
        gsp = str(int(2 * round(max(abs(geo_trans[1]), abs(geo_trans[5])))))
        dataset = None
        ortho_rec_app = OtbAppBank.CreateOrthoRectification({
            "in": io_src,
            "io.out": out_src,
            "map": "epsg",
            "map.epsg.code": code,
            "opt.gridspacing": gsp,
            "pixType": "uint16"
        })

        if write_features:
            ortho_rec_app[0].ExecuteAndWriteOutput()
        else:
            ortho_rec_app[0].Execute()

        ext = os.path.splitext(in_src)[1]
        final_ouput = os.path.join(
            path_wd,
            os.path.basename(in_src.replace(ext, ext.replace('.', '_COREG.'))))
        sup_imp_app = OtbAppBank.CreateSuperimposeApplication({
            "inr":
            src_clip,
            "inm":
            ortho_rec_app[0],
            "out":
            final_ouput,
            "pixType":
            "uint16"
        })
        sup_imp_app[0].ExecuteAndWriteOutput()

        shutil.move(final_ouput,
                    in_src.replace(ext, ext.replace('.', '_COREG.')))
        shutil.move(final_ouput.replace(ext, '.geom'),
                    in_src.replace(ext, '_COREG.geom'))

        # Mask registration if exists
        masks = glob.glob(
            os.path.dirname(in_src) + os.sep + 'MASKS' + os.sep +
            '*BINARY_MASK' + ext)
        if len(masks) != 0:
            for mask in masks:
                src_clip = os.path.join(path_wd, 'tempSrcClip.tif')
                extract_roi_app = OtbAppBank.CreateExtractROIApplication({
                    "in":
                    mask,
                    "mode":
                    "fit",
                    "mode.fit.im":
                    inref,
                    "out":
                    src_clip,
                    "pixType":
                    "uint16"
                })
                extract_roi_app.ExecuteAndWriteOutput()
                out_src = os.path.join(path_wd, 'temp_file.tif')
                io_src = str(mask + '?&skipcarto=true&geom=' + sensor_model)
                ortho_rec_app = OtbAppBank.CreateOrthoRectification({
                    "in":
                    io_src,
                    "io.out":
                    out_src,
                    "map":
                    "epsg",
                    "map.epsg.code":
                    code,
                    "opt.gridspacing":
                    gsp,
                    "pixType":
                    "uint16"
                })
                if write_features:
                    ortho_rec_app[0].ExecuteAndWriteOutput()
                else:
                    ortho_rec_app[0].Execute()

                ext = os.path.splitext(in_src)[1]
                final_mask = os.path.join(
                    path_wd,
                    os.path.basename(
                        mask.replace(ext, ext.replace('.', '_COREG.'))))
                sup_imp_app = OtbAppBank.CreateSuperimposeApplication({
                    "inr":
                    mask,
                    "inm":
                    ortho_rec_app[0],
                    "out":
                    final_mask,
                    "pixType":
                    "uint16"
                })
                sup_imp_app[0].ExecuteAndWriteOutput()

                if final_mask != mask.replace(ext, ext.replace('.',
                                                               '_COREG.')):
                    shutil.move(final_mask,
                                mask.replace(ext, ext.replace('.', '_COREG.')))
                    shutil.move(final_mask.replace(ext, '.geom'),
                                mask.replace(ext, '_COREG.geom'))

        if mode == 3:
            folders = glob.glob(os.path.join(datadir, '*'))

            if datatype in ['S2', 'S2_S2C']:
                dates = [
                    os.path.basename(fld).split('_')[1].split("-")[0]
                    for fld in folders
                ]
                ref_date = os.path.basename(in_src).split('_')[1].split("-")[0]
            elif datatype in ['L5', 'L8']:
                dates = [
                    os.path.basename(fld).split('_')[3] for fld in folders
                ]
                ref_date = os.path.basename(in_src).split('_')[3]
            dates.sort()
            ref_date_ind = dates.index(ref_date)
            bandref = band
            clean_dates = [ref_date]
            for curr_date in reversed(dates[:ref_date_ind]):
                inref = glob.glob(
                    os.path.join(datadir, '*' + clean_dates[-1] + '*',
                                 pattern))[0]
                insrc = glob.glob(
                    os.path.join(datadir, '*' + curr_date + '*', pattern))[0]
                src_clip = os.path.join(path_wd, 'srcClip.tif')
                extract_roi_app = OtbAppBank.CreateExtractROIApplication({
                    "in":
                    insrc,
                    "mode":
                    "fit",
                    "mode.fit.im":
                    inref,
                    "out":
                    src_clip,
                    "pixType":
                    "uint16"
                })
                extract_roi_app.ExecuteAndWriteOutput()
                out_sensor_model = os.path.join(
                    path_wd, 'SensorModel_%s.geom' % curr_date)
                try:
                    pmcm_app = OtbAppBank.CreatePointMatchCoregistrationModel({
                        "in":
                        src_clip,
                        "band1":
                        band,
                        "inref":
                        inref,
                        "bandref":
                        bandref,
                        "resample":
                        resample,
                        "precision":
                        str(prec),
                        "mfilter":
                        "1",
                        "backmatching":
                        "1",
                        "outgeom":
                        out_sensor_model,
                        "initgeobinstep":
                        str(step),
                        "mingeobinstep":
                        str(minstep),
                        "minsiftpoints":
                        str(minsiftpoints),
                        "iterate":
                        iterate
                    })
                    pmcm_app.ExecuteAndWriteOutput()
                except RuntimeError:
                    shutil.copy(sensor_model, out_sensor_model)
                    LOGGER.warning(
                        'Coregistration failed, %s will be process with %s' %
                        (insrc, out_sensor_model))
                    continue

                out_src = os.path.join(path_wd, 'temp_file.tif')
                io_src = str(src_clip + '?&skipcarto=true&geom=' +
                             out_sensor_model)
                dataset = gdal.Open(src_clip)
                prj = dataset.GetProjection()
                geo_trans = dataset.GetGeoTransform()
                srs = osr.SpatialReference()
                srs.ImportFromWkt(prj)
                code = srs.GetAuthorityCode(None)
                gsp = str(
                    int(2 * round(max(abs(geo_trans[1]), abs(geo_trans[5])))))
                dataset = None
                try:
                    ortho_rec_app = OtbAppBank.CreateOrthoRectification({
                        "in":
                        io_src,
                        "io.out":
                        out_src,
                        "map":
                        "epsg",
                        "map.epsg.code":
                        code,
                        "opt.gridspacing":
                        gsp,
                        "pixType":
                        "uint16"
                    })

                    if write_features:
                        ortho_rec_app[0].ExecuteAndWriteOutput()
                    else:
                        ortho_rec_app[0].Execute()
                except RuntimeError:
                    os.remove(out_sensor_model)
                    shutil.copy(sensor_model, out_sensor_model)
                    LOGGER.warning(
                        'Coregistration failed, %s will be process with %s' %
                        (insrc, out_sensor_model))
                    ortho_rec_app = OtbAppBank.CreateOrthoRectification({
                        "in":
                        io_src,
                        "io.out":
                        out_src,
                        "map":
                        "epsg",
                        "map.epsg.code":
                        code,
                        "opt.gridspacing":
                        gsp,
                        "pixType":
                        "uint16"
                    })
                    continue

                    if write_features:
                        ortho_rec_app[0].ExecuteAndWriteOutput()
                    else:
                        ortho_rec_app[0].Execute()

                ext = os.path.splitext(insrc)[1]
                final_ouput = os.path.join(
                    path_wd,
                    os.path.basename(
                        insrc.replace(ext, ext.replace('.', '_COREG.'))))
                sup_imp_app = OtbAppBank.CreateSuperimposeApplication({
                    "inr":
                    src_clip,
                    "inm":
                    ortho_rec_app[0],
                    "out":
                    final_ouput,
                    "pixType":
                    "uint16"
                })
                sup_imp_app[0].ExecuteAndWriteOutput()

                shutil.move(final_ouput,
                            insrc.replace(ext, ext.replace('.', '_COREG.')))
                shutil.move(final_ouput.replace(ext, '.geom'),
                            insrc.replace(ext, '_COREG.geom'))

                # Mask registration if exists
                masks = glob.glob(
                    os.path.dirname(insrc) + os.sep + 'MASKS' + os.sep +
                    '*BINARY_MASK' + ext)
                if len(masks) != 0:
                    for mask in masks:
                        src_clip = os.path.join(path_wd, 'srcClip.tif')
                        extract_roi_app = OtbAppBank.CreateExtractROIApplication(
                            {
                                "in": mask,
                                "mode": "fit",
                                "mode.fit.im": inref,
                                "out": src_clip,
                                "pixType": "uint16"
                            })
                        extract_roi_app.ExecuteAndWriteOutput()
                        out_src = os.path.join(path_wd, 'temp_file.tif')
                        io_src = str(src_clip + '?&skipcarto=true&geom=' +
                                     out_sensor_model)
                        ortho_rec_app = OtbAppBank.CreateOrthoRectification({
                            "in":
                            io_src,
                            "io.out":
                            out_src,
                            "map":
                            "epsg",
                            "map.epsg.code":
                            code,
                            "opt.gridspacing":
                            gsp,
                            "pixType":
                            "uint16"
                        })
                        if write_features:
                            ortho_rec_app[0].ExecuteAndWriteOutput()
                        else:
                            ortho_rec_app[0].Execute()

                        ext = os.path.splitext(insrc)[1]
                        final_mask = os.path.join(
                            path_wd,
                            os.path.basename(
                                mask.replace(ext, ext.replace('.',
                                                              '_COREG.'))))
                        sup_imp_app = OtbAppBank.CreateSuperimposeApplication({
                            "inr":
                            src_clip,
                            "inm":
                            ortho_rec_app[0],
                            "out":
                            final_mask,
                            "pixType":
                            "uint16"
                        })
                        sup_imp_app[0].ExecuteAndWriteOutput()

                        shutil.move(
                            final_mask,
                            mask.replace(ext, ext.replace('.', '_COREG.')))
                        shutil.move(final_mask.replace(ext, '.geom'),
                                    mask.replace(ext, '_COREG.geom'))

                if not write_features and os.path.exists(out_sensor_model):
                    os.remove(out_sensor_model)

                if datatype in ['S2', 'S2_S2C']:
                    mtd_file = glob.glob(
                        os.path.join(os.path.dirname(insrc), '*_MTD_ALL*'))[0]
                    cloud_clear = get_s2_tile_cloud_cover(mtd_file)
                    cover = get_s2_tile_coverage(mtd_file)
                    if cloud_clear > 0.6 and cover > 0.8:
                        clean_dates.append(curr_date)
                elif datatype in ['L5', 'L8']:
                    mlt_file = glob.glob(
                        os.path.join(os.path.dirname(insrc), '*_MTL*'))[0]
                    cloud_clear = get_l8_tile_cloud_cover(mlt_file)
                    if cloud_clear > 0.6:
                        clean_dates.append(curr_date)

            clean_dates = [ref_date]
            for curr_date in dates[ref_date_ind + 1:]:
                inref = glob.glob(
                    os.path.join(datadir, '*' + clean_dates[-1] + '*',
                                 pattern))[0]
                insrc = glob.glob(
                    os.path.join(datadir, '*' + curr_date + '*', pattern))[0]
                src_clip = os.path.join(path_wd, 'srcClip.tif')
                extract_roi_app = OtbAppBank.CreateExtractROIApplication({
                    "in":
                    insrc,
                    "mode":
                    "fit",
                    "mode.fit.im":
                    inref,
                    "out":
                    src_clip,
                    "pixType":
                    "uint16"
                })
                extract_roi_app.ExecuteAndWriteOutput()
                out_sensor_model = os.path.join(
                    path_wd, 'SensorModel_%s.geom' % curr_date)
                try:
                    pmcm_app = OtbAppBank.CreatePointMatchCoregistrationModel({
                        "in":
                        src_clip,
                        "band1":
                        band,
                        "inref":
                        inref,
                        "bandref":
                        bandref,
                        "resample":
                        resample,
                        "precision":
                        str(prec),
                        "mfilter":
                        "1",
                        "backmatching":
                        "1",
                        "outgeom":
                        out_sensor_model,
                        "initgeobinstep":
                        str(step),
                        "mingeobinstep":
                        str(minstep),
                        "minsiftpoints":
                        str(minsiftpoints),
                        "iterate":
                        iterate
                    })
                    pmcm_app.ExecuteAndWriteOutput()
                except RuntimeError:
                    shutil.copy(sensor_model, out_sensor_model)
                    LOGGER.warning(
                        'Coregistration failed, %s will be process with %s' %
                        (insrc, out_sensor_model))
                    continue

                out_src = os.path.join(path_wd, 'temp_file.tif')
                io_src = str(src_clip + '?&skipcarto=true&geom=' +
                             out_sensor_model)
                dataset = gdal.Open(src_clip)
                prj = dataset.GetProjection()
                geo_trans = dataset.GetGeoTransform()
                srs = osr.SpatialReference()
                srs.ImportFromWkt(prj)
                code = srs.GetAuthorityCode(None)
                gsp = str(
                    int(2 * round(max(abs(geo_trans[1]), abs(geo_trans[5])))))
                dataset = None
                try:
                    ortho_rec_app = OtbAppBank.CreateOrthoRectification({
                        "in":
                        io_src,
                        "io.out":
                        out_src,
                        "map":
                        "epsg",
                        "map.epsg.code":
                        code,
                        "opt.gridspacing":
                        gsp,
                        "pixType":
                        "uint16"
                    })

                    if write_features:
                        ortho_rec_app[0].ExecuteAndWriteOutput()
                    else:
                        ortho_rec_app[0].Execute()
                except RuntimeError:
                    os.remove(out_sensor_model)
                    shutil.copy(sensor_model, out_sensor_model)
                    ortho_rec_app = OtbAppBank.CreateOrthoRectification({
                        "in":
                        io_src,
                        "io.out":
                        out_src,
                        "map":
                        "epsg",
                        "map.epsg.code":
                        code,
                        "opt.gridspacing":
                        gsp,
                        "pixType":
                        "uint16"
                    })
                    continue

                    if write_features:
                        ortho_rec_app[0].ExecuteAndWriteOutput()
                    else:
                        ortho_rec_app[0].Execute()

                ext = os.path.splitext(insrc)[1]
                final_ouput = os.path.join(
                    path_wd,
                    os.path.basename(
                        insrc.replace(ext, ext.replace('.', '_COREG.'))))
                sup_imp_app = OtbAppBank.CreateSuperimposeApplication({
                    "inr":
                    src_clip,
                    "inm":
                    ortho_rec_app[0],
                    "out":
                    final_ouput,
                    "pixType":
                    "uint16"
                })
                sup_imp_app[0].ExecuteAndWriteOutput()

                shutil.move(final_ouput,
                            insrc.replace(ext, ext.replace('.', '_COREG.')))
                shutil.move(final_ouput.replace(ext, '.geom'),
                            insrc.replace(ext, '_COREG.geom'))

                # Mask registration if exists
                masks = glob.glob(
                    os.path.dirname(insrc) + os.sep + 'MASKS' + os.sep +
                    '*BINARY_MASK' + ext)
                if len(masks) != 0:
                    for mask in masks:
                        src_clip = os.path.join(path_wd, 'srcClip.tif')
                        extract_roi_app = OtbAppBank.CreateExtractROIApplication(
                            {
                                "in": mask,
                                "mode": "fit",
                                "mode.fit.im": inref,
                                "out": src_clip,
                                "pixType": "uint16"
                            })
                        extract_roi_app.ExecuteAndWriteOutput()
                        out_src = os.path.join(path_wd, 'temp_file.tif')
                        io_src = str(src_clip + '?&skipcarto=true&geom=' +
                                     out_sensor_model)
                        ortho_rec_app = OtbAppBank.CreateOrthoRectification({
                            "in":
                            io_src,
                            "io.out":
                            out_src,
                            "map":
                            "epsg",
                            "map.epsg.code":
                            code,
                            "opt.gridspacing":
                            gsp,
                            "pixType":
                            "uint16"
                        })
                        if write_features:
                            ortho_rec_app[0].ExecuteAndWriteOutput()
                        else:
                            ortho_rec_app[0].Execute()

                        ext = os.path.splitext(insrc)[1]
                        final_mask = os.path.join(
                            path_wd,
                            os.path.basename(
                                mask.replace(ext, ext.replace('.',
                                                              '_COREG.'))))
                        sup_imp_app = OtbAppBank.CreateSuperimposeApplication({
                            "inr":
                            src_clip,
                            "inm":
                            ortho_rec_app[0],
                            "out":
                            final_mask,
                            "pixType":
                            "uint16"
                        })
                        sup_imp_app[0].ExecuteAndWriteOutput()

                        shutil.move(
                            final_mask,
                            mask.replace(ext, ext.replace('.', '_COREG.')))
                        shutil.move(final_mask.replace(ext, '.geom'),
                                    mask.replace(ext, '_COREG.geom'))

                if not write_features and os.path.exists(out_sensor_model):
                    os.remove(out_sensor_model)

                if datatype in ['S2', 'S2_S2C']:
                    mtd_file = glob.glob(
                        os.path.join(os.path.dirname(insrc), '*_MTD_ALL*'))[0]
                    cloud_clear = get_s2_tile_cloud_cover(mtd_file)
                    cover = get_s2_tile_coverage(mtd_file)
                    if cloud_clear > 0.6 and cover > 0.8:
                        clean_dates.append(curr_date)
                elif datatype in ['L5', 'L8']:
                    mlt_file = glob.glob(
                        os.path.join(os.path.dirname(insrc), '*_MTL*'))[0]
                    cloud_clear = get_l8_tile_cloud_cover(mlt_file)
                    if cloud_clear > 0.6:
                        clean_dates.append(date)

        if not write_features and os.path.exists(sensor_model):
            os.remove(sensor_model)
    # mode 2 : application on the time series
    elif mode == 2:
        ext = os.path.splitext(insrc)[1]
        file_list = glob.glob(datadir + os.sep + '*' + os.sep + pattern)
        for insrc in file_list:
            src_clip = os.path.join(path_wd, 'tempSrcClip.tif')
            extract_roi_app = OtbAppBank.CreateExtractROIApplication({
                "in":
                insrc,
                "mode":
                "fit",
                "mode.fit.im":
                inref,
                "out":
                src_clip,
                "pixType":
                "uint16"
            })
            extract_roi_app.ExecuteAndWriteOutput()
            out_src = os.path.join(path_wd, 'temp_file.tif')
            io_src = str(src_clip + '?&skipcarto=true&geom=' + sensor_model)
            dataset = gdal.Open(src_clip)
            prj = dataset.GetProjection()
            geo_trans = dataset.GetGeoTransform()
            srs = osr.SpatialReference()
            srs.ImportFromWkt(prj)
            code = srs.GetAuthorityCode(None)
            gsp = str(int(2 *
                          round(max(abs(geo_trans[1]), abs(geo_trans[5])))))
            dataset = None
            ortho_rec_app = OtbAppBank.CreateOrthoRectification({
                "in":
                io_src,
                "io.out":
                out_src,
                "map":
                "epsg",
                "map.epsg.code":
                code,
                "opt.gridspacing":
                gsp,
                "pixType":
                "uint16"
            })

            if write_features:
                ortho_rec_app[0].ExecuteAndWriteOutput()
            else:
                ortho_rec_app[0].Execute()

            ext = os.path.splitext(insrc)[1]
            final_ouput = os.path.join(
                path_wd,
                os.path.basename(
                    insrc.replace(ext, ext.replace('.', '_COREG.'))))
            sup_imp_app = OtbAppBank.CreateSuperimposeApplication({
                "inr":
                src_clip,
                "inm":
                ortho_rec_app[0],
                "out":
                final_ouput,
                "pixType":
                "uint16"
            })
            sup_imp_app[0].ExecuteAndWriteOutput()

            shutil.move(final_ouput,
                        insrc.replace(ext, ext.replace('.', '_COREG.')))
            shutil.move(final_ouput.replace(ext, '.geom'),
                        insrc.replace(ext, '_COREG.geom'))

            # Mask registration if exists
            masks = glob.glob(
                os.path.dirname(insrc) + os.sep + 'MASKS' + os.sep +
                '*BINARY_MASK*' + ext)
            if len(masks) != 0:
                for mask in masks:
                    src_clip = os.path.join(path_wd, 'tempSrcClip.tif')
                    extract_roi_app = OtbAppBank.CreateExtractROIApplication({
                        "in":
                        mask,
                        "mode":
                        "fit",
                        "mode.fit.im":
                        inref,
                        "out":
                        src_clip,
                        "pixType":
                        "uint16"
                    })
                    extract_roi_app.ExecuteAndWriteOutput()
                    out_src = os.path.join(path_wd, 'temp_file.tif')
                    io_src = str(src_clip + '?&skipcarto=true&geom=' +
                                 sensor_model)
                    ortho_rec_app = OtbAppBank.CreateOrthoRectification({
                        "in":
                        io_src,
                        "io.out":
                        out_src,
                        "map":
                        "epsg",
                        "map.epsg.code":
                        code,
                        "opt.gridspacing":
                        gsp,
                        "pixType":
                        "uint16"
                    })
                    if write_features:
                        ortho_rec_app[0].ExecuteAndWriteOutput()
                    else:
                        ortho_rec_app[0].Execute()

                    ext = os.path.splitext(insrc)[1]
                    final_mask = os.path.join(
                        path_wd,
                        os.path.basename(
                            mask.replace(ext, ext.replace('.', '_COREG.'))))
                    sup_imp_app = OtbAppBank.CreateSuperimposeApplication({
                        "inr":
                        src_clip,
                        "inm":
                        ortho_rec_app[0],
                        "out":
                        final_mask,
                        "pixType":
                        "uint16"
                    })
                    sup_imp_app[0].ExecuteAndWriteOutput()

                    shutil.move(final_mask,
                                mask.replace(ext, ext.replace('.', '_COREG.')))
                    shutil.move(final_mask.replace(ext, '.geom'),
                                mask.replace(ext, '_COREG.geom'))

        os.remove(src_clip)
        if not write_features and os.path.exists(sensor_model):
            os.remove(sensor_model)


if __name__ == "__main__":

    PARSER = argparse.ArgumentParser(
        description="Computes a time series of features")
    PARSER.add_argument("-insrc",
                        dest="insrc",
                        help="Source raster",
                        required=True)
    PARSER.add_argument("-inref",
                        dest="inref",
                        help="Reference raster",
                        required=True)
    PARSER.add_argument("-band",
                        dest="band",
                        help="Band from the source raster",
                        default=3,
                        required=False)
    PARSER.add_argument("-bandref",
                        dest="bandref",
                        help="Band from the reference raster",
                        default=3,
                        required=False)
    PARSER.add_argument("-resample",
                        type=str2bool,
                        dest="resample",
                        help="path to the working directory",
                        default=False,
                        required=False)
    PARSER.add_argument("-step",
                        dest="step",
                        help="",
                        default=256,
                        required=False)
    PARSER.add_argument("-minstep",
                        dest="minstep",
                        help="",
                        default=16,
                        required=False)
    PARSER.add_argument("-minsiftpoints",
                        dest="minsiftpoints",
                        help="",
                        default=40,
                        required=False)
    PARSER.add_argument("-iterate",
                        type=str2bool,
                        dest="iterate",
                        help="path to the working directory",
                        default=True,
                        required=False)
    PARSER.add_argument("-prec",
                        dest="prec",
                        help="",
                        default=3,
                        required=False)
    PARSER.add_argument(
        "-mode",
        dest="mode",
        help=
        "1 : simple registration ; 2 : time series registration ; 3 : time series cascade registration",
        default=1,
        required=False)
    PARSER.add_argument("-dd",
                        dest="datadir",
                        help="path to the root data directory",
                        default=None,
                        required=False)
    PARSER.add_argument("-pattern",
                        dest="pattern",
                        help="pattern of the file to register",
                        default='*STACK',
                        required=False)
    PARSER.add_argument("-writeFeatures",
                        type=str2bool,
                        dest="writeFeatures",
                        help="path to the working directory",
                        default=False,
                        required=False)
    ARGS = PARSER.parse_args()

    ARGS.mode = int(ARGS.mode)
    if ARGS.mode not in [1, 2, 3]:
        sys.exit("Wrong mode argument, please use the following options : 1 : "
                 "simple registration ; 2 : time series registration ; "
                 "3 : time series cascade registration")
    elif ARGS.mode in [2, 3]:
        if (ARGS.datadir is None or not os.path.exists(ARGS.datadir)):
            sys.exit("Valid data direction needed for time series "
                     "registration (mode 2 and 3)")
        if ARGS.pattern is None:
            sys.exit("A pattern is needed for time series registration "
                     "(mode 2 and 3)")

    coregister(ARGS.insrc, ARGS.inref, ARGS.band, ARGS.bandref, ARGS.resample,
               ARGS.step, ARGS.minstep, ARGS.minsiftpoints, ARGS.iterate,
               ARGS.prec, ARGS.mode, ARGS.datadir, ARGS.pattern,
               ARGS.writeFeatures)
