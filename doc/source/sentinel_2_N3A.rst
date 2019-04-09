Sentinel-2 Level 3A
###################

Description
***********

Levels 3A are a monthly syntheses of cloud surface refectances.
A short documentation about the product is available at `CESBIO's multitemp blog <http://www.cesbio.ups-tlse.fr/multitemp/?page_id=14019#English>`_.

Also, the `ESA's document <https://zenodo.org/record/1401360/files/DPM.pdf?download=1>`_ provide explanations about algorithms used to generate L3A products.

Download data
*************

Data are downloadable from : https://theia.cnes.fr

iota2's cook
************

Configuration file parameter
============================

``chain.S2_L3A_Path`` is the parameter to enable the use of L3A products

.. code-block:: python

        chain:
        {
            ...
            S2_L3A_Path:"/absolute/path/to/Storage_directory"
            ...
        }

Data storage
============

Data must be stored by tiles as the following tree : 

.. code-block:: console

    └── Storage_directory
        ├── T31TCJ
        │   ├── SENTINEL2X_20181015-000000-000_L3A_T31TCJ_D_V1-1
        │   │   ├── MASKS
        │   │   │   └── *.tif
        │   │   └── *.tif
        │   └── ...
        ├── T31TDJ
        │   └── ...
        └── ...

Where tiles are T31TCJ, T31TDJ ...

Data usage
==========

Time series
+++++++++++

Every dates are chronologically stacked together in order to provide a temporal
series to the learning / classification system. Then, if the configuration file
parameter ``GlobChain.useGapFilling`` is set to ``True``, the gapfilling is processed.

.. Note:: Every bands are resample to a 10m resolution.

GapFilling
++++++++++

GapFilling allow iota2 the interpolation of clouds and resample every tile's
temporal series on the same temporal grid. The cloud interpolation is based on
masks provided by L3A products. 

Masks usage
+++++++++++

A ``BINARY_MASK`` raster is generated for each L3A dates and place next to native data.
``BINARY_MASK`` is the raster provided to the gapFilling algorithm to know pixels
to interpolate by dates. iota2 use ``_FLG_R1.tif`` raster to determine pixels to flag as to be interpolated.
Every pixels under ``0`` and ``1`` respectively ``NODATA`` and ``Cloud / Cloud's shadow`` will be interpolated.

Features
++++++++

Once the gapFilling is done, if the configuration file
parameter ``GlobChain.features`` is different from ``[]`` then features are compute
from the the gapfilled time series. ``NDVI, NDWI and brightness`` are automatically
computed. Also, users could provide a set of features describe as a BandMath
expression using : ``Sentinel_2_L3A.additionalFeatures`` configuration file parameter.
By default every bands are use as features and use by the classification process to
find pixels label, but with the joint use of ``Sentinel_2_L3A.keepBands`` and 
``iota2FeatureExtraction.extractBands`` only targeted bands will be used.

Available bands
+++++++++++++++

Every bands provided by THEIA L3A product are availble.

.. code-block:: python

        Sentinel_2_L3A:
        {
            keepBands:["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"]
        }
