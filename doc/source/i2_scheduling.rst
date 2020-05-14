Scheduling in iota2
-------------------

The control of task chaining in iota2 is very important. This is what we usually call task scheduling. A "task" is the generic term for something to be done. Fine control of these tasks provides maximum information to the user on the sequence of tasks that will be sent, which tasks will be launched in parallel, which ones will be launched sequentially, which tasks must be completed before launching next ones etc. In addition, in case of problems, the user will be able to find out which tasks did not finish correctly and why: special attention is given to logging.

This is why we have chosen to use dask to schedule our tasks, and more specifically `dask.delayed <https://docs.dask.org/en/latest/delayed.html>`_ and `dask.jobqueue <https://jobqueue.dask.org/en/latest/>`_ to respectively build the dependencies between tasks and then submit them for execution.

About dask
**********

A lot of documentation is available on dask's website : https://docs.dask.org/en/latest/

iota2, the context of a processing chain
****************************************

Iota2 is a modular processing chain, which is capable of handling a large amount of data implementing algorithms that can be massively parallel and/or non-parallel.
From this sentence we can deduce 3 major constraints which have oriented the chosen solutions for the scheduling:

- modularity

  This means that depending on the user's choice, an algorithm can be activated or not and is set up differently. As a result, the different sequences of tasks to be launched can be very different from one iota2 execution to another.

- management of computing resources

  Being able to assign a quota of resources per task must be possible in order to have an optimal scheduling when iota2 is launched on infrastructures (cluster, cloud) where the reservation of computing resources conditions the launch of a task and can be billable.

- Step selection

  iota2 must be able to provide its users with a simple interface to resume processing in the event of problems or to select the processing to be performed from a list of available steps to be processed.

This documentation proposes to guide the reader on the solution chosen in iota² for task scheduling with dask through a simple example, to meet each of the constraints expressed above. Then, the final solutions implemented in iota² will be shown.

Modularity
**********

dask.delayed : how to use it ?
==============================

The `dask.delayed <https://docs.dask.org/en/latest/delayed.html>`_ objects are the objects used in iota² to define the dependencies between Stages and tasks.

.. Warning:: in iota2 we use the term "Stage" to refer to executions that have a common purpose. For example learning, classifying and validating classifications are 3 distinct steps: at each launch of iota², a summary of the steps to be launched is shown to the user. In this documentation, we will also talk about tasks. From this point on, tasks will designate a subset of a step. For example, the learning step will consist of 2 tasks: "learning model 1" and "learning model 2".

First, let's construct a simple tasks' dependency thanks to two simple functions. The purpose is
to launch once the `function_A`. Once complete, launch the `function_B` one time.

.. code-block:: python
				
    def function_A(arg_a: int) -> int
        """
        """
        print(arg_a)
        return arg_a + 1

    def function_B(arg_b: int) -> int:
        """
        """
        print(arg_b)
        return arg_b + 1
		
    a_return = function_A(1)
    print("between two functions call")
    b_return = function_B(a_return)
    print(b_return)

then without surprise, we get the trace

.. code-block:: bash

	1
	between two functions call
	2
	3

However, by using dask.delayed :

.. code-block:: python
				
	a_return = dask.delayed(function_A)(1)
	print("between two functions call")
	b_return = dask.delayed(function_B)(a_return)
	print(b_return)

.. code-block:: bash
				
	between two functions call
	Delayed('function_B-66d71002-295c-4711-8c86-4a3184ee6163')

We only get a delayed object, **no function has been executed**. In order to trigger some processing, we must use the **compute()** method from the delayed object ``b_return``. Then we get :

.. code-block:: python
	a_return = dask.delayed(function_A)(1)
	print("between two function call")
	b_return = dask.delayed(function_B)(a_return)
	print(b_return)
	res = b_return.compute()
	print(res)

.. code-block:: bash

	between two function call
	Delayed('function_B-66d71002-295c-4711-8c86-4a3184ee6163')
	1
	2
	3

