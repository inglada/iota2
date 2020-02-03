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
import datetime
import subprocess
import sys
import logging
from typing import List
from timeit import default_timer as timer

logger = logging.getLogger(__name__)

class remove_in_string_list(object):
    """decorator use to remove element in return list according to strings
    """
    def __init__(self, *args: List[str]):
        self.pattern_list = args

    def __call__(self, f):
        def wrapped_f(*args):
            results = f(*args)
            results_filtered = []
            for pattern in self.pattern_list:
                for elem in results:
                    if pattern not in elem:
                        if elem not in results_filtered:
                            results_filtered.append(elem)
                    results = results_filtered
            return results_filtered
        return wrapped_f


class time_it(object):
    """chronometer decorator
    """
    def __init__(self, f):
        self.f = f
    
    def __call__(self, *args, **kwargs):
        import time
        start = time.time()
        results = self.f(*args, **kwargs)
        end = time.time()
        self.time_elapse = end - start
        print("ELAPSED time during the call of {} : {} [sec]".format(self.f.__name__,
                                                                     self.time_elapse))
        return results


def run(cmd, desc=None, env=os.environ, logger=logger):

    # Create subprocess
    start = timer()
    logger.debug("run command : " + cmd)
    p = subprocess.Popen(cmd, env=env, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # Get output as strings
    out, err = p.communicate()

    # Get return code
    rc = p.returncode

    stop = timer()

    # Log outputs
    logger.debug("out/err: {}".format(out.rstrip()))
    logger.debug("Done in {} seconds".format(stop-start))


    # Log error code
    if rc != 0:
        logger.error("Command {}  exited with non-zero return code {}".format(cmd, rc))
        exception_msg = "Launch command fail : {} {}".format(cmd, out)
        raise Exception(exception_msg)

class Opath(object):

    def __init__(self, opath, create=True, logger=logger):
        """
        Take the output path from main argument line and define and create the output folders
        """

        self.opath = opath
        self.opathT = opath+"/tmp"
        self.opathF = opath+"/Final"
        if create:
            if not os.path.exists(self.opath):
                try:
                    os.mkdir(self.opath)
                except OSError:
                    logger.debug(self.opath + "allready exists")

            if not os.path.exists(self.opathT):
                try:
                    os.mkdir(self.opathT)
                except OSError:
                    logger.debug(self.opathT + "allready exists")

            if not os.path.exists(self.opathT+"/REFL"):
                try:
                    os.mkdir(self.opathT+"/REFL")
                except OSError:
                    logger.debug(self.opathT+"/REFL"+ "allready exists")

            if not os.path.exists(self.opathF):
                try:
                    os.mkdir(self.opathF)
                except OSError:
                    logger.debug(self.opathF + "allready exists")
