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
import argparse
from dask.distributed import Client
from dask.distributed import LocalCluster

from iota2 import Iota2Builder as chain

if __name__ == "__main__":

    from iota2.Common import ServiceConfigFile as SCF
    parser = argparse.ArgumentParser(description="This function allow you to"
                                     "launch iota2 processing chain"
                                     "as MPI process or not")

    parser.add_argument("-config",
                        dest="configPath",
                        help="path to the configuration"
                        "file which rule le run",
                        required=True)
    parser.add_argument("-starting_step",
                        dest="start",
                        help="start chain from 'starting_step'",
                        default=0,
                        type=int,
                        required=False)
    parser.add_argument("-ending_step",
                        dest="end",
                        help="run chain until 'ending_step'"
                        "-1 mean 'to the end'",
                        default=0,
                        type=int,
                        required=False)
    parser.add_argument("-parameters",
                        dest="parameters",
                        help="Launch specific parameters",
                        nargs='+',
                        default=None,
                        required=False)
    parser.add_argument("-config_ressources",
                        dest="config_ressources",
                        help="path to IOTA2 ressources configuration file",
                        required=False)
    parser.add_argument("-execution_graph_file",
                        dest="graph_figure",
                        help="output execution graph",
                        default="",
                        required=False)
    parser.add_argument(
        "-only_summary",
        dest="launchChain",
        help=
        "if set, only the summary will be printed. The chain will not be launched",
        default=None,
        action='store_false',
        required=False)
    parser.add_argument("-param_index",
                        dest="param_index",
                        help="index of parameter to consider",
                        required=False,
                        type=int,
                        default=None)
    args = parser.parse_args()
    cfg = SCF.serviceConfigFile(args.configPath)
    cfg.checkConfigParameters()

    chain_to_process = chain.iota2(cfg.pathConf, args.config_ressources)
    if args.start == args.end == 0:
        all_steps = chain_to_process.get_steps_number()
        first_step_index = all_steps[0]
        last_step_index = all_steps[-1]
    else:
        first_step_index = args.start - 1
        last_step_index = args.end - 1
    print(
        chain_to_process.print_step_summarize(
            args.start, args.end, args.config_ressources is not None))
    final_graph = chain_to_process.get_final_i2_exec_graph(
        first_step_index, last_step_index)
    if args.graph_figure:
        final_graph.visualize(filename=args.graph_figure,
                              optimize_graph=True,
                              collapse_outputs=True)
    cluster = LocalCluster(n_workers=1)
    client = Client(cluster)

    print(f"dashboard available at : {client.dashboard_link}")

    res = client.submit(final_graph.compute)
    res.result()
