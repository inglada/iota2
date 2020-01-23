iota² and scikit-learn machine learning algorithms
##################################################

Iota2 is able to use some of machine learning algorithms coming from `scikit-learn <https://scikit-learn.org>`_ (more specially `ensemble methods <https://scikit-learn.org/stable/modules/classes.html#module-sklearn.ensemble>`_ and `SVC <https://scikit-learn.org/stable/modules/generated/sklearn.svm.SVC.html>`_).

This documentation exposes how configure iota2 in order to use scikit-learn library.

All scikit-learn parameters are available in the ``scikit_models_parameters`` section.
Some of them refer directly to scikit-learn models classifier parameters (keywordsArguments_).

Scikit-learn parameters table
*****************************

+----------------------------------+---------------+--------------+------------------------------------------------------------------------------------+
|Parameter Key                     |Parameter Type |Default value |Parameter purpose                                                                   |
+==================================+===============+==============+====================================================================================+
|standardization_                  |Boolean        | False        |Apply features standardization before learning and classification process           |
+----------------------------------+---------------+--------------+------------------------------------------------------------------------------------+
|cross_validation_parameters_      |Dictionary     | {}           |Range of estimator's parameters to be tested during cross-validation.               |
+----------------------------------+---------------+--------------+------------------------------------------------------------------------------------+
|cross_validation_grouped          |Boolean        | False        |If false, cross validation folds can contains mixed samples from different polygons |
+----------------------------------+---------------+--------------+------------------------------------------------------------------------------------+
|cross_validation_folds            |Integer        | 5            |Number of cross validation folds                                                    |
+----------------------------------+---------------+--------------+------------------------------------------------------------------------------------+
|model_type                        |String         | None         |scikit-learn classifier's name                                                      |
+----------------------------------+---------------+--------------+------------------------------------------------------------------------------------+
|keywordsArguments_                |               |              |                                                                                    |
+----------------------------------+---------------+--------------+------------------------------------------------------------------------------------+

.. _standardization:

About standardization
*********************

Standardize features by removing the mean and scaling to unit variance. 

.. Note:: The standardization implemented in iota2 comes from scikit-learn `StandardScaler <https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html>`_ method 
          and used will default values : StandardScaler(copy=True, with_mean=True, with_std=True)

.. _cross_validation_parameters:

Cross validation parameters
***************************

Cross validation [https://en.wikipedia.org/wiki/Cross-validation_(statistics)] is a method used to find the best optimized estimator's parameters according to a scorer function (overall-accuracy).
The user has to provide a list of estimator's parameters to optimize. This list
of parameters must be provided through a python dictionary. For instance , considering
a ``RandomForestClassifier`` machine learning classifier, the configuration file
could contains :

.. code-block:: python

    scikit_models_parameters:
    {
        model_type: "RandomForestClassifier"
        cross_validation_parameters: {'n_estimators': [50, 100, 150],
                                      'max_depth': [5, 10, 20]}
    }

Because ``n_estimators`` and ``min_samples_split`` are two parameters of `RandomForestClassifier <https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html#sklearn.ensemble.RandomForestClassifier>`_.
In this case, every couple in [50, 100, 150] and [5, 10, 20] will be tested and the best one, w.r.t the estimated scorer value,
will be used to build the RandomForestClassifier model.

.. Note:: The cross validation workflow implemented in iota2 comes from the scikit-learn `GridSearchCV <https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GridSearchCV.html>`_ method.

.. Note:: Once the cross validation is achieve, a text file call ``*_cross_val_param.cv`` is created next to models.
          This file contains every cross validation score for each parameters to optimize and the choosen parameters.

.. _keywordsArguments:

Model's keywords arguments
**************************

Every classifier from `ensemble methods <https://scikit-learn.org/stable/modules/classes.html#module-sklearn.ensemble>`_ and `SVC <https://scikit-learn.org/stable/modules/generated/sklearn.svm.SVC.html>`_ and are accessible in iota2,
each one with its own set of input parameters. For instance with the `RandomForestClassifier <https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html#sklearn.ensemble.RandomForestClassifier>`_, 
user can configure ``n_estimators``, ``criterion``, ``max_leaf_nodes`` etc.
Then the configuration file could contains :

.. code-block:: python

    scikit_models_parameters:
    {
        model_type: "RandomForestClassifier"
        criterion: "entropy"
        min_samples_split: 4
        
        cross_validation_parameters: {'n_estimators': [50, 100, 150],
                                      'max_depth': [5, 10, 20]}
    }

Configuration file example
**************************

Here is an example of a configuration file :download:`configuration <./config/config_scikitLearn.cfg>`
fully operational with the downloadable `data-set <http://osr-cesbio.ups-tlse.fr/echangeswww/TheiaOSO/IOTA2_TEST_S2.tar.bz2>`_ 
implementing scikit-learn machine learning algorithms.