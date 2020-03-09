#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sys, os
from osgeo import ogr
import argparse
import os.path
from os.path import basename
import glob


def mergeVectors(infiles, outfile, outformat='ESRI Shapefile'):
    """
   Merge a list of vector files in one 
   """
    '''
   if(not outfile.lower().endswith('.shp')):
      print(basename(outfile) + " is not a valid name for shapefile output." \
      "It will be replaced by " + basename(outfile)[:-4] + ".shp")
      outfile = basename(outfile)[:-4] + '.shp'
   '''

    driver = ogr.GetDriverByName(outformat)

    if os.path.exists(outfile):
        driver.DeleteDataSource(outfile)

    if not isinstance(infiles, list):
        print(infiles)
        files = glob.glob(infiles + '/' + "*.shp")
        files.append(glob.glob(infiles + '/' + "*.sqlite"))
        if not files:
            print("Folder " + infiles + "does not contain vector files")
            sys.exit(-1)
    else:
        files = infiles

    # Append first file to the output file
    file1 = files[0]
    fusion = "ogr2ogr -f '%s' " % (outformat) + outfile + " " + file1
    os.system(fusion)

    layername = os.path.splitext(os.path.basename(outfile))[0]
    # Append other files to the output file
    nbfiles = len(files)
    progress = 0
    for f in range(1, nbfiles):
        if not isinstance(files[f], list):
            fusion2 = "ogr2ogr -f '%s' -update -append " % (
                outformat) + outfile + " " + files[f] + " -nln " + layername
            os.system(fusion2)
        progress += 1
        print("Progress : %s" % (float(progress) / float(nbfiles) * 100.))

    return outfile


if __name__ == "__main__":
    if len(sys.argv) == 1:
        prog = os.path.basename(sys.argv[0])
        print('      ' + sys.argv[0] + ' [options]')
        print("     Help : ", prog, " --help")
        print("        or : ", prog, " -h")
        sys.exit(-1)
    else:
        usage = "usage: %prog [options] "
        parser = argparse.ArgumentParser(description="Merge shapefiles")
        parser.add_argument("-list", nargs ='+', dest ="shapefiles", action="store", \
                            help="List of input shapefiles")
        parser.add_argument("-p", dest="opath", action="store", \
                            help="Folder of input shapefiles")
        parser.add_argument("-o", dest="outshapefile", action="store", \
                            help="ESRI Shapefile output filename and path", required = True)
        parser.add_argument("-format", dest="outformat", action="store", \
                            help="output format (default : ESRI Shapefile)", default="ESRI Shapefile")
        args = parser.parse_args()
        if args.opath is None:
            if args.shapefiles is None:
                print(
                    "Either folder of input shapefiles or list of input shapefiles have to be given"
                )
                sys.exit(-1)
            else:
                mergeVectors(args.shapefiles, args.outshapefile,
                             args.outformat)
        else:
            mergeVectors(args.opath, args.outshapefile, args.outformat)
