#!/usr/bin/env python3
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

import os
import argparse
from typing import List, Union, Tuple
from osgeo import gdal
from osgeo import ogr
from osgeo import osr
from osgeo.gdalconst import *
import numpy as np
from iota2.Common import FileUtils as fu


def compute_kappa(confusion_matrix: np.ndarray) -> float:
    """compute kappa coefficients

    Parameters
    ----------
    confusion_matrix : np.array of np.array
        numpy array representing confusion matrix
    """

    nbr_good = confusion_matrix.trace()
    nbr_sample = confusion_matrix.sum()

    if nbr_sample == 0.0:
        overall_accuracy = -1
    else:
        overall_accuracy = float(nbr_good) / float(nbr_sample)

    ## the lucky rate.
    lucky_rate = 0.
    for i in range(confusion_matrix.shape[0]):
        sum_ij = 0.
        sum_ji = 0.
        for j in range(confusion_matrix.shape[0]):
            sum_ij += confusion_matrix[i][j]
            sum_ji += confusion_matrix[j][i]
        lucky_rate += sum_ij * sum_ji

    # Kappa.
    if float((nbr_sample * nbr_sample) - lucky_rate) != 0:
        kappa = float((overall_accuracy * nbr_sample * nbr_sample) -
                      lucky_rate) / float((nbr_sample * nbr_sample) -
                                          lucky_rate)
    else:
        kappa = 1000

    return kappa


def compute_precision_by_class(confusion_matrix: np.ndarray,
                               all_class: List[int]
                               ) -> List[Tuple[int, float]]:
    """compute precision by class
   
    Parameters
    ----------
    confusion_matrix : np.array of np.array
        numpy array representing confusion matrix
    all_class : list
        list of class' label
    Return
    ------
    list
        list of tuple as (label, precision)
    """
    precision = []  #[(class,precision),(...),()...()]

    for i in range(len(all_class)):
        denom = 0
        for j in range(len(all_class)):
            denom += confusion_matrix[j][i]
            if i == j:
                nom = confusion_matrix[j][i]
        current_pre = float(nom) / float(denom) if denom != 0 else 0.
        precision.append((all_class[i], current_pre))
    return precision


def compute_recall_by_class(confusion_matrix: np.ndarray,
                            all_class: List[int]) -> List[Tuple[int, float]]:
    """compute recall by class

    Parameters
    ----------
    confusion_matrix : np.array of np.array
        numpy array representing confusion matrix
    all_class : list
        list of class' label
    Return
    ------
    list
        list of tuple as (label, recall)
    """
    recall = []  #[(class,rec),(...),()...()]
    for i in range(len(all_class)):
        denom = 0
        for j in range(len(all_class)):
            denom += confusion_matrix[i][j]
            if i == j:
                nom = confusion_matrix[i][j]
        current_recall = float(nom) / float(denom) if denom != 0 else 0.
        recall.append((all_class[i], current_recall))
    return recall


def compute_fscore_by_class(precision: List[Tuple[int, float]],
                            recall: List[Tuple[int, float]],
                            all_class: List[int]) -> List[Tuple[int, float]]:
    """compute fscore for each class from precisions and recalls"""
    f_score = []
    for i in range(len(all_class)):
        if float(recall[i][1] + precision[i][1]) != 0:
            f_score.append(
                (all_class[i], float(2 * recall[i][1] * precision[i][1]) /
                 float(recall[i][1] + precision[i][1])))
        else:
            f_score.append((all_class[i], 0.0))
    return f_score


def write_csv(confusion_matrix: np.ndarray, all_class: List[int],
              path_out: str):
    """write CSV"""
    all_c = ""
    for i in range(len(all_class)):
        if i < len(all_class) - 1:
            all_c = all_c + str(all_class[i]) + ","
        else:
            all_c += str(all_class[i])
    csv_file = open(path_out, "w")
    csv_file.write("#Reference labels (rows):" + all_c + "\n")
    csv_file.write("#Produced labels (columns):" + all_c + "\n")
    for item in confusion_matrix:
        for j in range(len(item)):
            if j < len(item) - 1:
                csv_file.write(str(item[j]) + ",")
            else:
                csv_file.write(str(item[j]) + "\n")
    csv_file.close()


