#!/bin/bash

# Restore previous PATH env vars if they were set

unset PATH
if [[ -n "${_CONDA_SET_PATH}" ]]; then
    export PATH=${_CONDA_SET_PATH}
    unset _CONDA_SET_PATH
    #~ chmod uo-x ${CONDA_PREFIX}/lib/python3.6/site-packages/iota2/Iota2.py
    #~ chmod uo-x ${CONDA_PREFIX}/lib/python3.6/site-packages/iota2/Iota2Cluster.py
fi
