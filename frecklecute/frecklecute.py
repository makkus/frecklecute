# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import logging
from collections import OrderedDict

import yaml
from frkl import frkl
from six import string_types

from freckles.freckles_base_cli import create_external_task_list_callback, get_task_list_format
from freckles.freckles_defaults import *
from freckles.utils import create_and_run_nsbl_runner
from .utils import print_task_list_details

log = logging.getLogger("freckles")

DEFAULT_FRECKLECUTALBE_TASK_LIST_FORMAT = "freckles"


class Frecklecutable(object):
    def __init__(self,
                 name,
                 tasks,
                 vars,
                 tasks_format=None,
                 external_task_list_map={},
                 additional_roles=[]):

        self.name = name
        self.tasks = tasks
        if isinstance(tasks, string_types):
            self.tasks = yaml.safe_load(tasks)
            self.tasks_string = tasks
        elif isinstance(tasks, (list, tuple)):
            self.tasks = tasks
            self.tasks_string = yaml.safe_dump(tasks, default_flow_style=False)
        else:
            raise Exception("Invalid type for tasks list: {}".format(
                type(tasks)))

        self.vars = vars

        self.metadata = {}  # not used at the moment

        if tasks_format == None:
            log.debug("Trying to guess task-list format...")
            tasks_format = get_task_list_format(self.tasks)

            if tasks_format == None:
                log.info(
                    "Could not determine task list format for sure, falling back to '{}'.".
                    format(DEFAULT_FRECKLECUTALBE_TASK_LIST_FORMAT))
                tasks_format = DEFAULT_FRECKLECUTALBE_TASK_LIST_FORMAT
        self.tasks_format = tasks_format
        if self.tasks_format not in ["freckles", "ansible"]:
            raise Exception("Invalid task-list format: {}".format(
                self.tasks_format))

        self.external_task_list_map = external_task_list_map
        # getting ansible roles, this is not necessary for the 'freckles' configuration format
        self.additional_roles = additional_roles

        self.task_list_aliases = {}
        for name, details in self.external_task_list_map.items():
            self.task_list_aliases[name] = details["play_target"]

        # generating rendered tasks depending on task-list format
        if self.tasks_format == "ansible":
            relative_target_file = os.path.join(
                "{{ playbook_dir }}", "..", "task_lists",
                "frecklecutable_default_tasks.yml")
            self.final_tasks = [{
                "meta": {
                    "name": "include_tasks",
                    "task-desc": "[including tasks]",
                    "var-keys": ["free_form"],
                },
                "vars": {
                    "free_form": relative_target_file
                }
            }]

        else:
            self.final_tasks = self.tasks

        self.all_vars = frkl.dict_merge(
            vars, self.task_list_aliases, copy_dct=True)
        self.task_config = [{"tasks": self.final_tasks, "vars": self.all_vars}]


class Frecklecute(object):
    """Class to execute a list of tasks.

    This basically wraps an Ansible playbook run, including the generationn of an Ansible
    environment folder structure, auto-download/use of required roles, etc.
    """

    def __init__(self,
                 frecklecutables,
                 config=None,
                 ask_become_pass=False,
                 password=None):

        if not isinstance(frecklecutables, (list, tuple)):
            frecklecutables = [frecklecutables]

        self.frecklecutables = OrderedDict()
        for f in frecklecutables:
            self.frecklecutables[f.name] = f
        self.config = config
        self.ask_become_pass = ask_become_pass
        self.password = password

    def execute(self,
                hosts=["localhost"],
                no_run=False,
                output_format="default"):

        results = []
        for f in self.frecklecutables.keys():
            r = self.start_frecklecute_run(
                f, hosts=hosts, no_run=no_run, output_format=output_format)

    def start_frecklecute_run(self,
                              frecklecutable,
                              hosts=["localhost"],
                              no_run=False,
                              output_format="default"):

        f = self.frecklecutables.get(frecklecutable, False)
        if not f:
            raise Exception(
                "No frecklecutable '{}' found".format(frecklecutable))

        tasks_callback_map = [{
            "tasks": f.tasks,
            "tasks_string": f.tasks_string,
            "tasks_format": f.tasks_format,
            "target_name": "frecklecutable_default_tasks.yml"
        }]

        callback = create_external_task_list_callback(f.external_task_list_map,
                                                      tasks_callback_map)

        if no_run:
            parameters = create_and_run_nsbl_runner(
                f.task_config,
                task_metadata=f.task_metadata,
                output_format=output_format,
                pre_run_callback=callback,
                ask_become_pass=self.ask_become_pass,
                password=self.password,
                no_run=True,
                config=self.config,
                hosts_list=hosts,
                additional_roles=f.additional_roles)
            print_task_list_details(
                f.task_config,
                task_metadata=f.metadata,
                output_format=output_format,
                ask_become_pass=self.ask_become_pass,
                run_parameters=parameters)
            result = None
        else:
            result = create_and_run_nsbl_runner(
                f.task_config,
                task_metadata=f.metadata,
                output_format=output_format,
                pre_run_callback=callback,
                ask_become_pass=self.ask_become_pass,
                password=self.password,
                config=self.config,
                run_box_basics=True,
                hosts_list=hosts,
                additional_roles=f.additional_roles)

            click.echo()

        return result
