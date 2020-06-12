External Features
=================

What is the external features module ?
--------------------------------------

This module proposes to use user-provided code to compute additional features which will be used for training and prediction.

By default, and if possible depending on sensors, iota2 computes three spectral indices: NDVI, NDWI and Brightness. Additional radiometric features can also be provided using the ``additionalFeatures`` field in the configuration file.

However, features more complex than simple radiometric indices may need the ability to write some code. This module allows to compute these kind of features.

The main idea is to extract the pixel values as a numpy array, so it is easy to compute everything you want.


How use it ?
------------
The external features module requires only one python file, containing one or more functions.

The user must provide, using the configuration file, the path to this file, it's name, and the list of functions to be computed.

It is necessary to add the section ``Features`` to your configuration file.

To activate the external features mode, there are two mandatory parameters:

``module``
    the full path to the file containing source code. A ".py" extension is mandatory

``functions``
    the list of functions to be computed, separated by spaces

There are three optional parameters, initialized by default:

``chunk_size_mode``
    The split image mode. It can be ``split_number`` for dividing the image according to the number given or ``user_fixed`` for working with the chunk size indicated by parameters
``number_of_chunks``
    the number of chunks used to split input data and avoid memory overflow. Mode ``split_number`` only
``chunk_size_x`` and ``chunk_size_y``
    give a chunk size according to axis x and y

Once this field is correctly filled, iota2 can be run as usual.

Coding external features functions:
-----------------------------------
Before explaining how external features must be coded, some explainations about the available tools.

iota2 provides two classes used for external features:

``external_numpy_features``
    the high level class, used in the iota2 processing. This class uses the configuration file parameters to apply the user provided functions. For a standard use, the class has no interest for the user.

``data_container``
    this class provides functions to access data. The available methods change according to the sensors used.

To have an exhaustive list of available functions, it is possible to instanciate the ``data_container`` class, using a sensors parameters dictionnary and a tile name.

All functions contained in ``data_container`` are named as : ``get_sensors-name_Bx``, where ``x`` is the name of bands available in each sensor.

For instance for Sentinel2 (Theia format) it is possible to get all pixels corresponding to the band 2 with ``get_Sentinel2_B2()`` function. The returned numpy array is the complete time series for the corresponding spectral band. 
It is also possible to use iota2 default spectral indices, like NDVI. In this case, the get function is named ``get_Sentinel2_NDVI``.


Then, the function provided by the user must use these functions to get and produce a numpy array. The function must return also a list of label names (or empty for default naming). See examples below for a better understanding.

Recommendations:
----------------
A simple way to know which ``get`` functions are available, is to create a data container object like in the folowing example.

.. code-block:: python

        def print_get_methods(config_file: str, tile: str, output_path: str):
            """
            This function prints the list of methods available to access data
            """
            from iota2.Common import customNumpyFeatures as CNF
            from iota2.Common import ServiceConfigFile as SCF

            # At this stage, the tile name does not matter as it only used to
            # create the dictionary. This dictionary is the same for all tiles.
            sensors_parameters = SCF.iota2_parameters(
            config_file).get_sensors_parameters(tile)

            data_cont = CNF.data_container(tile, output_path, sensors_parameters)

            # This line show you all get methods available
            print(dir(data_cont))

Example:
--------
A full example for using external features, using Sentinel2.

First, create a python file, named ``my_module.py`` containing one function:

.. code-block:: python
				
        def get_soi(self):
            """
            compute the Soil Composition Index
            """
            coef = (self.get_Sentinel2_B11() - self.get_Sentinel2_B8()) / (
            self.get_Sentinel2_B11() + self.get_Sentinel2_B8())
            labels = [f"soi_{i+1}" for i in range(coef.shape[2])]
            return coef, labels

In the configuration file, add the following block to enable external feature mode

.. code-block:: python
		
	...
    external_features:
    {
        module:"path/to/module/my_module.py"
        functions:"get_soi"
        chunk_size_mode:"split_number"
        number_of_chunks:50
    }

Limitations:
------------
.. warning::
    External features can not be used with ``userFeatures`` sensors.
	Indeed, it is mandatory to have the bands information to provide the ``get`` methods.
	Also, ``Sentinel-1`` is not accessible in the external features workflow.

	Addtionnaly, scikit-learn models can not be use with this feature as well as the auto-context workflow.
