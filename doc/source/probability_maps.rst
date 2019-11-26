Probability map
###############

Probability maps are rasters containing as bands as class. Each band reprensents 
the probability of belonging to a given class in [0; 1000] range. Bands are ordered
from the lower to the greater integer label.

Parameters involved
===================

+-----------------------+------------------+--------------------------+--------------+------------------------------------------+
|Parameter Key          |Parameter section |Parameter Type            |Default value |Parameter purpose                         |
+=======================+==================+==========================+==============+==========================================+
|enable_probability_map |argClassification |Boolean                   | False        |enable the probability map generation     |
+-----------------------+------------------+--------------------------+--------------+------------------------------------------+

Parameters compatibility
========================

The probability maps can only be generated if the shark classifier is used during 
the run.

.. Warning:: 
    if ``enable_probability_map`` is ``True`` then ``classifier`` must be ``'sharkrf'``

Additionnal outputs
===================

Each classifications will generate it own probability map called ``PROBAMAP_TT_model_MM_seed_SS.tif``
in ``classif`` output iota² directory where TT is the tile's name MM the model's name
and SS the seed number. Once all generated, they are merged under the
``ProbabilityMap_seed_SS.tif`` name into the ``final`` directory.

Internal choices
================

In some case, there is many classifier decisions to a given pixel. This section
detail internal choices in order to provide a probability map without NoData labels.

Post-classification fusion
**************************

By enabling the ``dempster_shafer_SAR_Opt_fusion`` parameter flag, iota² will
class each pixels invoking the model built thanks to SAR data and the one built
by using optical data. Then, the dempster-shafer is used to attribute the final decision.

Here is the rules to attribute the vector of probability to each pixels

Consider :
    :math:`p`: the pixel of interest
    
    :math:`ProbaMapSAR`: the probability map provided by the SAR model
    
    :math:`ProbaMapOpt`: the probability map provided by the optical model
    
    :math:`ProbaMapOut`: the output probability map
    
    :math:`DS`: the dempster-shafer choice
    
    :math:`DS(p)` in :math:`{0, 1, 2, 3}`
        
        0 : no decision
        
        1 : choice is both
        
        2 : choice is SAR
        
        3 : choice is Optical

Then :
    :math:`ProbaMapOut(p) = 0` if :math:`DS(p) = 0`
    
    :math:`ProbaMapOut(p) = ProbaMapSAR(p)` if :math:`DS(p) = 2`
    
    :math:`ProbaMapOut(p) = ProbaMapOpt(p)` if :math:`DS(p) = 3`
    
    :math:`ProbaMapOut(p) = ProbaMapOpt(p)` if :math:`DS(p) = 1` and :math:`max(ProbaMapOpt(p)) > max(ProbaMapSAR(p))`
    
    :math:`ProbaMapOut(p) = ProbaMapSAR(p)` if :math:`DS(p) = 1` and :math:`max(ProbaMapSAR(p)) > max(ProbaMapOpt(p))`


Too huge regions
****************

Using both parameters ``classifMode`` to ``'separate'`` and ``mode_outside_RegionSplit`` to an integer value, 
many models will be built to a given region. Then each models will votes to each pixels inside the region and 
some fusion rules are involved. Here is the probability maps fusion rule :

the probability of a given class is the mean of all probability provided by each classifier.

Developers corner
=================

Some unittests are involved by probability maps generation

Tests
*****

UnitTests.ClassificationsTests.test_reorder_proba_map

UnitTests.OpticalSARFusionTests.test_compute_probamap_fusion
