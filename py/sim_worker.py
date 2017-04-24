import re
from functools import partial
import multiprocessing as mp
from py.mi_algorithm import MihalceaSentSimBNC


class SimBatchWorker(object):

    def __init__(self, sentences, announcer, batch_count, config):
        self.process_id = int(re.search("(\d+)$", mp.current_process().name).group(1))
        self.dest_file = "/app/data/temp_sim/sims-%d.csv" % self.process_id
        self.mi = MihalceaSentSimBNC()
        self.sentence_dict = sentences
        self.announcer = partial(announcer, process="SimBatchWorker-%d" % self.process_id)
        self.batch_count = batch_count
        self._cfg = config

    def write_to_file(self, lines):
        lt = "".join(["{},{},{:0.4f}\n".format(l, r, s) for l, r, s in lines])
        with open(self.dest_file, "a") as out_file:
            out_file.writelines(lt)

sbw: SimBatchWorker


def init_worker(sentences, announcer, batch_count, config):
    global sbw
    sbw = SimBatchWorker(sentences, announcer, batch_count, config)


def process_batch(batch_no, batch):
    global sbw
    rows = []
    for b in batch:
        try:
            l, r = b
            rows.append((l, r, sbw.mi.similarity(sbw.sentence_dict[l], sbw.sentence_dict[r])))
        except TypeError:
            pass
    sbw.write_to_file(rows)
    if batch_no % 100 == 0:
        sbw.announcer("wrote batch {:>7,d}/{:,d}".format(batch_no, sbw.batch_count))