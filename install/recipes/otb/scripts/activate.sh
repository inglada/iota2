#!/bin/bash

# Store existing env vars and set to this conda env

if [[ -n "${PYTHONPATH}" ]]; then
    export _CONDA_SET_PYTHONPATH=${PYTHONPATH}
fi

if [ -d ${CONDA_PREFIX}/lib/otb/python/ ]; then
    export PYTHONPATH=${CONDA_PREFIX}/lib/otb/python/:${_CONDA_SET_PYTHONPATH}
fi

if [[ -n "${OTB_APPLICATION_PATH}" ]]; then
    export _CONDA_SET_OTB_APPLICATION_PATH=${OTB_APPLICATION_PATH}
fi

if [ -d ${CONDA_PREFIX}/lib/otb/applications/ ]; then
    export OTB_APPLICATION_PATH=${CONDA_PREFIX}/lib/otb/applications
fi

if [[ -n "${LD_LIBRARY_PATH}" ]]; then
    export _CONDA_SET_LD_LIBRARY_PATH=${LD_LIBRARY_PATH}
fi

if [ -d ${CONDA_PREFIX}/lib64 ]; then
    export LD_LIBRARY_PATH=${CONDA_PREFIX}/lib64:${_CONDA_SET_LD_LIBRARY_PATH}
fi