This usage is the common usage of dask.delayed object : ``use returned object`` to generate a complete graph and submit it thanks to **compute()** or equivalent. ``However in iota²``, functions do not fit to this kind of use: functions are more data oriented and most of ``functions' returns is the None object``. The following code's snippet illustrates it :

.. code-block:: python

    def learn_model(vector_file: str, output_model: str) -> None:
        """ learn model according to features stored in a vector file
        """
        print(f"I'm learning {output_model} thanks to {vector_file}")

    def classify_tile(model_file: str, output_classif: str) -> None:
        """ perform classification thanks to a model
        """
        print(f"classification of {output_classif} thanks to {model_file}")

    database_file = "my_database.sqlite"
    model_file = "model_1.txt"
    from_learn_model = dask.delayed(learn_model)(vector_file=database_file, output_model=model_file)

    classification_1 = "Classif_1.tif"
    result = dask.delayed(classify_tile)(from_learn_model, classification_1)
    result.compute()

which produces the trace :

.. code-block:: bash

	I'm learning model_1.txt thanks to my_database.sqlite
	classification of Classif_1.tif thanks to None

The execution graph is well respected (learning then classification) but the trace show that ``classify_tile`` does not deal with a string object as expected but with the ``None`` one coming from the learn_model's return.

From this example, we can conclude that it is not possible to use functions in dasks that do not communicate with each other via their returned values to build dependency graphs. Another problem raised by these functions is the following: How to model with dask.delayed the possibility to run different executions of the same function in parallel ?
ie: when the learn_model function has finished its learning, how to launch two executions of classify_tile on two different tiles ? Or on the contrary, how to launch the learning of two models before classifying one and the same tile?

In order to answer these two problems, we have chosen to use a generic function that enables us to build any dependencies between any type of function and any sequence of functions' chaining thanks to task encapsulation. This function will be called ``tasks_launcher()``. 

.. _1:

rewrite the previous test using tasks_launcher()
................................................

.. code-block:: python

    def task_launcher(*args, **kwargs):
        # deep copy to avoid side effect.
        kwargs = kwargs.copy()

        task_kwargs = kwargs.get("task_kwargs", None)
		if task_kwargs:
            # get the function to execute
            func = task_kwargs["f"]
            # remove it from the input dictionnary
            task_kwargs.pop('f', None)
            # use the input dictionary as parameters of the stored function
            # the next line launch the task
            func(**task_kwargs)

    database_file = "my_database.sqlite"
    model_file = "model_1.txt"
    from_learn_model = dask.delayed(task_launcher)(task_kwargs={
         "f": learn_model,
         "vector_file": database_file,
         "output_model": model_file
    })

    classification_1 = "Classif_1.tif"
    res = dask.delayed(task_launcher)(from_learn_model,
                                      task_kwargs={
                                           "f": classify_tile,
                                           "model_file": database_file,
                                           "output_classif": classification_1
                                      })
    res.compute()

This time the execution and arguments are respected. To completely understand the workflow two points must be understood :

    - the functioning of dask.delayed(function_to_delayed)(parameters_of_function_to_delayed)

    - if one of the parameters of the delayed function is a dask.delayed, then the parameter will be triggered/executed before the function is called ie :

    .. code-block:: python

        def some_function(arg1, arg2: int):
            ...

        A = dask.delayed(...)(...)
        delayed_return = dask.delayed(some_function)(A, 2)
        delayed_return_value = delayed_return.compute()

	In this example, `A` is a dependency of `some_function`. Therefore, `A` will be executed before the call to some_function. ``It is this behaviour that allows the dependencies to be expressed in iota².``

This behaviour enables us to submit parallel tasks

Submitting parallel tasks
.........................

Now that the system of dependency between functions is set up, let's see how to integrate multiple dependencies with the following example: "generate 2 models before launching the classification of a tile, both models must be calculated at the same time". We can schematize this exercise by the following diagram:

.. code-block:: bash

            model_1       model_2
               \            /
                \          /
               classification

