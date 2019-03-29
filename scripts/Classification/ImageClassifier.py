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
import argparse
import shutil
import os
import ast
from config import Config
import logging
import otbApplication as otb
from Common import FileUtils as fu
from Common import OtbAppBank
from Common import GenerateFeatures as genFeatures
from Common import ServiceConfigFile as SCF
from Sampling import DimensionalityReduction as DR
import logging


logger = logging.getLogger(__name__)


def str2bool(v):
    if v.lower() not in ('yes', 'true', 't', 'y', '1', 'no', 'false', 'f', 'n', '0'):
        raise argparse.ArgumentTypeError('Boolean value expected.')

    retour = True
    if v.lower() in ('no', 'false', 'f', 'n', '0'):
        retour = False
    return retour


class iota2Classification():
    def __init__(self, cfg, classifier_type, model, tile, output_directory,
                 confidence=True, proba_map=False, classif_mask=None,
                 dim_red={}, pixType="uint8", working_directory=None,
                 logger=logger, mode="usually"):
        """
        TODO :
            remove the dependance from cfg which still needed to compute features (first, remove from generateFeatures)
            remove the 'mode' parameter
        """
        self.classification = ""
        self.confidence = ""
  
        self.proba_map_path = self.get_proba_map(classifier_type,
                                                 output_directory,
                                                 model,
                                                 tile, proba_map)

    
    def get_proba_map(self, classifier_type, output_directory, model, tile, gen_proba):
        """get probability map absolute path

        Parameters
        ----------
        classifier_type : string
            classifier's name (provided by OTB)
        output_directory : string
            output directory
        model : string
            model's absolute path
        tile : string
            tile's name to compute

        Return
        ------
        string
            absolute path to the probality map
        
        """
        model_name = self.get_model_name(model)
        seed = self.get_model_seed(model)
        proba_map_name = "PROBAMAP_{}_model_{}_seed_{}.tif".format(tile, model_name, seed)

        proba_map = ""
        classifier_avail = ["sharkrf"]
        if classifier_type in classifier_avail:
            proba_map = os.path.join(output_directory, proba_map_name)
        if gen_proba and proba_map is "":
            warn_mes = ("classifier '{}' not available to generate a probability "
                        "map, those available are {}").format(classifier_type, classifier_avail)
            logger.warning(warn_mes)
        return proba_map if gen_proba else ""

    def get_model_name(self, model):
        """
        """
        return os.path.splitext(os.path.basename(model))[0].split("_")[1]

    def get_model_seed(self, model):
        """
        """
        return os.path.splitext(os.path.basename(model))[0].split("_")[3]
        
    def generate(self):
        """
        """
        pass

def filterOTB_output(raster, mask, output, RAM, outputType="uint8"):

    bandMathFilter = otb.Registry.CreateApplication("BandMath")
    bandMathFilter.SetParameterString("exp", "im2b1>=1?im1b1:0")
    bandMathFilter.SetParameterStringList("il", [raster, mask])
    bandMathFilter.SetParameterString("ram", str(0.9 * float(RAM)))
    bandMathFilter.SetParameterString("out", output+"?&writegeom=false")
    if outputType=="uint8":
        bandMathFilter.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint8)
    elif outputType=="uint16":
        bandMathFilter.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint16)
    elif outputType=="float":
        bandMathFilter.SetParameterOutputImagePixelType("out", otb.ImagePixelType_float)
    bandMathFilter.ExecuteAndWriteOutput()


def computeClassifications(model, outputClassif, confmap, MaximizeCPU,
                           Classifmask, stats, AllFeatures, RAM, pixType="uint8"):
    """
    """
    classifier = otb.Registry.CreateApplication("ImageClassifier")
    if isinstance(AllFeatures, str):
        classifier.SetParameterString("in", AllFeatures)
    else:
        classifier.SetParameterInputImage("in", AllFeatures.GetParameterOutputImage("out"))
    classifier.SetParameterString("out", outputClassif+"?&writegeom=false")
    if pixType=="uint8":
        classifier.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint8)
    elif pixType=="uint16":
        classifier.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint16)
    classifier.SetParameterString("confmap", confmap+"?&writegeom=false")
    classifier.SetParameterString("probamap", outputClassif.replace(".tif", "_PROBAMAP.tif"))
    classifier.SetParameterString("nbclasses", "13")
    classifier.SetParameterString("model", model)
    classifier.SetParameterString("ram", str(0.4 * float(RAM)))

    if not MaximizeCPU:
        classifier.SetParameterString("mask", Classifmask)
    if stats:
        classifier.SetParameterString("imstat", stats)

    return classifier, AllFeatures


