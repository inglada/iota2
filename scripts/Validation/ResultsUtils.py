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

def remove_undecidedlabel(conf_mat_dic, undecidedlabel):
    """
    usage : use to remove samples with the undecidedlabel label from the
            confusion matrix
    """
    #remove prod labels
    for class_ref, prod_dict in conf_mat_dic.items():
        prod_dict.pop(undecidedlabel, None)

    #remove ref labels
    conf_mat_dic.pop(undecidedlabel, None)

    return conf_mat_dic


def parse_csv(csv_in):
    """
    usage : use to parse OTB's confusion matrix
    IN
    csv_in [string] path to a csv file

    OUT
    matrix [collections.OrderedDict of collections.OrderedDict]

    example :
    if csv_in contain :
    #Reference labels (rows):11,12,31,32,34,36,41,42,43,44,45,51,211,221,222
    #Produced labels (columns):11,12,31,32,34,36,41,42,43,44,45,51,211,221,222,255
    11100,586,13,2,54,0,0,25,2,0,0,2,291,47,4,338
    434,14385,12,0,171,1,0,31,43,0,0,3,475,52,10,484
    98,8,3117,109,160,0,0,3,0,0,0,9,33,105,66,494
    4,0,38,571,5,0,0,3,0,0,0,1,13,9,0,47
    53,310,72,52,9062,0,1,431,27,0,0,0,459,56,16,1065
    37,40,4,0,4,0,0,6,1,0,0,0,49,11,1,59
    1,1,0,0,13,0,56,146,24,0,0,0,0,0,0,31
    41,158,6,4,200,0,42,4109,249,1,0,11,390,46,11,642
    50,76,1,3,20,0,17,478,957,3,0,12,58,7,3,315
    1,5,0,0,0,0,0,22,102,12,0,0,0,0,0,20
    0,0,0,0,83,0,0,12,0,0,41,0,3,0,0,109
    95,66,3,4,0,1,0,3,12,0,0,6599,3,9,0,50
    171,425,30,9,348,0,0,9,0,0,0,0,17829,67,3,585
    180,166,111,4,93,0,0,61,5,0,0,5,668,1213,14,451
    159,143,1,0,180,0,0,33,0,0,0,0,149,22,304,258

    print matrix[11][221]
    > 4
    print matrix[11][222]
    > 338
    print matrix[255]
    > OrderedDict([(11, 0), (12, 0),..., (255, 0)])
    """
    import collections
    import csv

    with open(csv_in, 'rb') as csvfile:
        csv_reader = csv.reader(csvfile)
        ref_lab = [elem.replace("#Reference labels (rows):", "") for elem in csv_reader.next()]
        prod_lab = [elem.replace("#Produced labels (columns):", "") for elem in csv_reader.next()]

        all_labels = sorted(map(int, list(set(ref_lab + prod_lab))))

        #construct confusion matrix structure and init it at 0
        matrix = collections.OrderedDict()
        for lab in all_labels:
            matrix[lab] = collections.OrderedDict()
            for l in all_labels:
                matrix[lab][l] = 0

        #fill-up confusion matrix
        csv_dict = csv.DictReader(csvfile, fieldnames=prod_lab)
        for row_num, row_ref in enumerate(csv_dict):
            for klass, value in row_ref.items():
                ref = int(ref_lab[row_num])
                prod = int(klass)
                matrix[ref][prod] += float(value)

    return matrix

def get_coeff(matrix):
    """
    """
    import collections

    nan = -1000
    classes_labels = matrix.keys()

    OA_nom = sum([matrix[class_name][class_name] for class_name in matrix.keys()])
    nb_samples = sum([matrix[ref_class_name][prod_class_name] for ref_class_name in matrix.keys() for prod_class_name in matrix.keys()])


    if nb_samples != 0.0:
        OA = float(OA_nom)/float(nb_samples)
    else:
        OA = nan

    P_dic = collections.OrderedDict()
    R_dic = collections.OrderedDict()
    F_dic = collections.OrderedDict()
    luckyRate = 0.
    for classe_name in classes_labels:
        OA_class = matrix[classe_name][classe_name]
        P_denom = sum([matrix[ref][classe_name] for ref in classes_labels])
        R_denom = sum([matrix[classe_name][ref] for ref in classes_labels])
        if float(P_denom) != 0.0:
            P = float(OA_class) / float(P_denom)
        else:
            P = nan
        if float(R_denom) != 0.0:
            R = float(OA_class) / float(R_denom)
        else:
            R = nan
        if float(P + R) != 0.0:
            F = float(2.0 * P * R) / float(P + R)
        else:
            F = nan
        P_dic[classe_name] = P
        R_dic[classe_name] = R
        F_dic[classe_name] = F

        luckyRate += P_denom * R_denom

    K_denom = float((nb_samples * nb_samples) - luckyRate)
    K_nom = float((OA * nb_samples * nb_samples) - luckyRate)
    if K_denom != 0.0:
        K = K_nom / K_denom
    else:
        K = nan

    return K, OA, P_dic, R_dic, F_dic

