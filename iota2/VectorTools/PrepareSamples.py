#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os.path
import sys
import argparse
from osgeo import ogr
from iota2.VectorTools import vector_functions as vf
from iota2.VectorTools import NomenclatureHarmonisation as nh
from iota2.VectorTools import AddFieldID
from iota2.VectorTools import DeleteField
from iota2.VectorTools import AddFieldArea
from iota2.VectorTools import DeleteDuplicateGeometriesSqlite
from iota2.VectorTools import BufferOgr
from iota2.VectorTools import checkGeometryAreaThreshField
from iota2.VectorTools import SimplifyPoly


def traitEchantillons(shapefile,
                      outfile,
                      outpath,
                      areapix,
                      pix_thresh,
                      tmp,
                      fieldout,
                      bufferdist=0,
                      tolerance=None,
                      csvfile=1,
                      delimiter=1,
                      fieldin=1):

    # copy input shapefile into the outpath folder
    basefile = os.path.splitext(os.path.basename(shapefile))[0]
    baseext = os.path.splitext(os.path.basename(shapefile))[1]
    newshapefile = outpath + '/' + basefile + baseext

    if baseext == ".shp":
        outformat = "ESRI Shapefile"
    elif baseext == ".sqlite":
        outformat = "SQlite"
    else:
        print("Output format not managed")
        sys.exit()

    vf.copyShapefile(shapefile, newshapefile)

    # Table to store intermediate files paths
    intermediate = []

    intermediate.append(newshapefile)

    if csvfile != 1:
        # manage nomenclature (field CODE)
        nh.labelRecoding(newshapefile, csvfile, delimiter, fieldin, fieldout)

    # Refresh Id and Area fields, keep landcover field and delete other ones
    manageFieldShapefile(newshapefile, fieldout, areapix, outformat)

    #newshapefile = "/datalocal/tmp/PARCELLES_GRAPHIQUES.shp"
    # Simplify geometries
    if tolerance is not None:
        simplyFile = os.path.splitext(newshapefile)[0] + "_spfy.shp"
        SimplifyPoly.simplify(newshapefile, simplyFile, tolerance)
        intermediate.append(simplyFile)
        print("File geometries well simplified")
    else:
        simplyFile = newshapefile

    intermediate.append(simplyFile)

    # Empty geometry identification
    try:
        outShapefile, _ = vf.checkEmptyGeom(simplyFile, outformat)
        print('Check empty geometries succeeded')
    except Exception as e:
        print('Check empty geometries did not work for the following error :')
        print(e)

    # Duplicate geometries
    DeleteDuplicateGeometriesSqlite.deleteDuplicateGeometriesSqlite(
        outShapefile)

    intermediate.append(outShapefile)

    # Apply erosion (negative buffer)
    if bufferdist is not None:
        outbuffer = os.path.splitext(outShapefile)[0] + '_buff{}'.format(
            bufferdist) + '.shp'

        intermediate.append(outbuffer)
        try:
            BufferOgr.bufferPoly(outShapefile, outbuffer, bufferdist,
                                 outformat)
            print('Negative buffer of {} m succeeded'.format(bufferdist))
        except Exception as e:
            print('Negative buffer did not work for the following error :')
            print(e)
    else:
        outbuffer = outShapefile

    outfile = os.path.dirname(shapefile) + '/' + outfile
    checkGeometryAreaThreshField.checkGeometryAreaThreshField(
        outbuffer, areapix, pix_thresh, outfile)

    print('Samples vector file "{}" for classification are now ready'.format(
        outfile))

    if tmp:
        driver = ogr.GetDriverByName('ESRI Shapefile')
        for fileinter in intermediate:
            if os.path.exists(fileinter):
                driver.DeleteDataSource(fileinter)
                print('Intermediate file {} deleted'.format(fileinter))
    else:
        print('Intermediate files are preserved in folder {}'.format(
            os.path.dirname(os.path.realpath(intermediate[0]))))


