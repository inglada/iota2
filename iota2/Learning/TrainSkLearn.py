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

import logging
import pickle
import operator
import os
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.ensemble import BaggingClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.ensemble import VotingClassifier

from typing import List, Dict, Optional, Union
from config import Mapping

logger = logging.getLogger(__name__)

AVAIL_SKL_CLF = Union[SVC,
                      RandomForestClassifier,
                      ExtraTreesClassifier,
                      AdaBoostClassifier,
                      BaggingClassifier,
                      GradientBoostingClassifier,
                      VotingClassifier]


def get_learning_samples(learning_samples_dir: str,
                         config_path: str) -> List[Dict[str, Union[str, List[str]]]]:
    """get sorted learning samples files from samples directory

    Parameters
    ----------
    learning_samples_dir : str
        path to iota2 output directory containing learning data base
    config_path : str
        path to iota2 configuration file

    Return
    ------
    list
        ist of dictionaries
        example :
        get_learning_samples() = [{"learning_file": path to the learning file data base,
                                   "feat_labels": feature's labels,
                                   "model_path": output model path
                                  },
                                  ...
                                 ]
    """
    from Common import ServiceConfigFile
    from iota2.Common.FileUtils import FileSearch_AND
    from iota2.Common.FileUtils import getVectorFeatures

    sar_suffix = "SAR"

    ground_truth = ServiceConfigFile.serviceConfigFile(config_path).getParam("chain",
                                                                             "groundTruth")
    region_field = ServiceConfigFile.serviceConfigFile(config_path).getParam("chain",
                                                                             "regionField")
    sar_opt_post_fusion = ServiceConfigFile.serviceConfigFile(config_path).getParam("argTrain",
                                                                                    "dempster_shafer_SAR_Opt_fusion")
    iota2_outputs = ServiceConfigFile.serviceConfigFile(config_path).getParam("chain",
                                                                              "outputPath")
    iota2_models_dir = os.path.join(iota2_outputs, "model")

    parameters = []
    seed_pos = 3
    model_pos = 2
    learning_files = FileSearch_AND(learning_samples_dir,
                                    True,
                                    "Samples_region_", "_learn.sqlite")
    if sar_opt_post_fusion:
        learning_files_sar = FileSearch_AND(learning_samples_dir,
                                            True,
                                            "Samples_region_", "_learn_{}.sqlite".format(sar_suffix))
        learning_files += learning_files_sar

    learning_files_sorted = []
    output_model_files_sorted = []
    features_labels_sorted = []
    for learning_file in learning_files:
        seed = os.path.basename(learning_file).split("_")[seed_pos].replace("seed", "")
        model = os.path.basename(learning_file).split("_")[model_pos]
        learning_files_sorted.append((seed, model, learning_file))

    learning_files_sorted = sorted(learning_files_sorted, key=operator.itemgetter(0, 1))

    for _, _, learning_file in learning_files_sorted:
        seed = os.path.basename(learning_file).split("_")[seed_pos].replace("seed", "")
        model = os.path.basename(learning_file).split("_")[model_pos]
        model_name = "model_{}_seed_{}.txt".format(model, seed)
        if "{}.sqlite".format(sar_suffix) in learning_file:
            model_name = model_name.replace(".txt", "_{}.txt".format(sar_suffix))
        model_path = os.path.join(iota2_models_dir, model_name)
        output_model_files_sorted.append(model_path)
        features_labels_sorted.append(getVectorFeatures(ground_truth, region_field, learning_file))

    parameters = [{"learning_file": learning_file,
                   "feat_labels": features_labels,
                   "model_path": model_path
                   } for (seed, model, learning_file), model_path, features_labels in zip(learning_files_sorted,
                                                                                          output_model_files_sorted,
                                                                                          features_labels_sorted)]
    return parameters


