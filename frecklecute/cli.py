# -*- coding: utf-8 -*-

"""Console script for frecklecute."""

from __future__ import absolute_import, division, print_function

import logging
import os
import sys

import click
import click_completion
import click_log
import copy
import nsbl
import shutil
import yaml
from collections import OrderedDict
from six import string_types
from pprint import pprint
from frkl import frkl
from luci import Lucifier, DictletReader, DictletFinder, vars_file, TextFileDictletReader, parse_args_dict, output, JINJA_DELIMITER_PROFILES, replace_string, ordered_load, clean_user_input, readable_json
from . import print_version
from freckles.freckles_defaults import *
from freckles.utils import DEFAULT_FRECKLES_CONFIG, download_extra_repos, HostType, print_repos_expand, expand_repos,  create_and_run_nsbl_runner, freckles_jinja_extensions, download_repos
from freckles.freckles_base_cli import FrecklesBaseCommand, FrecklesLucifier, process_extra_task_lists, create_external_task_list_callback, get_task_list_format, parse_tasks_dictlet
from .frecklecute import Frecklecute
from .utils import print_task_list_details, find_frecklecutable_dirs, is_frecklecutable, find_frecklecutables_in_folder, FrecklecutableFinder, FrecklecutableReader

log = logging.getLogger("freckles")
click_log.basic_config(log)

# optional shell completion
click_completion.init()

# TODO: this is a bit ugly, probably have refactor how role repos are used
# nsbl.defaults.DEFAULT_ROLES_PATH = os.path.join(os.path.dirname(__file__), "external", "default_role_repo")

VARS_HELP = "variables to be used for templating, can be overridden by cli options if applicable"
DEFAULTS_HELP = "default variables, can be used instead (or in addition) to user input via command-line parameters"
KEEP_METADATA_HELP = "keep metadata in result directory, mostly useful for debugging"
FRECKLECUTE_EPILOG_TEXT = "frecklecute is free and open source software and part of the 'freckles' project, for more information visit: https://docs.freckles.io"



class FrecklecuteCommand(FrecklesBaseCommand):
    """Class to build the frecklecute command-line interface."""

    def __init__(self, extra_params=None, print_version_callback=print_version, **kwargs):

        super(FrecklecuteCommand, self).__init__(extra_params=extra_params, print_version_callback=print_version, **kwargs)

    def get_dictlet_finder(self):

        return FrecklecutableFinder(self.paths)

    def get_dictlet_reader(self):

        return FrecklecutableReader()

    def get_additional_args(self):
        return {}

    def freckles_process(self, command_name, default_vars, extra_vars, user_input, metadata, dictlet_details, config, parent_params, command_var_spec):


        all_vars = OrderedDict()
        frkl.dict_merge(all_vars, default_vars, copy_dct=False)
        for ev in extra_vars:
            frkl.dict_merge(all_vars, ev, copy_dct=False)
        frkl.dict_merge(all_vars, user_input, copy_dct=False)

        hosts = parent_params.get("hosts", ["localhost"])
        output_format = parent_params.get("output", "default")
        password_type = parent_params.get("password", None)
        no_run = parent_params.get("no_run", False)

        tasks_string = metadata.get(FX_TASKS_KEY_NAME, "")
        vars_string = metadata.get(FX_VARS_KEY_NAME, "")

        replaced_vars = replace_string(vars_string, all_vars, additional_jinja_extensions=freckles_jinja_extensions, **JINJA_DELIMITER_PROFILES["luci"])
        try:
            vars_dictlet = yaml.safe_load(replaced_vars)
        except (Exception) as e:
            raise Exception("Can't parse vars: {}".format(e))

        if vars_dictlet:
            temp_new_all_vars = frkl.dict_merge(all_vars, vars_dictlet, copy_dct=True)
        else:
            temp_new_all_vars = all_vars

        replaced_tasks = replace_string(tasks_string, temp_new_all_vars, additional_jinja_extensions=freckles_jinja_extensions, **JINJA_DELIMITER_PROFILES["luci"])
        try:
            tasks_list = ordered_load(replaced_tasks)
        except (Exception) as e:
            raise click.ClickException("Could not parse frecklecutable '{}': {}".format(command_name, e))

        extra_task_lists_map = process_extra_task_lists(metadata, dictlet_details["path"])

        # check for hardcoded task_list_format:
        task_list_format = metadata.get("__freckles__", {}).get("task_list_format", None)

        additional_roles = metadata.get("__freckles__", {}).get("roles", [])

        result_vars = {}
        for name, details in command_var_spec.items():
            if name in temp_new_all_vars and details.get("is_var", False) == True:
                result_vars[name] = temp_new_all_vars[name]

        f = Frecklecutable(command_name, tasks_list, result_vars, tasks_format=task_list_format, external_task_list_map=extra_task_lists_map, additional_roles=additional_roles, tasks_string=tasks_string)

        # placeholder, for maybe later
        task_metadata = {}

        if password_type is None:
            password_type = "no"

        if password_type == "ask":
            password = click.prompt("Please enter sudo password for this run", hide_input=True)
            click.echo()
            password_type = False
            # TODO: check password valid
        elif password_type == "ansible":
            password_type = True
            password = None
        elif password_type == "no":
            password_type = False
            password = None
        else:
            raise Exception("Can't process password: {}".format(password_type))

        run = Frecklecute(f, config=self.config, ask_become_pass=password_type, password=password)
        run.execute(hosts=hosts, no_run=no_run, output_format=output_format)

@click.command(name="frecklecute", cls=FrecklecuteCommand, epilog=FRECKLECUTE_EPILOG_TEXT, subcommand_metavar="FRECKLECUTEABLE")
@click_log.simple_verbosity_option(log, "--verbosity")
@click.pass_context
def cli(ctx, **kwargs):
    """Executes a list of tasks specified in a (yaml-formated) text file (called a 'frecklecutable').

    *frecklecute* comes with a few default frecklecutables that are used to manage itself (as well as its sister application *freckles*) as well as a few useful generic ones. Visit the online documentation for more details: https://docs.freckles.io/en/latest/frecklecute_command.html
    """
    pass

if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