def manageFieldShapefile(shapefile,
                         fieldout,
                         areapix,
                         outformat="ESRI shapefile"):

    # existing fields
    fieldList = vf.getFields(shapefile, outformat)
    #fieldList = [x.lower() for x in fieldList]
    #fieldList.remove(fieldout.lower())
    fieldList.remove(fieldout)

    # FID creation
    if 'ID' not in fieldList:
        AddFieldID.addFieldID(shapefile)
    else:
        fieldList.remove('ID')

    # Area field creation
    if 'Area' in fieldList:
        DeleteField.deleteField(shapefile, 'Area')
        AddFieldArea.addFieldArea(shapefile, areapix)
        fieldList.remove('Area')
    else:
        AddFieldArea.addFieldArea(shapefile, areapix)

    # Suppression des champs initiaux
    for field in fieldList:
        DeleteField.deleteField(shapefile, field)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        prog = os.path.basename(sys.argv[0])
        print('      ' + sys.argv[0] + ' [options]')
        print("     Help : ", prog, " --help")
        print("        or : ", prog, " -h")
        sys.exit(-1)
    else:
        usage = "usage: %prog [options] "
        parser = argparse.ArgumentParser(
            description="This function treats input vector file (-s)"
            "to use it for training / validation samples of classification"
            "proccess. Output vector file (-o) will be stored in the same folder"
            "than input vector file and intermediate files in a specified folder (-tmppath)"
        )
        parser.add_argument("-s",
                            dest="shapefile",
                            action="store",
                            help="Input shapefile",
                            required=True)
        parser.add_argument(
            "-o",
            dest="output",
            action="store",
            help=
            "Output shapefile name (store in the same folder than input shapefile)",
            required=True)
        parser.add_argument("-tmppath",
                            dest="tmppath",
                            action="store",
                            help="path to store intermediate layers",
                            required=True)
        parser.add_argument("-csv",
                            dest="csv",
                            action="store",
                            help="CSV or recode rules")
        parser.add_argument("-d",
                            dest="delimiter",
                            action="store",
                            help="CSV delimiter")
        parser.add_argument("-if",
                            dest="ifield",
                            action="store",
                            help="Existing field for rules condition")
        parser.add_argument(
            "-of",
            dest="ofield",
            action="store",
            help="Field to create and populate / Field storing landcover code",
            required=True)
        parser.add_argument("-areapix", dest="areapix", action="store", \
                            help="Pixel area of the image used for classification", required = True)
        parser.add_argument(
            "-areat",
            dest="pixthresh",
            action="store",
            help="Area threshold to select available polygons (in pixel)",
            required=True)
        parser.add_argument(
            "-buffer",
            dest="buffer",
            action="store",
            help="Buffer distance to erode polygon (negative value)",
            required=False)
        parser.add_argument("-simplify",
                            dest="simplify",
                            action="store",
                            help="Simplification tolerance (m)",
                            required=False)
        parser.add_argument(
            "-recode",
            action='store_true',
            help="Harmonisation of nomenclature with specific classes codes"
            "(please provide CSV recode rules, CSV delimiter, Existing field and Field to create)",
            default=False)
        parser.add_argument("-notmp",
                            action='store_true',
                            help="No Keeping intermediate files",
                            default=False)
        args = parser.parse_args()

        if args.recode:
            if (args.csv is None) or (args.delimiter is None) or (args.ofield
                                                                  is None):
                print(
                    'Please provide CSV recode rules (-csv), CSV delimiter (-d) and Field to populate (-of)'
                )
                sys.exit(-1)
            else:
                if args.buffer is not None:
                    if int(args.buffer) >= 0:
                        print(args.buffer)
                        print("Buffer distance must be negative")
                        sys.exit(-1)
                    else:
                        traitEchantillons(args.shapefile, args.output,
                                          args.tmppath, args.areapix,
                                          args.pixthresh, args.notmp,
                                          args.ofield, args.buffer,
                                          args.simplify, args.csv,
                                          args.delimiter, args.ifield)
                else:
                    traitEchantillons(args.shapefile, args.output,
                                      args.tmppath, args.areapix,
                                      args.pixthresh, args.notmp, args.ofield,
                                      args.buffer, args.simplify, args.csv,
                                      args.delimiter, args.ifield)
        else:
            traitEchantillons(args.shapefile, args.output, args.tmppath,
                              args.areapix, args.pixthresh, args.notmp,
                              args.ofield, args.buffer, args.simplify)
