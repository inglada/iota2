#!/bin/bash
# =========================================
# Project : OSO Land cover treatment chain
# OSO Environment variable setting
# Dedicated script for CNES cluster hpc-5g
# and for jenkins platform
# =========================================

function test_dir 
  if [ ! -d "$1" ]; then
    echo "$1 doesn't exist. Check your installation."
  fi


#----------------------------------------
# Check if OSO_PATH is define
if test -z "$OSO_PATH"; then
  echo "Environment variable OSO_PATH doesn't exist. Please define it."
else
  echo "Cleanning environnement"
  module purge
  echo "Load python and gdal"
  module load python
  module load pygdal/2.1.0-py2.7
  module load otb/develop
  module load cmake

  #----------------------------------------
  # General environment variables
  export IOTA2DIR=$OSO_PATH/iota2/
  test_dir $IOTA2DIR

  export LD_LIBRARY_PATH=$IOTA2DIR/install/lib:$LD_LIBRARY_PATH

  #----------------------------------------
  # PYTHONPATH environment variable
  export PYTHONPATH=$PYTHONPATH:$IOTA2DIR/data/test_scripts/
  export PYTHONPATH=$PYTHONPATH:$IOTA2DIR/scripts/common/
fi
