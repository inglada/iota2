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
import os
import shutil
import logging
from subprocess import Popen, PIPE
import numpy as np
from Common import ServiceLogger as sLog
from Common import ServiceError as sErr
from Common import ServiceConfigFile as SCF


def get_qsub_cmd(cfg, config_ressources=None, parallel_mode="MPI"):
    """
    build qsub cmd to launch iota2 on HPC
    """
    from Common.FileUtils import get_iota2_project_dir
    from Steps import PBS_scheduler

    log_dir = os.path.join(cfg.getParam("chain", "outputPath"), "logs")
    scripts = os.path.join(get_iota2_project_dir(), "iota2")
    job_dir = cfg.getParam("chain", "jobsPath")
    if job_dir is None:
        raise Exception("the parameter 'chain.jobsPath' is needed to launch IOTA2 on clusters")

    config_path = cfg.pathConf
    iota2_main = os.path.join(job_dir, "iota2.pbs")

    config_ressources_path = None
    if config_ressources:
        config_ressources_path = config_ressources

    scheduler = PBS_scheduler.PBS_scheduler(config_ressources_path)

    chainName = scheduler.name
    walltime = scheduler.walltime
    cpu = scheduler.cpu
    ram = scheduler.RAM

    log_err = os.path.join(log_dir, "iota2_err.log")
    log_out = os.path.join(log_dir, "iota2_out.log")

    if os.path.exists(iota2_main):
        os.remove(iota2_main)

    ressources = ("#!/bin/bash\n"
                  "#PBS -N {}\n"
                  "#PBS -l select=1"
                  ":ncpus={}"
                  ":mem={}\n"
                  "#PBS -l walltime={}\n"
                  "#PBS -o {}\n"
                  "#PBS -e {}\n").format(chainName, cpu, ram, walltime, log_out, log_err)

    py_path = os.environ.get('PYTHONPATH')
    path = os.environ.get('PATH')
    ld_lib_path = os.environ.get('LD_LIBRARY_PATH')
    otb_app_path = os.environ.get('OTB_APPLICATION_PATH')
    gdal_data = os.environ.get('GDAL_DATA')
    geotiff_csv = os.environ.get('GEOTIFF_CSV')

    modules = ("\nexport PYTHONPATH={}\n"
               "export PATH={}\n"
               "export LD_LIBRARY_PATH={}\n"
               "export OTB_APPLICATION_PATH={}\n"
               "export GDAL_DATA={}\n"
               "export GEOTIFF_CSV={}\n").format(py_path, path, ld_lib_path,
                                                 otb_app_path, gdal_data, geotiff_csv)

    exe = ("python {0}/Cluster.py -config {1} -mode {2}").format(scripts,
                                                                 config_path,
                                                                 parallel_mode)
    if config_ressources:
        exe = ("python {0}/Cluster.py -config {1} -config_ressources {2} -mode {3}").format(scripts,
                                                                                            config_path,
                                                                                            config_ressources,
                                                                                            parallel_mode)
    pbs = ressources + modules + exe

    with open(iota2_main, "w") as iota2_f:
        iota2_f.write(pbs)

    qsub = ("qsub {0}").format(iota2_main)
    return qsub


def launchChain(cfg, config_ressources=None, parallel_mode="MPI"):
    """
    launch iota2 to HPC
    """
    import Iota2Builder as chain
    # Check configuration file
    cfg.checkConfigParameters()
    # Starting of logging service
    sLog.serviceLogger(cfg, __name__)
    # Local instanciation of logging
    logger = logging.getLogger(__name__)
    logger.info("START of iota2 chain")
    qsub_cmd = get_qsub_cmd(cfg, config_ressources, parallel_mode)
    process = Popen(qsub_cmd, shell=True, stdout=PIPE, stderr=PIPE)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="This function allows you launch the chain according to a configuration file")
    parser.add_argument("-config", dest="config",
                        help="path to IOTA2 configuration file", required=True)
    parser.add_argument("-config_ressources", dest="config_ressources",
                        help="path to IOTA2 HPC ressources configuration file",
                        required=False, default=None)
    parser.add_argument("-mode", dest="parallel_mode",
                        help="parallel jobs strategy",
                        required=False,
                        default="MPI",
                        choices=["MPI", "JobArray"])
    args = parser.parse_args()
    cfg = SCF.serviceConfigFile(args.config)

    try:
        launchChain(cfg, args.config_ressources, args.parallel_mode)
    # Exception manage by the chain
    # We only print the error message
    except sErr.osoError as e:
        print (e)
    # Exception not manage (bug)
    # print error message + all stack
    except Exception as e:
        print (e)
        raise
