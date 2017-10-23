#!/usr/bin/python
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
Convert raster to sqlite point (pixel centroid) containing raster(s) value
"""

import sys, os, argparse, time

try:
    import BufferOgr
except ImportError:
    raise ImportError('Vector tools not well configured / installed')

try:
    import otbAppli
except ImportError:
    raise ImportError('Iota2 not well configured / installed')


def maskSampleSelection(path, raster, maskmer, ram):
    
    tifMasqueMer = os.path.join(path, 'masque_mer.tif')
    bmapp = otbAppli.CreateBandMathApplication(raster, "im1b1*0", ram, 'uint8', tifMasqueMer)
    bmapp.ExecuteAndWriteOutput()

    maskmerbuff = os.path.join(path, os.path.splitext(os.path.basename(maskmer))[0] + '_buff.shp')
    BufferOgr.bufferPoly(maskmer, maskmerbuff, 500)

    tifMasqueMerRecode = os.path.join(path, 'masque_mer_recode.tif')
    rastApp = otbAppli.CreateRasterizationApplication(maskmerbuff, tifMasqueMer, 1, tifMasqueMerRecode)
    rastApp.Execute()
    #command = "gdal_rasterize -burn 1 %s %s"%(maskmerbuff, tifMasqueMer)
    #os.system(command) 

    out = os.path.join(path, 'mask.tif')
    bmapp = otbAppli.CreateBandMathApplication([raster, rastApp], \
                                               "((im1b1==0) || (im1b1==51)) && (im2b1==0)?0:1", \
                                               ram, 'uint8', out)
    bmapp.ExecuteAndWriteOutput()

    return out

def sampleSelection(path, raster, vecteur, field, ram='128', split="", mask=""):

    timeinit = time.time()
    
    # polygon class stats (stats.xml)
    outxml = os.path.join(path, 'stats' + str(split) + '.xml')
    otbParams = {'in':raster, 'vec':vecteur, 'field':field, 'out':outxml, 'ram':ram}
    statsApp = otbAppli.CreatePolygonClassStatisticsApplication(otbParams)
    statsApp.ExecuteAndWriteOutput()

    timestats = time.time()     
    print " ".join([" : ".join(["Stats calculation", str(timestats - timeinit)]), "seconds"])

    if mask != '':
        mask = maskSampleSelection(path, raster, mask, ram)
    else:
        mask = ''
    
    # Sample selection
    outsqlite =  os.path.join(path, 'sample_selection' + str(split) + '.sqlite')
    otbParams = {'in':raster, 'vec':vecteur, 'field':field, 'instats': outxml, \
                 'out':outsqlite, 'mask':mask, 'ram':ram, 'strategy':'all', 'sampler':'random'}
    sampleApp = otbAppli.CreateSampleSelectionApplication(otbParams)
    sampleApp.ExecuteAndWriteOutput()

    timesample = time.time()     
    print " ".join([" : ".join(["Sample selection", str(timesample - timestats)]), "seconds"])

    return outsqlite

def sampleExtraction(raster, sample, field, outname, split, ram='128'):

    timesample = time.time()
    
    # Sample extraction
    outfile = os.path.splitext(str(outname))[0] + split + os.path.splitext(str(outname))[1]
    otbParams = {'in':raster, 'vec':sample, 'field':field.lower(), 'out':outfile, 'ram':ram}
    extractApp = otbAppli.CreateSampleExtractionApplication(otbParams)
    extractApp.ExecuteAndWriteOutput()

    timeextract = time.time()     
    print " ".join([" : ".join(["Sample extraction", str(timeextract - timesample)]), "seconds"])

def RastersToSqlitePoint(path, vecteur, field, outname, ram, rtype, rasters, maskmer="", split=""):

    timeinit = time.time()
    # Rasters concatenation
    if len(rasters) > 1:
        concatApp = otbAppli.CreateConcatenateImagesApplication(rasters, ram, rtype)
        concatApp.Execute()
        classif = otbAppli.CreateBandMathApplication(rasters[0], "im1b1", ram, rtype)
        classif.Execute()
    else:
        concatApp = otbAppli.CreateBandMathApplication(rasters, "im1b1", ram, rtype)
        concatApp.Execute()
        
    timeconcat = time.time()     
    print " ".join([" : ".join(["Raster concatenation", str(timeconcat - timeinit)]), "seconds"])

    # Stats and sample selection
    if len(rasters) == 1:
        classif = concatApp
        
    outsqlite = sampleSelection(path, classif, vecteur, field, ram, split, maskmer)

    # Stats extraction
    sampleExtraction(concatApp, outsqlite, field, outname, split, ram)            
    
if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
 
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Regulararize a raster")
        parser.add_argument("-wd", dest="path", action="store", \
                            help="Working directory", required = True)

        parser.add_argument("-zone", dest="zone", action="store", \
                            help="zonal entitites (shapefile)", required = True)

	parser.add_argument("-field", dest="field", action="store", \
                            help="field name", default = "value", required = False)        
                            
        parser.add_argument("-nbcore", dest="core", action="store", \
                            help="Number of cores to use for OTB applications", required = True)
                            
        parser.add_argument("-ram", dest="ram", action="store", \
                            help="Ram for otb processes", required = True)
                            
        parser.add_argument("-out", dest="out", action="store", \
                            help="output path ", required = True)                            

        parser.add_argument("-sea", dest="sea", action="store", \
                            help="terrestrial mask (to separate sea and inland waters)", required = False)
        
	parser.add_argument("-split", dest="split", action="store", \
                            help="split index",default = "",required = False)

        parser.add_argument("-listRast", dest="listRast", nargs='+', \
                            help="list of rasters to extract stats (first one have to be classification raster" \
                            "and rasters must have the same resolution)")
        
        parser.add_argument("-rtype", dest="rtype", action="store", \
                            help="Rasters pixel format (OTB style)", required = True)
        
        args = parser.parse_args()
        os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"]= str(args.core)
    
        sample_extract, time_poly_class_stats, \
        time_sample_selection, time_sample_extract = zonal_stats_otb(args.path, \
                                                                     args.zone, \
                                                                     args.field, \
                                                                     args.out, \
                                                                     args.ram, \
                                                                     args.rtype, \
                                                                     args.rasters, \
                                                                     args.sea, \
                                                                     args.split)