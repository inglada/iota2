#!/usr/bin/python

import os
import sys
import argparse
import vector_functions as vf

#This file produces a new file without double geometries in a shapefile"

def percentage(part, whole):
  return 100 * float(part)/float(whole)

def DeleteDupGeom(infile):
	ds = vf.openToWrite(infile)
	lyr = ds.GetLayer()
	features = vf.getNbFeat(infile)
	geoms = dict()
	newshp = vf.copyShp(infile, "nodoublegeom")
	for feat in lyr:
		ge = feat.GetGeometryRef()
		f =  feat.GetFID()
		geoms[f] = ge.ExportToWkt()

	inverted = dict()
	for (k, v) in geoms.iteritems():
  		if not inverted.has_key(v[0]):
    			inverted[v] = k

	new_dict = dict()
	for (k, v) in inverted.iteritems():
   		new_dict[v] = k
	print "Please wait ... copying features running"

        for k in new_dict:
		inFeat = lyr.GetFeature(k)
		vf.copyFeatInShp2(inFeat, newshp)
	print "Process done"
        
        return newshp

if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Delete double geometries in a shapefile")
        parser.add_argument("-s", dest="shapefile", action="store", \
                            help="Input shapefile", required = True)
	args = parser.parse_args()
        print 'Delete duplicate geometries...'
        DeleteDupGeom(args.shapefile)
		