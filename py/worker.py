import re
from functools import partial
from os import getenv
import multiprocessing as mp
from py.algorithm import MihalceaSentSimBNC

filename = getenv("TARGET", "variable_definition")


class SimBatchWorker(object):

    def __init__(self, sentences, announcer):
        self.process_id = int(re.search("(\d+)$", mp.current_process().name).group(1))
        self.dest_file = "/app/data/temp_sim/sims-%d.csv" % self.process_id
        self.mi = MihalceaSentSimBNC()
        self.sentence_dict = sentences
        self.announcer = partial(announcer, process="SimBatchWorker-%d" % self.process_id)

    def write_to_file(self, lines):
        lt = "".join(["{},{},{:0.4f}\n".format(l, r, s) for l, r, s in lines])
        with open(self.dest_file, "a") as out_file:
            out_file.writelines(lt)

sbw: SimBatchWorker


def init_worker(sentences, announcer):
    global sbw
    sbw = SimBatchWorker(sentences, announcer)


def process_batch(batch_no, batch):
    global sbw
    rows = []
    for b in batch:
        try:
            l, r = b
            rows.append((l, r, sbw.mi.similarity(sbw.sentence_dict[l], sbw.sentence_dict[r])))
        except ValueError:
            pass
    sbw.write_to_file(rows)
    if batch_no % 100 == 0:
        sbw.announcer("wrote batch {:,d}".format(batch_no))