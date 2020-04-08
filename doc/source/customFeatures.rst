Custom Features
===============

What is the custom features module ?
------------------------------------

This module propose to use an external code, to compute additional features which will be used for classification.

By default, and if possible depending on sensors, iota2 computes three spectral indices: NDVI, NDWI and Brightness.

But it will be usefull for particular application case to compute NDSI or RED_EDGE for instance. Now it will be simple to add these features.

How use it ?
------------
The custom features module require only one python file, containing one or more functions.

The user must provide, using the configuration file, the path to this file, it's name, and the list of functions to be computed.

It is necessary to add the field ``Features`` to your configuration file.

To activate the custom features mode, there are two mandatory parameters:

``module``
    the full path to the file containing source code. Ending by ".py" is mandatory

``functions``
    the list of functions to be computed, separated by space

There are three optional parameters, initialized by default:

``chunk_size_mode``
    The split image mode. It can be ``split_number`` for divide the image according to the number given or ``user_fixed`` for work on chunk size indicated by parameters
``number_of_chunks``
    the number of chunks used to split input data and avoid memory overflow. Mode ``split_number`` only
``chunk_size_x`` and ``chunk_size_y``
    give a chunk size according to axis x and y

Once this field is correctly filled, launch iota2 as usual.

Coding custom features function:
--------------------------------
Before explaining how a custom features must be coded, some explaination about available tools.

iota2 provides two classes used for custom features:

``custom_numpy_features``
    the high level class, used in the iota2 processing. This class use the configuration file parameters to apply the user provided functions. For a standard use, the class has no interest for the user.

``data_container``
    this class provides functions to access data. The available methods change according to the sensors used.

To have a exhaustive list of available functions, it is possible to instanciate the ``data_container`` class, using a sensors parameters dictionnary and a tile name.

All functions contained in ``data_container`` are named as : ``get_sensors-name_Bx``, where ``x`` is the name of bands available in each sensor.

For instance for Sentinel2 (theia format) it is possible to get all pixels corresponding to the band 2 with ``get_Sentinel2_B2()`` function.
It is also possible to use iota2 default spectral indices, like NDVI. In this case, the get function is named ``get_Sentinel2_NDVI``.


Then, the function provided by user, must use these function get and produce a numpy array. The function must return also a list of label name (or empty for default naming). See examples below for a better understanding.

Recommendations:
----------------
A simply way to know whose get functions are available is to create a data container object like in the folowing example.

.. code-block:: python

        def print_get_methods(config_file: str, tile: str, output_path: str):
            """
            This function print the list of methods available to access data
            """
            from iota2.Common import customNumpyFeatures as CNF
            from iota2.Common import ServiceConfigFile as SCF

            # At this stage, the tile name no matter as it only used to
            # create the dictionary. This dictionary is the same for all tiles.
            sensors_parameters = SCF.iota2_parameters(
            config_file).get_sensors_parameters(tile)

            data_cont = CNF.data_container(tile, output_path, sensors_parameters)

            # This line show you all get methods available
            print(dir(data_cont))

Example:
--------
A full example for using custom features, using Sentinel2.

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

In the configuration file, add the following block to enable custom feature mode

.. code-block:: python
		
	...
    Features:
    {
        module:"path/to/module/my_module.py"
        functions:"get_soi"
        chunk_size_mode:"split_number"
        number_of_chunks:50
    }
