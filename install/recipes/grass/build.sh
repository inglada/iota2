#! /bin/bash


if [[ $target_platform =~ linux.* ]]; then
    export LDFLAGS="$LDFLAGS -Wl,-rpath-link,${PREFIX}/lib"
fi

export PATH=$BUILD_PREFIX/bin:/usr/bin:/bin:/usr/sbin:/etc:/usr/lib

if [ $(uname) == Darwin ]; then
  export GRASS_PYTHON=$(which pythonw)
else
  export GRASS_PYTHON=$(which python)
  export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$PREFIX/lib:$SRC_DIR/dist.x86_64-pc-linux-gnu/lib
fi

CONFIGURE_FLAGS="\
  --prefix=$BUILD_PREFIX \
  --with-freetype \
  --with-freetype-includes=$BUILD_PREFIX/include/freetype2 \
  --with-freetype-libs=$BUILD_PREFIX/lib \
  --with-gdal=$BUILD_PREFIX/bin/gdal-config \
  --with-gdal-libs=$BUILD_PREFIX/lib \
  --with-proj=$BUILD_PREFIX/bin/proj \
  --with-proj-includes=$BUILD_PREFIX/include/ \
  --with-proj-libs=$BUILD_PREFIX/lib \
  --with-proj-share=$BUILD_PREFIX/share/proj \
  --with-geos=$BUILD_PREFIX/bin/geos-config \
  --with-jpeg-includes=$BUILD_PREFIX/include \
  --with-jpeg-libs=/$BUILD_PREFIX/lib \
  --with-png-includes=$BUILD_PREFIX/include \
  --with-png-libs=$BUILD_PREFIX/lib \
  --with-tiff-includes=$BUILD_PREFIX/include \
  --with-tiff-libs=$BUILD_PREFIX/lib \
  --without-postgres \
  --without-mysql \
  --with-sqlite \
  --with-sqlite-libs=$BUILD_PREFIX/lib \
  --with-sqlite-includes=$BUILD_PREFIX/include \
  --with-fftw-includes=$BUILD_PREFIX/include \
  --with-fftw-libs=$BUILD_PREFIX/lib \
  --with-cxx \
  --with-cairo \
  --with-cairo-includes=$BUILD_PREFIX/include/cairo \
  --with-cairo-libs=$BUILD_PREFIX/lib \
  --with-cairo-ldflags="-lcairo" \
  --without-readline \
  --enable-64bit \
  --with-libs=$BUILD_PREFIX/lib \
  --with-includes=$BUILD_PREFIX/include \
  --with-python3=$GRASS_PYTHON \
"

./configure $CONFIGURE_FLAGS
make -j4 GDAL_DYNAMIC= > out.txt 2>&1 || (tail -400 out.txt && echo "ERROR in make step" && exit -1)
make -j4 install

ACTIVATE_DIR=$PREFIX/etc/conda/activate.d
DEACTIVATE_DIR=$PREFIX/etc/conda/deactivate.d
mkdir -p $ACTIVATE_DIR
mkdir -p $DEACTIVATE_DIR
cp $RECIPE_DIR/scripts/activate.sh $ACTIVATE_DIR/grass-activate.sh
cp $RECIPE_DIR/scripts/deactivate.sh $DEACTIVATE_DIR/grass-deactivate.sh
