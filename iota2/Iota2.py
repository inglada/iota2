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

import Iota2Builder as chain
from iota2.Common import FileUtils as fut
import argparse

import sys
import traceback
import datetime
import dill
import time
import numpy as np
from mpi4py import MPI
from iota2.Common import ServiceLogger as sLog
from iota2.Common.FileUtils import ensure_dir
import os
import shutil

# This is needed in order to be able to send python objects throug MPI send
import mpi4py
MPI_VERSION = int("".join((mpi4py.__version__).split(".")))
if MPI_VERSION == 200:
    MPI.pickle.dumps = dill.dumps
    MPI.pickle.loads = dill.loads
elif MPI_VERSION >= 300:
    MPI.pickle.__init__(dill.dumps, dill.loads)


class MPIService():
    """
    Class for storing the MPI context
    """
    def __init__(self):
        self.comm = MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        self.size = self.comm.Get_size()


class JobArray():
    """
    Class for storing a function to be applied to an array of parameters.
    - job is a callable object like a lambda expression;
      it takes a single parameter
    - param_array is a list of the parameters for each call to job
    """
    def __init__(self, job, param_array):
        self.job = job
        self.param_array = param_array


def str2bool(v):
    if v.lower() not in ('yes', 'true', 't', 'y', '1', 'no', 'false', 'f', 'n',
                         '0'):
        raise argparse.ArgumentTypeError('Boolean value expected.')

    retour = True
    if v.lower() in ('no', 'false', 'f', 'n', '0'):
        retour = False
    return retour


def stop_workers(mpi_service):
    """
    stop workers
    :param mpi_service
    """
    for i in range(1, mpi_service.size):
        print("Worker process with rank {}/{} stopped".format(
            i, mpi_service.size - 1))
        mpi_service.comm.send(None, dest=i, tag=1)


def launchTask(function, parameter, logger, mpi_services=None):
    """
    usage :
    IN
    OUT
    """
    import sys
    logger.root.log(51, '************* WORKER REPORT *************')
    if mpi_services:
        logger.root.log(51, "worker : " + str(mpi_services.rank))

    logger.root.log(51, "-----------> TRACE <-----------")

    start_job = time.time()
    start_date = datetime.datetime.now()
    returned_data = None
    try:
        returned_data = function(parameter)
        parameter_success = True
        logger.root.log(51, "parameter : '" + str(parameter) + "' : ended")
    except KeyboardInterrupt:
        raise
    except:
        traceback.print_exc()
        parameter_success = False
        logger.root.log(51, "parameter : '" + str(parameter) + "' : failed")

    end_job = time.time()
    end_date = datetime.datetime.now()

    logger.root.log(51, "---------> END TRACE <---------")
    logger.root.log(51, "Execution time [sec] : " + str(end_job - start_job))
    logger.root.log(51, "****************************************\n")

    worker_complete_log = logger.root.handlers[0].stream.getvalue()
    logger.root.handlers[0].stream.close()

    return worker_complete_log, start_date, end_date, returned_data, parameter_success


