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
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


def get_learning_samples(learning_samples_dir: str, config_path: str) -> List[str]:
    """get sorted learning samples files from samples directory
    """
    from Common import ServiceConfigFile
    from iota2.Common.FileUtils import FileSearch_AND
    from iota2.Common.FileUtils import getVectorFeatures

    first_tile = ServiceConfigFile.serviceConfigFile(config_path).getParam("chain", "listTile").split(" ")[0]
    ground_truth = ServiceConfigFile.serviceConfigFile(config_path).getParam("chain", "groundTruth")
    region_field = ServiceConfigFile.serviceConfigFile(config_path).getParam("chain", "regionField")

    parameters = []
    seed_pos = 3
    model_pos = 2
    learning_files = FileSearch_AND(learning_samples_dir,
                                    True,
                                    "Samples_region_", "_learn.sqlite")
    feat_labels = getVectorFeatures(ground_truth, region_field, learning_files[0])
    learning_files_sorted = []
    for learning_file in learning_files:
        seed = os.path.basename(learning_file).split("_")[seed_pos].replace("seed", "")
        model = os.path.basename(learning_file).split("_")[model_pos]
        learning_files_sorted.append((seed, model, learning_file))
    learning_files_sorted = sorted(learning_files_sorted, key=operator.itemgetter(0, 1))
    parameters = [{"learning_file": learning_file,
                   "seed": seed,
                   "feat_labels": feat_labels,
                   "model": model} for seed, model, learning_file in learning_files_sorted]
    return parameters


def model_name_to_function(model_name: str):
    """
    """
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.ensemble import ExtraTreesClassifier
    from sklearn.svm import SVC
    dico_clf = {"RandomForestClassifier": RandomForestClassifier,
                "ExtraTreesClassifier": ExtraTreesClassifier,
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
        True if all user cross validation parameters can be estimate
        else False
    """
    # get_params is comming from scikit-learn BaseEstimator class -> Base class for all estimators
    user_cv_parameters = list(cv_paramerters.keys())
    avail_cv_parameters = list(clf.get_params(clf).keys())
    check = [user_cv_parameter in avail_cv_parameters for user_cv_parameter in user_cv_parameters]

    return all(check)


def cast_config_cv_parameters(config_cv_parameters):
    """cast cross validation parameters coming from config to a compatible sklearn type
    """
    sklearn_cv_parameters = dict(config_cv_parameters)
    for k, v in sklearn_cv_parameters.items():
        sklearn_cv_parameters[k] = list(v)
    return sklearn_cv_parameters


def save_cross_val_best_param(output_path: str, clf) -> None:
    """save cross validation parameters in a text file
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


def force_proba(sk_classifier) -> None:
    """force the classifier model to be able of generate proabilities
    """
    from sklearn.svm import SVC
    sk_classifier_parameters = sk_classifier.get_params()
    if isinstance(sk_classifier, SVC):
        sk_classifier_parameters["probability"] = True
    sk_classifier.set_params(**sk_classifier_parameters)


def sk_learn(data_set: Dict[str, str],
             data_field: str,
             model_directory: str,
             sk_model_name: str,
             apply_Standardization: Optional[bool] = False,
             cv_parameters: Optional[Dict] = None,
             cv_grouped: Optional[bool] = False,
             cv_folds: Optional[int] = 5,
             **kwargs):
    """
    TODO : manage SAR and optical post classifications
    """
    import sqlite3
    import numpy as np
    import pandas as pd

    from iota2.VectorTools.vector_functions import getLayerName

    from sklearn.model_selection import GridSearchCV, KFold, GroupKFold
    from sklearn.preprocessing import StandardScaler

    dataset_path = data_set["learning_file"]
    dataset_model_name = data_set["model"]
    dataset_seed_num = data_set["seed"]
    features_labels = data_set["feat_labels"]

    logger.info("Features use to build model : {}".format(features_labels))
    suffix = ""
    model_path = os.path.join(model_directory,
                              "model_{}_seed_{}{}.txt".format(dataset_model_name,
                                                              dataset_seed_num,
                                                              suffix))
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
                        "with the parameters {}".format(model_name, list(cv_parameters.keys())))
            logger.error(fail_msg)
            raise ValueError(fail_msg)

    clf = clf(**kwargs)
    force_proba(clf)

    scaler = None
    if apply_Standardization:
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
                           n_jobs=-1,
                           cv=splitter,
                           return_train_score=True)

    logger.info("Fit model")
    clf.fit(features_values, labels_values)

    sk_model = clf
    if cv_parameters:
        cross_val_path = model_path.replace(".txt", "_cross_val_param.cv")
        save_cross_val_best_param(cross_val_path, clf)
        sk_model = clf.best_estimator_
    logger.info("Save model")
    model_file = open(model_path, 'wb')
    pickle.dump((sk_model, scaler), model_file)
    model_file.close()
