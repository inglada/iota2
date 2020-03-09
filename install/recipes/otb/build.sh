#!/usr/bin/env bash

set +x
set -e # Abort on error

[[ -d build ]] || mkdir build
cd build

if [[ $target_platform =~ linux.* ]]; then
    export LDFLAGS="$LDFLAGS -Wl,-rpath-link,${PREFIX}/lib"
fi

# symlinks to enable remote modules
ln -s $SRC_DIR/iota2 $SRC_DIR/OTB/Modules/Remote/iota2
ln -s $SRC_DIR/temporalgapfilling $SRC_DIR/OTB/Modules/Remote/temporalgapfilling
ln -s $SRC_DIR/MultitempFiltering/MultitempFiltering $SRC_DIR/OTB/Modules/Remote/MultitempFiltering
ln -s $SRC_DIR/otbPointMatchCoregistrationModel $SRC_DIR/OTB/Modules/Remote/otbPointMatchCoregistrationModel

ln -s $SRC_DIR/slicAutoContext/Modules/Remote/SLIC $SRC_DIR/OTB/Modules/Remote/SLIC
ln -s $SRC_DIR/slicAutoContext/Modules/Remote/ModuleAutoContext $SRC_DIR/OTB/Modules/Remote/ModuleAutoContext

rm $SRC_DIR/OTB/Modules/Remote/temporal-gapfilling.remote.cmake
#~ rm -r $SRC_DIR/OTB/Modules/Wrappers/QGIS

CC=${BUILD_PREFIX}/bin/${HOST}-gcc CXX=$BUILD_PREFIX/bin/${HOST}-g++ \
    cmake -G "Ninja"\
    -DOTB_USE_SPTW:BOOL=ON \
    -DCMAKE_BUILD_TYPE:STRING=Release \
    -DCMAKE_CXX_FLAGS:STRING="-std=c++14" \
    -DCMAKE_INSTALL_PREFIX:STRING=$PREFIX \
    -DBUILD_TESTING:BOOL=OFF \
    -DOTB_USE_6S:BOOL= ON \
    -DOTB_USE_CURL:BOOL=OFF \
    -DOTB_USE_GLEW:BOOL=OFF \
    -DOTB_USE_GLFW:BOOL=OFF \
    -DOTB_USE_GLUT:BOOL=OFF \
    -DOTB_USE_GSL:BOOL=ON \
    -DOTB_USE_LIBKML:BOOL=ON \
    -DOTB_USE_LIBSVM:BOOL=ON \
    -DOTB_USE_MAPNIK:BOOL=OFF \
    -DOTB_USE_MPI:BOOL=ON \
    -DOTB_USE_MUPARSER:BOOL=ON \
    -DOTB_USE_MUPARSERX:BOOL=ON \
    -DOTB_USE_OPENCV:BOOL=ON \
    -DOTB_USE_OPENGL:BOOL=OFF \
    -DOTB_USE_QT:BOOL=OFF \
    -DOTB_USE_QWT:BOOL=OFF \
    -DOTB_USE_SHARK:BOOL=ON \
    -DOTB_USE_SIFTFAST:BOOL=ON \
    -DOTB_USE_SPTW:BOOL=OFF \
    -DOTB_WRAP_PYTHON:BOOL=ON \
    -DOTB_USE_OPENMP:BOOL=ON \
    -DOTB_USE_SSE_FLAGS:BOOL=ON \
    -DModule_IOTA2:BOOL=ON \
    -DModule_OTBTemporalGapFilling:BOOL=ON \
    -DModule_OTBAppPointMatchCoregistration:BOOL=ON \
    -DModule_MultitempFiltering:BOOL=ON \
    -DModule_OTBSLIC:BOOL=ON \
    -DModule_OTBAutoContext:BOOL=ON \
    ../OTB

ninja install -j 30

ACTIVATE_DIR=$PREFIX/etc/conda/activate.d
DEACTIVATE_DIR=$PREFIX/etc/conda/deactivate.d
mkdir -p $ACTIVATE_DIR
mkdir -p $DEACTIVATE_DIR
cp $RECIPE_DIR/scripts/activate.sh $ACTIVATE_DIR/otb-activate.sh
cp $RECIPE_DIR/scripts/deactivate.sh $DEACTIVATE_DIR/otb-deactivate.sh