def write_results(f_score: List[float], recall: List[float],
                  precision: List[float], kappa: float,
                  overall_accuracy: float, all_class: List[int],
                  path_out: str) -> None:
    """write report in a text file as otb confusion matrix output

    Parameters
    ----------
    f_score: list
        list of F-score by class
    recall: list
        list of recall by class
    precision: list
        list of precision by class
    kappa: float
        kappa value
    overall_accuracy: float
        overall accuracy value
    all_class: list
        list of all class
    path_out: str
        output file to store report
    """
    res_file = open(path_out, "w")
    res_file.write("#Reference labels (rows):")
    for i in range(len(all_class)):
        if i < len(all_class) - 1:
            res_file.write(str(all_class[i]) + ",")
        else:
            res_file.write(str(all_class[i]) + "\n")
    res_file.write("#Produced labels (columns):")
    for i in range(len(all_class)):
        if i < len(all_class) - 1:
            res_file.write(str(all_class[i]) + ",")
        else:
            res_file.write(str(all_class[i]) + "\n\n")

    for i in range(len(all_class)):
        res_file.write("Precision of class [" + str(all_class[i]) +
                       "] vs all: " + str(precision[i][1]) + "\n")
        res_file.write("Recall of class [" + str(all_class[i]) + "] vs all: " +
                       str(recall[i][1]) + "\n")
        res_file.write("F-score of class [" + str(all_class[i]) +
                       "] vs all: " + str(f_score[i][1]) + "\n\n")

    res_file.write("Precision of the different classes: [")
    for i in range(len(all_class)):
        if i < len(all_class) - 1:
            res_file.write(str(precision[i][1]) + ",")
        else:
            res_file.write(str(precision[i][1]) + "]\n")
    res_file.write("Recall of the different classes: [")
    for i in range(len(all_class)):
        if i < len(all_class) - 1:
            res_file.write(str(recall[i][1]) + ",")
        else:
            res_file.write(str(recall[i][1]) + "]\n")
    res_file.write("F-score of the different classes: [")
    for i in range(len(all_class)):
        if i < len(all_class) - 1:
            res_file.write(str(f_score[i][1]) + ",")
        else:
            res_file.write(str(f_score[i][1]) + "]\n\n")
    res_file.write("Kappa index: " + str(kappa) + "\n")
    res_file.write("Overall accuracy index: " + str(overall_accuracy))

    res_file.close()


def replace_annual_crop_in_conf_mat(confusion_matrix: np.ndarray,
                                    all_class: List[Union[int, str]],
                                    annual_crop: List[Union[int, str]],
                                    label_replacement: int):
    """
        IN :
            confusion_matrix [np.array of np.array] : confusion matrix
            all_class [list of integer] : ordinates integer class label
            annual_crop : [list of string] : list of class number (string)
            label_replacement : [string] : label replacement
        OUT :
            outMatrix [np.array of np.array] : new confusion matrix
            all_classAC [list of integer] : new ordinates integer class label
        Exemple :

            all_class = [1,2,3,4]
            confusion_matrix = [[1 2 3 4] [5 6 7 8] [9 10 11 12] [13 14 15 16]]

            confusion_matrix.csv
            #ref label rows : 1,2,3,4
            #prod label col : 1,2,3,4
            1,2,3,4
            5,6,7,8
            9,10,11,12
            13,14,15,16

            annual_crop = ['1','2']
            label_replacement = '0'

            outMatrix,outall_class = replace_annual_crop_in_conf_mat(confusion_matrix,all_class,annual_crop,label_replacement)

            outall_class = [0,3,4]
            confusion_matrix = [[14 10 12] [19 11 12] [27 15 16]]
    """
    all_index = []
    out_matrix = []

    for current_class in annual_crop:
        try:
            ind = all_class.index(int(current_class))
            all_index.append(ind)
        except ValueError:
            raise Exception("Class : " + current_class + " doesn't exists")

    all_class_ac = all_class[:]
    for label_annual_crop in annual_crop:
        all_class_ac.remove(int(label_annual_crop))
    all_class_ac.append(int(label_replacement))
    all_class_ac.sort()
    index_ac = all_class_ac.index(int(label_replacement))

    #replace ref labels in confusion matrix
    matrix = []
    for y in range(len(all_class)):
        if y not in all_index:
            matrix.append(confusion_matrix[y])
    tmp_y = [0] * len(all_class)
    for y in all_index:
        tmp_y = tmp_y + confusion_matrix[y, :]
    matrix.insert(index_ac, tmp_y)

    #replace produced labels in confusion matrix
    for item in matrix:
        tmp_x = []
        buff = 0
        for x in range(len(matrix[0])):
            if x not in all_index:
                tmp_x.append(item[x])
            else:
                buff += item[x]
        tmp_x.insert(index_ac, buff)
        out_matrix.append(tmp_x)
    return np.asarray(out_matrix), all_class_ac


