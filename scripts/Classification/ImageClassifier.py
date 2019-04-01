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

from Common import ServiceConfigFile as SCF

logger = logging.getLogger(__name__)


def str2bool(v):
    if v.lower() not in ('yes', 'true', 't', 'y', '1', 'no', 'false', 'f', 'n', '0'):
        raise argparse.ArgumentTypeError('Boolean value expected.')

    retour = True
    if v.lower() in ('no', 'false', 'f', 'n', '0'):
        retour = False
    return retour


class iota2Classification():
    def __init__(self, cfg, features_stack, classifier_type, model, tile, output_directory, nb_class, 
                 confidence=True, proba_map=False, classif_mask=None,
                 dim_red={}, pixType="uint8", working_directory=None,
                 stat_norm=None, RAM=128, logger=logger, mode="usually"):
        """
        TODO :
            remove the dependance from cfg which still needed to compute features (first, remove from generateFeatures)
            remove the 'mode' parameter
        """
        self.classif_mask = classif_mask
        self.output_directory = output_directory
        self.RAM = RAM
        self.pixType = pixType
        self.stats = stat_norm
        self.classifier_model = model
        self.model_name = self.get_model_name(model)
        self.seed = self.get_model_seed(model)
        self.features_stack = features_stack
        self.classification = os.path.join(output_directory,
                                           "Classif_{}_model_{}_seed_{}.tif".format(tile,
                                                                                    self.model_name,
                                                                                    self.seed))
        self.confidence = os.path.join(output_directory,
                                       "{}_model_{}_confidence_seed_{}.tif".format(tile,
                                                                                   self.model_name,
                                                                                   self.seed))
        self.proba_map_path = self.get_proba_map(classifier_type,
                                                 output_directory,
                                                 model,
                                                 tile, proba_map)
        self.working_directory = working_directory
    
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
        proba_map_name = "PROBAMAP_{}_model_{}_seed_{}.tif".format(tile,
                                                                   model_name,
                                                                   seed)
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
        import shutil
        from Common.OtbAppBank import CreateImageClassifierApplication
        from Common.OtbAppBank import CreateBandMathApplication

        if self.working_directory:
            self.classification = os.path.join(self.working_directory, os.path.split(self.classification)[-1])
            self.confidence = os.path.join(self.working_directory, os.path.split(self.confidence)[-1])
        classifier_options = {"in": self.features_stack,
                              "model": self.classifier_model,
                              "confmap": self.confidence,
                              "ram": str(0.4 * float(self.RAM)),
                              "pixType": self.pixType,
                              "out": self.classification}
        if self.proba_map_path:
            if self.working_directory:
                self.proba_map_path = os.path.join(self.working_directory, os.path.split(self.proba_map_path)[-1])
            classifier_options["probamap"] = self.proba_map_path
            classifier_options["nbclasses"] = "10"
        if self.stats:
            classifier_options["imstat"] = self.stats
        classifier = CreateImageClassifierApplication(classifier_options)
        logger.info("Compute Classification : {}".format(self.classification))
        classifier.ExecuteAndWriteOutput()
        logger.info("Classification : {} done".format(self.classification))

        if self.classif_mask:
            mask_filter = CreateBandMathApplication({"il": [self.classification, self.classif_mask],
                                                     "ram": self.RAM,
                                                     "pixType": self.pixType,
                                                     "out": self.classification,
                                                     "exp": "im2b1>=1?im1b1:0"})
            mask_filter.ExecuteAndWriteOutput()
            mask_filter = CreateBandMathApplication({"il": [self.confidence, self.classif_mask],
                                                     "ram": self.RAM,
                                                     "pixType": self.pixType,
                                                     "out": self.confidence,
                                                     "exp": "im2b1>=1?im1b1:0"})
            mask_filter.ExecuteAndWriteOutput()
            if self.proba_map_path:
                mask_filter = CreateBandMathApplication({"il": [self.proba_map_path, self.classif_mask],
                                                         "ram": self.RAM,
                                                         "pixType": self.pixType,
                                                         "out": self.proba_map_path,
                                                         "exp": "im2b1>=1?im1b1:0"})
                mask_filter.ExecuteAndWriteOutput()
        if self.working_directory:
            shutil.copy(self.classification, os.path.join(self.output_directory,
                                                          os.path.split(self.classification)[-1]))
            os.remove(self.classification)
            shutil.copy(self.confidence, os.path.join(self.output_directory,
                                                          os.path.split(self.confidence)[-1]))
            os.remove(self.confidence)
            if self.proba_map_path:
                shutil.copy(self.proba_map_path, os.path.join(self.output_directory,
                                                              os.path.split(self.proba_map_path)[-1]))
                os.remove(self.proba_map_path)

def launchClassification(tempFolderSerie, Classifmask, model, stats,
                         outputClassif, confmap, pathWd, cfg, pixType,
                         MaximizeCPU=True, RAM=500, logger=logger):
    """
    """
    from Common import GenerateFeatures as genFeatures
    from Sampling import DimensionalityReduction as DR
    
    from Common import FileUtils as fu
    from Common.OtbAppBank import getInputParameterOutput
    if not isinstance(cfg, SCF.serviceConfigFile):
        cfg = SCF.serviceConfigFile(cfg)

    classifier_type = cfg.getParam('argTrain', 'classifier')
    output_directory = os.path.join(cfg.getParam('chain', 'outputPath'), "classif")
    tiles = (cfg.getParam('chain', 'listTile')).split()
    tile = fu.findCurrentTileInString(Classifmask, tiles)
    
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
    # these two parameters should come from the configuration file
    nb_class = 10
    proba_map_expected = True
    classif = iota2Classification(cfg, ClassifInput, classifier_type, model, tile, output_directory,
                                  nb_class, proba_map=proba_map_expected, working_directory=pathWd,
                                  classif_mask=Classifmask, pixType=pixType, stat_norm=stats, RAM=RAM,
                                  mode=mode)
    classif.generate()


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







