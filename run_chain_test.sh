#/bin/bash

source config_oso.sh
src_dir=$PWD
working_dir=$PTMPCI/inglada/tmp
data_dir=$PTMPCI/inglada/tuiles
insitu_dir=$data_dir/in-situ
rm -rf $working_dir
mkdir $working_dir
cd $data_dir

# Assumes that the $data_dir contains folders named like Landsat8_D0004H0002 and that each folder contains all the dates of the tile named like LANDSAT8_OLITIRS_XS_20130414_N2A_France-MetropoleD0004H0002.tgz

# We decompress all the tgz in their respective tile directory
for tuile in $(ls -d Landsat8*)
do
echo "Preparing tile $tuile"
echo "---------------------"
tuile_dir=${tuile:0:19}
cd $tuile_dir
for im in $(ls *tgz)
do
    echo "Decompressing $im"
    #tar xzf $im
done

ipath=$data_dir/$tuile_dir
opath=$working_dir/$tuile_dir
mkdir $opath
vectorfile=$insitu_dir/$tuile_dir/FR_SUD_2013_LC_SM_V2.shp
tile=${tuile:9:19}

cd $src_dir
echo "python ProcessingChain.py ${ipath} ${opath} ${vectorfile} ${tile}"
#python ProcessingChain.py ${ipath} ${opath} ${vectorfile} ${tile}

cd $data_dir
done


