IOTA² input parameters
######################

IOTA² is fully configurable by using one file given to IOTA² at launch.
This file is called the 'configuration file' throughout the documentation.
This section is dedicated to the description of each parameter in it.

IOTA² parameters are split in 4 families: ``chain``, ``argTrain``,
``argClassification``, ``GlobChain`` and ``coregistration``. 

chain available parameters
**************************

chain.outputPath
================
*Description*
    Absolute path to the output folder. It is recommended to have one folder by run of the chain
*Type*
    string
*Default value*
    ``mandatory``
*Example*
    outputPath : '/absolute/path/to/IOTA2_output/' 
*Notes*
    the target directory will be created by IOTA²

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.remove_outputPath
=======================
*Description*
    if set to True, remove the directory in the field 'outputPath'
*Type*
    bool
*Default value*
    ``mandatory``
*Example*
    remove_outputPath : True

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.nomenclaturePath
======================
*Description*
    absolute path to the nomenclature description file
*Type*
    string
*Default value*
    ``mandatory``
*Example*
    nomenclaturePath : '/to/Nomenclature.csv'
*Notes*
    the nomenclature file is the way IOTA² establishes the link between
    the verbose class name and their labels. The file contents must respect
    the following syntax:
    
    .. code-block:: console
    
        my_crop_class:1
        my_urbain_class:2
        ...

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.listTile
==============
*Description*
    list of tiles to process
*Type*
    string
*Default value*
    ``mandatory``
*Example*
    listTile : 'D0003H0001 D0008H0004'
*Notes*
    tiles in the list must be separated by one space character

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.L8Path
============
*Description*
    absolute path to Landsat-8 images comming from THEIA
*Type*
    string
*Default value*
    'None'
*Example*
    L8Path : '/to/L8/Path/'
*Notes*
    see the note about tiled sensors data storage : :ref:`tiled data storage`

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.L8Path_old
============
*Description*
    absolute path to Landsat-8 images comming from old THEIA format (D*H*)
*Type*
    string
*Default value*
    'None'
*Example*
    L8Path_old : '/to/L8_old/Path/'
*Notes*
    see the note about tiled sensors data storage : :ref:`tiled data storage`

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.L5Path_old
============
*Description*
    absolute path to Landsat-5 images comming from old THEIA format (D*H*)
*Type*
    string
*Default value*
    'None'
*Example*
    L5Path : '/to/L5/Path/'
*Notes*
    see the note : :ref:`tiled data storage`

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.S2Path
============
*Description*
    absolute path to  Sentinel_2 images (THEIA format)
*Type*
    string
*Default value*
    'None'
*Example*
    S2Path : '/to/S2/path/'
*Notes*
    see the note about tiled sensors data storage : :ref:`tiled data storage`

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.S2_output_path
====================
*Description*
    Sentinel-2 data need some pre-processing whose results are 
    written to disk for efficiency purposes. Usually, these data are stored next to
    raw images provided by the user. The field ``S2_output_path`` allows to
    store these data in a directory of your choice.
*Type*
    string
*Default value*
    None
*Example*
    S2_output_path : '/absolute/path/to/StorageDirectory'

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.S2_S2C_Path
=================
*Description*
    absolute path to  Sentinel_2 images (Sen2Cor format)
*Type*
    string
*Default value*
    'None'
*Example*
    S2Path : '/to/S2/path/'
*Notes*
    see the note about tiled sensors data storage : :ref:`tiled data storage`

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.S2_S2C_output_path
========================
*Description*
    Sentinel-2 data need some pre-processing whose results are 
    written to disk for efficiency purposes. Usually, these data are stored next to
    raw images provided by the user. The field ``S2_S2C_output_path`` allows to
    store these data in a directory of your choice.
*Type*
    string
*Default value*
    None
*Example*
    S2_S2C_output_path : '/absolute/path/to/StorageDirectory'

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.S1Path
============
*Description*
    absolute path to the configuration file needed for Sentinel-1 data
