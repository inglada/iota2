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


def run(args):
    """
    """
    cfg = SCF.serviceConfigFile(args.configPath)
    cfg.checkConfigParameters()
    chain_to_process = chain.iota2(cfg.pathConf, args.config_ressources)
    if args.start == args.end == 0:
        all_steps = chain_to_process.get_steps_number()
        args.start = all_steps[0]
        args.end = all_steps[-1]

    first_step_index = args.start - 1
    last_step_index = args.end - 1

    final_graph = chain_to_process.get_final_i2_exec_graph(
        first_step_index, last_step_index, args.graph_figure)

    print(
        chain_to_process.print_step_summarize(
            args.start, args.end, args.config_ressources is not None))

    cluster = LocalCluster(n_workers=1)
    client = Client(cluster)

    print(f"dashboard available at : {client.dashboard_link}")

    # final_graph.compute()
    if not args.only_summary:
        res = client.submit(final_graph.compute)
        res.result()


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
        dest="only_summary",
        help=
        "if set, only the summary will be printed. The chain will not be launched",
        default=False,
        action='store_true',
        required=False)
    parser.add_argument("-param_index",
                        dest="param_index",
                        help="index of parameter to consider",
                        required=False,
                        type=int,
                        default=None)
    args = parser.parse_args()
    run(args)
    # launch chain
    # if not args.only_summary:
    #     res = client.submit(final_graph.compute)
    #     res.result()
