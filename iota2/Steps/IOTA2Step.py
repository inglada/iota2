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
import os
import dask
import logging
from functools import wraps
from typing import Dict, Optional
from dask.distributed import Client
from dask_jobqueue import PBSCluster

LOGGER = logging.getLogger(__name__)


class StepContainer(object):
    """
    this class is dedicated to contains Step
    """
    def __init__(self):
        self.container = []

    def append(self, step, step_group=""):

        if not step in self.container:
            self.container.append(step)
            step.step_group = step_group
        else:
            raise Exception("step '{}' already present in container".format(
                step.step_name))
        # link steps
        if len(self.container) > 1:
            self.container[len(self.container) - 2].next_step = step
            step.previous_step = self.container[len(self.container) - 2]

    def __contains__(self, step_ask):
        """
        The __contains__ method is based on step's name
        """
        return any(
            [step.step_name == step_ask.step_name for step in self.container])

    def __setitem__(self, index, val):
        self.container[index] = val

    def __getitem__(self, index):
        return self.container[index]

    def __str__(self):
        return "[{}]".format(", ".join(step.step_name
                                       for step in self.container))

    def __len__(self):
        return len(self.container)


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


class Step(object):
    """
    This class is the definition of a IOTA² step. New steps must herit from
    """
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
            if " " in self.task_name:
                self.task_name = self.task_name.replace(" ", "")
                print(
                    f"WARNING: task_name = {task_name} contains whitespaces, casted as {self.task_name}"
                )
            if "-" in self.task_name:
                self.task_name = self.task_name.replace("-", "")
                print(
                    f"WARNING: task_name contains '-' character, automatically removed"
                )
            self.log_err = os.path.join(log_dir, f"{task_name}.err")
            self.log_out = os.path.join(log_dir, f"{task_name}.out")
            self.execution_mode = execution_mode
            self.parameters = task_parameters
            self.resources = inner_resources
            # check if the task is not already present in the list of tasks.
            # Indeed, a task must be unique
            for task in Step.tasks_container:
                if self.task_name == task.task_name:
                    raise ValueError(
                        f"iota2 task called {self.task_name} already exists")
            Step.tasks_container.add(self)

    tiles = []
    spatial_models_distribution = {}

    # will contains every steps
    step_container = []
    step_container_first = []

    # useful to control the fact that tasks must be unique
    tasks_container = set()

    # will contains tasks dependencies, keys could be added
    tasks_graph = {
        "first_task": None,
        "tile_tasks": {},
        "region_tasks": {},
        "tile_tasks_model": {}
    }

    def __init__(self, cfg, cfg_resources_file, resources_block_name=None):
        """
        """
        from iota2.Common import ServiceConfigFile as SCF

        # attributes
        self.cfg = cfg
        self.step_name = self.build_step_name()
        self.step_group = ""

        # get resources needed
        self.resources = self.parse_resource_file(resources_block_name,
                                                  cfg_resources_file)

        # define log path
        outputPath = SCF.serviceConfigFile(self.cfg).getParam(
            'chain', 'outputPath')

        log_dir = os.path.join(outputPath, "logs")
        self.log_dir = log_dir
        self.log_step_dir = os.path.join(self.log_dir,
                                         "{}".format(self.step_name))
        self.step_container.append(self)

    @classmethod
    def set_models_spatial_information(cls, tiles,
                                       spatial_models_distribution):
        cls.tiles = tiles
        cls.spatial_models_distribution = spatial_models_distribution

    @classmethod
    def get_exec_graph(cls):
        """
        """
        return dask.delayed(
            cls.task_launcher)(*cls.step_container[-1].step_tasks)

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
        from iota2.Common.FileUtils import ensure_dir
        kwargs = kwargs.copy()
        task_kwargs = kwargs.get("task_kwargs", None)

        if task_kwargs:
            log_dir, _ = os.path.split(log_err)
            if not os.path.exists(log_dir):
                ensure_dir(log_dir)

            func = task_kwargs["f"]
            task_kwargs.pop('f', None)
            f_kwargs = task_kwargs

            # here we launch the fonction with all the arguments of kwargs
            if scheduler_type == "cluster":

                env_vars = [
                    f"export PYTHONPATH={os.environ.get('PYTHONPATH')}",
                    f"export PATH={os.environ.get('PATH')}",
                    f"export LD_LIBRARY_PATH={os.environ.get('LD_LIBRARY_PATH')}",
                    f"export OTB_APPLICATION_PATH={os.environ.get('OTB_APPLICATION_PATH')}",
                    f"export GDAL_DATA={os.environ.get('GDAL_DATA')}",
                    f"export GEOTIFF_CSV={os.environ.get('GEOTIFF_CSV')}"
                ]

                extras = [f"-N {pbs_worker_name[0:30]}"]
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
                client.wait_for_workers(1)
                for _, worker_meta in client.scheduler_info()["workers"].items(
                ):
                    working_dir = os.path.split(
                        worker_meta["local_directory"])[0]
                f_kwargs = self.set_working_dir_parameter(
                    f_kwargs, working_dir)
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

    def set_working_dir_parameter(self, t_kwargs: Dict,
                                  worker_working_dir: str) -> Dict:
        """
        """
        new_t_kwargs = t_kwargs.copy()
        working_dir_names = [
            "working_directory", "pathWd", "workingDirectory", "working_dir",
            "path_wd"
        ]
        for working_dir_name in working_dir_names:
            if working_dir_name in new_t_kwargs:
                new_t_kwargs[working_dir_name] = worker_working_dir
        return new_t_kwargs

    def add_task_to_i2_processing_graph_graph(
            self,
            task,
            task_group: str,
            task_sub_group: Optional[str] = None,
            task_dep_group: Optional[str] = None,
            task_dep_sub_group: Optional[str] = None) -> dask.delayed:
        """
        """
        new_task = None

        if task_group not in self.tasks_graph:
            self.tasks_graph[task_group] = {}

        if task_group == "first_task":
            if self.tasks_graph["first_task"] is not None:
                raise ValueError("first task already present")
            new_task = dask.delayed(
                change_name(task.task_name)(self.task_launcher))(
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
                    change_name(task.task_name)(self.task_launcher))(
                        self.tasks_graph[task_dep_group],
                        log_err=task.log_err,
                        log_out=task.log_out,
                        scheduler_type=task.execution_mode,
                        pbs_worker_name=task.task_name,
                        resources=task.resources,
                        task_kwargs=task.parameters)
            else:
                new_task = dask.delayed(
                    change_name(task.task_name)(self.task_launcher))(
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

    def add_task_to_i2_processing_graph(
            self,
            task,
            task_group: str,
            task_sub_group: Optional[str] = None,
            task_dep_group: Optional[str] = None,
            task_dep_sub_group: Optional[str] = None) -> dask.delayed:
        """
        """
        # print(self.step_container)
        # print(len(self.step_container))
        # pause = input("W8")
        new_task = None

        if task_group not in self.tasks_graph:
            self.tasks_graph[task_group] = {}

        if task_group == "first_task":
            if self.tasks_graph["first_task"] is not None:
                raise ValueError("first task already present")
            new_task = dask.delayed(self.task_launcher)(
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
                new_task = dask.delayed(self.task_launcher)(
                    self.tasks_graph[task_dep_group],
                    log_err=task.log_err,
                    log_out=task.log_out,
                    scheduler_type=task.execution_mode,
                    pbs_worker_name=task.task_name,
                    resources=task.resources,
                    task_kwargs=task.parameters)
            elif len(self.step_container) != 1:
                new_task = dask.delayed(self.task_launcher)(
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
            else:
                new_task = dask.delayed(self.task_launcher)(
                    log_err=task.log_err,
                    log_out=task.log_out,
                    scheduler_type=task.execution_mode,
                    pbs_worker_name=task.task_name,
                    resources=task.resources,
                    task_kwargs=task.parameters)
            self.tasks_graph[task_group][task_sub_group] = new_task

        return new_task

    def parse_resource_file(self, step_name, cfg_resources_file):
        """
        parse a configuration file dedicated to reserve resources to HPC
        """
        from config import Config

        default_cpu = 1
        default_ram = "5gb"
        default_walltime = "00:10:00"

        cfg_resources = None
        if cfg_resources_file and os.path.exists(cfg_resources_file):
            cfg_resources = Config(cfg_resources_file)

        resource = {}
        cfg_step_resources = getattr(cfg_resources, str(step_name), {})
        resource["cpu"] = getattr(cfg_step_resources, "nb_cpu", default_cpu)
        resource["ram"] = getattr(cfg_step_resources, "ram", default_ram)
        resource["walltime"] = getattr(cfg_step_resources, "walltime",
                                       default_walltime)
        resource["resource_block_name"] = str(step_name)
        resource["resource_block_found"] = False
        if cfg_resources:
            resource["resource_block_found"] = str(step_name) in cfg_resources
        return resource

    def build_step_name(self):
        """
        strategy to build step name
        the name define logging ouput files and resources access
        """
        return self.__class__.__name__

    def __str__(self):
        return "{}".format(self.step_name)

    def step_description(self):
        return "quick step description"
