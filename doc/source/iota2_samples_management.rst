iota²'s samples management
##########################

This chapter is dedicated to give explanations about how samples are managed during 
the iota² run. First, we will see how to tell iota² about the dataBase location and
some restrictions on it. Next, a focus will be done on fields dedicated to set-up 
a sampling strategy.

Input dataBase location and label's field
*****************************************

+-------------+--------------------------+--------------+------------------------------------------+
|Parameter Key|Parameter Type            |Default value |Parameter purpose                         |
+=============+==========================+==============+==========================================+
|groundTruth  |String                    | Mandatory    |Input dataBase                            |
+-------------+--------------------------+--------------+------------------------------------------+
|dataField    |String                    | Mandatory    |field into the dataBase containing labels |
+-------------+--------------------------+--------------+------------------------------------------+

.. Note:: 
    In the downloadable data-set `here <http://osr-cesbio.ups-tlse.fr/echangeswww/TheiaOSO/IOTA2_TEST_S2.tar.bz2>`_, 
    the dataBase is the file 'groundTruth.shp' and the field of interest (dataField) is 'CODE'

Sampling strategy fields
************************

+------------------+--------------------------+-----------------+-------------------------------------------------------------------------------------------------------------------+
|Parameter Key     |Parameter Type            |Default value    |Parameter purpose                                                                                                  |
+==================+==========================+=================+===================================================================================================================+
|ratio             |float                     | 0.5             |ratio ]0;1[ learning samples / validation samples                                                                  |
+------------------+--------------------------+-----------------+-------------------------------------------------------------------------------------------------------------------+
|splitGroundTruth  |boolean                   | True            |enable the split in samples / validation samples set                                                               |
+------------------+--------------------------+-----------------+-------------------------------------------------------------------------------------------------------------------+
|runs              |integer                   | 1               |number of random splits between learning samples and validation samples                                            |
+------------------+--------------------------+-----------------+-------------------------------------------------------------------------------------------------------------------+
|cloud_threshold   |integer                   | 1               |threshold to pick-up learning samples. Every samples which are valid > cloud_threshold could be use to learn models|
+------------------+--------------------------+-----------------+-------------------------------------------------------------------------------------------------------------------+
|sampleSelection   |python's dictionnary      | cf Note 1       |sampling strategy in learning polygons                                                                             |
+------------------+--------------------------+-----------------+-------------------------------------------------------------------------------------------------------------------+
|sampleAugmentation|python's dictionnary      | cf Note 2       |generate synthetic samples                                                                                         |
+------------------+--------------------------+-----------------+-------------------------------------------------------------------------------------------------------------------+

*Note 1* : sampleSelection default value

.. code-block:: python

    sampleSelection:
    {
        "sampler": "random",
        "strategy": "all"
    }

which mean all pixels under learning polygons will use to build models.

*Note 2* : sampleAugmentation default value

.. code-block:: python

    sampleAugmentation:
    {
        "activate": False
    }

which mean no sample augmentation will be done.

Differents strategies illustrated by examples
*********************************************

Every examples comes with a configuration file allowing users to reproduce outputs.
These configarations files will produce iota²'s outputs in ``'/XXXX/IOTA2_TEST_S2/IOTA2_Outputs/Results'`` 
directory.

splitGroundTruth
----------------

By default this parameter is set to ``False``. Let's have a look at iota²'s outputs
if this parameter is set to ``True``. :download:`configuration <./config/config_splitGroundTruth.cfg>`

In iota²'s outputs, there is a directory named ``dataAppVal`` which contains by
tiles all learning and validation polygons. After launching iota², the dataAppVal directory
should contains two files : ``T31TCJ_seed_0_learn.sqlite`` and ``T31TCJ_seed_0_val.sqlite``.

.. Note:: files T31TCJ_seed_0_*.sqlite contains polygons for each models, here 
discriminate thanks the field ``region``.

As input dataBase was not split, the two files must contains the same number of features.
The entire dataBase is used to learn the model and to evaluate classifications. This kind 
of feature could be use if the validation comes from an external source.

ratio
-----

Unlike the ``splitGroundTruth``, the ``ratio`` parameter allow users to tune the
ratio between polygons dedicated to learn models to polygons used to evaluate 
classifications. By launching iota² with a the ratio parameter :download:`configuration <./config/config_ratio.cfg>` 

we can observe the content of files ``T31TCJ_seed_0_*.sqlite`` in the iota²'s
output directory ``dataAppVal``.

The input dataBase provided ``groundTruth.shp`` contains 26 features and 13
differents class. Then by setting the ratio at ``0.5``, files ``T31TCJ_seed_0_learn.sqlite`` 
and ``T31TCJ_seed_0_val.sqlite`` will contains 13 features each.

.. Warning:: the ratio is computed considering the number of polygons, not area.
    Then polygons belonging to a same class should almost cover the same surface. Also, 
    the ratio is processed by class and by models in order to keep the origin dataBase
    class repartition.

.. Note:: ``ratio:0.6`` mean ``60%`` of eligible polygons will be use to learn models 
and 40% to evaluate classifications


cloud_threshold
---------------

This parameter allow users to clean-up the dataBase from samples which can not 
be used to learn models or to evaluate classifications. The pixel validity is 
used to determine if samples are usable. Considering a remote acquisition, a valid
pixel is a pixel which is not under clouds, cloud's shadow or saturated. Thus, 
valid samples are samples which are more than ``cloud_threshold`` times consider 
as valid.

Let's observe the influence of the ``cloud_threshold`` parameter by launching the
`configuration file <./config/config_cloudThreshold.cfg>`

First, here is the tree from the ``features`` iota² output directory

.. code-block:: console

    features
    └── T31TCJ
        ├── CloudThreshold_2.dbf
        ├── CloudThreshold_2.prj
        ├── CloudThreshold_2.shp
        ├── CloudThreshold_2.shx
        ├── nbView.tif
        └── tmp
            ├── MaskCommunSL.dbf
            ├── MaskCommunSL.prj
            ├── MaskCommunSL.shp
            ├── MaskCommunSL.shx
            ├── MaskCommunSL.tif
            └── Sentinel2_T31TCJ_reference.tif

Let's open nbView.tif and CloudThreshold_2.shp files.

+--------------------------------------------------+--------------------------------------------------+
| .. figure:: ./Images/PixVal_Example.png          | .. figure:: ./Images/CloudThreshold_vector.png   |
|   :alt: Pixel validity raster                    |   :alt: Cloud threshold vector                   |
|   :scale: 50 %                                   |   :scale: 45 %                                   |
|   :align: center                                 |   :align: center                                 |
|                                                  |                                                  |
|   Pixel validity raster                          |   Cloud threshold vector                         |
+--------------------------------------------------+--------------------------------------------------+

As you can noticed, every pixels in the validity raster which is ``superior or equal``
to the parameter ``cloud_threshold`` value (here 2) belong to a geometry in the 
vector file CloudThreshold_2.shp. Next available polygons are the ones resulting
from the intersection of the CloudThreshold_2.shp vector file and the input dataBase.


sampleSelection
---------------

some text

sampleAugmentation
------------------

some text
