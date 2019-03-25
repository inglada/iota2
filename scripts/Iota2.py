#!/usr/bin/env python
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
import sys
import os
import dask
#~ dask.config.set({'distributed.worker.multiprocessing-method': 'spawn'})
dask.config.set({'distributed.worker.multiprocessing-method': 'fork'})
from dask_jobqueue import PBSCluster
from dask.distributed import Client
import argparse
import numpy as np

import Iota2Builder as chain
from Common import FileUtils as fut
from Common import ServiceLogger as sLog


def str2bool(v):
    if v.lower() not in ('yes', 'true', 't', 'y', '1', 'no', 'false', 'f', 'n', '0'):
        raise argparse.ArgumentTypeError('Boolean value expected.')
    retour = True
    if v.lower() in ('no', 'false', 'f', 'n', '0'):
        retour = False
    return retour


def remove_tmp_files(cfg, current_step, chain):
    """
    use to keep only /final directory
    """
    import shutil
    iota2_outputs_dir = cfg.getParam('chain', 'outputPath')

    keep_dir = ["final", "features"]

    last_step = chain.get_steps_number()[-1]
    directories = chain.get_dir()
    dirs_to_rm = [d for d in directories if not os.path.split(d)[-1] in keep_dir]

    if current_step == last_step:
        for dir_to_rm in dirs_to_rm:
            if os.path.exists(dir_to_rm):
                shutil.rmtree(dir_to_rm)


def get_dask_client(client_type="local", step_num=0, nb_tasks=1):
    """
    Return
        a dask client scaled
    """
    from distributed import LocalCluster

    client = None

    if client_type.lower()=="cluster":
        client = PBSCluster(cores=2,
                            memory="10GB",
                            project='SmartName',
                            name='worker_{}'.format(step_num),
                            walltime='04:00:00',
                            interface='ib0',
                            env_extra=["export LD_LIBRARY_PATH={}:/work/logiciels/rh7/Python/3.5.2/lib".format(os.environ.get('LD_LIBRARY_PATH')),
                                       "export PYTHONPATH={}:{}/scripts".format(os.environ.get('PYTHONPATH'), fut.get_iota2_project_dir()),
                                       "export PATH={}".format(os.environ.get('PATH')),
                                       "export OTB_APPLICATION_PATH={}".format(os.environ.get('OTB_APPLICATION_PATH')),
                                       "export GDAL_DATA={}".format(os.environ.get('GDAL_DATA')),
                                       "export GEOTIFF_CSV={}".format(os.environ.get('GEOTIFF_CSV'))],
                            local_directory='$TMPDIR')
        client.scale(nb_tasks)
    elif client_type.lower()=="localcluster":
        client =  LocalCluster(n_workers=nb_tasks, threads_per_worker=1,
							   processes=True, loop=None,
							   start=None, ip=None, scheduler_port=0,
							   silence_logs=30, diagnostics_port=8787,
							   services=None, worker_services=None,
							   service_kwargs=None, asynchronous=False,
							   security=None, memory_limit='5GB')
    elif client_type.lower()=="cloud":
        # not implemented
        pass
    return client


if __name__ == "__main__":

    from Common import ServiceConfigFile as SCF

    parser = argparse.ArgumentParser(description = "This function allow you to"
                                                   "launch iota2 processing chain"
                                                   "as MPI process or not")
    parser.add_argument("-config",dest = "configPath", help="path to the configuration"
                                                            "file which rule le run",
                        required=True)
    parser.add_argument("-starting_step",dest="start", help="start chain from 'starting_step'",
                        default=0,
                        type=int,
                        required=False)
    parser.add_argument("-ending_step",dest="end", help="run chain until 'ending_step'"
                                                        "-1 mean 'to the end'",
                        default=0,
                        type=int,
                        required=False)
    parser.add_argument("-parameters",dest="parameters", help="Launch specific parameters",
                        nargs='+',
                        default=None,
                        required=False)
    parser.add_argument("-config_ressources", dest="config_ressources",
                        help="path to IOTA2 ressources configuration file",
                        required=False)
    parser.add_argument("-only_summary", dest="launchChain",
                        help="if set, only the summary will be printed. The chain will not be launched",
                        default=None,
                        action='store_false',
                        required=False)
    parser.add_argument("-client", dest="client",
                        help="deployed client architecture [local/cluster/cloud] default=local",
                        choices=["local", "localCluster", "cluster", "cloud"],
                        required=False,
                        default="local")
    args = parser.parse_args()

    cfg = SCF.serviceConfigFile(args.configPath)
    cfg.checkConfigParameters()
    chain_to_process = chain.iota2(cfg.pathConf, args.config_ressources)

    logger_lvl = cfg.getParam('chain', 'logFileLevel')
    enable_console = cfg.getParam('chain', 'enableConsole')
    try:
        rm_tmp = cfg.getParam('chain', 'remove_tmp_files')
    except:
        rm_tmp = False

    if args.start == args.end == 0:
        all_steps = chain_to_process.get_steps_number()
        args.start = all_steps[0]
        args.end = all_steps[-1]

    steps = chain_to_process.steps

    if args.end == -1:
        args.end = len(steps)

    print chain_to_process.print_step_summarize(args.start, args.end)

    if args.launchChain is False:
        sys.exit()

    for step in np.arange(args.start, args.end+1):
        params = steps[step-1].step_inputs()
        if args.parameters:
            params = args.parameters

        for group in chain_to_process.steps_group.keys():
            if step in chain_to_process.steps_group[group].keys():
                print "Running step {}: {} ({} tasks)".format(step, chain_to_process.steps_group[group][step],
                                                              len(params))
                break

        dask_client = get_dask_client(args.client, step, len(params))
        if dask_client is not None:
            client = Client(dask_client)
        else :
            client = Client(processes=False)
        results = client.gather(client.map(steps[step-1].step_execute(), params))

        if dask_client is not None:
            dask_client.close()
        client.close()
        dask_client = client = None