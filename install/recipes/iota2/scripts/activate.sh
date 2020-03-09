#!/bin/bash

# Store existing env vars and set to this conda env

if [[ -n "${PATH}" ]]; then
    export _CONDA_SET_PATH=${PATH}
fi

if [ -d ${CONDA_PREFIX}/lib/python3.6/site-packages/iota2 ]; then
    export PATH=${CONDA_PREFIX}/lib/python3.6/site-packages/iota2:${_CONDA_SET_PATH}
    chmod uo+x ${CONDA_PREFIX}/lib/python3.6/site-packages/iota2/Iota2.py
    chmod uo+x ${CONDA_PREFIX}/lib/python3.6/site-packages/iota2/Iota2Cluster.py
fi
