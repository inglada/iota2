Playing with features in iota2
##############################

.. toctree::

Write outputs
*************

.. Note:: It is assumed that examples in :doc:`IOTA2_Example <IOTA2_Example>` were properly run.

The first steps of iota2 correspond to the definition of data cubes: all temporal acquisitions are stacked together. For instance, with 10 temporal acquisitions and 4 spectral bands, an hypercube of 40 spectro-temporal features is used for the processing. If needed, additionnal steps are required to handle irregular time sampling and clouds/shadows, such as describe in `https://www.mdpi.com/2072-4292/11/4/433`: this is a common situation when processing several Sentinel-2 tiles. Such steps will basically project all the data onto a same and regular sampletime (whose step is define by the variable ``Sensor.temporalResolution``). It is termed /Gapfilling/.

Because it can leads to a very large set of files, the default behavior of iota2 is to **not** write the temporal cubes used for the processing. Everythings are computed in memory (i.e., in the RAM), and only the necessary (or light) files are written to the hard drive. It also improves the processing time since writting data is time comsumming.

Off course, it is possible to tell iota2 to write outputs, for instance for further analysis. This feature is controled by the variable ``GlobChain.writeOutputs``. To do so, the variable must be set to ``True`` in the configuration file:

.. code-block:: python
		
		GlobChain:
		{
		# Your parameters
		writeOutputs:True
		}

With respect to the standard ouput, for each tile, the data cube before and after the gapfilling, and the complete cube of feature (spectral bands + spectral indices) after gapfilling are written. Using the same data than in :doc:`IOTA2_Example <IOTA2_Example>`, the folder /features/T31TCJ/tmp/ contains now 3 additional files after a proper run of iota2.

.. code-block:: console
		
		features/
		└── T31TCJ
		    ├── CloudThreshold_0.dbf
		    ├── CloudThreshold_0.prj
		    ├── CloudThreshold_0.shp
 		    ├── CloudThreshold_0.shx
		    ├── nbView.tif
		    └── tmp
		        ├── MaskCommunSL.dbf
                        ├── MaskCommunSL.prj
                        ├── MaskCommunSL.shp
                        ├── MaskCommunSL.shx
                        ├── MaskCommunSL.tif
                        ├── Sentinel2_T31TCJ_input_dates.txt
                        ├── Sentinel2_T31TCJ_interpolation_dates.txt
                        ├── Sentinel2_T31TCJ_MASKS.tif
                        ├── Sentinel2_T31TCJ_reference.tif
                        ├── Sentinel2_T31TCJ_TSG.tif
                        ├── Sentinel2_T31TCJ_TS.tif
                        └── T31TCJ_Features.tif


Select a subset of features
***************************

Default iota2' behavior is to use the spectral bands and compute few spectral indices. It is possible to select a few of them for the processing. For instance, with Sentinel-2 to use only the spectral bands at 10m/pixel the variable ``Sensor.keepBands`` can be changed to

.. code-block:: python
		
		Sentinel_2:
		{
		# Your parameters
		keepBands:["B2", "B3", "B4", "B8"]
		}

Also, the variable ``iota2FeatureExtraction.extractBands`` **must be** set to true:

.. code-block:: python

		iota2FeatureExtraction:
		{
		extractBands:True
		}

If you don't want the spectral indices, the variable ``GlobChain.features`` can be set to an empty list:

.. code-block:: python

		GlobChain:
		{
		# Your parameters
		features : []
		}

Note that it is possible to include additionnal spectral indices using the variable ``Sensor.additionalFeatures``. Again, it is possible to write such feature to the hard drive by setting ``GlobChain.writeOutputs`` to ``True``.

Use precomputed features
************************
Once the features have been written on the hard drive, it possible to use them in iota2 and saving pre-processing time. It also possible to include additionnal precomputed features such as elevation or any feature that match the spatial resolution and footprint of the data.

.. Warning:: It is up to you to check spatial coherence (resolution and footprint) of the provided data.

To tell iota2 to use your feature, your first have to specify the path to the data with the variable ``chain.userFeatPath``. 

.. code-block:: python

		chain
		{
		# Your parameters
		userFeatPath: "/path/to/the/features/"
		}

Then you have to explain to iota2 which features use and how to combine them with the other feature, this is done with the section ``userFeat``. Assuming you want to use the datacube written in the first section (/Sentinel2_T31TCJ_TSG.tif/) you have to make a folder corresponding to the tile T31TCJ (one folder per tile, as for Sentinel-2 original data sets) and copy the data:

.. code-block:: console
		
		/path/to/the/features/
		             └── T31TCJ
			         └── Sentinel2_T31TCJ_TSG.tif

.. Note:: You can use symbolic link 

Then, in the configuration file you should set the section as

.. code-block:: python

		userFeat:
		{
		arbo:"/*"
		patterns:"TSG"
		}

``arbo:"/*"`` tells iota2 to scan all the folders in the directory, and ``patterns:"TSG"`` tells iota2 to process files with the pattern "TSG" in their names. It is possible to provide a list of pattern, e.g., "TSG,MNT,NDVI".