.. code-block:: python

    model_1_delayed = dask.delayed(task_launcher)(task_kwargs={
        "f": learn_model,
        "vector_file": database_file,
        "output_model": model_file_1
    })

    model_2_delayed = dask.delayed(task_launcher)(task_kwargs={
         "f": learn_model,
         "vector_file": database_file,
         "output_model": model_file_2
    })

    classification_1 = "Classif_1.tif"

    res = dask.delayed(task_launcher)(model_1_delayed,
                                      model_2_delayed,
                                      task_kwargs={
                                          "f": classify_tile,
                                          "model_file": database_file,
                                          "output_classif": classification_1
                                      })
    # there is no execution until the next line
    res.compute()

In the exemple above, ``model_1_delayed`` and ``model_2_delayed`` become dependencies of the execution of the function task_launcher which will launch the classification function. Consequently, the function ``learn_model`` will be executed two times before the ``classify_tile`` call.

Also, we can re-write dependencies like the following :

.. code-block:: python

    dependencies = [model_1_delayed, model_2_delayed]
    res = dask.delayed(task_launcher)(*dependencies,
                                      task_kwargs={
                                          "f": classify_tile,
                                          "model_file": database_file,
                                          "output_classif": classification_1
                                      })
    # there is no execution until the next line
    res.compute()

Two key points can be learned from this example:

    - we can store dependencies (delayed objects) in usual python's objects: list, dictionary...

    - the first parameter of task_launcher(), ``*args``, represents the variable number of dependencies. Thanks to it, it is pretty easy to express dependencies between functions at the condition that the parameters of the functions to launch are known beforehand. Indeed, every task_kwargs parameters must contain the exhaustive list of parameters of the function to launch.


Submitting tasks
================

We have seen that in order to trigger processing, we must use the compute() function of the dask.delayed objects. This method allows us to execute locally the desired function. However, dask also offers the possibility to trigger the execution on different computing architecture, this is what is proposed by the dask_jobqueue module. In iota2, we will give special attention to the LocalCluster and PBSCluster objects which allow respectively to create on a local machine a cluster or to use a real cluster scheduled by PBS.

We had :

.. code-block:: python

    ...
    res = dask.delayed(task_launcher)(*dependencies,
                                      task_kwargs={
                                          "f": classify_tile,
                                          "model_file": database_file,
                                          "output_classif": classification_1
                                      })
    # there is no execution until the next line
    res.compute()

now we get

.. code-block:: python

    if __name__ == '__main__':
        from dask.distributed import Client
        from dask.distributed import LocalCluster
        from dask_jobqueue import PBSCluster

        ...

        res = dask.delayed(task_launcher)(*dependencies,
                                          task_kwargs={
                                              "f": classify_tile,
                                              "model_file": database_file,
                                              "output_classif": classification_1
                                          })
        cluster = PBSCluster(n_workers=1, cores=1, memory='5GB')
        client = Client(cluster)

        # there is no execution until next line
        sub_results = client.submit(res.compute)
        # wait until tasks are complete
        sub_results.result()

.. note::

    In order to reproduce the exemples and if you don't have an access to a HPC cluster scheduled by PBS, you can replace the line :

    .. code-block:: python

        cluster = PBSCluster(n_workers=1, cores=1, memory='5GB')

    by

    .. code-block:: python

        cluster = LocalCluster(n_workers=1, threads_per_worker=1)

Here, a cluster object is created with one worker, one core and 5 Gb of RAM. Then tasks are sended to the PBS scheduler thanks to the submit function.

You may notice that resources can now be set. Now we will have a look on how we could assign resources to different tasks in iota².

Set ressources by tasks
***********************

Currently, dask does not offer solutions for attaching resources by tasks, so we have to find a way to do this using what dask can offer. For this we will rely on the ``task_launcher()`` function which is the place where each task is sent. In fact, we are going to add a new parameter to this function, a python dictionary, which will characterize the resources needed to execute a task. These resources will be used to create inside the task_launcher() function a cluster object with the correct resource reservation. It is on this cluster, instantiated in task_launcher() that the task will be executed.

Here is its definition:

