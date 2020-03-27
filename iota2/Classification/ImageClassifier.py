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

import argparse
import os
import logging
from typing import List, Dict, Union, Optional
from iota2.Common import FileUtils as fu
SENSORS_PARAMS = Dict[str, Union[str, List[str], int]]

LOGGER = logging.getLogger(__name__)


def str2bool(v):
    if v.lower() not in ('yes', 'true', 't', 'y', '1', 'no', 'false', 'f', 'n',
                         '0'):
        raise argparse.ArgumentTypeError('Boolean value expected.')

    retour = True
    if v.lower() in ("no", "false", "f", "n", "0"):
        retour = False
    return retour


def autoContext_classification_param(iota2_directory, data_field):
    """
    Parameters
    ----------
    iota2_run_dir : string
        path to iota² output path
    """
    import re
    from iota2.Common.FileUtils import FileSearch_AND
    from iota2.Common.FileUtils import getListTileFromModel
    from iota2.Common.FileUtils import getFieldElement

    models_description = os.path.join(iota2_directory, "config_model",
                                      "configModel.cfg")
    models_directory = os.path.join(iota2_directory, "model")
    sample_sel_directory = os.path.join(iota2_directory, "samplesSelection")

    parameters = []
    all_models = sorted(os.listdir(models_directory))
    for model in all_models:
        model_name = model.split("_")[1]
        seed_num = model.split("_")[-1]
        tiles = sorted(getListTileFromModel(model_name, models_description))
        #~ samples_region_1f1_seed_0.shp
        model_sample_sel = FileSearch_AND(
            sample_sel_directory, True,
            "samples_region_{}_seed_{}.shp".format(model_name, seed_num))[0]
        labels = getFieldElement(model_sample_sel,
                                 driverName="ESRI Shapefile",
                                 field=data_field,
                                 mode="unique")
        models = FileSearch_AND(os.path.join(models_directory, model), True,
                                ".rf")
        for tile in tiles:
            tile_mask = FileSearch_AND(
                os.path.join(iota2_directory, "shapeRegion"), True,
                "{}_{}.tif".format(model_name.split("f")[0], tile))[0]
            tile_seg = FileSearch_AND(
                os.path.join(iota2_directory, "features", tile, "tmp"), True,
                "SLIC_{}.tif".format(tile))[0]
            parameters.append({
                "model_name":
                model_name,
                "seed_num":
                seed_num,
                "tile":
                tile,
                "tile_segmentation":
                tile_seg,
                "tile_mask":
                tile_mask,
                "labels_list":
                labels,
                "model_list":
                sorted(models,
                       key=lambda x: int(
                           re.findall("\d", os.path.basename(x))[0]))
            })
    return parameters


def autoContext_launch_classif(
        parameters_dict: List[Dict[str, Union[str, List[str]]]],
        classifier_type: str, tile: str, proba_map_expected: bool, dimred,
        data_field: str, write_features: bool, reduction_mode,
        iota2_run_dir: str, sar_optical_post_fusion: bool,
        nomenclature_path: str, sensors_parameters: SENSORS_PARAMS, RAM: int,
        WORKING_DIR: str):
    """
    """
    from iota2.Common.FileUtils import getOutputPixType

    pixType = getOutputPixType(nomenclature_path)

    models = parameters_dict["model_list"]
    classif_mask = parameters_dict["tile_mask"]

    tempFolderSerie = ""
    stats = os.path.join(
        iota2_run_dir, "stats",
        "Model_{}_seed_{}.xml".format(parameters_dict["model_name"],
                                      parameters_dict["seed_num"]))

    outputClassif = "Classif_{}_model_{}_seed_{}.tif".format(
        parameters_dict["tile"], parameters_dict["model_name"],
        parameters_dict["seed_num"])
    confmap = "{}_model_{}_confidence_seed_{}.tif".format(
        parameters_dict["tile"], parameters_dict["model_name"],
        parameters_dict["seed_num"])

    launchClassification(tempFolderSerie,
                         classif_mask,
                         models,
                         stats,
                         outputClassif,
                         confmap,
                         WORKING_DIR,
                         classifier_type,
                         tile,
                         proba_map_expected,
                         dimred,
                         sar_optical_post_fusion,
                         iota2_run_dir,
                         data_field,
                         write_features,
                         reduction_mode,
                         sensors_parameters,
                         pixType,
                         MaximizeCPU=True,
                         RAM=RAM,
                         auto_context={
                             "labels_list":
                             parameters_dict["labels_list"],
                             "tile_segmentation":
                             parameters_dict["tile_segmentation"]
                         })


