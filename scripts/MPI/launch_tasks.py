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

import traceback
import datetime
import dill
import os
from mpi4py import MPI
import argparse
import time
import pickle
import datetime
import sys
import subprocess

def launchBashCmd(bashCmd):
    """
    usage : function use to launch bashCmd
    """
    #using subprocess will be better.
    os.system(bashCmd)
    #bashCmd.split(" ")
    #subprocess.check_output(bashCmd, shell=False)

def queuedProcess(cmd_list,N_processes=4,shell=False,delay=0):

    cmd_queue = cmd_list
    prc_queue = []

    for t in range(N_processes):
        if len(cmd_queue) > 0:
            prc_queue.append(subprocess.Popen(cmd_queue.pop(0), shell=shell))
            time.sleep(delay)

    while len(prc_queue) > 0:
        for i in range(len(prc_queue)):
            if prc_queue[i].poll() is not None:
                prc_queue.pop(i)
                if len(cmd_queue) > 0:
                    prc_queue.append(subprocess.Popen(cmd_queue.pop(0), shell=shell))
                    time.sleep(delay)
                break

def launchPythonCmd(f, *arg):
    """
    Launch function with args
    """
    f(*arg)


class Tasks():
    """
    Class tasks definition : this class launch MPI process
    """
    def __init__(self, tasks, ressources, iota2_config):
        """
        :param tasks [tuple] first element must be lambda function
                             second element is a list of parameters
        :param ressources [Ressources Object]
        """
        self.jobs = tasks[0]
        self.parameters = tasks[1]
        self.TaskName = ressources.name
        self.ressources = ressources
        self.nb_cpu = ressources.nb_cpu

        self.logFile = os.path.join(iota2_config.getParam('chain', 'outputPath'),
                                    "logs",
                                    self.TaskName + "_log.log")