.. code-block:: python

    def task_launcher(*args,
                      resources={"cpu": 1,
                                 "ram": "5Gb"},
                      **kwargs):

        kwargs = kwargs.copy()
        task_kwargs = kwargs.get("task_kwargs", None)
		if task_kwargs:
            # get the function to execute
            func = task_kwargs["f"]
            # remove it from the input dictionnary
            task_kwargs.pop('f', None)
        
            # next line launch the function locally
            # func(**task_kwargs)

            # next lines deploy the function to the cluster with the necessary resources.
            cluster = PBSCluster(n_workers=1,
                                 cores=resources["cpu"],
                                 memory=resources["ram"])
            client = Client(cluster)
            client.wait_for_workers(1)
            sub_results = client.submit(func, **task_kwargs)
            sub_results.result()
            # shutdown the cluster/client dedicated to one task
            cluster.close()
            client.close()

Every task has to create its own cluster object with the right resources reservation. Once the cluster is ready, execute the function on it.
So now, if learning tasks are monothreads and the classification task is multithreads, our main code may looks like:

.. _previously:
.. _2:

.. code-block:: python

    if __name__ == '__main__':
        database_file = "my_database.sqlite"
        model_file_1 = "model_1.txt"
        model_file_2 = "model_2.txt"
        model_1_delayed = dask.delayed(task_launcher)(task_kwargs={
                                                      "f": learn_model,
                                                      "vector_file": database_file,
                                                      "output_model": model_file_1
                                                      },
                                                      resources={
                                                      "cpu": 1,
                                                      "ram": "5Gb"
                                                      })

        model_2_delayed = dask.delayed(task_launcher)(task_kwargs={
                                                      "f": learn_model,
                                                      "vector_file": database_file,
                                                      "output_model": model_file_2
                                                      },
                                                      resources={
                                                      "cpu": 1,
                                                      "ram": "5Gb"
                                                      })

        classification_1 = "Classif_1.tif"
        dependencies = [model_1_delayed, model_2_delayed]

        res = dask.delayed(task_launcher)(*dependencies,
                                          task_kwargs={
                                              "f": classify_tile,
                                              "model_file": database_file,
                                              "output_classif": classification_1
                                          },
                                          resources={
                                              "cpu": 2,
                                              "ram": "10Gb"
                                          })

        cluster = LocalCluster(n_workers=1)
        client = Client(cluster)

        client.wait_for_workers(1)

        # there is no execution until next line
        sub_results = client.submit(res.compute)
        # wait until tasks are terminated
        sub_results.result()

In the example above, we have the learning tasks that will start with a resource reservation of 1 cpu and 5GB of RAM while the classification step will be sent with a resource reservation twice as large. 

At this point, we can say that two thirds of the scheduling solution is already in place, because scheduling allows dependencies between tasks and the assignment of resources by tasks is possible. The last phase that remains to be dealt with is to offer the possibility for users to select a step interval to be executed. This is the subject of the following section.

Activate and deactivate steps
*****************************

In a processing chain composed of several steps it can sometimes be interesting for users to select a step interval to rerun. Several use cases can lead the user to make this choice: replaying a processing chain in case of errors, some steps are not necessary because already done outside iota² (learning a model, generating a database, ...) or the user wants to rerun a step but with different parameters. Iota² must be able to offer this kind of service which is very appreciated by users, but also by step developers.

Problem illustration, apply on the previous example
===================================================

In the previous example, the task sequence graph is rigid, in the sense that if a step (the group of learning tasks and/or classification) is removed, no more execution will be possible: the dependency tree is broken. The goal here is to find a generic way to express a step sequence that will work regardless of the steps that are removed from the execution graph.
A first trivial solution will be exposed, its limitations will show that it is necessary to move towards a more complex and generic solution which is the one implemented in iota².

remove the last task
....................

Based on the solution proposed previously_, it is relatively easy to manage the case where only the classification is desired
Assuming the second python argument is the first step index to execute and the third argument the last.