*Type*
    string
*Default value*
    'None'
*Example*
    S1Path:'/path/to/SAR_data.cfg'
*Notes*
    see the documentation about how to fill-up the Sentinel-1 configuration file 
    (comming soon)

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.userFeatPath
==================
*Description*
    absolute path to the user's features path (they must be stored by tiles)
*Type*
    string
*Default value*
    'None'
*Example*
    userFeatPath:'/../../MNT_L8Grid'
*Notes*
    see the note about tiled sensors data storage : :ref:`tiled data storage`

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. _groundTruth:

chain.groundTruth
=================

*Description*
    absolute path to ground truth 
*Type*
    string
*Default value*
    ``mandatory``
*Example*
    groundTruth : '/to/my/groundTruth.shp'
*Notes*
    the ground truth file must respect the following rules

    1. It must be a shapeFile (.shp)
    2. The file must contain an integer field to descriminate features which belong to the same class
    3. Geometries hav to be of ``POLYGON`` type
    4. No overlapping between polygons

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.dataField
===============
*Description*
    field name discriminating features which belong to the same class in
    ground truth
*Type*
    string
*Default value*
    ``mandatory``
*Example*
    dataField : 'My_integer_field' 
*Notes*
    that field must contain integer

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.regionPath
================
*Description*
    absolute path to the shapeFile containing regions for spatial stratification
*Type*
    string
*Default value*
    None
*Example*
    regionPath : '/to/my/region.shp'
*Notes*
    The use of this field enables IOTA² to generate one model per region.
    The purpose of this feaure is highlighted by the example : :ref:`two-zones`

    the regions file must respect the following rules

    1. It must be a shapeFile (.shp)
    2. The file must contain an string field to descriminate regions
    3. Geometries have to be ``POLYGON`` or ``MULTIPOLYGON``
    4. No overlapping between polygons

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.regionField
=================
*Description*
    field that discriminates regions into the region shapeFile
*Type*
    string
*Default value*
    None
*Example*
    regionField : 'My_string_region'
*Notes*
    that field must contain string

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.runs
==========
*Description*
    number of random samples for training and validation
*Type*
    int
*Default value*
    1
*Example*
    runs : 1
*Notes*
    must be an integer greater than 0

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.logFileLevel
==================
*Description*
    logging level, 5 levels are available : "CRITICAL"<"ERROR"<"WARNING"<"INFO"<"DEBUG"
*Type*
    string
*Default value*
    'INFO'
*Example*
    logFileLevel:"DEBUG"

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.enableConsole
===================
*Description*
    enable console logging
*Type*
    bool
*Default value*
    False
*Example*
    enableConsole:False

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.colorTable
================
*Description*
    absolute path to the file wich link classes and their colors
*Type*
    string
*Default value*
    ``mandatory``
*Example*
    colorTable:'/path/to/MyColorFile.txt'
*Notes*
    The color file is the way IOTA² establishes the link between
    the class label and it's color (useful for vizualisation). It must
    respect the following syntax :
    
    .. code-block:: console
    
        0 255 255 255
        10 255 85 0
        11 255 85 0
        ...

    here the class 0 has the RGB code 255 255 255, the class 10 : 255 85 0 etc...

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.mode_outside_RegionSplit
==============================
*Description*
    This parameter is available if regionPath is used and argClassification.classifMode
    is set to ``fusion``. It represents the maximum size covered by a region.
    If the regions are larger than this threshold, then N models are built
    by randomly selecting features inside the region.
*Type*
    float
*Default value*
    0.1
*Example*
    mode_outside_RegionSplit : 0.001
*Notes*
    the threshold is expressed in km²

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.ratio
===========
*Description*
    ratio between training and validation sets
*Type*
    float
*Default value*
    0.5
*Example*
    ratio : 0.6
