from functools import partial
from itertools import combinations, count, zip_longest
from os import mkdir
from shutil import rmtree
from datetime import datetime
import subprocess
from py.mi_algorithm import clean_string
import py.sim_worker as w
import multiprocessing as mp

from py.configurator import CalculateSettings

BATCH_SIZE = 1000
CHUNK_SIZE = 100


class MiSim(object):

    def __init__(self, config: CalculateSettings, announcer):
        self._cfg = config
        self.sentences = dict()
        self.announcer = partial(announcer, process="MiSim", start=datetime.now())
        self.batch_count = 0

    def load_sentences(self):
        raw_sentences = {}
        for file_name in self._cfg.sentence_files:
            with open("/app/data/%s" % file_name) as in_file:
                in_file.readline()
                raw_sentences.update({x[0]: x[1] for x in [l.split("\t") for l in in_file.readlines()]})
        self.announcer("loaded sentences")
        self.sentences = {k: clean_string(v) for k, v in raw_sentences.items()}
        self.announcer("cleaned sentences")
        self.batch_count = (len(self.sentences)*(len(self.sentences)-1)//2)//BATCH_SIZE
        return self.sentences

    def create_temp_dir(self):
        try:
            rmtree("/app/data/temp_sim")
        except FileNotFoundError:
            pass
        mkdir("/app/data/temp_sim")
        self.announcer("made temp_dir")

    def create_batch(self):
        pairs = combinations(self.sentences, 2)
        for batch_no, batch in zip(count(), zip_longest(*[iter(pairs)]*BATCH_SIZE, fillvalue=None)):
            yield batch_no, batch

    def calculate_similarities(self):
        self.announcer("made pairs")
        with mp.Pool(self._cfg.num_cores, initializer=w.init_worker, initargs=(self.sentences, self.announcer, self.batch_count, self._cfg)) as pool:
            pool.starmap_async(w.process_batch, self.create_batch(), chunksize=CHUNK_SIZE).get()
        self.announcer("calculated similarities")

    def merge_similarity_files(self):
        subprocess.run("cat /app/data/temp_sim/sims-*.csv > /app/data/output/%s_Mi.csv" % self._cfg.output_file, shell=True)
        self.announcer(msg="Catted all files to sims.csv")
        rmtree("/app/data/temp_sim")
        self.announcer(msg="Removed temp_sims")

    def main(self):
        self.load_sentences()
        self.create_batch()
        self.create_temp_dir()
        self.calculate_similarities()
        self.merge_similarity_files()