#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sys
import os
import sqlite3 as lite
import argparse

def deleteDuplicateGeometriesSqlite(shapefile, outformat = "ESRI shapefile", do_corrections=True, output_file=None):
    """Check if a features is duplicates, then if it does it will not be copied in output shapeFile

    Parameters
    ----------
    input_shape : string
        input shapeFile
    do_correction : bool
        flag to remove dupplicates
    output_shape : string
        output shapeFile, if set to None output_shape = input_shape
    Return
    ------
    tuple
        (output_shape, duplicates_features_number) where duplicates_features_number
        is the number of duplicated features
    """
    if outformat != "SQlite":
        tmpnamelyr = "tmp" + os.path.splitext(os.path.basename(shapefile))[0]
        tmpname = "%s.sqlite"%(tmpnamelyr)
        outsqlite = os.path.join(os.path.dirname(shapefile), tmpname)
        os.system("ogr2ogr -f SQLite %s %s -nln tmp"%(outsqlite, shapefile))
    else:
        outsqlite = shapefile

    conn = lite.connect(outsqlite)
    cursor = conn.cursor()

    cursor.execute("select count(*) from tmp")
    nbfeat0 = cursor.fetchall()
    
    cursor.execute("create temporary table to_del (ogc_fid int, geom blob);")
    cursor.execute("insert into to_del(ogc_fid, geom) select min(ogc_fid), GEOMETRY from tmp group by GEOMETRY having count(*) > 1;")
    cursor.execute("delete from tmp where exists(select * from to_del where to_del.geom = tmp.GEOMETRY and to_del.ogc_fid <> tmp.ogc_fid);")

    cursor.execute("select count(*) from tmp")
    nbfeat1 = cursor.fetchall()

    nb_dupplicates = int(nbfeat0[0][0]) - int(nbfeat1[0][0])

    if do_corrections:
        conn.commit()

        if output_file is None and outformat != "SQlite":
            os.system("rm %s"%(shapefile))

        shapefile = output_file if output_file is not None else shapefile
        
        if output_file is None and outformat != "SQlite":
            os.system("ogr2ogr -f 'ESRI Shapefile' %s %s"%(shapefile, outsqlite))

        if nb_dupplicates != 0:
            print("Analyse of duplicated features done. %s duplicates found and deleted"%(nb_dupplicates))
        else:
            print("Analyse of duplicated features done. No duplicates found")
            
        cursor = conn = None
        
    if outformat != "SQlite":
        os.remove(outsqlite)
        
    return shapefile, nb_dupplicates

if __name__ == "__main__":
    if len(sys.argv) == 1:
        prog = os.path.basename(sys.argv[0])
        print('      '+sys.argv[0]+' [options]') 
        print("     Help : ", prog, " --help")
        print("        or : ", prog, " -h")
        sys.exit(-1)  
    else:
        usage = "usage: %prog [options] "
        parser = argparse.ArgumentParser(description = "Find geometries duplicates based on sqlite method")
        
        parser.add_argument("-in", dest="inshape", action="store", \
                            help="Input shapefile to analyse", required = True)
                                  
        args = parser.parse_args()

        deleteDuplicateGeometriesSqlite(args.inshape)