def get_nomenclature(nom_path):
    """
    usage parse nomenclature file and return a python dictionary
    """
    import csv

    nom_dict = {}
    with open(nom_path, 'rb') as csvfile:
        csv = csv.reader(csvfile, delimiter=':')
        for class_name, label in csv:
            nom_dict[int(label)] = class_name
    return nom_dict


def get_RGB_mat(norm_conf, diag_cmap, not_diag_cmap):
    """
    usage convert normalise confusion matrix to a RGB image
    """
    RGB_list = []
    for row_num, row in enumerate(norm_conf):
        RGB_list_row = []
        for col_num, col in enumerate(row):
            if col_num == row_num:
                RGB_list_row.append(diag_cmap(col))
            else:
                RGB_list_row.append(not_diag_cmap(col))
        RGB_list.append(RGB_list_row)
    return RGB_list


def get_RGB_pre(pre_val, coeff_cmap):
    """
    """
    RGB_list = []
    for raw in pre_val:
        raw_rgb = []
        for val in raw:
            raw_rgb.append(coeff_cmap(val))
        RGB_list.append(raw_rgb)
    return RGB_list


def get_RGB_rec(coeff, coeff_cmap):
    """
    usage convert normalise confusion matrix to a RGB image
    """
    RGB_list = []

    for raw in coeff:
        raw_rgb = []
        for val in raw:
            if val != 0.:
                raw_rgb.append(coeff_cmap(val))
            else:
                raw_rgb.append((0, 0, 0, 0))
        RGB_list.append(raw_rgb)

    return RGB_list