def model_name_to_function(model_name: str) -> AVAIL_SKL_CLF:
    """cast the model'name from string to sklearn object

    This function must be fill-in with new scikit-learn classifier we want to
    manage in iota2

    Parameters
    ----------
    model_name : str
        scikit-learn model's name (ex: "RandomForestClassifier")

    Return
    ------
    a scikit-learn classifier object
    """
    dico_clf = {"RandomForestClassifier": RandomForestClassifier,
                "AdaBoostClassifier": AdaBoostClassifier,
                "BaggingClassifier": BaggingClassifier,
                "ExtraTreesClassifier": ExtraTreesClassifier,
                "GradientBoostingClassifier": GradientBoostingClassifier,
                "VotingClassifier": VotingClassifier,
                "SupportVectorClassification": SVC}
    if model_name not in dico_clf:
        raise ValueError("{} not suported in iota2 sklearn models : {}".format(model_name,
                                                                               ", ".join(dico_clf.keys())))
    return dico_clf[model_name]


def can_perform_cv(cv_paramerters, clf) -> bool:
    """check if the cross validation can be done

    Parameters
    ----------
    cv_paramerters : dict
        model parameters to estimate
    clf : ABCMeta
        scikit learn estimator class

    Return
    ------
    bool
        True if all user cross validation parameters can be estimate, else False
    """
    # get_params is comming from scikit-learn BaseEstimator class -> Base class for all estimators
    user_cv_parameters = list(cv_paramerters.keys())
    avail_cv_parameters = list(clf.get_params(clf).keys())
    check = [user_cv_parameter in avail_cv_parameters for user_cv_parameter in user_cv_parameters]

    return all(check)


def cast_config_cv_parameters(config_cv_parameters: Mapping) -> Dict[str, List[int]]:
    """cast cross validation parameters coming from config to a compatible sklearn type

    Parameters
    ----------
    config_cv_parameters : config.Mapping
        cross validation parameters from iota2's configuration file

    Return
    ------
    dict
        cross validation parameters as a dictionary containing lists
    """
    sklearn_cv_parameters = dict(config_cv_parameters)
    for k, v in sklearn_cv_parameters.items():
        sklearn_cv_parameters[k] = list(v)
    return sklearn_cv_parameters


def save_cross_val_best_param(output_path: str, clf: AVAIL_SKL_CLF) -> None:
    """save cross validation parameters in a text file

    Parameters
    ----------
    output_path : str
        output path
    clf : SVC / RandomForestClassifier / ExtraTreesClassifier
        classifier comming from scikit-learn
    """
    with open(output_path, "w") as cv_results:
        cv_results.write("Best Score: {}\n".format(clf.best_score_))
        cv_results.write("Best Parameters:\n")
        cv_results.write("{}\n\n".format(clf.best_params_))

        means = clf.cv_results_['mean_test_score']
        stds = clf.cv_results_['std_test_score']
        for mean, std, params in zip(means,
                                     stds,
                                     clf.cv_results_['params']):
            cv_results.write("{0} (+/- {1}) for {2}\n".format(mean,
                                                              2 * std,
                                                              params))


def force_proba(sk_classifier: AVAIL_SKL_CLF) -> None:
    """force the classifier model to be able of generate proabilities

    change the classifier parameter in place
    Parameters
    ----------
    sk_classifier : SVC / RandomForestClassifier / ExtraTreesClassifier
        classifier comming from scikit-learn
    """
    from sklearn.svm import SVC
    sk_classifier_parameters = sk_classifier.get_params()
    if isinstance(sk_classifier, SVC):
        sk_classifier_parameters["probability"] = True
    sk_classifier.set_params(**sk_classifier_parameters)


