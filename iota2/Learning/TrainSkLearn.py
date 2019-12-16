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


def get_learning_samples(learning_samples_dir: str) -> List[str]:
    """get sorted learning samples files from samples directory
    """
    from iota2.Common.FileUtils import FileSearch_AND
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
             features_labels: List[str],
             model_directory: str,
             **kwargs):
    """
    TODO : manage SAR and optical post classifications
    """
    import sqlite3
    import numpy as np
    import pandas as pd

    from iota2.VectorTools.vector_functions import getLayerName

    from sklearn.model_selection import GridSearchCV
    
    model_name = kwargs["model_type"]
    del kwargs["model_type"]
    dataset_path = data_set["learning_file"]
    dataset_model_name = data_set["model"]
    dataset_seed_num = data_set["seed"]

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

    # Cross validation
    model_cv = GridSearchCV(clf(),
                            parameters,
                            n_jobs=-1,
                            cv=5)
    model_cv.fit(features_values, labels_values)

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
    pickle.dump(model_cv.best_estimator_, model_file)
    model_file.close()
