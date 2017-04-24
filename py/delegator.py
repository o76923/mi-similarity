from datetime import datetime
from functools import partial

from py.configurator import ConfigSettings
from py.sim_calculator import MiSim


def echo_message(msg, process, start, ):
    diff = datetime.now()-start
    days = diff.days
    hours = diff.seconds//3600
    minutes = diff.seconds//60 - hours * 60
    seconds = diff.seconds - minutes * 60
    print("{process:<20}{ts:<20}{msg:<39}".format(process=process, ts="{:02d}d {:02d}h {:02d}m {:02d}s".format(days, hours, minutes, seconds), msg=msg))


if __name__ == "__main__":
    start_time = datetime.now()
    announcer = partial(echo_message, process="Delegator", start=start_time)
    cfg = ConfigSettings()
    announcer("Loaded Configuration")
    for task in cfg.tasks:
        s = MiSim(task, partial(echo_message, start=start_time))
        s.main()
        announcer("Finished Task")
    announcer("Done")