def sk_learn(dataset_path: str,
             features_labels: List[str],
             model_path: str,
             data_field: str,
             sk_model_name: str,
             apply_standardization: Optional[bool] = False,
             cv_parameters: Optional[Dict] = None,
             cv_grouped: Optional[bool] = False,
             cv_folds: Optional[int] = 5,
             available_ram: Optional[int] = None,
             **kwargs):
    """Train a model thanks to scikit-learn

    The resulting model is serialized and save thanks to pickle. The serialized
    object at 'model_path' is a tuple as (scikit-learn model, scaler)

    Parameters
    ----------
    dataset_path: str
        input data base (SQLite format)
    features_labels : list
        column's name into the data base to consider in order to learn the model
    model_path : str
        output model path
    data_field: str
        label data field
    sk_model_name: str
        scikit-learn classifier's name
        availabale ones are "SVC", "RandomForestClassifier" or "ExtraTreesClassifier"
    apply_standardization: bool
        flag to apply feature standardization
    cv_parameters: dict
        cross validation dictionary
    cv_grouped: bool
        if true, each cross validation folds are constitute of samples inside polygons.
    cv_folds: int
        number of cross validation folds
    available_ram : int
        available ram in Mb
    kwargs : dict
        scikit-learn models parameters
    """
    import math
    import sqlite3
    import numpy as np
    import pandas as pd

    from iota2.Common.FileUtils import memory_usage_psutil
    from iota2.VectorTools.vector_functions import getLayerName

    from sklearn.model_selection import GridSearchCV, KFold, GroupKFold
    from sklearn.preprocessing import StandardScaler

    logger.info("Features use to build model : {}".format(features_labels))
    layer_name = getLayerName(dataset_path, "SQLite")
    conn = sqlite3.connect(dataset_path)
    df_features = pd.read_sql_query("select {} from {}".format(",".join(features_labels),
                                                               layer_name),
                                    conn)
    features_values = df_features.to_numpy()

    df_labels = pd.read_sql_query("select {} from {}".format(data_field,
                                                             layer_name),
                                  conn)
    labels_values = np.ravel(df_labels.to_numpy())

    clf = model_name_to_function(sk_model_name)

    if cv_parameters:
        if not can_perform_cv(cv_parameters, clf):
            fail_msg = ("ERROR : impossible to cross validate the model `{}` "
                        "with the parameters {}".format(sk_model_name,
                                                        list(cv_parameters.keys())))
            logger.error(fail_msg)
            raise ValueError(fail_msg)

    clf = clf(**kwargs)
    force_proba(clf)

    scaler = None
    if apply_standardization:
        logger.info("Apply standardization")
        scaler = StandardScaler()
        scaler.fit(features_values)  # TODO: if regression, we have to scale also labels_values
        if .0 in scaler.var_:
            logger.warning(("features std with 0 values was found, "
                            "automatically replaced by 1 by scikit-learn"))
        features_values = scaler.transform(features_values)

    if cv_parameters:
        logger.info("Cross validation in progress")
        if cv_grouped:
            df_groups = pd.read_sql_query("select {} from {}".format("originfid",
                                                                     layer_name),
                                          conn)
            groups = np.ravel(df_groups.to_numpy())

            splitter = list(GroupKFold(n_splits=cv_folds).split(features_values,
                                                                labels_values,
                                                                groups))
        else:
            splitter = KFold(n_splits=cv_folds)

        clf = GridSearchCV(clf,
                           cv_parameters,
                           cv=splitter,
                           return_train_score=True)
    jobs = 1
    if available_ram:
        current_ram = memory_usage_psutil()
        jobs = int(math.floor(available_ram / current_ram))
        jobs = jobs if jobs >= 1 else 1
        if hasattr(clf, "n_jobs"):
            clf.n_jobs = jobs
        if hasattr(clf, "pre_dispatch"):
            clf.pre_dispatch = jobs

    logger.info("Fit model using {} jobs".format(jobs))
    clf.fit(features_values, labels_values)

    sk_model = clf
    if cv_parameters:
        file_name, file_ext = os.path.splitext(os.path.basename(model_path))
        cross_val_path = model_path.replace(file_ext, "_cross_val_param.cv")
        save_cross_val_best_param(cross_val_path, clf)
        sk_model = clf.best_estimator_

    logger.info("Save model")
    model_file = open(model_path, 'wb')
    pickle.dump((sk_model, scaler), model_file)
    model_file.close()