def fig_conf_mat(conf_mat_dic, nom_dict, K, OA, P_dic, R_dic, F_dic,
                 out_png, dpi=900, write_conf_score=True, grid_conf=False):
    """
    usage : generate a figure representing the confusion matrix
    """
    import os
    import numpy as np
    import matplotlib
    matplotlib.get_backend()
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    from matplotlib.axes import Subplot

    nan = 0

    labels_ref = [nom_dict[lab] for lab in conf_mat_dic.keys()]
    labels_prod = [nom_dict[lab] for lab in conf_mat_dic[conf_mat_dic.keys()[0]].keys()]

    #convert conf_mat_dic to a list of lists
    conf_mat_array = np.array([[v for k, v in prod_dict.items()] for ref, prod_dict in conf_mat_dic.items()])

    color_map_coeff = plt.cm.RdYlGn
    diag_cmap = plt.cm.RdYlGn
    not_diag_cmap = plt.cm.Reds

    #normalize by ref samples
    norm_conf = []
    for i in conf_mat_array:
        a = 0
        tmp_arr = []
        a = sum(i, 0)
        for j in i:
            if float(a) != 0:
                tmp_arr.append(float(j) / float(a))
            else:
                tmp_arr.append(nan)
        norm_conf.append(tmp_arr)
    norm_conf = np.array(norm_conf)

    RGB_matrix = get_RGB_mat(norm_conf, diag_cmap, not_diag_cmap)

    fig = plt.figure(figsize=(10, 10))

    gs = gridspec.GridSpec(3, 3, width_ratios=[1, 1.0 / len(labels_ref), 1.0 / len(labels_ref)],
                           height_ratios=[1, 1.0 / len(labels_prod), 1.0 / len(labels_prod)])

    gs.update(wspace=0.1, hspace=0.1)

    plt.clf()
    ax = fig.add_subplot(gs[0])
    ax.set_aspect(1)
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position('top')
    #confusion's matrix grid
    if grid_conf:
        ax.set_xticks(np.arange(-.5, len(labels_prod), 1), minor=True)
        ax.set_yticks(np.arange(-.5, len(labels_ref), 1), minor=True)
        ax.grid(which='minor', color='gray', linestyle='-', linewidth=1, alpha=0.5)

    maxtrix = norm_conf

    res = ax.imshow(RGB_matrix,
                    interpolation='nearest', alpha=0.8, aspect='auto')

    width, height = maxtrix.shape
    if write_conf_score:
        for x in xrange(width):
            for y in xrange(height):
                ax.annotate(str(conf_mat_array[x][y]), xy=(y, x),
                            horizontalalignment='center',
                            verticalalignment='center',
                            fontsize='xx-small',
                            rotation=45)

    plt.xticks(range(width), labels_prod, rotation=90)
    plt.yticks(range(height), labels_ref)

    #recall
    ax2 = fig.add_subplot(gs[1])
    rec_val = np.array([[0, r_val] for class_name, r_val in R_dic.items()])

    rec_val_rgb = get_RGB_rec(rec_val, color_map_coeff)
    R = ax2.imshow(rec_val_rgb,
                   interpolation='nearest', alpha=0.8, aspect='auto')

    ax2.set_xlim(0.5, 1.5)
    ax2.set_title('Rappel', rotation=90, verticalalignment='bottom')
    ax2.get_yaxis().set_visible(False)
    ax2.get_xaxis().set_visible(False)


    for y in xrange(len(labels_ref)):
        ax2.annotate("{:.3f}".format(rec_val[y][1]), xy=(1, y),
                     horizontalalignment='center',
                     verticalalignment='center',
                     fontsize='xx-small')

    #Precision
    pre_val = []
    ax3 = fig.add_subplot(gs[3])
    pre_val_tmp = [p_val for class_name, p_val in P_dic.items()]
    pre_val.append(pre_val_tmp)
    pre_val.append(pre_val_tmp)
    pre_val = np.array(pre_val)

    pre_val_rgb = get_RGB_pre(pre_val, color_map_coeff)
    P = ax3.imshow(pre_val_rgb,
                   interpolation='none', alpha=0.8, aspect='auto')
    ax3.set_ylim(0.5, 1.5)
    ax3.get_yaxis().set_visible(False)

    for x in xrange(len(labels_prod)):
        ax3.annotate("{:.3f}".format(pre_val[0][x]), xy=(x, 1),
                     horizontalalignment='center',
                     verticalalignment='center',
                     fontsize='xx-small')
    ax3.set_xlabel("Precision")
    ax3.set_xticklabels([])

    #F-score
    ax4 = fig.add_subplot(gs[2])
    fs_val = np.array([[0, r_val] for class_name, r_val in F_dic.items()])
    fs_val_rgb = get_RGB_rec(fs_val, color_map_coeff)
    F = ax4.imshow(fs_val_rgb,
                   interpolation='none', alpha=0.8, aspect='auto')
    ax4.set_xlim(0.5, 1.5)
    #~ ax4.title.set_text('F-Score')
    ax4.set_title('F-Score', rotation=90, verticalalignment='bottom')
    ax4.get_yaxis().set_visible(False)
    ax4.get_xaxis().set_visible(False)


    for y in xrange(len(labels_ref)):
        ax4.annotate("{:.3f}".format(fs_val[y][1]), xy=(1, y),
                     horizontalalignment='center',
                     verticalalignment='center',
                     fontsize='xx-small')

    #K and OA
    fig.text(0, 1, 'KAPPA : {:.3f} OA : {:.3f}'.format(K, OA), ha='center', va='center')

    plt.savefig(out_png, format='png', dpi=dpi, bbox_inches='tight')


def gen_confusion_matrix_fig(csv_in, out_png, nomenclature_path,
                             undecidedlabel=None, dpi=900,
                             write_conf_score=True, 
                             grid_conf=False):
    """
    usage : generate a confusion matrix figure
    
    Parameters
    ----------
    
    csv_in : string
        path to a csv confusion matrix (OTB's computeConfusionMatrix output)
    out_png : string
        output path
    nomenclature_path : string
        path to the file which describre the nomenclature
    undecidedlabel : int
        undecided label
    dpi : int
        dpi
    write_conf_score : bool
        allow the display of confusion score
    grid_conf : bool
        display confusion matrix grid
    """
    conf_mat_dic = parse_csv(csv_in)

    if undecidedlabel:
        conf_mat_dic = remove_undecidedlabel(conf_mat_dic, undecidedlabel)

    K, OA, P_dic, R_dic, F_dic = get_coeff(conf_mat_dic)

    nom_dict = get_nomenclature(nomenclature_path)

    fig_conf_mat(conf_mat_dic, nom_dict, K, OA, P_dic, R_dic, F_dic,
                 out_png, dpi, write_conf_score, grid_conf)


