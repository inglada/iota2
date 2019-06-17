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
In this section, steps to install iota2 from scratch will be detailed.

We assume that installation will be done in the directory: ``MyInstall``

**Step 1 :** download iota2

.. code-block:: console

    cd MyInstall
    git clone -b develop https://framagit.org/iota2-project/iota2

Now you have the directory ``iota2`` in ``MyInstall`` which contains all iota2 source code.

**Step 2 :** get iota2 light dependencies

if you are using Ubuntu :

.. code-block:: console

     sudo ./MyInstall/iota2/install/init_Ubuntu.sh
    
if you are using CentOS :

.. code-block:: console

     sudo ./MyInstall/iota2/install/init_CentOS.sh

**Step 3 :** get OTB

.. code-block:: console

     sudo ./MyInstall/iota2/install/generation.sh --all

Then OTB ant its dependencies will be downloaded (around 5Gb) and installed. If you only want to download or install OTB, you could use options ``--update`` or ``--compil`` instead of ``--all``.
This step can be long (up to several hours depending on your hardware).

How to test the installation
----------------------------

iota2 tests are implemented using the unittest framework which is a well known Python library.
To check your iota2 install you should launch the commands below:

.. code-block:: console

    source /MyInstall/iota2/scripts/install/prepare_env.sh
    cd /MyInstall/iota2/scripts/Tests/UnitTests
    python -m unittest Iota2Tests

At the end, a short summary of the success/fail status of the tests is printed to the console. If everything is ok you will get something similar to this:

.. code-block:: console

    Ran 42 tests in 46.632s

    OK

In order to run iota2 to produce land cover maps you could follow one of these :doc:`examples. <IOTA2_Example>`

        
