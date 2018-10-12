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
import IOTA2Step

class FirstStep(IOTA2Step.Step):
    def __init__(self):
        # heritage init
        super(FirstStep, self).__init__()
    def execute():
        print "EXECUTION de la first STEP !"