def get_max_labels(conf_mat_dic, nom_dict):
    """
    """
    labels_ref = [nom_dict[lab] for lab in conf_mat_dic.keys()]
    labels_prod = [nom_dict[lab] for lab in conf_mat_dic[conf_mat_dic.keys()[0]].keys()]

    labels = set(labels_prod + labels_ref)
    return max([len(lab) for lab in labels]), labels_prod, labels_ref


def CreateCell(string, maxSize):

    if len(string) > maxSize:
        maxSize = len(string)

    newString = []
    out = ""
    for i in range(maxSize):
        newString.append(" ")

    start = round((maxSize-len(string))/2.0)
    for i in range(len(string)):
        newString[i+int(start)] = string[i]

    for i in range(len(newString)):
        out = out+newString[i]
    return out


def get_conf_max(conf_mat_dic, nom_dict):
    """
    usage : get confusion max by class
    """
    import collections

    conf_max = {}
    for class_ref, prod in conf_mat_dic.items():
        buff = collections.OrderedDict()
        for class_prod, value in prod.items():
            buff[nom_dict[class_prod]] = value
        buff = sorted(buff.iteritems(), key=lambda (k, v): (v, k))[::-1]
        conf_max[class_ref] = [class_name for class_name, value in buff]
    return conf_max


def compute_interest_matrix(all_matrix, f_interest="mean"):
    """
    """
    import collections
    import numpy as np

    #get all ref' labels
    ref_labels = []
    prod_labels = []
    for currentMatrix in all_matrix:
        ref_labels += [ref for ref, _ in currentMatrix.items()]
        prod_labels += [prod_label for _, prod in currentMatrix.items() for prod_label, _ in prod.items()]
        
    ref_labels = sorted(list(set(ref_labels)))
    prod_labels = sorted(list(set(prod_labels)))
    
    #matrix will contains by couple of ref / prod the list of values
    
    #init matrix
    matrix = collections.OrderedDict()
    output_matrix = collections.OrderedDict()
    for ref_label in ref_labels:
        matrix[ref_label] = collections.OrderedDict()
        output_matrix[ref_label] = collections.OrderedDict()
        for prod_label in prod_labels:
            matrix[ref_label][prod_label] = []
            output_matrix[ref_label][prod_label] = -1

    #fill-up matrix
    for currentMatrix in all_matrix:
        for ref_lab, prod in currentMatrix.items():
            for prod_lab, prod_val in prod.items():
                matrix[ref_lab][prod_lab].append(prod_val)

    #Compute interest output matrix
    for ref_lab, prod in matrix.items():
        for prod_lab, prod_val in prod.items():
            if f_interest.lower() == "mean":
                output_matrix[ref_lab][prod_lab] = "{0:.2f}".format(np.mean(matrix[ref_lab][prod_lab]))

    return output_matrix
    

def get_interest_coeff(runs_coeff, nb_lab, f_interest="mean"):
    """
    use to compute mean coefficient and 95% confidence interval. 
    store it by class as string
    """
    import collections
    import numpy as np
    from scipy import stats

    nb_run = len(runs_coeff)

    #get all labels
    for run in runs_coeff:
        ref_labels = [label for label, value in run.items()]
    ref_labels = sorted(list(set(ref_labels)))
    #init
    coeff_buff = collections.OrderedDict()
    for ref_lab in ref_labels:
        coeff_buff[ref_lab] = []
    #fill-up
    for run in runs_coeff:
        for label, value in run.items():
            coeff_buff[label].append(value)
    #Compute interest coeff
    coeff_out = collections.OrderedDict()
    for label, values in coeff_buff.items():
        if f_interest.lower() == "mean":
            mean = np.mean(values)
            b_inf, b_sup = stats.t.interval(0.95, nb_lab - 1,
                                            loc=np.mean(values),
                                            scale=stats.sem(values))
            if nb_run > 1:
                coeff_out[label] = "{:.3f} +- {:.3f}".format(mean, b_sup - mean)
            elif nb_run == 1:
                coeff_out[label] = "{:.3f}".format(mean)
    return coeff_out