.. code-block:: python

    if __name__ == '__main__':
        import sys
        first_step = int(sys.argv[1])
        last_step = int(sys.argv[2])
		
        ...

        if first_step == 1 and last_step == 2:
            res = dask.delayed(task_launcher)(*dependencies,
                                              task_kwargs={
                                                  "f": classify_tile,
                                                  "model_file": database_file,
                                                  "output_classif":
                                                  classification_1
                                              },
                                              resources={
                                                  "cpu": 2,
                                                  "ram": "10Gb"
                                              })
        elif first_step == 2 and last_step == 2:
            # if only the classification is asked, then classifications tasks get no dependencies
            res = dask.delayed(task_launcher)(task_kwargs={
                "f": classify_tile,
                "model_file": database_file,
                "output_classif": classification_1
            },
                                              resources={
                                                  "cpu": 2,
                                                  "ram": "10Gb"
                                              })
        ...
        sub_results = client.submit(res.compute)
		sub_results.results()

This solution works when only the last step is required. If only the classification step is required (first_step == last_step == 2), then the classification taks get no dependencies.
However, the solution will not work when only the learning tasks are requested. Indeed, the line :

.. code-block:: python

    sub_results = client.submit(res.compute)

will not be able to launch the learning tasks because the variable ``res`` (defining the tasks to be launched) and ``dependencies`` (containing the learning tasks) are two different types: one is a dask.delayed and the other is a list of dask.delayed. A generic way to send tasks to the cluster must therefore be found. Below is the one proposed in iota²: a container of the last steps to be sent, ``step_tasks``.

.. _3:

remove the first task
.....................

.. code-block:: python

    if __name__ == '__main__':
        import sys

        first_step = int(sys.argv[1])
        last_step = int(sys.argv[2])

        ...
		step_tasks = []
        if first_step == 1:
            model_1_delayed = dask.delayed(task_launcher)(...)
            model_2_delayed = dask.delayed(task_launcher)(...)
            step_tasks = [model_1_delayed, model_2_delayed]

        ...

        if first_step == 1 and last_step == 2:
            dependencies = [model_1_delayed, model_2_delayed]
            classif_delayed = dask.delayed(task_launcher)(*dependencies, ...)
            step_tasks.append(classif_delayed)
        elif first_step == 2 and last_step == 2:
            classif_delayed = dask.delayed(task_launcher)(...)
            step_tasks.append(classif_delayed)
    
    # there is no execution until the next line
    final_dask_graph = dask.delayed(task_launcher)(*step_tasks)
    sub_results = client.submit(final_dask_graph.compute)
    # wait until tasks are terminated
    sub_results.result()

The step_tasks container is redefined for each step and contains all the tasks to be lauched for a step. This step container, through the use of ``task_launcher()``, enables to gather all the tasks defined in a step of iota².
All scheduling constraints have been exposed and solved, the following script summarizes all these solutions by introducing an additional complexity which is present in iota², all steps are represented by classes. Thus, this script allows to be the minimal representation of what scheduling is in iota².


Scheduling solution in iota²
****************************

It is easy to notice that steps have common functionnalities: creating tasks, associating dependencies to them and launching tasks. All these steps' common features have been gathered in the base class: ``i2_step()``.
The next section shows the slightly simplified, but functional, definition of this class and parallels between the definition of this class and the previous examples are highlighted.
It is therefore important that the examples 1_, 2_ and 3_ are well understood.

.. _BaseClass:

Base class dedicated to steps
=============================

