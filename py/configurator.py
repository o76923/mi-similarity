import multiprocessing as mp
import yaml


class TaskSettings(object):
    num_cores: int

    def __init__(self, num_cores):
        self.num_cores = num_cores


class CalculateSettings(TaskSettings):
    sentence_files: list
    pair_mode: str
    headers: bool
    output_file: str
    output_null: str

    def __init__(self, num_cores):
        super().__init__(num_cores)


class ConfigSettings(object):
    tasks: list
    num_cores: int

    def __init__(self, filename="/app/data/config.yml"):
        self._read_config(filename)
        self._load_global()
        self.tasks = []

        for t in self._cfg['tasks']:
            self.tasks.append(self._load_task(t))

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

    def _load_task(self, t):
        task = CalculateSettings(self.num_cores)
        try:
            if t["type"] != "calculate_similarity":
                raise Exception("The only task type supported at this time is calculate_similarity.")
        except KeyError:
            pass

        try:
            task.sentence_files = t["from"]["files"]
        except KeyError:
            raise Exception("You must specify source files containing texts to be compared")

        try:
            if t["from"]["pairs"] == "all":
                task.pair_mode = "all"
            else:
                raise Exception("The only currently supported pair mode is all")
        except KeyError:
            task.pair_mode = "all"

        try:
            if "headers" in t["from"]:
                task.headers = t["from"]["headers"]
            else:
                task.headers = False
        except KeyError:
            task.headers = False

        try:
            task.output_file = t["output"]["filename"]
        except KeyError:
            task.output_file = "sims.txt"

        try:
            if "nulls" in t['output']:
                task.null_output = str(t['output']['nulls'])
            else:
                task.null_output = "NULL"
        except KeyError:
            task.null_output = "NULL"
        return task