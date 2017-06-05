import os
from datetime import datetime
from functools import partial
from shutil import rmtree
from py.utils import *
from py.configurator import Config
from py.sim_calculator import SimCalculator

start_time = datetime.now()
announcer = partial(announcer, process="Delegator", start=start_time)

cfg = Config()
announcer("Loaded Configuration")

os.makedirs(cfg.temp_dir)
announcer("Created temp directory at {}".format(cfg.temp_dir))

for task in cfg.tasks:
    t = SimCalculator(task, start_time)
    t.main()
    announcer("Finished Task")
announcer("Finished All Tasks")

rmtree(cfg.temp_dir)
announcer("Removed temp directory")

announcer("Done")