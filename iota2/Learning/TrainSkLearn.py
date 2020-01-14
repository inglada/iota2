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
import os
import pickle
import operator
from typing import List, Dict


def get_learning_samples(learning_samples_dir: str, config_path: str) -> List[str]:
    """get sorted learning samples files from samples directory
    """
    from Common import ServiceConfigFile
    from iota2.Common.FileUtils import FileSearch_AND
    from iota2.Common.GenerateFeatures import generateFeatures

    first_tile = ServiceConfigFile.serviceConfigFile(config_path).getParam("chain", "listTile").split(" ")[0]
    _, feat_labels, _ = generateFeatures(None, first_tile, ServiceConfigFile.serviceConfigFile(config_path))
    
    parameters = []
    seed_pos = 3
    model_pos = 2
    learning_files = FileSearch_AND(learning_samples_dir,
                                    True,
                                    "Samples_region_", "_learn.sqlite")
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
    dico_param = {"SupportVectorClassification": {'kernel': ['rbf'],
                                                  'gamma': [0.0625, 0.125,
                                                            0.25, 0.5, 1,
                                                            2, 4, 8, 16],
                                                  'C': [1, 10, 100, 1000]},
                  "RandomForestClassifier": {'n_estimators': [50, 100, 200,
                                                            400, 600]},
                  "ExtraTreesClassifier": {'n_estimators': [50, 100, 200,
                                                          400, 600]}}

    if model_name not in dico_clf:
        raise ValueError("{} not suported in iota2 sklearn models : {}".format(model_name,
                                                                               ", ".join(dico_clf.keys())))
    return dico_clf[model_name], dico_param[model_name]


def sk_learn(data_set: Dict[str, str],
             data_field: str,
             model_directory: str,
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
    
    model_name = kwargs["model_type"]
    del kwargs["model_type"] ## ??
    dataset_path = data_set["learning_file"]
    dataset_model_name = data_set["model"]
    dataset_seed_num = data_set["seed"]
    features_labels = data_set["feat_labels"]
    suffix = ""
    model_path = os.path.join(model_directory,
                              "model_{}_seed_{}{}.txt".format(dataset_model_name,
                                                              dataset_seed_num,
                                                              suffix))

    layer_name = getLayerName(dataset_path, "SQLite")
    conn = sqlite3.connect(dataset_path)
    df_features = pd.read_sql_query("select {} from {}".format(",".join(features_labels), layer_name),
                                    conn)
    features_values = df_features.to_numpy()

    df_labels = pd.read_sql_query("select {} from {}".format(data_field, layer_name),
                                  conn)
    labels_values = np.ravel(df_labels.to_numpy())

    clf, parameters = model_name_to_function(model_name, **kwargs)

    # Options
    grouped = True
    n_splits = 5

    # Standardization
    scaler = StandardScaler()
    scaler.fit(features_values)  # TODO: if regression, we have to scale also labels_values
    features_values_scaled = scaler.transform(features_values)

    # Cross validation
    if grouped:
        df_groups = pd.read_sql_query("select {} from {}".format("originfid",
                                                                 layer_name),
                                      conn)
        groups = np.ravel(df_groups.to_numpy())
        
        splitter = list(GroupKFold(n_splits=n_splits).split(features_values_scaled,
                                                            labels_values,
                                                            groups))

        model_cv = GridSearchCV(clf(),
                                parameters,
                                n_jobs=-1,
                                cv=splitter,
                                return_train_score=True)
    else:
        splitter = KFold(n_splits=n_splits)
        model_cv = GridSearchCV(clf(),
                                parameters,
                                n_jobs=-1,
                                cv=splitter,
                                return_train_score=True)

    model_cv.fit(features_values_scaled, labels_values)

    # Save CV output
    with open("cv_results.txt", "w") as cv_results:
        cv_results.write("Best Score: {}\n".format(model_cv.best_score_))
        cv_results.write("Best Parameters:\n")
        cv_results.write("{}\n\n".format(model_cv.best_params_))

        means = model_cv.cv_results_['mean_test_score']
        stds = model_cv.cv_results_['std_test_score']
        for mean, std, params in zip(means,
                                     stds,
                                     model_cv.cv_results_['params']):
            cv_results.write("{0} (+/- {1}) for {2}\n".format(mean,
                                                           2*std,
                                                           params))

    # Save model
    model_file = open(model_path, 'wb')
    pickle.dump((model_cv.best_estimator_, scaler), model_file)
    model_file.close()

