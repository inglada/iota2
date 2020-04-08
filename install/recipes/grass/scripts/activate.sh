#!/bin/bash

# Store existing env vars and set to this conda env

if [[ -n "${GDAL224DIR}" ]]; then
    export _CONDA_SET_GDAL224DIR=${GDAL224DIR}
fi

if [ -d ${CONDA_PREFIX}/bin ]; then
    export GDAL224DIR=${CONDA_PREFIX}/bin
fi

if [[ -n "${GRASSDIR}" ]]; then
    export _CONDA_SET_GRASSDIR=${GRASSDIR}
fi

export GRASSDIR=${CONDA_PREFIX}
