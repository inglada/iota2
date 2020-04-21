#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# =========================================================================
#   Program:   iota2
#
#   Copyright (c) CESBIO. All rights reserved.
#
#   See LICENSE for details.
#
#   This software is distributed WITHOUT ANY WARRANTY; without even
#   the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the above copyright notices for more information.
#
# =========================================================================
import dask
import os
from functools import wraps
from typing import Optional, Dict
from dask.distributed import Client
from dask_jobqueue import PBSCluster
import logging

LOGGER = logging.getLogger(__name__)

# class change_name():
#     """
#     decorator to temporary change fonction's name
#     useful to plot dask graph
#     """
#     def __init__(self, new_name: str):
#         self.new_name = new_name

#     def __call__(self, f):
#         if "__name__" in dir(f):
#             f.__name__ = self.new_name
#         else:
#             f.__func__.__name__ = self.new_name

#         @wraps(f)
#         def wrapped_f(*args, **kwargs):
#             return f(*args, **kwargs)

#         return wrapped_f


class step():
    """simulating the iota2 base class IOTA2Step.Step"""
    class change_name():
        """
        decorator to temporary change fonction's name
        useful to plot dask graph
        """
        def __init__(self, new_name: str):
            self.new_name = new_name

        def __call__(self, f):
            if "__name__" in dir(f):
                f.__name__ = self.new_name
            else:
                f.__func__.__name__ = self.new_name

            @wraps(f)
            def wrapped_f(*args, **kwargs):
                return f(*args, **kwargs)

            return wrapped_f

    class i2_task():
        """data class to modelize a iota2 task"""
        def __init__(self,
                     task_name: str,
                     log_dir: str,
                     execution_mode: str,
                     task_parameters: Dict,
                     task_resources: Optional[Dict[str, str]] = {
                         "cpu": 1,
                         "ram": "5Gb",
                         "walltime": "01:00:00"
                     }):
            # care about __closure__
            inner_resources = task_resources.copy()

            self.task_name = task_name

            if not isinstance(task_name, str):
                raise ValueError("parameter 'task_name' must be a string")
            # due to PBS limitations
            if len(task_name) > 25:
                self.task_name = task_name[0:24]
                print(
                    "WARNING: task_name = {task_name} too long, casted as {self.task_name}"
                )
            if " " in self.task_name:
                self.task_name = self.task_name.replace(" ", "")
                print(
                    "WARNING: task_name = {task_name} contains whitespaces, casted as {self.task_name}"
                )
            if "-" in self.task_name:
                self.task_name = self.task_name.replace("-", "")
                print(
                    "WARNING: task_name contains '-' character, automatically removed"
                )
            self.log_err = os.path.join(log_dir, f"{task_name}.err")
            self.log_out = os.path.join(log_dir, f"{task_name}.out")
            self.execution_mode = execution_mode
            self.parameters = task_parameters
            self.resources = inner_resources
            # check if the task is not already present in the list of tasks.
            # Indeed, a task must be unique
            for task in step.tasks_container:
                if self.task_name == task.task_name:
                    raise ValueError(
                        f"iota2 task called {self.task_name} already exists")
            step.tasks_container.add(self)

    # use a the step container class instead of class attribute
    step_container = []

    # useful to control the fact that tasks must be unique
    tasks_container = set()

    # will contains tasks dependencies, keys could be added
    tasks_graph = {"first_task": None, "tile_tasks": {}, "region_task": {}}

    # we infer this informations are available at the begining of
    # the iota2 launch
    list_tiles = ["T31TCJ", "T31TDJ"]
    list_models = {
        "1": {
            "name": "model_1",
            "tiles": ["T31TCJ", "T31TDJ"]
        },
        "2": {
            "name": "model_2",
            "tiles": ["T31TDJ"]
        }
    }

    def __init__(self):
        step.step_container.append(self)
        # and more in real Iota2Step.py implementation

    @classmethod
    def get_final_i2_exec_graph(cls):
        """
        """
        #import iota2
        from iota2.dask_scheduler_POC import iota2_step
        # return dask.delayed(change_name("gather results")(
        #     cls.task_launcher3))(*cls.step_container[-1].step_tasks)
        # print(cls)
        # print(cls.__class__)
        # print(step)
        # pause = input("??")

        # print("AVANT")
        # dask.delayed(
        #     change_name("gather results")(iota2_step.step.task_launcher3))(
        #         *iota2_step.step.step_container[-1].step_tasks).compute()
        # print("APRES")

        return dask.delayed(iota2_step.step.task_launcher3)(
            *iota2_step.step.step_container[-1].step_tasks)

    def add_task_to_i2_processing_graph(
            self,
            task,
            task_group: str,
            task_sub_group: Optional[str] = None,
            task_dep_group: Optional[str] = None,
            task_dep_sub_group: Optional[str] = None) -> dask.delayed:
        """
        """
        new_task = None

        # TODO : add method to add new key in tasks_graph ?
        if task_group not in self.tasks_graph:
            self.tasks_graph[task_group] = {}

        if task_group == "first_task":
            if self.tasks_graph["first_task"] is not None:
                raise ValueError("first task already present")
            new_task = dask.delayed(
                self.change_name(task.task_name)(self.task_launcher))(
                    log_err=task.log_err,
                    log_out=task.log_out,
                    scheduler_type=task.execution_mode,
                    pbs_worker_name=task.task_name,
                    resources=task.resources,
                    task_kwargs=task.parameters)
            self.tasks_graph["first_task"] = new_task
        else:
            # second step case, then the dependency is the "first_task"
            if task_dep_sub_group is None:
                new_task = dask.delayed(
                    self.change_name(task.task_name)(self.task_launcher))(
                        self.tasks_graph[task_dep_group],
                        log_err=task.log_err,
                        log_out=task.log_out,
                        scheduler_type=task.execution_mode,
                        pbs_worker_name=task.task_name,
                        resources=task.resources,
                        task_kwargs=task.parameters)
            else:
                new_task = dask.delayed(
                    self.change_name(task.task_name)(self.task_launcher))(
                        *[
                            self.tasks_graph[task_dep_group][dep]
                            for dep in task_dep_sub_group
                        ],
                        log_err=task.log_err,
                        log_out=task.log_out,
                        scheduler_type=task.execution_mode,
                        pbs_worker_name=task.task_name,
                        resources=task.resources,
                        task_kwargs=task.parameters)
            self.tasks_graph[task_group][task_sub_group] = new_task
        return new_task

    def add_task_to_i2_processing_graph2(
            self,
            task,
            task_group: str,
            task_sub_group: Optional[str] = None,
            task_dep_group: Optional[str] = None,
            task_dep_sub_group: Optional[str] = None) -> dask.delayed:
        """
        """
        new_task = None

        # TODO : add method to add new key in tasks_graph ?
        if task_group not in self.tasks_graph:
            self.tasks_graph[task_group] = {}

        if task_group == "first_task":
            if self.tasks_graph["first_task"] is not None:
                raise ValueError("first task already present")
            # new_task = dask.delayed(
            #     change_name(task.task_name)(self.task_launcher2))(
            #         log_err=task.log_err,
            #         log_out=task.log_out,
            #         scheduler_type=task.execution_mode,
            #         pbs_worker_name=task.task_name,
            #         resources=task.resources,
            #         task_kwargs=task.parameters)
            new_task = dask.delayed(self.task_launcher2)(
                log_err=task.log_err,
                log_out=task.log_out,
                scheduler_type=task.execution_mode,
                pbs_worker_name=task.task_name,
                resources=task.resources,
                task_kwargs=task.parameters)
            self.tasks_graph["first_task"] = new_task
        else:
            # second step case, then the dependency is the "first_task"
            if task_dep_sub_group is None:
                # new_task = dask.delayed(
                #     change_name(task.task_name)(self.task_launcher2))(
                #         self.tasks_graph[task_dep_group],
                #         log_err=task.log_err,
                #         log_out=task.log_out,
                #         scheduler_type=task.execution_mode,
                #         pbs_worker_name=task.task_name,
                #         resources=task.resources,
                #         task_kwargs=task.parameters)
                new_task = dask.delayed(self.task_launcher2)(
                    self.tasks_graph[task_dep_group],
                    log_err=task.log_err,
                    log_out=task.log_out,
                    scheduler_type=task.execution_mode,
                    pbs_worker_name=task.task_name,
                    resources=task.resources,
                    task_kwargs=task.parameters)
            else:
                # new_task = dask.delayed(
                #     change_name(task.task_name)(self.task_launcher2))(
                #         *[
                #             self.tasks_graph[task_dep_group][dep]
                #             for dep in task_dep_sub_group
                #         ],
                #         log_err=task.log_err,
                #         log_out=task.log_out,
                #         scheduler_type=task.execution_mode,
                #         pbs_worker_name=task.task_name,
                #         resources=task.resources,
                #         task_kwargs=task.parameters)
                new_task = dask.delayed(self.task_launcher2)(
                    *[
                        self.tasks_graph[task_dep_group][dep]
                        for dep in task_dep_sub_group
                    ],
                    log_err=task.log_err,
                    log_out=task.log_out,
                    scheduler_type=task.execution_mode,
                    pbs_worker_name=task.task_name,
                    resources=task.resources,
                    task_kwargs=task.parameters)
            self.tasks_graph[task_group][task_sub_group] = new_task
        return new_task

    @classmethod
    def get_dependencies_keys(cls):
        """expose the state of the tasks graph by showing last
        task'name associated to tasks graph keys
        """
        tasks_dict = {}
        for key_dep, key_sub_dep in cls.tasks_graph.items():
            if key_dep not in tasks_dict:
                tasks_dict[key_dep] = {}
            if isinstance(key_sub_dep, dict):
                for key_sub_dep_name, delayed_obj in key_sub_dep.items():
                    tasks_dict[key_dep][
                        key_sub_dep_name] = delayed_obj.key.split("-")[0]
            else:
                task_name = key_sub_dep.key.split("-")[0]
                tasks_dict[key_dep] = task_name
        return tasks_dict

    def task_launcher(self,
                      *args,
                      log_err: Optional[str] = None,
                      log_out: Optional[str] = None,
                      scheduler_type: Optional[str] = "local",
                      pbs_worker_name: Optional[str] = "i2-worker",
                      resources: Optional[Dict[str, str]] = {
                          "cpu": 1,
                          "ram": "5Gb",
                          "walltime": "01:00:00"
                      },
                      **kwargs) -> None:
        """this function encapsulate tasks to be delayed

        *args: dask.delayed dependencies
            list of tasks dependencies

        i2_log_dir : str
            path to a directory which will contains tasks files
        scheduler_type : str
            scheduling strategies 'local' or 'cluster'
        resources : dict
            dictionary of resources
        kwargs : dict
           dictionary containing the function to launch with its parameters
        """
        import time

        kwargs = kwargs.copy()
        task_kwargs = kwargs.get("task_kwargs", None)
        if task_kwargs:
            func = task_kwargs["f"]
            task_kwargs.pop('f', None)
            f_kwargs = task_kwargs
            # here we launch the fonction with all the arguments of kwargs
            if scheduler_type == "cluster":

                env_vars = [
                    f"export PYTHONPATH={os.environ.get('PYTHONPATH')}:{os.path.dirname(os.path.realpath(__file__))}",
                    f"export PATH={os.environ.get('PATH')}:{os.path.dirname(os.path.realpath(__file__))}",
                    f"export LD_LIBRARY_PATH={os.environ.get('LD_LIBRARY_PATH')}",
                    f"export OTB_APPLICATION_PATH={os.environ.get('OTB_APPLICATION_PATH')}",
                    f"export GDAL_DATA={os.environ.get('GDAL_DATA')}",
                    f"export GEOTIFF_CSV={os.environ.get('GEOTIFF_CSV')}"
                ]

                extras = [f"-N {pbs_worker_name}"]
                if log_err is not None:
                    extras.append(f"-e {log_err}")
                if log_out is not None:
                    extras.append(f"-o {log_out}")
                cluster = PBSCluster(n_workers=1,
                                     cores=resources["cpu"],
                                     memory=resources["ram"],
                                     walltime=resources["walltime"],
                                     env_extra=env_vars,
                                     interface='ib0',
                                     silence_logs="error",
                                     processes=1,
                                     job_extra=extras,
                                     local_directory='$TMPDIR')

                client = Client(cluster)
                sub_results = client.submit(func, **f_kwargs)
                sub_results.result()
                cluster.close()
                client.close()
                time.sleep(5)
                # wait and see : restart if fail ? differents strategies
                # of relaunch can be implemented here...
            elif scheduler_type == "local":
                func(**f_kwargs)
        else:
            LOGGER.warning("WARNING : the variable 'task_kwargs' is missing")

    def task_launcher2(self,
                       *args,
                       log_err: Optional[str] = None,
                       log_out: Optional[str] = None,
                       scheduler_type: Optional[str] = "local",
                       pbs_worker_name: Optional[str] = "i2-worker",
                       resources: Optional[Dict[str, str]] = {
                           "cpu": 1,
                           "ram": "5Gb",
                           "walltime": "01:00:00"
                       },
                       **kwargs) -> None:
        """this function encapsulate tasks to be delayed

        *args: dask.delayed dependencies
            list of tasks dependencies

        i2_log_dir : str
            path to a directory which will contains tasks files
        scheduler_type : str
            scheduling strategies 'local' or 'cluster'
        resources : dict
            dictionary of resources
        kwargs : dict
           dictionary containing the function to launch with its parameters
        """
        import time

        kwargs = kwargs.copy()
        task_kwargs = kwargs.get("task_kwargs", None)
        if task_kwargs:
            func = task_kwargs["f"]
            task_kwargs.pop('f', None)
            f_kwargs = task_kwargs
            # here we launch the fonction with all the arguments of kwargs
            if scheduler_type == "cluster":

                env_vars = [
                    f"export PYTHONPATH={os.environ.get('PYTHONPATH')}:{os.path.dirname(os.path.realpath(__file__))}",
                    f"export PATH={os.environ.get('PATH')}:{os.path.dirname(os.path.realpath(__file__))}",
                    f"export LD_LIBRARY_PATH={os.environ.get('LD_LIBRARY_PATH')}",
                    f"export OTB_APPLICATION_PATH={os.environ.get('OTB_APPLICATION_PATH')}",
                    f"export GDAL_DATA={os.environ.get('GDAL_DATA')}",
                    f"export GEOTIFF_CSV={os.environ.get('GEOTIFF_CSV')}"
                ]

                extras = [f"-N {pbs_worker_name}"]
                if log_err is not None:
                    extras.append(f"-e {log_err}")
                if log_out is not None:
                    extras.append(f"-o {log_out}")
                cluster = PBSCluster(n_workers=1,
                                     cores=resources["cpu"],
                                     memory=resources["ram"],
                                     walltime=resources["walltime"],
                                     env_extra=env_vars,
                                     interface='ib0',
                                     silence_logs="error",
                                     processes=1,
                                     job_extra=extras,
                                     local_directory='$TMPDIR')

                client = Client(cluster)
                sub_results = client.submit(func, **f_kwargs)
                sub_results.result()
                cluster.close()
                client.close()
                time.sleep(5)
                # wait and see : restart if fail ? differents strategies
                # of relaunch can be implemented here...
            elif scheduler_type == "local":
                func(**f_kwargs)
        else:
            LOGGER.warning("WARNING : the variable 'task_kwargs' is missing")

    def task_launcher3(self,
                       *args,
                       log_err: Optional[str] = None,
                       log_out: Optional[str] = None,
                       scheduler_type: Optional[str] = "local",
                       pbs_worker_name: Optional[str] = "i2-worker",
                       resources: Optional[Dict[str, str]] = {
                           "cpu": 1,
                           "ram": "5Gb",
                           "walltime": "01:00:00"
                       },
                       **kwargs) -> None:
        """this function encapsulate tasks to be delayed

        *args: dask.delayed dependencies
            list of tasks dependencies

        i2_log_dir : str
            path to a directory which will contains tasks files
        scheduler_type : str
            scheduling strategies 'local' or 'cluster'
        resources : dict
            dictionary of resources
        kwargs : dict
           dictionary containing the function to launch with its parameters
        """
        import time

        kwargs = kwargs.copy()
        task_kwargs = kwargs.get("task_kwargs", None)
        if task_kwargs:
            func = task_kwargs["f"]
            task_kwargs.pop('f', None)
            f_kwargs = task_kwargs
            # here we launch the fonction with all the arguments of kwargs
            if scheduler_type == "cluster":

                env_vars = [
                    f"export PYTHONPATH={os.environ.get('PYTHONPATH')}:{os.path.dirname(os.path.realpath(__file__))}",
                    f"export PATH={os.environ.get('PATH')}:{os.path.dirname(os.path.realpath(__file__))}",
                    f"export LD_LIBRARY_PATH={os.environ.get('LD_LIBRARY_PATH')}",
                    f"export OTB_APPLICATION_PATH={os.environ.get('OTB_APPLICATION_PATH')}",
                    f"export GDAL_DATA={os.environ.get('GDAL_DATA')}",
                    f"export GEOTIFF_CSV={os.environ.get('GEOTIFF_CSV')}"
                ]

                extras = [f"-N {pbs_worker_name}"]
                if log_err is not None:
                    extras.append(f"-e {log_err}")
                if log_out is not None:
                    extras.append(f"-o {log_out}")
                cluster = PBSCluster(n_workers=1,
                                     cores=resources["cpu"],
                                     memory=resources["ram"],
                                     walltime=resources["walltime"],
                                     env_extra=env_vars,
                                     interface='ib0',
                                     silence_logs="error",
                                     processes=1,
                                     job_extra=extras,
                                     local_directory='$TMPDIR')

                client = Client(cluster)
                sub_results = client.submit(func, **f_kwargs)
                sub_results.result()
                cluster.close()
                client.close()
                time.sleep(5)
                # wait and see : restart if fail ? differents strategies
                # of relaunch can be implemented here...
            elif scheduler_type == "local":
                func(**f_kwargs)
        else:
            LOGGER.warning("WARNING : the variable 'task_kwargs' is missing")
