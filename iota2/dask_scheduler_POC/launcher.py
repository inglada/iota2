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

from iota2_step import step
from first_step import first_step
from second_step import second_step
from third_step import third_step
from forth_step import forth_step
from fifth_step import fifth_step
from fusion_step import fusion_step
from mosaic_step import mosaic_step

from dask.distributed import Client
from dask.distributed import LocalCluster
from dask_jobqueue import PBSCluster

if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(description="iota2 dask scheduling POC")
    PARSER.add_argument("-running_dir",
                        dest="running_directory",
                        help="directory which will contains some outputs",
                        required=True)
    PARSER.add_argument("-graph_file",
                        dest="graph_file",
                        help="png file which will contains dependencies graph",
                        required=True)
    ARGS = PARSER.parse_args()
    graph_file = ARGS.graph_file
    running_directory = ARGS.running_directory
    # generate steps, as already done in Iota2Builder.py
    list_of_sorted_i2_steps = [
        first_step(running_directory),
        second_step(running_directory),
        third_step(running_directory),
        forth_step(running_directory),
        fifth_step(running_directory),
        fusion_step(running_directory),
        mosaic_step(running_directory)
    ]
    # list_of_sorted_i2_steps = [
    #     first_step(running_directory),
    #     second_step(running_directory)
    # ]

    # get tasks to be launched
    final_graph = step.get_final_i2_exec_graph()

    # visualizing graph could be useful in case of long run in order to
    # know what tasks as been processes and what tasks as to be launched
    # figure path must be a parameter of Iota2.py (output directories not created)

    # TODO : be able of using dask dashboard, very useful for production operators to monitor the chain
    # color="order"
    final_graph.visualize(filename=graph_file)

    cluster = cluster = LocalCluster(n_workers=1)
    client = Client(cluster)
    #final_graph.compute()

    print(f"dashboard available at : {client.dashboard_link}")

    # then, launch tasks (it's a blocking line)
    res = client.submit(final_graph.compute)
    res.result()
    # python launcher.py -running_dir /home/uz/vincenta/tmp/dask_scheduler/dask_scheduler -graph_file /home/uz/vincenta/tmp/dask_scheduler/dask_scheduler/graphe_POC.png