def confusion_models_merge_parameters(iota2_dir: str):
    """
    function use to feed confusion_models_merge function

    Parameter
    ---------
    iota2_dir : string
        path to the iota2 running directory
    Return
    ------
    list
        list containing all sub confusion matrix which must be merged.
    """
    ds_sar_opt_conf_dir = os.path.join(iota2_dir, "dataAppVal", "bymodels")
    csv_seed_pos = 4
    csv_model_pos = 2
    all_csv = fu.FileSearch_AND(ds_sar_opt_conf_dir, True, "samples", ".csv")
    # group by models
    model_group = []
    for csv in all_csv:
        _, csv_name = os.path.split(csv)
        csv_seed = csv_name.split("_")[csv_seed_pos]
        csv_model = csv_name.split("_")[csv_model_pos]
        # csv_mode = "SAR.csv" or "val.csv", use to descriminate models
        csv_mode = csv_name.split("_")[-1]

        key_param = (csv_model, csv_seed, csv_mode)

        model_group.append((key_param, csv))
    return [param for key, param in fu.sortByFirstElem(model_group)]


def merge_confusions(csv_in, labels, csv_out):
    """
    from a list of confusion matrix, generate an unique one

    Parameters
    ----------
    csv_in : list
        paths to csv confusion matrix
    labels : list
        all possible labels
    csv_out : string
        output path
    """
    csv = fu.confCoordinatesCSV(csv_in)
    csv_f = fu.sortByFirstElem(csv)
    conf_mat = fu.gen_confusionMatrix(csv_f, labels)
    write_csv(conf_mat, labels, csv_out)


def confusion_models_merge(csv_list):
    """
    """
    from iota2.Validation.ResultsUtils import parse_csv

    csv_path, csv_name = os.path.split(csv_list[0])
    csv_seed_pos = 4
    csv_model_pos = 2
    csv_seed = csv_name.split("_")[csv_seed_pos]
    csv_model = csv_name.split("_")[csv_model_pos]
    csv_suffix = ""
    if "SAR" in csv_name:
        csv_suffix = "_SAR"
    output_merged_csv_name = "model_{}_seed_{}{}.csv".format(
        csv_model, csv_seed, csv_suffix)
    output_merged_csv = os.path.join(csv_path, output_merged_csv_name)
    labels = []
    for csv in csv_list:
        conf_mat_dic = parse_csv(csv)
        labels_ref = list(conf_mat_dic.keys())
        labels_prod = [
            lab
            for lab in list(conf_mat_dic[list(conf_mat_dic.keys())[0]].keys())
        ]
        all_labels = labels_ref + labels_prod
        labels += all_labels

    labels = sorted(list(set(labels)))
    merge_confusions(csv_list, labels, output_merged_csv)