def launchClassification(tempFolderSerie, Classifmask, model, stats,
                         outputClassif, confmap, pathWd, cfg, pixType,
                         MaximizeCPU=True, RAM=500, logger=logger):
    """
    """
    
    from Common.OtbAppBank import getInputParameterOutput
    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)

    classifier_type = cfg.getParam('argTrain', 'classifier')
    output_directory = os.path.join(cfg.getParam('chain', 'outputPath'), "classif")
    tiles = (cfg.getParam('chain', 'listTile')).split()
    tile = fu.findCurrentTileInString(Classifmask, tiles)
    
    classif = iota2Classification(cfg, classifier_type, model, tile, output_directory, proba_map=True)

    pause = raw_input("STOP")

    
    wMode = cfg.getParam('GlobChain', 'writeOutputs')
    outputPath = cfg.getParam('chain', 'outputPath')
    featuresPath = os.path.join(outputPath, "features")
    dimred = cfg.getParam('dimRed', 'dimRed')
    wd = pathWd
    if not pathWd: 
        wd = featuresPath

    try:
        useGapFilling = cfg.getParam('GlobChain', 'useGapFilling')
    except:
        useGapFilling = True
    wd = os.path.join(featuresPath, tile)

    if pathWd:
        wd = os.path.join(pathWd, tile)
        if not os.path.exists(wd):
            try:
                os.mkdir(wd)
            except:
                logger.warning(wd + "Allready exists")

    mode = "usually"
    if "SAR.tif" in outputClassif:
        mode = "SAR"
    
    AllFeatures, feat_labels, dep_features = genFeatures.generateFeatures(wd, tile, cfg, mode=mode)

    feature_raster = AllFeatures.GetParameterValue(getInputParameterOutput(AllFeatures))
    if wMode:
        if not os.path.exists(feature_raster):
            AllFeatures.ExecuteAndWriteOutput()
        AllFeatures = feature_raster
    else:
        AllFeatures.Execute()

    ClassifInput = AllFeatures

    if dimred:
        logger.debug("Classification model : {}".format(model))
        dimRedModelList = DR.GetDimRedModelsFromClassificationModel(model)
        logger.debug("Dim red models : {}".format(dimRedModelList))
        [ClassifInput, other] = DR.ApplyDimensionalityReductionToFeatureStack(cfg,AllFeatures,
                                                                              dimRedModelList)
        
        if wMode:
            ClassifInput.ExecuteAndWriteOutput()
        else:
            ClassifInput.Execute()

    classifier, inputStack = computeClassifications(model, outputClassif,
                                                    confmap, MaximizeCPU,
                                                    Classifmask, stats,
                                                    ClassifInput, RAM, 
                                                    pixType=pixType)

    logger.info("Compute Classification : {}".format(outputClassif))
    classifier.ExecuteAndWriteOutput()
    logger.info("Classification : {} done.".format(outputClassif))
    if MaximizeCPU:
        filterOTB_output(outputClassif, Classifmask, outputClassif, RAM, outputType=pixType)
        filterOTB_output(confmap, Classifmask, confmap, RAM, outputType="float")

    if pathWd:
        shutil.copy(outputClassif, outputPath+"/classif")
        os.remove(outputClassif)
    if pathWd:
        shutil.copy(confmap, outputPath+"/classif")
        os.remove(confmap)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Performs a classification of the input image (compute in RAM) according to a model file, ")
    parser.add_argument("-in", dest="tempFolderSerie", help="path to the folder which contains temporal series", default=None, required=True)
    parser.add_argument("-mask", dest="mask", help="path to classification's mask", default=None, required=True)
    parser.add_argument("-pixType", dest="pixType", help="pixel format", default=None, required=True)
    parser.add_argument("-model", dest="model", help="path to the model", default=None, required=True)
    parser.add_argument("-imstat", dest="stats", help="path to statistics", default=None, required=False)
    parser.add_argument("-out", dest="outputClassif", help="output classification's path", default=None, required=True)
    parser.add_argument("-confmap", dest="confmap", help="output classification confidence map", default=None, required=True)
    parser.add_argument("-ram", dest="ram", help="pipeline's size", default=128, required=False)
    parser.add_argument("--wd", dest="pathWd", help="path to the working directory", default=None, required=False)
    parser.add_argument("-conf", help="path to the configuration file (mandatory)", dest="pathConf", required=True)
    parser.add_argument("-maxCPU", help="True : Class all the image and after apply mask",
                        dest="MaximizeCPU", default="False", choices=["True", "False"], required=False)
    args = parser.parse_args()

    # load configuration file
    cfg = SCF.serviceConfigFile(args.pathConf)

    launchClassification(args.tempFolderSerie, args.mask, args.model, args.stats, args.outputClassif,
                         args.confmap, args.pathWd, cfg, args.pixType, args.MaximizeCPU)







