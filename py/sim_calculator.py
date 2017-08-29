import sys
from itertools import combinations

import h5py
import numpy as np
import multiprocessing as mp
import os
import shutil
# from mpi4py import MPI
from py.configurator import Calculate
from py.string_cleaner import init_worker, clean_string
from py.utils import *
from functools import partial
from py.mi_algorithm import MiSim
from nltk.corpus import wordnet as wn


@memoize
def in_wordnet(word):
    return len(wn.synsets(word, 'nv')) > 0


class SimCalculator(object):
    def __init__(self, config: Calculate, start_time):
        self._cfg = config
        self.announcer = partial(announcer, process="Calculator", start=start_time)
        self.raw_sentences = dict()
        self.sentences = dict()
        self.wn_tokens = dict()
        self.sorted_ids = []
        self._init_h5()

    def _init_h5(self):
        string_dt = h5py.h5t.special_dtype(vlen=str)
        if self._cfg.output_format == OUTPUT_FORMAT.H5:
            self.file_name = '/app/data/{}'.format(self._cfg.output_file)
        if self._cfg.output_format == OUTPUT_FORMAT.CSV:
            self.file_name = '/app/data/{}'.format(self._cfg.output_file)[:-3] + 'h5'
        self.f = h5py.File(self.file_name, 'w', libver='latest')
        shutil.chown(self.f.filename, user=1000)
        self.f.attrs.create("jcn", COMPONENT_ALGORITHM.JCN in self._cfg.sim_algorithms, dtype=bool)
        self.f.attrs.create("lin", COMPONENT_ALGORITHM.LIN in self._cfg.sim_algorithms, dtype=bool)
        self.f.attrs.create("wup", COMPONENT_ALGORITHM.WUP in self._cfg.sim_algorithms, dtype=bool)
        self.f.attrs.create("lch", COMPONENT_ALGORITHM.LCH in self._cfg.sim_algorithms, dtype=bool)
        self.f.attrs.create("path", COMPONENT_ALGORITHM.PATH in self._cfg.sim_algorithms, dtype=bool)

        self.input = self.f.require_group("input")
        self.input.attrs.create("description", "Source data fed into the algorithm and preprocessing steps.",
                             dtype=string_dt)

        sim = self.f.require_group("sim")
        sim.attrs.create("description", "Semantic similarity scores between pairs of sentences.", dtype=string_dt)
        self.f.flush()

    def _save_inputs(self):
        string_dt = h5py.h5t.special_dtype(vlen=str)
        id_ = self.input.require_dataset("id",
                                      dtype='u8',
                                      shape=(len(self.sentences),),
                                      data=np.array(self.sorted_ids))
        id_.attrs.create("description", "The id for each sentence provided by the user.", dtype=string_dt)
        text = self.input.require_dataset("text",
                                       dtype=string_dt,
                                       shape=(len(self.sentences),),
                                       data=[" ".join(self.raw_sentences[x]).encode('utf-8') for x in self.sorted_ids])
        text.attrs.create("description", "The raw text of the sentence provided by the user.", dtype=string_dt)
        tok = self.input.require_dataset("tokenized_text",
                                      dtype=string_dt,
                                      shape=(len(self.sentences),),
                                      data=[" ".join(self.sentences[x]).encode('utf-8') for x in self.sorted_ids])
        tok.attrs.create("description", "The tokenized words from the text with punctuation and stopwords removed.",
                         dtype=string_dt)
        wnt = self.input.require_dataset("wordnet_tokens",
                                      dtype=string_dt,
                                      shape=(len(self.sentences),),
                                      data=[" ".join(self.wn_tokens[x]).encode('utf-8') for x in self.sorted_ids])
        wnt.attrs.create("description",
                         "The tokens from tokenized_text where wordnet has at least one synset that  is either a noun "
                         "or a verb.",
                         dtype=string_dt)

        text.dims.create_scale(id_, 'sentence_id')
        text.dims[0].attach_scale(id_)
        tok.dims[0].attach_scale(id_)
        wnt.dims[0].attach_scale(id_)

        self.ds = self.f["/sim"].require_dataset(self._cfg.ds_name,
                                      dtype=np.float16,
                                      shape=(len(self.sentences), len(self.sentences)),
                                      fillvalue=0.0,
                                      compression="gzip",
                                      compression_opts=9,
                                      shuffle=True)
        self.ds.attrs.create("description",
                             "The similarity scores between pairs of sentences according to the Mi algorithm",
                             dtype=string_dt)
        self.f.flush()

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
        self.wn_tokens = {k: [w for w in v if in_wordnet(w)] for k, v in self.sentences.items()}
        self.sorted_ids = sorted(self.sentences.keys())

    def _close_file(self):
        print("close filename", self.f.filename)
        self.f.flush()
        self.f.close()

    # def launch_workers(self):
    #     comm = MPI.COMM_SELF.Spawn(sys.executable,
    #                                args=['-m', 'py.sim_worker'],
    #                                maxprocs=self._cfg.num_cores-1).Merge()
    #     self.announcer("Workers launched")
    #     comm.bcast(self.announcer, root=0)
    #     self.announcer("Announcer broadcast")
    #     comm.bcast(self.file_name, root=0)
    #     self.announcer("file_name broadcast")
    #     comm.bcast(self._cfg.sim_algorithms, root=0)
    #     self.announcer("Broadcast cfg")
    #     comm.Disconnect()
    #     self.announcer("Disconnected from COMM_SELF")

    def calculate_sims(self):
        mi = MiSim(self._cfg.sim_algorithms)
        self.announcer("init mi")
        for ix in range(len(self.sorted_ids)):
            self.ds[ix, ix] = 1.0
        for (left_index, left_id), (right_index, right_id) in combinations(enumerate(self.sorted_ids), 2):
            self.ds[left_index, right_index] = mi.similarity(self.wn_tokens[left_id], self.wn_tokens[right_id])
            # print(left_id, right_id, self.ds[left_index, right_index], self.wn_tokens[left_id], self.wn_tokens[right_id])

    def convert_to_csv(self):
        sims = self.ds[:]
        with open('/app/data/{}'.format(self._cfg.output_file), "w") as out_file:
            for (left, right), val in zip(combinations(self.sorted_ids, 2), sims[np.triu_indices_from(sims, k=1)]):
                out_file.write("{},{},{:0.3f}\n".format(left, right, val))

    def main(self):
        self.load_sentences()
        self.announcer("Loaded sentences")
        self.clean_sentences()
        self.announcer("Cleaned sentences")
        self._save_inputs()
        self.announcer("Saved sentences")
        self.calculate_sims()
        self.announcer("calculated similarities")
        if self._cfg.output_format == OUTPUT_FORMAT.CSV:
            self.announcer("converting to CSV")
            self.convert_to_csv()
            self.announcer("Made CSV")
        self._close_file()
        self.announcer("Closed h5 file")
        # self.launch_workers()
