#!/usr/bin/env bash

$PYTHON setup.py install

ACTIVATE_DIR=$PREFIX/etc/conda/activate.d
DEACTIVATE_DIR=$PREFIX/etc/conda/deactivate.d
mkdir -p $ACTIVATE_DIR
mkdir -p $DEACTIVATE_DIR
cp $RECIPE_DIR/scripts/activate.sh $ACTIVATE_DIR/iota2-activate.sh
cp $RECIPE_DIR/scripts/deactivate.sh $DEACTIVATE_DIR/iota2-deactivate.sh
