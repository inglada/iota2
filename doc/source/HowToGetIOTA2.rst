How to get iota2 ?
==================

Licence
-------

:abbr:`iota2 (Infrastructure pour l'Occupation des sols par Traitement Automatique Incorporant les Orfeo Toolbox Applications)`
is a free software under the GNU Affero General Public License v3.0. See `here <http://www.gnu.org/licenses/agpl.html>`_ 
for details.

How to install iota2 ?
----------------------

iota2 is only tested on some Linux distributions : Ubuntu and CentOS.
In order to install iota² and its dependencies easily, it is distributed through the package management system `Conda`.
In this section, steps to install iota² from scratch will be detailed.

**Step 1 :** download and install Miniconda

If Miniconda or Anaconda is already install on your system, you can skip this step. 
Otherwise, you can download and install Miniconda thanks to the 
`bash installer <https://conda.io/en/latest/miniconda.html>`_ (2 minutes) even if 
your are not the system administrator.

**Step 2 :** add iota²'s channel

Add the iota²'s channel to inform Conda where iota²'s packages are. This information 
has to be added in the ``.condarc`` file. In order to locate the file, please enter the following 
command :

.. code-block:: console

    conda info

then a list of informations are printed, especially :

.. code-block:: console

    active environment : None
            shell level : 0
       user config file : /absolute/path/to/.condarc
 populated config files : /absolute/path/to/.condarc
          conda version : 4.7.10
    conda-build version : 3.18.2
    ...

.. Note:: maintain conda up to date thanks ``conda update conda`` command

Once the ``.condarc`` file is located, you must add the following in it.

.. code-block:: console

    channel_priority: true
    channels:
        - iota2
        - conda-forge
        ...
    ...

**Step 3 :** get iota²'s package and install it

.. code-block:: console

    # create an empty conda environment : iota2-env
    conda create --name iota2-env

    # install iota2 in iota2-env (it could take a few hours)
    conda install -c iota2 iota2 -n iota2-env

    
How to test the installation ?
------------------------------

You can test the installation by following the :doc:`tutorial <IOTA2_Example>`.
