#!/usr/bin/python
#-*- coding: utf-8 -*-

# =========================================================================
#   Program:   vector tools
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

import argparse

def str2bool(v):
    """
    usage : use in argParse as function to parse options

    IN:
    v [string]
    out [bool]
    """
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def do_check(input_vector, output_vector, epsg, pix_area,
             pix_area_threshold, do_corrections):
    """
    """
    import checkGeometryAreaThreshField
if __name__ == "__main__":
    description=("This function allow user if the inpute dataBase can be used by IOTA²'s\n"
                 "\t- remove empty geometries\n"
                 "\t- remove duplicate geometries\n"
                 "\t- split multi-polygons to polygons\n"
                 "\t- polygons could be filtered by Area\n"
                 "\t- check projection\n"
                 "\t- check if the label field is integer type")
    parser = argparse.ArgumentParser(description)
    parser.add_argument("-in.vector",
                        help="absolute path to the vector (mandatory)",
                        dest="input_vector", required=True)
    parser.add_argument("-out.vector",
                        help="output vector",
                        dest="output_vector", required=False,
                        default=None)
    parser.add_argument("-dataField",
                        help="field containing labels (mandatory)",
                        dest="data_field", required=True)
    parser.add_argument("-epsg",
                        help="EPSG's code (mandatory)",
                        dest="epsg", required=True,
                        type=int)
    parser.add_argument("-pixArea",
                        help="pixel's area (mandatory)",
                        dest="pix_area", required=True,
                        type=float)
    parser.add_argument("-pixAreaThreshold",
                        help="pixel's area threshold",
                        dest="pix_area_threshold", required=False,
                        default=0.0, type=float)
    parser.add_argument("-doCorrections",
                        help="enable corrections (default = False)",
                        dest="do_corrections", required=False,
                        default=False, type=str2bool)
    args = parser.parse_args()

    do_check(args.input_vector, args.output_vector,
             args.epsg, args.pix_area, args.pix_area_threshold,
             args.do_corrections)
