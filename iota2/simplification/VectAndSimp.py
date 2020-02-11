#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vectorisation and simplification of a raster file with grass library
"""

import shutil
import sys, os, argparse
import time
import logging
logger = logging.getLogger(__name__)
try:
    from Common import Utils    
    from VectorTools import DeleteDuplicateGeometriesSqlite as ddg
    from VectorTools import checkGeometryAreaThreshField as checkGeom
    from VectorTools import vector_functions as vf
    from VectorTools import AddFieldArea as afa
    from VectorTools import DeleteField as df   
except ImportError:
    raise ImportError('Vector tools not well configured / installed')



#------------------------------------------------------------------------------
            
def init_grass(path, grasslib, debuglvl, epsg="2154"):

    """
    Initialisation of Grass GIS in lambert 93.
    
    in : 
        path : directory where create grassdata directory
        grasslib : install directory of Grass GIS
    """ 
    
    global gscript  
    
    # Grass folder Initialisation
    if not os.path.exists(os.path.join(path, "grassdata")):
        os.mkdir(os.path.join(path, "grassdata"))
    path_grassdata = os.path.join(path, "grassdata")
    
    # Init Grass environment
    gisbase = os.environ['GISBASE'] = grasslib
    gisdb = os.path.join(path_grassdata)
    sys.path.append(os.path.join(os.environ["GISBASE"], "etc", "python"))
    os.environ["GISBASE"] = gisbase

    # Overwrite and verbose parameters
    debugdic = {"critical" : '0', "error" : '0', "warning":'1', "info":'2' , "debug":'3'}
    os.environ["GRASS_OVERWRITE"] = "1"
    os.environ['GRASS_VERBOSE']= debugdic[debuglvl]

    # Grass functions import
    import grass.script.setup as gsetup
    import grass.script as gscript
    
    # Init Grass
    gsetup.init(gisbase, gisdb)
    
    # Delete existing location
    if os.path.exists(os.path.join(gisdb, "demolocation")):
        shutil.rmtree(os.path.join(gisdb, "demolocation"))
    
    # Create the location in Lambert 93
    gscript.run_command("g.proj", flags="c", epsg, location="demolocation")    
    
    # Create datas mapset
    if not os.path.exists(os.path.join(gisdb, "/demolocation/datas")) :
        try:
            gscript.start_command("g.mapset", flags="c", mapset = "datas", location = "demolocation", dbase = gisdb)
        except:
            raise Exception("Folder '%s' does not own to current user")%(gisdb)

def topologicalPolygonize(path, grasslib, raster, angle, out="", outformat = "ESRI_Shapefile", debulvl="info", epsg = "2154", logger=logger):

    timeinit = time.time()
    
    if out == "":
        out = os.path.splitext(raster)[0] + '.shp'

    if not os.path.exists(out) and os.path.exists(raster):
        print('Polygonize of raster file %s'%(os.path.basename(raster)))
        logger.info('Polygonize of raster file %s'%(os.path.basename(raster)))
        # local environnement
        localenv = os.path.join(path, "tmp%s"%(os.path.basename(os.path.splitext(raster)[0])))
        if os.path.exists(localenv):shutil.rmtree(localenv)
        os.mkdir(localenv)

        init_grass(localenv, grasslib,  debulvl)
        
        # classification raster import
        gscript.run_command("r.in.gdal", flags="e", input=raster, output="tile", overwrite=True)
        gscript.run_command("r.null", map="tile@datas", setnull=0)        
        
        timeimport = time.time()     
        logger.info(" ".join([" : ".join(["Classification raster import", str(timeimport - timeinit)]), "seconds"]))

        # manage grass region
        gscript.run_command("g.region", raster="tile")

        if angle:
            # vectorization with corners of pixel smoothing 
            gscript.run_command("r.to.vect", flags = "sv", input="tile@datas", output="vectile", type="area", overwrite=True)

        else:
            # vectorization without corners of pixel smoothing 
            gscript.run_command("r.to.vect", flags = "v", input = "tile@datas", output="vectile", type="area", overwrite=True)

            
        #gscript.run_command("v.edit", map = "vectile", tool = "delete", where = "cat > 250 or cat < 1")
        
        timevect = time.time()     
        logger.info(" ".join([" : ".join(["Classification vectorization", str(timevect - timeimport)]), "seconds"]))

        # Export vector file
        gscript.run_command("v.out.ogr", input = "vectile", output = out, format = outformat)

        timeexp = time.time()     
        logger.info(" ".join([" : ".join(["Vectorization exportation", str(timeexp - timevect)]), "seconds"]))

        shutil.rmtree(localenv)

    else:        
        logger.info("Output vector %s file already exists"%(os.path.basename(out)))
    
    return out

def generalizeVector(path, grasslib, vector, paramgene, method, mmu="", ncolumns="cat", out="", outformat = "ESRI_Shapefile", debulvl="info", epsg = "2154", logger=logger):

    timeinit = time.time()
    
    if out == "":
        out = os.path.splitext(vector)[0] + '_%s.shp'%(method)    

    if not os.path.exists(out) and os.path.exists(vector):        
        logger.info('Generalize (%s) of vector file %s'%(method, os.path.basename(vector)))
        # local environnement
        layer = os.path.basename(os.path.splitext(vector)[0])
        localenv = os.path.join(path, "tmp%s"%(layer))
        if os.path.exists(localenv):shutil.rmtree(localenv)
        os.mkdir(localenv)
        init_grass(localenv, grasslib,  debulvl, epsg)

        # remove non "cat" fields
        for field in vf.getFields(vector):
            if field != 'cat':
                df.deleteField(vector, field)

        gscript.run_command("v.in.ogr", flags="e", input=vector, output=layer, columns=["id", ncolumns], overwrite=True)
        
        try:            
            gscript.run_command("v.generalize", \
                                input = "%s@datas"%(layer), \
                                method=method, \
                                threshold="%s"%(paramgene), \
                                output="generalize",
                                overwrite=True)
        except:
            raise Exception("Something goes wrong with generalization parameters (method '%s' or input data)"%(method))

        if mmu != "":
            gscript.run_command("v.clean", input = "generalize", output="cleanarea", tool="rmarea", thres=mmu, type="area")                
            gscript.run_command("v.out.ogr", input = "cleanarea", output = out, format = outformat)            
        else:
            gscript.run_command("v.out.ogr", input = "generalize", output = out, format = outformat)

        timedouglas = time.time()     
        logger.info(" ".join([" : ".join(["Douglas simplification and exportation", str(timedouglas - timeinit)]), "seconds"]))

        # clean geometries
        tmp = os.path.join(localenv, "tmp.shp")
        checkGeom.checkGeometryAreaThreshField(out, 1, 0, tmp)

        for ext in ['.shp', '.dbf', '.shx', '.prj']:            
            shutil.copy(os.path.splitext(tmp)[0] + ext, os.path.splitext(out)[0] + ext)
            
        shutil.rmtree(localenv)

    else:    
        logger.info("Output vector file already exists")
        
    return out

def clipVectorfile(path, vector, clipfile, clipfield="", clipvalue="", outpath="", prefix="", debulvl="info", logger=logger):

    timeinit = time.time()

    if outpath == "":
        out = os.path.join(os.path.dirname(vector), '%s_%s.shp'%(prefix, str(clipvalue)))
    else:
        out = os.path.join(outpath, '%s_%s.shp'%(prefix, str(clipvalue)))

    # clean geometries
    tmp = os.path.join(path, "tmp.shp")
    checkGeom.checkGeometryAreaThreshField(vector, 1, 0, tmp)

    for ext in ['.shp', '.dbf', '.shx', '.prj']:            
        shutil.copy(os.path.splitext(tmp)[0] + ext, os.path.splitext(vector)[0] + ext)

    if not os.path.exists(out):
        if clipfile is not None:
            logger.info('Clip vector file %s with %s (%s == %s)'%(os.path.basename(vector), os.path.basename(clipfile), clipfield, clipvalue))
            print('Clip vector file %s with %s (%s == %s)'%(os.path.basename(vector), os.path.basename(clipfile), clipfield, clipvalue))
            
            # local environnement
            localenv = os.path.join(path, "tmp%s"%(str(clipvalue)))

            if os.path.exists(localenv):shutil.rmtree(localenv)
            os.mkdir(localenv)

            for ext in ['.shp', '.dbf', '.shx', '.prj']:            
                shutil.copy(os.path.splitext(clipfile)[0] +  ext, localenv)

            clipfile = os.path.join(localenv, os.path.basename(clipfile))

            if vf.getNbFeat(clipfile) != 1:
                clip = os.path.join(localenv, "clip.shp")
                layer = vf.getFirstLayer(clipfile)
                fieldType = vf.getFieldType(os.path.join(localenv, clipfile), clipfield)

                if fieldType == str:
                    command = "ogr2ogr -sql \"SELECT * FROM %s WHERE %s = \'%s\'\" %s %s"%(layer, \
                                                                                           clipfield, \
                                                                                           clipvalue, \
                                                                                           clip, \
                                                                                           clipfile)
                    Utils.run(command)
                elif fieldType == int or fieldType == float:
                    command = "ogr2ogr -sql \"SELECT * FROM %s WHERE %s = %s\" %s %s"%(layer, \
                                                                                       clipfield, \
                                                                                       clipvalue, \
                                                                                       clip, \
                                                                                       clipfile)

                    Utils.run(command)             
                else:
                    raise Exception('Field type %s not handled'%(fieldType))
            else:
                clip = os.path.join(path, clipfile)
                logger.info("'%s' shapefile has only one feature which will used to clip data"%(clip))

            # clip
            clipped = os.path.join(localenv, "clipped.shp")

            command = "ogr2ogr -select cat -clipsrc %s %s %s"%(clip, \
                                                               clipped, \
                                                               vector)

            Utils.run(command)

        else:
            clipped = os.path.join(localenv, "merge.shp")

        timeclip = time.time()     
        logger.info(" ".join([" : ".join(["Clip final shapefile", str(timeclip - timeinit)]), "seconds"]))

        # Delete duplicate geometries
        ddg.deleteDuplicateGeometriesSqlite(clipped)

        for ext in [".shp",".shx",".dbf",".prj"]:
            shutil.copy(os.path.splitext(clipped)[0] + ext, os.path.join(localenv, "clean") + ext)
            os.remove(os.path.splitext(clipped)[0] + ext)

        timedupli = time.time()     
        logger.info(" ".join([" : ".join(["Delete duplicated geometries", str(timedupli - timeclip)]), "seconds"]))

        # Check geom
        vf.checkValidGeom(os.path.join(localenv, "clean.shp"))

        # Add Field Area (hectare)
        afa.addFieldArea(os.path.join(localenv, "clean.shp"), 10000)    

        for ext in [".shp",".shx",".dbf",".prj"]:
            shutil.copy(os.path.join(localenv, "clean" + ext), os.path.splitext(out)[0] + ext)

        shutil.rmtree(localenv)

        timeclean = time.time()     
        logger.info(" ".join([" : ".join(["Clean empty geometries and compute areas (ha)", str(timeclean - timedupli)]), "seconds"]))

    else:
  
        logger.info("Output vector file '%s' already exists"%(out))
        
            
        
def simplification(path, raster, grasslib, out, douglas, hermite, mmu, angle=True, debulvl="info", logger=logger):
    """
        Simplification of raster dataset with Grass GIS.
        
        in :
            path : path where do treatments
            raster : classification raster name
            douglas : Douglas-Peucker reduction value
            hermite : Hermite smoothing level
            angle : Smooth corners of pixels (45°)
            grasslib : Path of folder with grass GIS install
            
        out : 
            shapefile with standart name ("tile_ngrid.shp")
    """
    
    timeinit = time.time()

    init_grass(path, grasslib,  debulvl)
        
    # classification raster import        
    gscript.run_command("r.in.gdal", flags="e", input=raster, output="tile", overwrite=True)

    timeimport = time.time()     
    logger.info(" ".join([" : ".join(["Classification raster import", str(timeimport - timeinit)]), "seconds"]))
    
    # manage grass region
    gscript.run_command("g.region", raster="tile")
    
    if angle:
        # vectorization with corners of pixel smoothing 
        gscript.run_command("r.to.vect", flags = "sv", input="tile@datas", output="vectile", type="area", overwrite=True)
        
    else:
        # vectorization without corners of pixel smoothing 
        gscript.run_command("r.to.vect", flags = "v", input = "tile@datas", output="vectile", type="area", overwrite=True)

    timevect = time.time()     
    logger.info(" ".join([" : ".join(["Classification vectorization", str(timevect - timeimport)]), "seconds"]))
    
    inputv = "vectile"
    # Douglas simplification    
    if douglas is not None:
        gscript.run_command("v.generalize", \
                            input = "%s@datas"%(inputv), \
                            method="douglas", \
                            threshold="%s"%(douglas), \
                            output="douglas",
                            overwrite=True)
        inputv = "douglas"
        
        timedouglas = time.time()     
        logger.info(" ".join([" : ".join(["Douglas simplification", str(timedouglas - timevect)]), "seconds"]))
        timevect = timedouglas
    
    # Hermine simplification
    if hermite is not None:
        gscript.run_command("v.generalize", \
                            input = "%s@datas"%(inputv), \
                            method="hermite", \
                            threshold="%s"%(hermite), \
                            output="hermine", \
                            overwrite=True)
        inputv = "hermine"

        timehermine = time.time()     
        logger.info(" ".join([" : ".join(["Hermine smoothing", str(timehermine - timevect)]), "seconds"]))
        timevect = timehermine
        
    # Delete non OSO class polygons (sea water, nodata and crown entities)
    gscript.run_command("v.edit", map = "%s@datas"%(inputv), tool = "delete", where = "cat > 250 or cat < 1")

    # Export shapefile vector file
    if os.path.splitext(out)[1] != '.shp':
        out = os.path.splitext(out)[0] + '.shp'
        logger.info("Output name has been changed to '%s'"%(out))

    # Delete under MMU limit    
    gscript.run_command("v.clean", input = "%s@datas"%(inputv), output="cleanarea", tool="rmarea", thres=mmu, type="area")        

    # Export vector file
    gscript.run_command("v.out.ogr", input = "cleanarea", output = out, format = "ESRI_Shapefile")

    timeexp = time.time()     
    logger.info(" ".join([" : ".join(["Vectorization exportation", str(timeexp - timevect)]), "seconds"]))
        
    shutil.rmtree(os.path.join(path, "grassdata"))

    timeend = time.time()     
    logger.info(" ".join([" : ".join(["Global Vectorization and Simplification process", str(timeend - timeinit)]), "seconds"]))
    
if __name__ == "__main__":
    if len(sys.argv) == 1:
        prog = os.path.basename(sys.argv[0])
        print('      '+sys.argv[0]+' [options]') 
        print("     Help : ", prog, " --help")
        print("        or : ", prog, " -h")
        sys.exit(-1)  
    else:
        usage = "usage: %prog [options] "
        parser = argparse.ArgumentParser(description = "Vectorisation and simplification of a raster file")
        
        parser.add_argument("-wd", dest="path", action="store", \
                            help="Working directory", required = True)
        
        parser.add_argument("-grass", dest="grass", action="store", \
                            help="path of grass library", required = True)
                            
        parser.add_argument("-in", dest="raster", action="store", \
                            help="classification raster", required = True)
                            
        parser.add_argument("-out", dest="out", action="store", \
                            help="output folder and name", required = True)  
                            
        parser.add_argument("-douglas", dest="douglas", action="store", \
                            help="Douglas-Peucker reduction value, if empty no Douglas-Peucker reduction")   
                            
        parser.add_argument("-hermite", dest="hermite", action="store", \
                            help="Hermite smoothing level, if empty no Hermite smoothing reduction")   
                            
        parser.add_argument("-angle", action="store_true", \
                            help="Smooth corners of pixels (45°), if empty no corners smoothing", default = False)
        
        parser.add_argument("-mmu", dest="mmu", action="store", \
                                help="Mininal Mapping Unit (shapefile area unit)", type = int, required = True)                        

        parser.add_argument("-debuglvl", dest="debuglvl", action="store", \
                                help="Debug level", default = "info", required = False)                        
                                
        args = parser.parse_args()

        simplification(args.path, args.raster, args.grass, args.out, args.douglas, args.hermite, args.mmu, args.angle, args.debuglvl)