*Notes*
    must be a float between ]0;1[

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.cloud_threshold
=====================
*Description*
    To train models, IOTA² will use **only**, polygons (or part of them)
    which are "seen" at least 'cloud_treshold' times. A valid area is a
    zone which is not covered by clouds or cloud's shadows and which is 
    not saturated.
*Type*
    int
*Default value*
    1
*Example*
    cloud_threshold:1
*Notes*
    must be an integer >= 0

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.firstStep
===============
*Description*
    parameter used to restart the chain from a specific step
*Type*
    string
*Default value*
    'init'
*Example*
    firstStep:'init'
*Notes*
    Must be chosen into the list of available steps.

    Available choices are 'init', 'sampling', 'learning', 'classification',
    'mosaic', 'validation', 'regularisation', 'vectorisation' or 'lcstatistics'

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.lastStep
==============
*Description*
    parameter used to stop the chain at a specific step
*Type*
    string
*Default value*
    'validation'
*Example*
    firstStep:'learning'
*Notes*
    Must be chosen into the list of available steps.

    Available choices are 'init', 'sampling', 'learning', 'classification',
    'mosaic', 'validation', 'regularisation', 'vectorisation' or 'lcstatistics'

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.merge_final_classifications
=================================
*Description*
    flag to set in order to compute a raster which is the fusion of final classifications (one by run)
*Type*
    bool
*Default value*
    False
*Example*
    merge_final_classifications:True
*Notes*
    the fusion of classifications is saved under the name : ``Classifications_fusion.tif``

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.merge_final_classifications_ratio
=======================================
*Description*
    percentage of samples to use in order to evaluate the fusion raster
*Type*
    float
*Default value*
    0.1
*Example*
    merge_final_classifications_ratio:0.1
*Notes*
    IOTA² will extract, for each models, a percentage of samples before the
    learning/validation split.

    percentage must be between ``]0; 1[``

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.merge_final_classifications_undecidedlabel
================================================
*Description*
    fusion of classifications can produce undecisions (in the case of a tie in voting), this field is the
    label for undecisions
*Type*
    int
*Default value*
    255
*Example*
    merge_final_classifications_undecidedlabel:255

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.merge_final_classifications_method
========================================
*Description*
    fusion of classifications method
*Type*
    string
*Default value*
    'majorityvoting'
*Example*
    merge_final_classifications_method : 'dempstershafer'
*Notes*
    Their are two choices: 'majorityvoting' or 'dempstershafer'

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.dempstershafer_mob
========================
*Description*
    If ``merge_final_classifications`` is set to ``True``, and
    ``merge_final_classifications_method`` is set to ``'dempstershafer'``,
    define the Dempster Shafer's mass of belief estimation method
*Type*
    string
*Default value*
    'precision'
*Example*
    dempstershafer_mob : 'kappa'
*Notes*
    Available choice are : 'precision', 'recall' , 'accuracy' or 'kappa'

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.keep_runs_results
=======================
*Description*
    If ``merge_final_classifications`` is set to ``True``, two final reports can
    be computed. One by seed classification and one evaluating the fusion
    of classifications. If this flag is set to ``False``, then the computation
    of seed results is not done. 
*Type*
    bool
*Default value*
    True
*Example*
    keep_runs_results:True

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.fusionOfClassificationAllSamplesValidation
================================================
*Description*
    Available if ``merge_final_classifications`` is set to ``True``.
    If fusionOfClassificationAllSamplesValidation is ``True``, the validation of
    fusion of classifications will be done with the entire set of available
    samples in :ref:`groundTruth`
*Type*
    bool
*Default value*
    False
*Example*
    fusionOfClassificationAllSamplesValidation : True

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.remove_tmp_files
======================
*Description*
    IOTA² produces a lot of data before being able to compute final 
    classifications. This flag is used to remove all temporary directories
    (ie : containing models, classifications...) and to keep final results only.
*Type*
    bool
*Default value*
    False
*Example*
    remove_tmp_files : True

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.outputStatistics
======================
*Description*
    flag used to genererate additionnal statistics (confidence by learning / validation pixels)
*Type*
    bool
*Default value*
    False
*Example*
    outputStatistics:True
*Notes*
    outputs are addtionals PNG files under /final directory

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.enableCrossValidation
===========================
*Description*
    flag used to enable cross validation mode
*Type*
    bool
*Default value*
    False
*Example*
    enableCrossValidation : True
*Notes*
    Folds number is given by the field 'runs'

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.splitGroundTruth
======================
*Description*
    Flag used to allow IOTA² to split ground truth. If set to ``False`` then
    the chain will use all polygons to train models and for validation.
*Type*
    bool
*Default value*
    True
*Example*
    splitGroundTruth : False

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.jobsPath
==============
*Description*
    Absolute path to a directory used to store job scripts
*Type*
    string
*Default value*
    None
*Example*
    jobsPath : '/path/JobsDirectory'
*Notes*
    The directory must exists before the launch of IOTA²

    ``only available`` if IOTA² is launch using ``Iota2Cluster.py``

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

chain.OTB_HOME
==============
*Description*
    absolute path to the OTB installation directory
*Type*
    string
*Default value*
    'None'
*Example*
    OTB_HOME : 'MyOTBInstall'
*Notes*
    ``only available`` if IOTA² is run using ``Iota2Cluster.py``

.. _tiled data storage:

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

About tiled data storage
=========================

Sensor data must be stored by sensor / tile / date as the following tree

    .. code-block:: console

        ├── Sentinel2_MAJA
        │   ├── T31TCJ
        │   │   ├── SENTINEL2A_20180511-105804-037_L2A_T31TCJ_D_V1-7
        │   │   │   ├── MASKS
        │   │   │   │   └── *.tif
        │   │   │   └── *.tif
        │   │   └── SENTINEL2A_20180521-105702-711_L2A_T31TCJ_D_V1-7
        │   │       ├── MASKS
        │   │       │   └── *.tif
        │   │       └── *.tif
        │   ├── ...
        │   └── T31TDK
        │       └── ...
        ├── Sentinel2_Sen2Cor
        │   ├── T31TCJ
        │   ├── ...
        │   └── T31TDK
        │       └── ...
        ├── LandSat8
        │   ├── D0005H0002
        │   ├── ...
        │   └── D0005H0008
        ├── ...

argTrain available parameters
*****************************

argTrain.dempster_shafer_SAR_Opt_fusion
=======================================
*Description*
    IOTA² can process optical and SAR data to produce land cover maps.
    This data can be mixed together to train a single model, or one model
    per sensor.
*Type*
    bool
*Default value*
    False
*Example*
    dempster_shafer_SAR_Opt_fusion : True
*Notes*
    IOTA² implement the Dempster-Shafer fusion rule to choose labels
    comming from SAR and optical maps.
    A fully detailed example is available :doc:`here <SAR_Opt_postClassif_fusion>`

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. _refSampleSelection:

argTrain.sampleSelection
========================
*Description*
    This field parameters the strategy of polygon sampling. It directly refers to
    options of OTB's `SampleSelection <https://www.orfeo-toolbox.org/CookBook/Applications/app_SampleSelection.html>`_ 
    application.
*Type*
    dictionnary
*Default value*
    .. code-block:: python
    
        {"sampler":"random", "strategy":"all"}
*Example*
    .. code-block:: python
    
        sampleSelection : {"sampler":"random",
                           "strategy":"percent",
                           "strategy.percent.p":0.2,
                           "per_models":[{"target_model":"4",
                                          "sampler":"periodic"}]
                           }
*Notes*
    In the example above, all polygons will be sampled with the 20% ratio. But 
    the polygons which belong to the model 4 will be periodically sampled,
    instead of the ransom sampling used for other polygons.
    
    Notice than ``per_models`` key contains a list of strategies. Then we can imagine
    the following :
    
    .. code-block:: python
    
        sampleSelection : {"sampler":"random",
                           "strategy":"percent",
                           "strategy.percent.p":0.2,
                           "per_models":[{"target_model":"4",
                                          "sampler":"periodic"},
                                         {"target_model":"1",
                                          "sampler":"random",
                                          "strategy", "byclass",
                                          "strategy.byclass.in", "/path/to/myCSV.csv"
                                         }]
                           }

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

argTrain.sampleAugmentation
===========================
*Description*
    In supervised classification the balance between class samples is important. There are
    many ways to manage class balancing in IOTA², using :ref:`refSampleSelection` or 
    the classifier's options to limit the number of samples by class.
    
    An other approch is to generate synthetic samples. It is the purpose of this
    functionality, which is called "sample augmentation".
*Type*
    dictionnary
*Default value*
    .. code-block:: python
    
        {"activate":False}

*Example*
    .. code-block:: python

        sampleAugmentation : {"target_models":["1", "2"],
                              "strategy" : "jitter",
                              "strategy.jitter.stdfactor" : 10,
                              "strategy.smote.neighbors"  : 5,
                              "samples.strategy" : "balance",
                              "activate" : True
                              }
*Notes*
    IOTA² implements an interface to the OTB `SampleAugmentation <https://www.orfeo-toolbox.org/CookBook/Applications/app_SampleSelection.html>`_ application.
    There are three methods to generate samples : replicate, jitter and smote.
    The documentation :doc:`here <sampleAugmentation_explain>` explains the difference between these approaches.
    
    ``samples.strategy`` specifies how many samples must be created.
    There are 3 different strategies:

        - minNumber
            To set the minimum number of samples by class required
        - balance
            balance all classes with the same number of samples as the majority one
        - byClass
            augment only some of the classes

    Parameters related to ``minNumber`` and ``byClass`` strategies are
    
        - samples.strategy.minNumber
            minimum number of samples
        - samples.strategy.byClass
            path to a CSV file containing in first column the class's label and 
            in the second column the minimum number of samples required.

    In the above example, classes of models "1" and "2" will be augmented to the
    the most represented class in the corresponding model using the jitter method.

argTrain.sampleManagement
=========================
*Description*
    absolute path to a CSV file containing samples transfert strategies
*Type*
    string
*Default value*
    None
*Example*
    .. code-block:: python

        sampleManagement : '/absolute/path/myRules.csv'

        >>> cat /absolute/path/myRules.csv
                1,2,4,2

        Mean:

        +--------+-------------+------------+----------+
        | source | destination | class name | quantity |
        +========+=============+============+==========+
        |   1    |      2      |      4     |     2    |
        +--------+-------------+------------+----------+

argTrain.classifier
===================
*Description*
    OTB's classifier name
*Type*
    string
*Default value*
    ``mandatory``
*Example*
    .. code-block:: python

        classifier : 'rf'

argTrain.options
================
*Description*
    OTB's classifier's options
*Type*
    string
*Default value*
    ``mandatory``
*Example*
    .. code-block:: python

        options : ' -classifier.rf.min 5 -classifier.rf.max 25 '

Sensors available parameters
****************************

Sensors available list : Landsat5_old / Landsat8 / Landsat8_old / Sentinel_2 / Sentinel_2_S2C / Sentinel_2_L3A

Sensor.full_pipline
===================
*Description*
    Only available to Sentinel_2 / Sentinel_2_S2C / Sentinel_2_L3A sensors.
    If set to False, then IOTA² will write date's stack on disk to improve computations.
    Else, every computation will be done in RAM, saving disk space.
*Type*
    bool
*Default value*
    False
*Example*
    .. code-block:: python

        full_pipline : True

Sensor.startDate
================
*Description*
    first insterpolation date
*Type*
    string
*Default value*
    None
*Example*
    .. code-block:: python

        startDate : '20170131'

Sensor.endDate
==============
*Description*
    last insterpolation date
*Type*
    string
*Default value*
    None
*Example*
    .. code-block:: python

        endDate : '20170131'

Sensor.temporalResolution
=========================
*Description*
    Temporal resolution, time between two interpolations
*Type*
    int
*Default value*
    None
*Example*
    .. code-block:: python

        temporalResolution : 10

Sensor.additionalFeatures
=========================
*Description*
    IOTA² allow adding features by dates. Format is the one provided by OTB's BandMath 
    application.

*Type*
    string
*Default value*
    None
*Example*
    .. code-block:: python

        additionalFeatures : 'b1+b2,(b1-b2)/(b1+b2)'
*Notes*
    Custom features must be coma separated.

Sensor.keepBands
================
*Description*
    List of bands to use in the IOTA² run.
*Type*
    list
*Default value*
    all available bands
*Example*
    .. code-block:: python

        keepBands:["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"] # Sentinel-2 case

coregistration available parameters
**************************

coregistration.VHRPath
======================
*Description*
    absolute path to VHR image
*Type*
    string
*Default value*
    'None'
*Example*
    VHRPath: 'path/to/the/VHR.tif'

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

coregistration.dateVHR
======================
*Description*
    date ``YYYYMMDD`` of the VHR image
*Type*
    string
*Default value*
    'None'
*Example*
    dateVHR: '20180601'
*Notes*
    The ``dateVHR`` is used to find automatically the best image of the timeseries for coregistration

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

coregistration.dateSrc
======================
*Description*
    date ``YYYYMMDD`` of the 
*Type*
    string
*Default value*
    'None'
*Example*
    dateSrc: '20180601'
*Notes*
    If no ``dateSrc`` is mentionned, the best image will be automatically choose for coregistration

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

coregistration.bandRef
======================
*Description*
    Number of the band of the VHR image to use for coregistration
*Type*
    int
*Default value*
    1
*Example*
    bandRef: 1

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

coregistration.bandSrc
======================
*Description*
    Number of the band of the src raster to use for coregistration
*Type*
    int
*Default value*
    3
*Example*
    bandSrc: 3

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

coregistration.resample
=======================
*Description*
    Resample the reference and the source raster to the same resolution to find sift points
*Type*
    bool
*Default value*
    True
*Example*
    resample: True

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

coregistration.step
===================
*Description*
    Initial size of steps between bins in pixels
*Type*
    int
*Default value*
    256
*Example*
    step: 256

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

coregistration.minstep
======================
*Description*
    Minimal size of steps between bins in pixels
*Type*
    int
*Default value*
    16
*Example*
    minstep: 16

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

coregistration.minsiftpoints
============================
*Description*
    Minimal number of sift points to find to create the new RPC model
*Type*
    int
*Default value*
    40
*Example*
    minsiftpoints: 40

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

coregistration.iterate
======================
*Description*
    Proceed several iterationby reducing the step between geobin to find sift points
*Type*
    bool
*Default value*
    True
*Example*
    iterate: True

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

coregistration.prec
===================
*Description*
    Estimated shift between source and reference raster in pixel (source raster resolution)
*Type*
    int
*Default value*
    3
*Example*
    prec: 3

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

coregistration.mode
===================
*Description*
    Coregistration mode of the timeseries:
        1: single coregistration between one source image (and its masks) and the VHR image
        2: this mode operates a coregistration between a image of the timeseries and the VHR image, then the same RPC model is used to orthorectify every images of the timeseries
        3: cascade mode, this mode operates a first coregistration between a source image and the VHR image, then each image of the timeseries is coregistered step by step with the closest temporal images of the timeseries already coregistered
*Type*
    int
*Default value*
    2
*Example*
    mode: 2

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

coregistration.pattern
======================
*Description*
    Pattern of the timeseries files to coregister
*Type*
    string
*Default value*
    'None'
*Example*
    pattern: '*STACK.tif'
*Notes*
    By default the value is left to ``'None'`` and the pattern depends on the sensor used (``*STACK.tif`` for Sentinel2, ``ORTHO_SURF_CORR_PENTE*.TIF``)