def confusion_fusion(input_vector: str, data_field: str, csv_out: str,
                     txt_out: str, csv_path: str, runs: int, crop_mix: bool,
                     annual_crop: List[str],
                     annual_crop_label_replacement: int) -> None:
    """merge otb tile confusion matrix

    Parameters
    ----------
    input_vector: str
        input database
    data_field: str
        data field
    csv_out: str
        output csv file which will contains the merge of matrix
    txt_out: str
        diretory which will contains the resulting file of merged matrix
    csv_path: str
        path to the directory which contains all *.csv files to merge
    runs: int
        number of random learning/validation samples-set
    crop_mix: bool
        inform if cropMix workflow is enable
    annual_crop: list
        list of annual labels
    annual_crop_label_replacement: int
        replace annual labels by annual_crop_label_replacement
    """

    for seed in range(runs):
        #Recherche de toute les classes possible
        all_class = []
        all_class = fu.getFieldElement(input_vector, "ESRI Shapefile",
                                       data_field, "unique")
        all_class = sorted(all_class)

        #Initialisation de la matrice finale
        all_conf = fu.FileSearch_AND(csv_path, True,
                                     "seed_" + str(seed) + ".csv")
        csv = fu.confCoordinatesCSV(all_conf)
        csv_f = fu.sortByFirstElem(csv)

        conf_mat = fu.gen_confusionMatrix(csv_f, all_class)
        if crop_mix:
            write_csv(
                conf_mat, all_class,
                csv_out + "/MatrixBeforeClassMerge_" + str(seed) + ".csv")
            conf_mat, all_class = replace_annual_crop_in_conf_mat(
                conf_mat, all_class, annual_crop,
                annual_crop_label_replacement)
        write_csv(conf_mat, all_class,
                  csv_out + "/Classif_Seed_" + str(seed) + ".csv")
        nbr_good = conf_mat.trace()
        nbr_sample = conf_mat.sum()

        overall_acc = float(nbr_good) / float(nbr_sample) if nbr_sample > 1 else 0.0
        kappa = compute_kappa(conf_mat)
        precision = compute_precision_by_class(conf_mat, all_class)
        recall = compute_recall_by_class(conf_mat, all_class)
        f_score = compute_fscore_by_class(precision, recall, all_class)

        write_results(
            f_score, recall, precision, kappa, overall_acc, all_class,
            txt_out + "/ClassificationResults_seed_" + str(seed) + ".txt")


if __name__ == "__main__":
    from iota2.Common.FileUtils import str2bool
    PARSER = argparse.ArgumentParser(
        description=
        "This function merge confusionMatrix.csv from different tiles")
    PARSER.add_argument("-input_vector",
                        help="path to the entire ground truth",
                        dest="input_vector",
                        required=True)
    PARSER.add_argument("-data_field",
                        help="data's field inside the ground truth shape",
                        dest="data_field",
                        required=True)
    PARSER.add_argument("-csv_out",
                        help="output csv file",
                        dest="csv_out",
                        required=True)
    PARSER.add_argument("-txt_out",
                        help="output txt file",
                        dest="txt_out",
                        required=True)
    PARSER.add_argument("-csv_path",
                        help="directory containing all csv files",
                        dest="csv_path",
                        required=True)
    PARSER.add_argument(
        "-runs",
        help="number of random learning/validation samples-set",
        dest="runs",
        type=int,
        required=True)
    PARSER.add_argument("-crop_mix",
                        help="is crop mix workflow was enable ?",
                        dest="crop_mix",
                        type=str2bool,
                        default=False,
                        required=False)
    PARSER.add_argument("-annual_crop",
                        help="list of annual labels",
                        dest="annual_crop",
                        nargs='+',
                        required=True)
    PARSER.add_argument("-annual_crop_label_replacement",
                        help="new label for annual labels",
                        dest="annual_crop_label_replacement",
                        type=int,
                        default=1,
                        required=False)
    ARGS = PARSER.parse_args()

    confusion_fusion(ARGS.input_vector, ARGS.data_field, ARGS.csv_out,
                     ARGS.txt_out, ARGS.csv_path, ARGS.runs, ARGS.crop_mix,
                     ARGS.annual_crop, ARGS.annual_crop_label_replacement)
