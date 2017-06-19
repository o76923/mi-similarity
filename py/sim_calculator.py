import sys
import h5py as h5
import numpy as np
import multiprocessing as mp
import os
import shutil
from mpi4py import MPI
from py.configurator import Calculate
from py.string_cleaner import init_worker, clean_string
from py.utils import *
from functools import partial


class SimCalculator(object):
    def __init__(self, config: Calculate, start_time):
        self._cfg = config
        self.announcer = partial(announcer, process="Calculator", start=start_time)
        self.raw_sentences = dict()
        self.sentences = dict()
        self.sorted_ids = []
        self._init_hdf5()

    def _init_hdf5(self):
        try:
            os.mkdir("/app/data/output")
            shutil.chown("/app/data/output/", user=1000)
        except FileExistsError:
            pass
        self.f = h5.File("/app/data/output/{}".format(self._cfg.output_file), 'w')
        shutil.chown(self.f.filename, user=1000)

    def load_sentences(self):
        self.raw_sentences = {}
        for source_file in self._cfg.source_files:
            with open("/app/data/{}".format(source_file)) as in_file:
                new_documents = {}
                if self._cfg.headers:
                    in_file.readline()

                if self._cfg.numbered:
                    for line in in_file.readlines():
                        sentence_id, sentence_text = line[:-1].split("\t")
                        new_documents[int(sentence_id)] = sentence_text
                else:
                    sentence_id = 0
                    for line in in_file:
                        new_documents[sentence_id] = line[:-1]
                        sentence_id += 1
                self.raw_sentences.update(new_documents)

    def clean_sentences(self):
        with mp.Pool(self._cfg.num_cores, initializer=init_worker) as pool:
            self.sentences = {k: v for k, v in
                              pool.starmap_async(func=clean_string, iterable=self.raw_sentences.items()).get()}
        self.sentences = {k: v for k, v in self.sentences.items() if len(v) > 0}
        self.sorted_ids = sorted(self.sentences.keys())

    def save_input(self):
        in_data = self.f.require_group("input")
        in_data.require_dataset("id",
                                dtype=np.uint32,
                                shape=(len(self.sentences),),
                                data=np.array(self.sorted_ids))
        string_dt = h5.h5t.special_dtype(vlen=str)
        in_data.require_dataset("text",
                                dtype=string_dt,
                                shape=(len(self.sentences),),
                                data=[self.raw_sentences[x].encode('utf-8') for x in self.sorted_ids],
                                compression="gzip",
                                compression_opts=9,
                                shuffle=True)
        in_data.require_dataset("tokenized_text",
                                dtype=string_dt,
                                shape=(len(self.sentences),),
                                data=[" ".join(self.sentences[x]).encode('utf-8') for x in self.sorted_ids],
                                compression="gzip",
                                compression_opts=9,
                                shuffle=True)

    def _init_sim(self):
        sim = self.f.require_group("sim")
        self.ds = sim.require_dataset(self._cfg.ds_name,
                                      dtype=np.float32,
                                      shape=(len(self.sentences), len(self.sentences)),
                                      fillvalue=0.0)

    def _close_file(self):
        self.f.flush()
        self.f.close()

    def launch_workers(self):
        comm = MPI.COMM_SELF.Spawn(sys.executable,
                                   args=['-m', 'py.sim_worker'],
                                   maxprocs=self._cfg.num_cores-1).Merge()
        self.announcer("Workers launched")
        comm.bcast(self.announcer, root=0)
        comm.bcast("/app/data/output/{}".format(self._cfg.output_file), root=0)
        comm.bcast(self._cfg.sim_algorithms, root=0)
        self.announcer("Broadcast filename, alg list, and announcer")
        comm.Disconnect()
        self.announcer("Disconnected from COMM_SELF")

    def main(self):
        self.load_sentences()
        self.announcer("Loaded sentences")
        self.clean_sentences()
        self.announcer("Cleaned sentences")
        self.save_input()
        self.announcer("Saved sentences")
        self._init_sim()
        self.announcer("Initialized similarities")
        self._close_file()
        self.announcer("Closed h5 file")
        self.launch_workers()