def mpi_schedule(iota2_step,
                 param_array_origin,
                 mpi_service=MPIService(),
                 logPath=None,
                 logger_lvl="INFO",
                 enable_console=False):
    """
    A simple MPI scheduler to execute jobs in parallel.
    """
    if mpi_service.rank != 0:
        return None

    job = iota2_step.step_execute()

    returned_data_list = []
    parameters_success = []

    if not param_array_origin:
        print("JobArray must contain a list of parameter as argument")
        with open(logPath, "a+") as log_f:
            log_f.write(
                "JobArray must contain a list of parameter as argument.\n")
            log_f.write("An earlier stage probably behaved erratically.")
        return [], False
    try:
        if os.path.exists(logPath):
            os.remove(logPath)
        if callable(param_array_origin):
            param_array = param_array_origin()
        else:
            #shallowCopy
            param_array = [param for param in param_array_origin]

        if mpi_service.size > 1:
            # master
            nb_completed_tasks = 0
            nb_tasks = len(param_array)
            for i in range(1, mpi_service.size):
                if len(param_array) > 0:
                    task_param = param_array.pop(0)
                    mpi_service.comm.send(
                        [job, task_param, logger_lvl, enable_console],
                        dest=i,
                        tag=0)
            while nb_completed_tasks < nb_tasks:
                [
                    worker_rank,
                    [start, end, worker_complete_log, returned_data, success]
                ] = mpi_service.comm.recv(source=MPI.ANY_SOURCE, tag=0)
                returned_data_list.append(returned_data)
                parameters_success.append(success)
                #Write worker log
                fut.ensure_dir(os.path.split(logPath)[0])
                with open(logPath, "a+") as log_f:
                    log_f.write(worker_complete_log)
                nb_completed_tasks += 1
                if len(param_array) > 0:
                    task_param = param_array.pop(0)
                    mpi_service.comm.send(
                        [job, task_param, logger_lvl, enable_console],
                        dest=worker_rank,
                        tag=0)
        else:
            #if not lanch thanks to mpirun, launch each parameters one by one
            for param in param_array:
                worker_log = sLog.Log_task(logger_lvl, enable_console)
                worker_complete_log, start_date, end_date, returned_data, success = launchTask(
                    job, param, worker_log)
                fut.ensure_dir(os.path.split(logPath)[0])
                with open(logPath, "a+") as log_f:
                    log_f.write(worker_complete_log)
                returned_data_list.append(returned_data)
                parameters_success.append(success)
    except KeyboardInterrupt:
        raise
    except Exception as e:
        print(e)
        parameters_success.append(False)
        if mpi_service.rank == 0 and mpi_service.size > 1:
            print("Something went wrong, we should log errors.")
            traceback.print_exc()
            stop_workers(mpi_service)
            sys.exit(1)

    step_completed = all(parameters_success)
    if step_completed:
        iota2_step.step_clean()
    return returned_data_list, step_completed


def start_workers(mpi_service):
    mpi_service.comm.barrier()
    if mpi_service.rank != 0:
        # Sending started signal
        mpi_service.comm.send(mpi_service.rank, dest=0, tag=0)
        mpi_status = MPI.Status()
        while 1:
            # waiting sending works by master
            task = mpi_service.comm.recv(source=0,
                                         tag=MPI.ANY_TAG,
                                         status=mpi_status)
            if task is None:
                sys.exit(0)
            # unpack task

            [task_job, task_param, logger_lvl, enable_console] = task

            worker_log = sLog.Log_task(logger_lvl, enable_console)
            worker_complete_log, start_date, end_date, returned_data, success = launchTask(
                task_job, task_param, worker_log, mpi_service)
            mpi_service.comm.send([
                mpi_service.rank,
                [
                    start_date, end_date, worker_complete_log, returned_data,
                    success
                ]
            ],
                                  dest=0,
                                  tag=0)
    else:
        nb_started_workers = 0
        while nb_started_workers < mpi_service.size - 1:
            rank = mpi_service.comm.recv(source=MPI.ANY_SOURCE, tag=0)
            print("Worker process with rank {}/{} started".format(
                rank, mpi_service.size - 1))
            nb_started_workers += 1


def remove_tmp_files(cfg, current_step, chain):
    """
    use to keep only /final directory
    """
    import shutil
    iota2_outputs_dir = cfg.getParam('chain', 'outputPath')

    keep_dir = ["final", "features"]

    last_step = chain.get_steps_number()[-1]
    directories = chain.get_dir()
    dirs_to_rm = [
        d for d in directories if not os.path.split(d)[-1] in keep_dir
    ]

    if current_step == last_step:
        for dir_to_rm in dirs_to_rm:
            if os.path.exists(dir_to_rm):
                shutil.rmtree(dir_to_rm)


