Adding a new step to IOTA²
##########################

IOTA² is based on a sequence of steps. As example, if the purpose is to achieve
a supervised classification, then steps could roughly be : "prepare data",
"learn models", "classify" then "validate classifications". Step's number define
IOTA² granularity. Each steps must have a well define goal. 

In the previous example, "prepare data" is too abstact to define a entiere step.
We could split it until getting a coherent purpose / goal / aim by step.
"prepare data" could become "prepare raster data" and "prepare input vector data"

Step's definition
*****************

The pupose of a step is to achieve something. In most case in IOTA², step has to 
be reproduce douzens of times : on a set of tiles or by dates etc... 
In order to provide to developers a generic workflow, steps has to be lambda functions.

lambda
======

lambda functions could be use as the following :

.. code-block:: python

        x = lambda a : a + 10
        print(x(5))
        >>> 15

In the example ``x is the lambda`` function and ``a is the variable parameter`` of x.
The value of `a` is dynamically determined when x is used. In IOTA², lambda functions
receive a function.

.. code-block:: python

        def MyFunction(arg_1, arg_2):
            """
            some usefull code-strings
            """
            print arg_2

        x = lambda a: MyFunction(1, a)
        list_of_args = [1, 2, 3]
        for arg in list_of_args:
            x(arg)

        >>> 1
        >>> 2
        >>> 3

MyFunction could be the one dedicated to learn a model, classify tiles etc...
In some case, it could be hard to find parameters. 

How feed the lambda
===================

IOTA² allow two ways to feed the lambda function 

1 - using an iterable
2 - using a callable returning a iterable

Existing steps
**************

Every available steps are stored in ...

Define a new step
*****************

herit
example of adding a new dummy step
Note : 
    resources 

Steps resources
***************

Why resources ?

Rules
*****

input parameter list must be the same at during the whole step process.