class iota2Classification():
    def __init__(self,
                 features_stack,
                 classifier_type,
                 model,
                 tile,
                 output_directory,
                 models_class,
                 confidence=True,
                 proba_map=False,
                 classif_mask=None,
                 pixType="uint8",
                 working_directory=None,
                 stat_norm=None,
                 RAM=128,
                 auto_context={},
                 logger=LOGGER,
                 targeted_chunk=None,
                 mode="usually"):
        """
        TODO :
            remove the dependance from cfg which still needed to compute features (first, remove from generateFeatures)
            remove the 'mode' parameter
        """
        self.models_class = models_class
        self.classif_mask = classif_mask
        self.output_directory = output_directory
        self.RAM = RAM
        self.pixType = pixType
        self.stats = stat_norm
        self.classifier_model = model
        self.auto_context = auto_context
        self.tile = tile
        self.custom_features = targeted_chunk is not None
        if isinstance(model, list):
            self.model_name = self.get_model_name(os.path.split(model[0])[0])
            self.seed = self.get_model_seed(os.path.split(model[0])[0])
        else:
            self.model_name = self.get_model_name(model)
            self.seed = self.get_model_seed(model)
        self.features_stack = features_stack
        sub_name = ("" if targeted_chunk is None else
                    f"_SUBREGION_{targeted_chunk}_")
        classification_name = (f"Classif_{tile}_model_{self.model_name}"
                               f"_seed_{self.seed}{sub_name}.tif")
        confidence_name = (f"{tile}_model_{self.model_name}_"
                           f"confidence_seed_{self.seed}{sub_name}.tif")
        proba_map_name = (f"PROBAMAP_{tile}_model_"
                          f"{self.model_name}_seed_{self.seed}{sub_name}.tif")
        if mode == "SAR":
            classification_name = classification_name.replace(
                ".tif", "_SAR.tif")
            confidence_name = confidence_name.replace(".tif", "_SAR.tif")
            proba_map_name = proba_map_name.replace(".tif", "_SAR.tif")
        self.classification = os.path.join(output_directory,
                                           classification_name)
        self.confidence = os.path.join(output_directory, confidence_name)
        self.proba_map_path = self.get_proba_map(classifier_type,
                                                 output_directory, model, tile,
                                                 proba_map, proba_map_name)
        self.working_directory = working_directory

    def get_proba_map(self, classifier_type, output_directory, model, tile,
                      gen_proba, proba_map_name):
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
        proba_map_name : string
            probability raster name
        Return
        ------
        string
            absolute path to the probality map

        """
        if isinstance(model, list):
            model_name = self.get_model_name(os.path.split(model[0])[0])
            seed = self.get_model_seed(os.path.split(model[0])[0])
        else:
            model_name = self.get_model_name(model)
            seed = self.get_model_seed(model)
        proba_map = ""
        classifier_avail = ["sharkrf"]
        if classifier_type in classifier_avail:
            proba_map = os.path.join(output_directory, proba_map_name)
        if gen_proba and proba_map is "":
            warn_mes = (
                "classifier '{}' not available to generate a probability "
                "map, those available are {}").format(classifier_type,
                                                      classifier_avail)
            LOGGER.warning(warn_mes)
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
        from iota2.Common.OtbAppBank import CreateImageClassifierApplication
        from iota2.Common.OtbAppBank import CreateClassifyAutoContext
        from iota2.Common.OtbAppBank import CreateBandMathApplication
        from iota2.Common.OtbAppBank import CreateBandMathXApplication
        from iota2.Common.FileUtils import ensure_dir

        if self.working_directory:
            self.classification = os.path.join(
                self.working_directory,
                os.path.split(self.classification)[-1])
            self.confidence = os.path.join(self.working_directory,
                                           os.path.split(self.confidence)[-1])
        classifier_options = {
            "in": self.features_stack,
            "model": self.classifier_model,
            "confmap": "{}?&writegeom=false".format(self.confidence),
            "ram": str(0.4 * float(self.RAM)),
            "pixType": self.pixType,
            "out": "{}?&writegeom=false".format(self.classification)
        }
        if self.auto_context:
            tmp_dir = os.path.join(
                self.output_directory,
                "tmp_model_{}_seed_{}_tile_{}".format(self.model_name,
                                                      self.seed, self.tile))
            if self.working_directory:
                tmp_dir = os.path.join(
                    self.working_directory,
                    "tmp_model_{}_seed_{}_tile_{}".format(
                        self.model_name, self.seed, self.tile),
                )

            ensure_dir(tmp_dir)
            classifier_options = {
                "in": self.features_stack,
                "inseg": self.auto_context["tile_segmentation"],
                "models": self.classifier_model,
                "lablist":
                [str(lab) for lab in self.auto_context["labels_list"]],
                "confmap": "{}?&writegeom=false".format(self.confidence),
                "ram": str(0.4 * float(self.RAM)),
                "pixType": self.pixType,
                "tmpdir": tmp_dir,
                "out": "{}?&writegeom=false".format(self.classification)
            }
        if self.proba_map_path:
            all_class = []
            for _, dico_seed in list(self.models_class.items()):
                for _, avail_class in list(dico_seed.items()):
                    all_class += avail_class
            all_class = sorted(list(set(all_class)))
            nb_class_run = len(all_class)
            if self.working_directory:
                self.proba_map_path = os.path.join(
                    self.working_directory,
                    os.path.split(self.proba_map_path)[-1])
            classifier_options["probamap"] = "{}?&writegeom=false".format(
                self.proba_map_path)
            classifier_options["nbclasses"] = str(nb_class_run)

        if self.stats:
            classifier_options["imstat"] = self.stats
        if self.auto_context:
            classifier = CreateClassifyAutoContext(classifier_options)
        else:
            classifier = CreateImageClassifierApplication(classifier_options)

        LOGGER.info(f"Compute Classification : {self.classification}")
        LOGGER.info("RAM before classification : "
                    f"{fu.memory_usage_psutil()} MB")
        classifier.ExecuteAndWriteOutput()
        LOGGER.info("RAM after classification : "
                    f"{fu.memory_usage_psutil()} MB")
        LOGGER.info("Classification : {} done".format(self.classification))

        if self.classif_mask:
            mask_filter = CreateBandMathApplication({
                "il": [self.classification, self.classif_mask],
                "ram":
                str(self.RAM),
                "pixType":
                self.pixType,
                "out":
                self.classification,
                "exp":
                "im2b1>=1?im1b1:0"
            })
            mask_filter.ExecuteAndWriteOutput()
            mask_filter = CreateBandMathApplication({
                "il": [self.confidence, self.classif_mask],
                "ram":
                str(self.RAM),
                "pixType":
                "float",
                "out":
                self.confidence,
                "exp":
                "im2b1>=1?im1b1:0"
            })
            mask_filter.ExecuteAndWriteOutput()
            if self.proba_map_path:
                expr = "im2b1>=1?im1:{}".format("{" + ";".join(["0"] *
                                                               nb_class_run) +
                                                "}")
                mask_filter = CreateBandMathXApplication({
                    "il": [self.proba_map_path, self.classif_mask],
                    "ram":
                    str(self.RAM),
                    "pixType":
                    "uint16",
                    "out":
                    self.proba_map_path,
                    "exp":
                    expr
                })
                mask_filter.ExecuteAndWriteOutput()

        if self.proba_map_path:
            class_model = self.models_class[self.model_name][int(self.seed)]
            if len(class_model) != len(all_class):
                LOGGER.info("reordering the probability map : '{}'".format(
                    self.proba_map_path))
                self.reorder_proba_map(self.proba_map_path,
                                       self.proba_map_path, class_model,
                                       all_class)

        if self.working_directory:
            shutil.copy(
                self.classification,
                os.path.join(self.output_directory,
                             os.path.split(self.classification)[-1]))
            # os.remove(self.classification)
            shutil.copy(
                self.confidence,
                os.path.join(self.output_directory,
                             os.path.split(self.confidence)[-1]))
            # os.remove(self.confidence)
            if self.proba_map_path:
                shutil.copy(
                    self.proba_map_path,
                    os.path.join(self.output_directory,
                                 os.path.split(self.proba_map_path)[-1]))
                os.remove(self.proba_map_path)
            if self.auto_context:
                shutil.rmtree(tmp_dir)

    def reorder_proba_map(self, proba_map_path_in, proba_map_path_out,
                          class_model, all_class):
        """reorder the probability map

        in order to merge proability raster containing a different number of effective
        class it is needed to reorder them according to a reference

        Parameters
        ----------
        proba_map_path_in : string
            input probability map
        proba_map_path_out : string
            output probability map
        class_model : list
            list containing labels in the model used to classify
        all_class : list
            list containing all possible labels
        """
        from iota2.Common.OtbAppBank import CreateBandMathXApplication

        class_model_copy = [elem for elem in class_model]

        # NODATA index in probability map
        NODATA_LABEL_idx = len(all_class)
        NODATA_LABEL_buff = "NODATALABEL"
        nb_class_diff = len(class_model) - len(all_class)
        index_vector = []

        for index_label, expected_label in enumerate(all_class):
            if expected_label not in class_model:
                class_model_copy.insert(index_label, NODATA_LABEL_buff)
        for class_model_label in class_model_copy:
            if class_model_label in class_model:
                idx = class_model.index(class_model_label) + 1
            else:
                idx = NODATA_LABEL_idx
            index_vector.append(idx)
        exp = "bands(im1, {})".format("{" + ",".join(map(str, index_vector)) +
                                      "}")
        reorder_app = CreateBandMathXApplication({
            "il": proba_map_path_in,
            "ram": str(self.RAM),
            "exp": exp,
            "out": proba_map_path_out
        })
        reorder_app.ExecuteAndWriteOutput()


def get_model_dictionnary(model):
    classes = []
    with open(model) as modelfile:
        line = next(modelfile)
        if "#" in line and "with_dictionary" in line:
            classes = next(modelfile).split(" ")[1:-1]
            classes = [int(x) for x in classes]
    return classes


def get_class_by_models(iota2_samples_dir, data_field, model=None):
    """ inform which class will be used to by models

    Parameters
    ----------
    iota2_samples_dir : string
        path to the directory containing samples dedicated to learn models

    data_field : string
        field which contains labels in vector file

    Return
    ------
    dic[model][seed]

    Example
    -------
    >>> dico_models = get_class_by_models("/somewhere/learningSamples", "code")
    >>> print dico_models["1"][0]
    >>> [11, 12, 31]
    """
    from iota2.Common.FileUtils import FileSearch_AND
    from iota2.Common.FileUtils import getFieldElement

    class_models = {}
    if model is not None:
        modelpath = os.path.dirname(model)
        models_files = FileSearch_AND(modelpath, True, "model", "seed", ".txt")

        for model_file in models_files:
            model_name = os.path.splitext(
                os.path.basename(model_file))[0].split("_")[1]
            class_models[model_name] = {}
            seed_number = int(
                os.path.splitext(
                    os.path.basename(model_file))[0].split("_")[3].replace(
                        ".txt", ""))
            classes = get_model_dictionnary(model_file)
            class_models[model_name][seed_number] = classes
    else:
        samples_files = FileSearch_AND(iota2_samples_dir, True,
                                       "Samples_region_", "_seed",
                                       "_learn.sqlite")

        for samples_file in samples_files:
            model_name = os.path.splitext(
                os.path.basename(samples_file))[0].split("_")[2]
            class_models[model_name] = {}
        for samples_file in samples_files:
            model_name = os.path.splitext(
                os.path.basename(samples_file))[0].split("_")[2]
            seed_number = int(
                os.path.splitext(
                    os.path.basename(samples_file))[0].split("_")[3].replace(
                        "seed", ""))
            class_models[model_name][seed_number] = sorted(
                getFieldElement(samples_file,
                                driverName="SQLite",
                                field=data_field.lower(),
                                mode="unique",
                                elemType="int"))
    return class_models


def launchClassification(tempFolderSerie,
                         Classifmask,
                         model,
                         stats,
                         outputClassif,
                         confmap,
                         pathWd,
                         classifier_type: str,
                         tile: str,
                         proba_map_expected: bool,
                         dimred,
                         sar_optical_post_fusion,
                         output_path: str,
                         data_field: str,
                         write_features: bool,
                         reduction_mode,
                         sensors_parameters,
                         pixType,
                         MaximizeCPU=True,
                         RAM=500,
                         auto_context={},
                         force_standard_labels=None,
                         custom_features: Optional[bool] = False,
                         code_path: Optional[str] = None,
                         module_name: Optional[str] = None,
                         list_functions: Optional[str] = None,
                         number_of_chunks: Optional[int] = None,
                         targeted_chunk: Optional[int] = None,
                         logger=LOGGER):
    """
    """
    from iota2.Common import GenerateFeatures as genFeatures
    from iota2.Sampling import DimensionalityReduction as DR
    from iota2.Common.OtbAppBank import getInputParameterOutput
    from iota2.Common.OtbAppBank import CreateExtractROIApplication

    output_directory = os.path.join(output_path, "classif")

    # wMode = cfg.getParam('GlobChain', 'writeOutputs')
    featuresPath = os.path.join(output_path, "features")

    wd = pathWd
    if not pathWd:
        wd = featuresPath

    wd = os.path.join(featuresPath, tile)

    if pathWd:
        wd = os.path.join(pathWd, tile)
        if not os.path.exists(wd):
            try:
                os.mkdir(wd)
            except Exception:
                logger.warning(f"{wd} Allready exists")

    mode = "usually"
    if "SAR.tif" in outputClassif:
        mode = "SAR"

    AllFeatures, _, dep_features = genFeatures.generateFeatures(
        pathWd=wd,
        tile=tile,
        sar_optical_post_fusion=sar_optical_post_fusion,
        output_path=output_path,
        sensors_parameters=sensors_parameters,
        mode=mode,
        custom_features=custom_features,
        code_path=code_path,
        module_name=module_name,
        list_functions=list_functions,
        targeted_chunk=targeted_chunk,
        number_of_chunks=number_of_chunks,
        force_standard_labels=force_standard_labels)
    feature_raster = AllFeatures.GetParameterValue(
        getInputParameterOutput(AllFeatures))
    if write_features:
        if not os.path.exists(feature_raster):
            AllFeatures.ExecuteAndWriteOutput()
        AllFeatures = feature_raster
    else:
        AllFeatures.Execute()
    ClassifInput = AllFeatures

    if dimred:
        logger.debug(f"Classification model : {model}")
        dimRedModelList = DR.get_dim_red_models_from_classification_model(
            model)
        logger.debug("Dim red models : {}".format(dimRedModelList))
        [ClassifInput,
         other_dep] = DR.apply_dimensionality_reduction_to_feature_stack(
             reduction_mode, output_path, AllFeatures, dimRedModelList)
        if write_features:
            ClassifInput.ExecuteAndWriteOutput()
        else:
            ClassifInput.Execute()
    remove_flag = False
    if Classifmask and custom_features:
        chunked_mask = os.path.join(
            wd, f"Chunk_{targeted_chunk}_classif_mask.tif")
        roi_param = {
            "in": Classifmask,
            "out": chunked_mask,
            "mode": "fit",
            "mode.fit.im": AllFeatures,
            "ram": RAM
        }
        roi_mask = CreateExtractROIApplication(roi_param)
        roi_mask.ExecuteAndWriteOutput()
        roi_mask = None
        Classifmask = chunked_mask
        remove_flag = True
    iota2_samples_dir = os.path.join(output_path, "learningSamples")
    models_class = get_class_by_models(
        iota2_samples_dir,
        data_field,
        model=model if proba_map_expected else None)
    classif = iota2Classification(ClassifInput,
                                  classifier_type,
                                  model,
                                  tile,
                                  output_directory,
                                  models_class,
                                  proba_map=proba_map_expected,
                                  working_directory=pathWd,
                                  classif_mask=Classifmask,
                                  pixType=pixType,
                                  stat_norm=stats,
                                  RAM=RAM,
                                  mode=mode,
                                  targeted_chunk=targeted_chunk,
                                  auto_context=auto_context)
    classif.generate()
    if remove_flag:
        os.remove(chunked_mask)


if __name__ == "__main__":
    from iota2.Common.FileUtils import str2bool
    from iota2.Common import ServiceConfigFile as SCF
    PARSER = argparse.ArgumentParser(
        description=("Performs a classification of the input image "
                     "(compute in RAM) according to a model file, "))
    PARSER.add_argument(
        "-in",
        dest="tempFolderSerie",
        help="path to the folder which contains temporal series",
        default=None,
        required=True)
    PARSER.add_argument("-mask",
                        dest="Classifmask",
                        help="path to classification's mask",
                        default=None,
                        required=True)
    PARSER.add_argument("-classifier_type",
                        dest="classifier_type",
                        help="classifier name",
                        required=True)
    PARSER.add_argument("-tile",
                        dest="tile",
                        help="tile's name",
                        required=True)
    PARSER.add_argument("-proba_map_expected",
                        dest="proba_map_expected",
                        help="is probality maps were generated",
                        type=str2bool,
                        default=False,
                        required=False)
    PARSER.add_argument("-dimred",
                        dest="dimred",
                        help="flag to use dimensionality reduction",
                        type=str2bool,
                        default=False,
                        required=False)
    PARSER.add_argument("-sar_optical_post_fusion",
                        dest="sar_optical_post_fusion",
                        help=("flag to enable sar and optical "
                              "post-classification fusion"),
                        type=str2bool,
                        default=False,
                        required=False)
    PARSER.add_argument("-reduction_mode",
                        dest="reduction_mode",
                        help="reduction mode",
                        default=None,
                        required=True)
    PARSER.add_argument(
        "-data_field",
        dest="data_field",
        help="field containing labels in the groundtruth database",
        default=None,
        required=True)
    PARSER.add_argument("-pixType",
                        dest="pixType",
                        help="pixel format",
                        default=None,
                        required=True)
    PARSER.add_argument("-model",
                        dest="model",
                        help="path to the model",
                        default=None,
                        required=True)
    PARSER.add_argument("-imstat",
                        dest="stats",
                        help="path to statistics",
                        default=None,
                        required=False)
    PARSER.add_argument("-out",
                        dest="outputClassif",
                        help="output classification's path",
                        default=None,
                        required=True)
    PARSER.add_argument("-confmap",
                        dest="confmap",
                        help="output classification confidence map",
                        default=None,
                        required=True)
    PARSER.add_argument("-output_path",
                        dest="output_path",
                        help="iota2 output path",
                        required=True)
    PARSER.add_argument("-ram",
                        dest="ram",
                        help="pipeline's size",
                        default=128,
                        required=False)
    PARSER.add_argument("--wd",
                        dest="pathWd",
                        help="path to the working directory",
                        default=None,
                        required=False)
    PARSER.add_argument("-conf",
                        help="path to the configuration file (mandatory)",
                        dest="pathConf",
                        required=True)
    PARSER.add_argument("-maxCPU",
                        help="True : Class all the image and after apply mask",
                        dest="MaximizeCPU",
                        default="False",
                        choices=["True", "False"],
                        required=False)
    ARGS = PARSER.parse_args()
    CFG = SCF.serviceConfigFile(ARGS.pathConf)
    I2_PARAMS = SCF.iota2_parameters(ARGS.pathConf)
    SENSORS_PARAMETERS = I2_PARAMS.get_sensors_parameters(ARGS.tile)
    AUTO_CONTEXT_PARAMS = {}
    if CFG.getParam("chain", "enable_autoContext"):
        AUTO_CONTEXT_PARAMS = autoContext_classification_param(
            ARGS.output_path, ARGS.data_field)
    launchClassification(ARGS.tempFolderSerie, ARGS.Classifmask, ARGS.model,
                         ARGS.stats, ARGS.outputClassif, ARGS.confmap,
                         ARGS.pathWd, ARGS.classifier_type, ARGS.tile,
                         ARGS.proba_map_expected, ARGS.dimred,
                         ARGS.sar_optical_post_fusion, ARGS.output_path,
                         ARGS.data_field, ARGS.write_features,
                         ARGS.reduction_mode, SENSORS_PARAMETERS, ARGS.pixType,
                         AUTO_CONTEXT_PARAMS)
