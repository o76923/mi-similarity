import subprocess
from datetime import datetime
from enum import Enum

TASK_TYPE = Enum('TASK_TYPE', 'CREATE PROJECT CALCULATE')
PAIR_MODE = Enum('PAIR_MODE', 'ALL CROSS LIST')
OUTPUT_FORMAT = Enum('OUTPUT_FORMAT', 'H5 CSV')


def run_cmd(cmd, raw=False):
    if raw:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run(["bash", "-c", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def announcer(msg, process, start):
    diff = datetime.now()-start
    days = diff.days
    hours = diff.seconds//3600
    minutes = diff.seconds//60 - hours * 60
    seconds = diff.seconds - minutes * 60 - hours * 3600
    print("{process:<20}{ts:<20}{msg:<39}".format(process=process,
                                                  ts="{:02d}d {:02d}h {:02d}m {:02d}s".format(days,
                                                                                              hours,
                                                                                              minutes,
                                                                                              seconds),
                                                  msg=msg))
