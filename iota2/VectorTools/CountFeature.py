#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sys
from iota2.VectorTools import vector_functions as vf

if len(sys.argv) != 2:
    print("usage: <shapefile>")
    sys.exit(1)
else:
    print(vf.getNbFeat(sys.argv[1]))
    sys.exit(0)
