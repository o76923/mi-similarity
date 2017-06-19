import multiprocessing as mp
import os
import warnings
import yaml
from uuid import uuid4
from typing import Optional, List, Set, Text
from py.utils import *

CONFIG_FILE = "/app/data/" + os.environ.get("CONFIG_FILE", "config.yml")


class Task(object):
    num_cores: int
    temp_dir: Text
    type: TASK_TYPE

    def __init__(self, global_settings):
        self.num_cores = global_settings["num_cores"]
        self.temp_dir = global_settings["temp_dir"]


class Calculate(Task):
    source_files: List[Text]
    sim_algorithms: Set[COMPONENT_ALGORITHM]
    headers: bool
    numbered: bool
    output_format: OUTPUT_FORMAT
    output_file: Optional[Text]
    ds_name: Text

    def __init__(self, global_settings, task_settings):
        super().__init__(global_settings)

        self.type = TASK_TYPE.CALCULATE
        self.source_files = task_settings["from"]["files"]
        try:
            self.headers = task_settings["from"]["headers"]
        except KeyError:
            self.headers = False
        try:
            self.numbered = task_settings["from"]["numbered"]
        except KeyError:
            self.numbered = False
        try:
            self.output_format = OUTPUT_FORMAT[task_settings["output"]["format"]]
        except KeyError:
            self.output_format = OUTPUT_FORMAT.H5
        try:
            self.output_file = task_settings["output"]["file_name"]
        except KeyError:
            raise Exception("You must specify an output file_name when saving output")
        try:
            self.ds_name = task_settings["output"]["ds_name"]
        except KeyError:
            self.ds_name = 'sim'
            warnings.warn("No ds_name specified, using 'sim' as name of data source in sims")

        self.sim_algorithms = set()
        if "options" in task_settings:
            for alg in ("jcn", "res", "lin", "wup", "lch", "path"):
                try:
                    alg_setting = task_settings["options"][alg]
                    if alg_setting:
                        self.sim_algorithms.add(COMPONENT_ALGORITHM[alg.upper()])
                except KeyError:
                    pass
        else:
            print("no options present")


class Config(object):
    tasks: List[Task]
    temp_dir: str
    num_cores: int

    def __init__(self):
        self._read_config(CONFIG_FILE)
        self._load_global()
        self.temp_dir = "/app/data/tmp/mi_calc_{}".format(uuid4())
        self.tasks = []

        global_settings = {
            "temp_dir": self.temp_dir,
            "num_cores": self.num_cores,
            "tasks": self.tasks
        }

        for task in self._cfg['tasks']:
            self.tasks.append(self._load_task(global_settings, task))

    def _read_config(self, filename):
        with open(filename) as in_file:
            self._cfg = yaml.load(in_file.read())

    def _load_global(self):
        try:
            self.num_cores = int(self._cfg["options"]["cores"])
        except KeyError:
            self.num_cores = mp.cpu_count() - 1
            raise Warning("Number of cores not specified, defaulting to one less than max")
        except TypeError:
            self.num_cores = mp.cpu_count() - 1
            raise Warning("The number of cores must be an int, defaulting to one less than max insetad")

    def _load_task(self, global_settings, task_settings):
        try:
            if task_settings["type"] == "calculate_similarity":
                return Calculate(global_settings, task_settings)
            else:
                raise Exception("Invalid task type supplied")
        except KeyError:
            raise Exception("No task type specified")