def stats_report(csv_in, nomenclature_path, out_report, undecidedlabel=None):
    """
    usage : sum-up statistics in a txt file
    """
    import collections
    import numpy as np
    from scipy import stats

    nb_seed = len(csv_in)
    all_K = []
    all_OA = []
    all_P = []
    all_R = []
    all_F = []
    all_matrix = []
    for csv in csv_in:
        conf_mat_dic = parse_csv(csv)
        if undecidedlabel:
            conf_mat_dic = remove_undecidedlabel(conf_mat_dic, undecidedlabel)
        K, OA, P_dic, R_dic, F_dic = get_coeff(conf_mat_dic)
        all_matrix.append(conf_mat_dic)
        all_K.append(K)
        all_OA.append(OA)
        all_P.append(P_dic)
        all_R.append(R_dic)
        all_F.append(F_dic)

    conf_mat_dic = compute_interest_matrix(all_matrix, f_interest="mean")
    nom_dict = get_nomenclature(nomenclature_path)
    size_max, labels_prod, labels_ref = get_max_labels(conf_mat_dic, nom_dict)
    P_mean = get_interest_coeff(all_P, nb_lab=len(labels_ref), f_interest="mean")
    R_mean = get_interest_coeff(all_R, nb_lab=len(labels_ref), f_interest="mean")
    F_mean = get_interest_coeff(all_F, nb_lab=len(labels_ref), f_interest="mean")
    
    confusion_max = get_conf_max(conf_mat_dic, nom_dict)

    coeff_summarize_lab = ["Classes", "Precision mean", "Rappel mean", "F-score mean", "Confusion max"]
    label_size_max = max(map(len, coeff_summarize_lab))
    label_size_max_P = max([len(coeff) for lab, coeff in P_mean.items()])
    label_size_max_R = max([len(coeff) for lab, coeff in R_mean.items()])
    label_size_max_F = max([len(coeff) for lab, coeff in F_mean.items()])
    label_size_max = max([label_size_max, label_size_max_P, label_size_max_R, label_size_max_F, size_max])

    with open(out_report, "w") as res_file:
        res_file.write("#row = reference\n#col = production\n\n*********** Matrice de confusion ***********\n\n")

        #Confusion Matrix
        prod_ref_labels = "".join([" " for i in range(size_max)])+ "|" + "|".join(CreateCell(label, size_max) for label in labels_prod) + "\n"
        res_file.write(prod_ref_labels)
        for k, v in conf_mat_dic.items():
            prod = ""
            prod += CreateCell(nom_dict[k], size_max) + "|"
            for kk, vv in v.items():
                prod += CreateCell(str(vv), size_max) + "|"
            prod += CreateCell(nom_dict[k], size_max) + "\n"
            res_file.write(prod)

        #KAPPA and OA
        Kappa = np.mean(all_K)
        OA = np.mean(all_OA)
        
        K = "\nKAPPA : {:.3f}\n".format(Kappa)
        OA_ = "OA : {:.3f}\n\n".format(OA)
        if nb_seed > 1:
            K_inf, K_sup = stats.t.interval(0.95, len(labels_ref) - 1, loc=np.mean(all_K), scale=stats.sem(all_K))
            K = "\nKAPPA : {:.3f} +- {:.3f}\n".format(Kappa, K_sup - Kappa)
            OA_inf, OA_sup = stats.t.interval(0.95, len(labels_ref) - 1, loc=np.mean(all_OA), scale=stats.sem(all_OA))
            OA_ = "OA : {:.3f} +- {:.3f}\n\n".format(OA, OA_sup - OA)
        res_file.write(K)
        res_file.write(OA_)

        #Precision, Recall, F-score, max confusion
        sum_head = [CreateCell(lab, label_size_max) for lab in coeff_summarize_lab]
        sum_head = " | ".join(sum_head)+"\n"
        sep_c = "-"
        sep = ""
        for i in range(len(sum_head)):
            sep += sep_c
        res_file.write(sum_head)
        res_file.write(sep + "\n")
        for label in P_dic.keys():
            class_sum = [CreateCell(nom_dict[label], label_size_max),
                         CreateCell(P_mean[label], label_size_max),
                         CreateCell(R_mean[label], label_size_max),
                         CreateCell(F_mean[label], label_size_max),
                         ", ".join(confusion_max[label][0:3])]
            res_file.write(" | ".join(class_sum) + "\n")