.. code-block:: python

   class i2_step():
       """base class for every iota2 steps"""
       class i2_task():
           """class dedicated to reprensent a task in iota2"""
           def __init__(self, task_parameter: Dict, task_resources: Dict):
               self.task_parameter = task_parameter
               self.task_resources = task_resources

        step_container = []
        tasks_graph = {}

        # parameters known before the iota2's launch
        database_file = "my_database.sqlite"
        models_to_learn = ["model_1.txt", "model_2.txt"]
        classifications_to_perform = ["Classif_1.tif"]

        def __init__(self):
            self.step_container.append(self)
            self.step_tasks = []

        @classmethod
        def get_final_execution_graph(cls):
            return dask.delayed(
                cls.task_launcher)(*cls.step_container[-1].step_tasks)

        def task_launcher(*args, resources={"cpu": 1, "ram": "5Gb"}, **kwargs):
            """method to launch task"""
            kwargs = kwargs.copy()
            task_kwargs = kwargs.get("task_kwargs", None)
            if task_kwargs:
                func = task_kwargs["f"]
                task_kwargs.pop('f', None)
                task_cluster = PBSCluster(n_workers=1,
                                          cores=resources["cpu"],
                                          memory=resources["ram"])

                task_client = Client(task_cluster)
                task_client.wait_for_workers(1)
                task_results = task_client.submit(func, **task_kwargs)
                task_results.result()
                task_cluster.close()
                task_client.close()

                # func(**task_kwargs)

        def add_task_to_i2_processing_graph(
                self,
                task,
                task_group: str,
                task_sub_group: Optional[str] = None,
                task_dep_dico: Optional[Dict[str, List[str]]] = None) -> None:
            """use to build the tasks' execution graph
            """
            if task_group not in self.tasks_graph:
                self.tasks_graph[task_group] = {}

            # if there is no steps in the step container that mean no dependencies have
            # to be set

            if len(self.step_container) == 1:
                new_task = dask.delayed(self.task_launcher)(
                    task_kwargs=task.task_parameter, resources=task.task_resources)
            else:
                task_dependencies = []
                for task_group_name, tasks_name in task_dep_dico.items():
                    if task_group_name in self.tasks_graph:
                        for dep_task in tasks_name:
                            task_dependencies.append(
                                self.tasks_graph[task_group_name][dep_task])
                new_task = dask.delayed(self.task_launcher)(
                    *task_dependencies,
                    task_kwargs=task.task_parameter,
                    resources=task.task_resources)
			# update the dependency graph
            self.tasks_graph[task_group][task_sub_group] = new_task
			# save current step's tasks
            self.step_tasks.append(new_task)

This class allows the possibility to define dependencies between tasks and to have different resources per tasks.
Indeed, with the use the ``task_launcher()`` function which has exactly the same definition as the examples above.
Also, dependencies between tasks are managed thanks to the "add_task_to_i2_processing_graph()`.
This function relies on the class attribute "tasks_graph" which, like "dependencies" in the example 2_, 
allows to save the dependencies between tasks and thus build a dependency graph using dask.

However, ``tasks_graph`` and ``dependencies`` are a bit different: dependencies was a simple ``list of dask.delayed objects``, while tasks_graph is a ``dictionary of dictionaries``.
This change makes it possible to 'name' the dependencies and to be clearer than a simple list when traveling between stages.

All dependency management between tasks will be handled by the class attribute ``tasks_graph`` and the method ``add_task_to_i2_processing_graph()``.
Each task must belong to a task group and must define its dependencies if needed. For example, let's take the previous example where 2 models have to be created.
So there will be 2 tasks that we will name "model 1" and "model 2" that we will group together under the task group "models".
Somewhere in the code 2 there will be a call to add_task_to_i2_processing_graph() like this:

.. code-block:: python

    add_task_to_i2_processing_graph(task, "models", "model 1")
	...
    add_task_to_i2_processing_graph(task, "models", "model 2")

where ``task`` is a class containing two dictionaries, one resuming the task and the other resuming task's resources. These dictionaries are the same that the ones we can find in 3_ under the names ``task_kwargs`` and ``resources``.
It is important to note that in this example, no dependencies have been mentioned because the learning step will be the first step in our example processing chain. We can Define our learning step as a class that inherits the functionality of the ``i2_step'' class :

.. code-block:: python

    class learn_model(i2_step):
        """class simulation the learn of models"""
        def __init__(self):
            super(learn_model, self).__init__()
            for model in self.models_to_learn:
                model_task = self.i2_task(task_parameter={
                    "f": self.learn_model,
                    "vector_file": self.database_file,
                    "output_model": model
                },
                                          task_resources={
                                              "cpu": 1,
                                              "ram": "5Gb"
                                          })
                self.add_task_to_i2_processing_graph(model_task,
                                                     task_group="models",
                                                     task_sub_group=model)

        def learn_model(self, vector_file: str, output_model: str) -> None:
            """ learn model according to features stored in a vector file
            """
            print(f"I'm learning {output_model} thanks to {vector_file}")

Likewise, we can define the classification step

