from functools import partial
from itertools import combinations, count, zip_longest
from os import getenv, mkdir
from shutil import rmtree
from datetime import datetime

import subprocess

from py.algorithm import clean_string
import py.worker as w
import multiprocessing as mp

filename = getenv("TARGET", "variable_definition")


def echo_message(msg, process, start, ):
    print("{:<20}{:<20}{:<39}".format(process, str(datetime.now()-start), msg))


class MiSim(object):

    def __init__(self):
        self.sentences = dict()
        self.announcer = partial(echo_message, process="MiSim", start=datetime.now())

    def load_sentences(self):
        with open("/app/data/%s.txt" % filename) as in_file:
            in_file.readline()
            raw_sentences = {x[0]: x[1] for x in [l.split("\t") for l in in_file.readlines()]}
        self.announcer("load sentences")
        self.sentences = {k: clean_string(v) for k, v in raw_sentences.items()}
        self.announcer("cleaned sentences")
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
        batch_size = 10000
        # batch_count = len(self.sentences)*(len(self.sentences)-1)//2
        for batch_no, batch in zip(count(), zip_longest(*[iter(pairs)]*batch_size, fillvalue=None)):
            yield batch_no, batch

    def calculate_similarities(self):
        self.announcer("made pairs")
        with mp.Pool(19, initializer=w.init_worker, initargs=(self.sentences, self.announcer)) as pool:
            pool.starmap_async(w.process_batch, self.create_batch(), chunksize=10).get()
        self.announcer("calculated similarities")

    def merge_similarity_files(self):
        subprocess.run("cat /app/data/temp_sim/sims-*.csv > /app/data/output/%s_Mi.csv" % filename, shell=True)
        self.announcer(msg="Catted all files to sims.csv")
        rmtree("/app/data/temp_sim")
        self.announcer(msg="Removed temp_sims")

    def main(self):
        self.load_sentences()
        self.create_batch()
        self.create_temp_dir()
        self.calculate_similarities()

if __name__ == "__main__":
    m = MiSim()
    m.main()