if __name__ == "__main__":

    from iota2.Common import ServiceConfigFile as SCF
    from iota2.Common import DebugUtils as du
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
    if os.path.exists(chain_to_process.iota2_pickle):
        chain_to_process = chain_to_process.load_chain()

    logger_lvl = cfg.getParam('chain', 'logFileLevel')
    enable_console = cfg.getParam('chain', 'enableConsole')
    param_index = args.param_index
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

    if MPIService().rank == 0:
        print(
            chain_to_process.print_step_summarize(
                args.start, args.end, args.config_ressources is not None))
    if args.launchChain is False:
        sys.exit()

    # Initialize MPI service
    mpi_service = MPIService()

    # Start worker processes
    start_workers(mpi_service)
    # Remove all existing outputs
    root = cfg.getParam('chain', 'outputPath')
    rm_PathTEST = cfg.getParam("chain", "remove_outputPath")
    start_step = cfg.getParam("chain", "firstStep")

    for step in np.arange(args.start, args.end + 1):

        if os.path.exists(
                root
        ) and root != "/" and rm_PathTEST and start_step == "init" and steps[
                step - 1].step_name == "IOTA2DirTree":
            shutil.rmtree(root, ignore_errors=False)
        ensure_dir(root)
        params = steps[step - 1].step_inputs()
        param_array = []
        if callable(params):
            param_array = params()
        else:
            param_array = [param for param in params]
        for group in list(chain_to_process.steps_group.keys()):
            if step in list(chain_to_process.steps_group[group].keys()):
                print("Running step {}: {} ({} tasks)".format(
                    step, chain_to_process.steps_group[group][step],
                    len(param_array)))
                break

        if args.parameters:
            params = args.parameters
        else:
            params = param_array
        #~ if steps[step-1].previous_step:
        #~ print "Etape précédente : {}".format(steps[step-1].previous_step.step_status)
        steps[step - 1].step_status = "running"
        logFile = steps[step - 1].logFile

        if not os.path.exists(steps[step - 1].log_step_dir):
            os.makedirs(steps[step - 1].log_step_dir)
        try:
            logFileTmp = open(steps[step - 1].logFile, "w")
            logFileTmp.close()
        except Exception as exc:
            print(exc)
            raise

        dico_tmp = chain_to_process.steps_group[cfg.getParam(
            'chain', 'firstStep')].copy()
        key_init = dico_tmp.popitem(last=False)[0]
        states = chain_to_process.print_step_summarize(key_init,
                                                       step,
                                                       log=True,
                                                       running_step=True)
        global_log_file = os.path.join(cfg.getParam('chain', 'outputPath'),
                                       "logs/Global_status.log")
        global_log = open(global_log_file, "w")
        global_log.write(states)
        global_log.close()

        if param_index is not None:
            params = [params[param_index]]
            logFile = (steps[step - 1].logFile).replace(
                ".log", "_{}.log".format(param_index))
        _, step_completed = mpi_schedule(steps[step - 1], params, mpi_service,
                                         logFile, logger_lvl)
        if not step_completed:
            steps[step - 1].step_status = "fail"
            states = chain_to_process.print_step_summarize(key_init,
                                                           step,
                                                           log=True,
                                                           running_step=True,
                                                           running_sym='f')
            global_log_file = os.path.join(cfg.getParam('chain', 'outputPath'),
                                           "logs/Global_status.log")
            global_log = open(global_log_file, "w")
            global_log.write(states)
            log_info = du.get_log_info(cfg.getParam('chain', 'outputPath'),
                                       args.configPath, logFile)
            global_log.write(log_info)
            global_log.close()

            break
        else:
            steps[step - 1].step_status = "success"
            states = chain_to_process.print_step_summarize(key_init,
                                                           step,
                                                           log=True)
            global_log_file = os.path.join(cfg.getParam('chain', 'outputPath'),
                                           "logs/Global_status.log")
            global_log = open(global_log_file, "w")
            global_log.write(states)
            global_log.close()

        if rm_tmp and param_index is None:
            remove_tmp_files(cfg, current_step=step, chain=chain_to_process)
    #~ chain_to_process.save_chain()
    stop_workers(mpi_service)

    if not step_completed:
        sys.exit(-1)