.. code-block:: python

    class classifications(i2_step):
        """class to simulate classifications"""
        def __init__(self):
            super(classifications, self).__init__()
            classification_task = self.i2_task(task_parameter={
                "f":
                self.classify_tile,
                "model_file":
                self.models_to_learn[0],
                "output_classif":
                self.classifications_to_perform[0]
            },
                                               task_resources={
                                                   "cpu": 2,
                                                   "ram": "10Gb"
                                                })
            self.add_task_to_i2_processing_graph(
                classification_task,
                task_group="classifications",
                task_sub_group=self.classifications_to_perform[0],
                task_dep_dico={"models": self.models_to_learn})

        def classify_tile(self, model_file: str, output_classif: str) -> None:
            """
            """
            print(f"classification of {output_classif} thanks to {model_file}")

This time dependencies have been set when creating the classification task :
the classification task needs both learning tasks to be completed in order to be run.

.. code-block:: python

    task_dep_dico={"models": self.models_to_learn}

which means: "I need that every tasks named as in the list of tasks's name self.models_to_learn of the group of tasks 'models' has been finished to be launched".
Furthermore, it is possible to create tasks which depend of many groups of tasks. Let's create a new class : ``confusion`` which depend of the classification and one learning task.

.. code-block:: python

    class confusion(i2_step):
        """class to simulate classifications"""
        def __init__(self):
            super(confusion, self).__init__()
            confusion_task = self.i2_task(task_parameter={
                "f": self.confusion,
                "output_confusion_file": "confusion.csv"
            },
                                          task_resources={
                                              "cpu": 2,
                                              "ram": "10Gb"
                                          })
            self.add_task_to_i2_processing_graph(
                confusion_task,
                task_group="confusion",
                task_sub_group="confusion_tile_T31TCJ",
                task_dep_dico={
                    "classifications": [self.classifications_to_perform[0]],
                    "models": [self.models_to_learn[-1]]
                })

        def confusion(self, output_confusion_file) -> None:
            """
            """
            print(f"generetating confusion : {output_confusion_file}")

This class generates only one task, which depends on the first classification task (actually, there is only one) 
and the last task of learning step.

Once our steps class are defined, it is time to instanciate them. 
To achieve this pupose, we use the class called ``i2_builder()`` which manage the step's instanciation
considering 2 parameters : the index of the first and the last step to launch. This way, we satisfy the last constraint: being able to select an interval of step to execute in a sequence of steps.

Then after the call of ``get_final_i2_exec_graph()``, the full processing chain will be ready to be launched. In fact,
the only purpose of this method is to instanciate the asked steps and by extension build the final dask graph.

.. Note:: self.step_tasks and the varialbe ``step_tasks`` in example 3_ have the same goal, save step's tasks

.. code-block:: python

    class i2_builder():
        """define step sequence to be launched"""
        def __init__(self, first_step: int, last_step: int):
            self.first_step = first_step
            self.last_step = last_step
            self.steps = self.build_steps()

            if self.last_step > len(self.steps):
                raise ValueError(f"last step must be <= {len(self.steps)}")

        def build_steps(self):
            """prepare steps sequence"""
            from functools import partial
            steps_constructors = []
            steps_constructors.append(partial(learn_model))
            steps_constructors.append(partial(classifications))
            steps_constructors.append(partial(confusion))
            return steps_constructors

        def get_final_i2_exec_graph(self):
            # instanciate steps which must me launched
            steps_to_exe = [
                step() for step in self.steps[self.first_step:self.last_step + 1]
            ]
            return i2_step.get_final_execution_graph()


    if __name__ == '__main__':

        import sys

        run_first_step = int(sys.argv[1]) - 1
        run_last_step = int(sys.argv[2]) - 1

        assert run_last_step >= run_first_step
        i2_chain = i2_builder(run_first_step, run_last_step)
        graph = i2_chain.get_final_i2_exec_graph()
        graph.compute()

The full solution of tasks scheduling in iota² has been shown. As already mentionned, this example is a minimal
example of tasks scheduling, however most part of the script presented in the section :ref:`BaseClass` can be found in iota² package.
