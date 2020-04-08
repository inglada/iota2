#!/bin/bash

# Restore previous PYTHONPATH env vars if they were set

unset GDAL224DIR
if [[ -n "${_CONDA_SET_GDAL224DIR}" ]]; then
    export GDAL224DIR=${_CONDA_SET_PYTHONPATH}
    unset _CONDA_SET_GDAL224DIR
fi

unset GRASSDIR
if [[ -n "${_CONDA_SET_GRASSDIR}" ]]; then
    export GRASSDIR=${_CONDA_SET_GRASSDIR}
    unset _CONDA_SET_GRASSDIR
fi
