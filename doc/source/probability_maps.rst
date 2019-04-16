Probability map
###############

Probability maps are rasters containing as bands as class. Each band reprensents 
the probability of belonging to a given class in [0; 1000] range. Bands are ordered
from the lower to the greater integer label.

Parameters involved
===================

+-----------------------+--------------------------+--------------+------------------------------------------+
|Parameter Key          |Parameter Type            |Default value |Parameter purpose                         |
+=======================+==========================+==============+==========================================+
|enable_probability_map |Boolean                   | False        |enable the probability map generation     |
+-----------------------+--------------------------+--------------+------------------------------------------+

Parameters compatibility
========================

The probability maps can only be generated if the shark classifier is used during 
the run.

.. Warning:: 
    if enable_probability_map is True then classifier must be ``'sharkrf'``

Additionnal outputs
===================

Each classifications generate it own probability map called ``PROBAMAP_TT_model_MM_seed_SS.tif``
in ``classif`` output iota² directory where TT is the tile's name MM the model's name
and SS the seed number. Once they are all generated, they are merged under the
``ProbabilityMap_seed_SS.tif`` name into the ``final`` directory.

Developers corner
=================

Some unittests are involved by probability maps generation

Tests
*****

UnitTests.ClassificationsTests.test_reorder_proba_map

UnitTests.OpticalSARFusionTests.test_compute_probamap_fusion
