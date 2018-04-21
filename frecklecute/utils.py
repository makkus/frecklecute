# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import logging
from collections import OrderedDict

import yaml
from frkl import frkl
from luci import DictletFinder, TextFileDictletReader, JINJA_DELIMITER_PROFILES

from freckles.freckles_base_cli import parse_tasks_dictlet
from freckles.freckles_defaults import *

log = logging.getLogger("freckles")

def print_task_list_details(task_config, task_metadata={}, output_format="default", ask_become_pass="auto",
                            run_parameters={}):
    """Prints the details of a frecklecutable run (if started with the 'no-run' option).
    """

    click.echo()
    click.secho("========================================================", bold=True)
    click.echo()
    click.echo("'no-run' was specified, not executing frecklecute run.")
    click.echo()
    click.echo("Details about this run:")
    click.echo()
    click.secho("frecklecutable:", bold=True, nl=False)
    click.echo(" {}".format(task_metadata.get("command_name", "n/a")))
    click.echo()
    click.secho("Path:", bold=True, nl=False)
    click.echo(" {}".format(task_metadata.get("command_path", "n/a")))
    click.secho("Generated ansible environment:", bold=True, nl=False)
    click.echo(" {}".format(run_parameters.get("env_dir", "n/a")))
    # click.echo("config:")
    # output = yaml.safe_dump(task_config, default_flow_style=False, allow_unicode=True)
    # click.echo()
    # click.echo(output)
    #click.echo(pprint.pformat(task_config))
    # click.echo("")

    # pprint.pprint(run_parameters)
    click.echo("")
    click.secho("Tasks:", bold=True)
    for task in run_parameters["task_details"]:
        details = task.pretty_details()

        # pprint.pprint(details)
        output = yaml.safe_dump(details, default_flow_style=False)

        click.echo("")
        click.echo(output)
        click.echo("")

def find_frecklecutable_dirs(path, use_root_path=True):
    """Helper method to find 'child' frecklecutable dirs.

    Frecklecutables can either be in the root of a provided 'trusted-repo', or
    in any subfolder within, as long as the subfolder is called 'frecklecutables'.
    Also, if a subfolder contains a marker file called '.frecklecutables'.

    Args:
      path (str): the root path (usually the path to a 'trusted repo').
      use_root_path (bool): whether to include the supplied path
    Returns:
      list: a list of valid 'frecklecutable' paths
    """

    if not os.path.isdir(path):
        return []

    if use_root_path:
        result = [path]
    else:
        result = []

    for root, dirnames, filenames in os.walk(os.path.realpath(path), topdown=True, followlinks=True):

        dirnames[:] = [d for d in dirnames if d not in DEFAULT_EXCLUDE_DIRS]

        for dirname in dirnames:
            if dirname == "frecklecutables" or dirname == ".frecklecutables":
                dir_path = os.path.join(root, dirname)
                if dir_path not in result:
                    result.append(dir_path)

        for filename in filenames:
            if filename == ".frecklecutables":
                if root not in result:
                    result.append(root)

    return result

def is_frecklecutable(file_path, allow_dots_in_filename=False):

    if not allow_dots_in_filename and "." in os.path.basename(file_path):
        log.debug("Not using '{}' as frecklecutable: filename contains '.'".format(file_path))
        return False

    if not os.path.isfile(file_path):
        return False

    return True

def find_frecklecutables_in_folder(path, allow_dots_in_filename=False):

    result = OrderedDict()
    for child in os.listdir(path):

        file_path = os.path.realpath(os.path.join(path, child))

        if not is_frecklecutable(file_path):
            continue

        result[child] = {"path": file_path, "type": "file"}

    return result


class FrecklecutableFinder(DictletFinder):
    """Finder class for frecklecutables.

    First it checks whether there exists a file with the provided name.
    If that is not the case, it checks all configured context repos and tries
    to find the requested file in the root of the context repo, or in any subfolder that
    is called 'frecklecutables', or that has a marker file called '.frecklecutables' in
    it.

    Frecklecutables are not allowed to have a '.' in their file name (for now anyway).
    """

    def __init__(self, paths, **kwargs):

        super(FrecklecutableFinder, self).__init__(**kwargs)
        self.paths = paths
        self.frecklecutable_cache = None
        self.path_cache = {}

    def get_all_dictlet_names(self):

        return self.get_all_dictlets().keys()

    def get_all_dictlets(self):
        """Find all frecklecutables."""

        if self.frecklecutable_cache is None:
            self.frecklecutable_cache = {}
        all_frecklecutables = OrderedDict()

        for path in self.paths:
            if path not in self.path_cache.keys():
                commands = OrderedDict()
                dirs = find_frecklecutable_dirs(path)

                for f_dir in dirs:
                    fx = find_frecklecutables_in_folder(f_dir)
                    frkl.dict_merge(commands, fx, copy_dct=False)

                self.path_cache[path] = commands
                frkl.dict_merge(self.frecklecutable_cache, commands, copy_dct=False)

            frkl.dict_merge(all_frecklecutables, self.path_cache[path], copy_dct=False)

        return all_frecklecutables

    def get_dictlet(self, name):

        dictlet = None
        if self.frecklecutable_cache is None:
            # try path first
            abs_file = os.path.realpath(name)
            if os.path.isfile(abs_file) and is_frecklecutable(abs_file):
                dictlet = {"path": abs_file, "type": "file"}

        if dictlet is None:
            self.get_all_dictlet_names()
            dictlet = self.frecklecutable_cache.get(name, None)

        if dictlet is None:
            return None
        else:
            return dictlet

class FrecklecutableReader(TextFileDictletReader):
    """Reads a text file and generates metadata for frecklecute.

    The file needs to be in yaml format, if it contains a key 'args' the value of
    that is used to generate the frecklecutables command-line interface.
    The key 'defaults' is used for, well, default values. The most important key, and only
    required one is 'tasks'. The value of this is read as a string, which will then be used
    as a jinja2 template to create a valid task list, after overlaying several levels of default
    values if necessary.
    """

    def __init__(self, delimiter_profile=JINJA_DELIMITER_PROFILES["luci"], **kwargs):

        super(FrecklecutableReader, self).__init__(**kwargs)
        self.delimiter_profile = delimiter_profile
        self.tasks_keyword = FX_TASKS_KEY_NAME
        self.vars_keyword = FX_VARS_KEY_NAME

    def process_lines(self, content, current_vars):

        log.debug("Processing: {}".format(content))

        result = parse_tasks_dictlet(content, current_vars, self.tasks_keyword, self.vars_keyword, self.delimiter_profile)

        return result
