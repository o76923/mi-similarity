import math
import difflib
import numpy as np
from itertools import product, groupby
from collections import defaultdict
from functools import partial
from nltk.corpus import wordnet as wn
from nltk.corpus import wordnet_ic
from nltk.corpus.reader import Synset
from nltk.corpus import stopwords
from py.utils import *


class MiSim(object):

    # Based on all leaf nouns that didn't have an IC of 1e+300
    MAX_ICx2 = 19.05665959003492 ** 2.0

    # Based on orthographic word count from http://www.natcorp.ox.ac.uk/corpus/index.xml?ID=numbers
    LN_SYN_COUNT = math.log(96986707.0)

    # The max depth based on wn._compute_max_depth('n', False) is 19
    LCH_MAX = -math.log(1.0/(2.0*19.0))

    def __init__(self, algs):
        self._load_idf()
        self.ic = wordnet_ic.ic('ic-bnc.dat')
        self.stopwords = set(stopwords.words('english'))
        self._set_algs(algs)

    def _load_idf(self):
        self.idf = {}
        with open('/app/data/bnc.ic', 'r') as bnc_idf:
            for line in bnc_idf:
                word, score = line.split(',')
                self.idf[word] = float(score)

    def _set_algs(self, algs):
        self.sim_functions = []
        if COMPONENT_ALGORITHM.JCN in algs:
            self.sim_functions.append(self.jcn_sim)
        if COMPONENT_ALGORITHM.RES in algs:
            self.sim_functions.append(self.res_sim)
        if COMPONENT_ALGORITHM.LIN in algs:
            self.sim_functions.append(partial(wn.lin_similarity, ic=self.ic))
        if COMPONENT_ALGORITHM.WUP in algs:
            self.sim_functions.append(wn.wup_similarity)
        if COMPONENT_ALGORITHM.LCH in algs:
            self.sim_functions.append(self.lch_sim)
        if COMPONENT_ALGORITHM.PATH in algs:
            self.sim_functions.append(wn.path_similarity)

    def jcn_sim(self, left_syn, right_syn):
        raw_sim = wn.jcn_similarity(left_syn, right_syn, self.ic)
        raw_dist = 1.0/raw_sim
        scaled_sim = 1.0 - raw_dist / self.MAX_ICx2
        return scaled_sim

    def res_sim(self, left_syn, right_syn):
        raw_sim = wn.res_similarity(left_syn, right_syn, self.ic)
        scaled_sim = raw_sim / self.LN_SYN_COUNT
        return scaled_sim

    def lch_sim(self, left_syn, right_syn):
        raw_sim = wn.lch_similarity(left_syn, right_syn)
        scaled_sim = raw_sim / self.LCH_MAX
        return scaled_sim

    def lesk_sim(self, left_syn: Synset, right_syn: Synset):
        from uuid import uuid4
        left_data = {
            "also": ' #{}# '.format(uuid4()).join(left_syn.also_sees()),
            "attr": ' #{}# '.format(uuid4()).join(left_syn.also_sees()),
            "example": ' #{}# '.format(uuid4()).join(left_syn.examples()),
            "glos": left_syn.definition(),
            "holo": ' #{}# '.format(uuid4()).join([l.definition() for l in left_syn.member_holonyms() + left_syn.part_holonyms() + left_syn.substance_holonyms()]),
            "hype": ' #{}# '.format(uuid4()).join([l.definition() for l in left_syn.hypernyms()]),
            "hypo": ' #{}# '.format(uuid4()).join([l.definition() for l in left_syn.hyponyms()]),
            "mero": ' #{}# '.format(uuid4()).join([l.definition() for l in left_syn.member_meronyms() + left_syn.part_meronyms() + left_syn.substance_meronyms()]),
            "pert": ' #{}# '.format(uuid4()).join([' #{}# '.format(uuid4()).join(l.pertainyms()) for l in left_syn.lemmas()]),
            "sim": ' #{}# '.format(uuid4()).join(left_syn.similar_tos()),
            "syns": ' #{}# '.format(uuid4()).join(set([l.name() for l in left_syn.lemmas()]))
        }
        left_data = {k:  [t for t in v.split(' ') if len(t) > 0] for (k, v) in left_data.items()}
        right_data = {
            "also": ' #{}# '.format(uuid4()).join(right_syn.also_sees()),
            "attr": ' #{}# '.format(uuid4()).join(right_syn.also_sees()),
            "example": ' #{}# '.format(uuid4()).join(right_syn.examples()),
            "glos": right_syn.definition(),
            "holo": ' #{}# '.format(uuid4()).join([l.definition() for l in right_syn.member_holonyms() + right_syn.part_holonyms() + right_syn.substance_holonyms()]),
            "hype": ' #{}# '.format(uuid4()).join([l.definition() for l in right_syn.hypernyms()]),
            "hypo": ' #{}# '.format(uuid4()).join([l.definition() for l in right_syn.hyponyms()]),
            "mero": ' #{}# '.format(uuid4()).join([l.definition() for l in right_syn.member_meronyms() + right_syn.part_meronyms() + right_syn.substance_meronyms()]),
            "pert": ' #{}# '.format(uuid4()).join([' #{}# '.format(uuid4()).join(l.pertainyms()) for l in right_syn.lemmas()]),
            "sim": ' #{}# '.format(uuid4()).join(right_syn.similar_tos()),
            "syns": ' #{}# '.format(uuid4()).join(set([l.name() for l in right_syn.lemmas()]))
        }
        right_data = {k: [t for t in v.split(' ') if len(t) > 0] for (k, v) in right_data.items()}
        combinations = (
            ("also", "also"),
            ("also", "attr"),
            ("also", "glos"),
            ("also", "holo"),
            ("also", "hype"),
            ("also", "hypo"),
            ("also", "mero"),
            ("also", "pert"),
            ("also", "sim"),
            ("attr", "also"),
            ("attr", "attr"),
            ("attr", "glos"),
            ("attr", "holo"),
            ("attr", "hype"),
            ("attr", "hypo"),
            ("attr", "mero"),
            ("attr", "pert"),
            ("attr", "sim"),
            ("example", "example"),
            ("example", "glos"),
            ("example", "syns"),
            ("glos", "also"),
            ("glos", "attr"),
            ("glos", "example"),
            ("glos", "glos"),
            ("glos", "holo"),
            ("glos", "hype"),
            ("glos", "hypo"),
            ("glos", "mero"),
            ("glos", "pert"),
            ("glos", "sim"),
            ("glos", "syns"),
            ("holo", "also"),
            ("holo", "attr"),
            ("holo", "glos"),
            ("holo", "holo"),
            ("holo", "hype"),
            ("holo", "hypo"),
            ("holo", "mero"),
            ("holo", "pert"),
            ("holo", "sim"),
            ("hype", "also"),
            ("hype", "attr"),
            ("hype", "glos"),
            ("hype", "holo"),
            ("hype", "hype"),
            ("hype", "hypo"),
            ("hype", "mero"),
            ("hype", "pert"),
            ("hype", "sim"),
            ("hypo", "also"),
            ("hypo", "attr"),
            ("hypo", "glos"),
            ("hypo", "holo"),
            ("hypo", "hype"),
            ("hypo", "hypo"),
            ("hypo", "mero"),
            ("hypo", "pert"),
            ("hypo", "sim"),
            ("mero", "also"),
            ("mero", "attr"),
            ("mero", "glos"),
            ("mero", "holo"),
            ("mero", "hype"),
            ("mero", "hypo"),
            ("mero", "mero"),
            ("mero", "pert"),
            ("mero", "sim"),
            ("pert", "also"),
            ("pert", "attr"),
            ("pert", "glos"),
            ("pert", "holo"),
            ("pert", "hype"),
            ("pert", "hypo"),
            ("pert", "mero"),
            ("pert", "pert"),
            ("pert", "sim"),
            ("sim", "also"),
            ("sim", "attr"),
            ("sim", "glos"),
            ("sim", "holo"),
            ("sim", "hype"),
            ("sim", "hypo"),
            ("sim", "mero"),
            ("sim", "pert"),
            ("sim", "sim"),
            ("syns", "example"),
            ("syns", "glos"),
        )
        for left_key, right_key in combinations:
            print(left_key, right_key)
            sm = difflib.SequenceMatcher(None, left_data[left_key], right_data[right_key])
            for a, b, size in sm.get_matching_blocks()[:-1]:
                overlap = left_data[left_key][a:a+size]
                if not all([o in self.stopwords for o in overlap]):
                    print(left_data[left_key], right_data[right_key])
                    print(overlap)
        exit()

    @memoize
    def get_synsets(self, word):
        ret = defaultdict(list)
        group = {k: list(i[1] for i in v) for k, v in groupby([(s.pos(), s) for s in wn.synsets(word)], key=lambda x: x[0])}
        ret.update(group)
        return ret

    @memoize
    def average_syn_score(self, left_syn, right_syn):
        # If words are same, return 1.0
        if left_syn == right_syn:
            return 1.0
        sims = [fn(left_syn, right_syn) for fn in self.sim_functions]
        # print(left_syn, right_syn, sims)
        return np.nanmean(sims)

    @memoize
    def average_word_score(self, left_word, right_word):
        if left_word == right_word:
            return 1.0

        left_syns = self.get_synsets(left_word)
        right_syns = self.get_synsets(right_word)

        best_sim = 0.0
        for pos in ('n', 'v'):
            for left_syn, right_syn in product(left_syns[pos], right_syns[pos]):
                new_sim = self.average_syn_score(left_syn, right_syn)
                if new_sim > best_sim:
                    best_sim = new_sim

        return best_sim

    def token_sim_matrix(self, left_tokens, right_tokens):
        # Make an empty matrix to store each word-word similarity
        sim_mat = np.zeros((len(left_tokens), len(right_tokens)))

        # Iterate through each word in both sentences
        for left_index, left_word in enumerate(left_tokens):
            for right_index, right_word in enumerate(right_tokens):
                sim_mat[left_index, right_index] = self.average_word_score(left_word, right_word)

        # return the sim matrix
        return sim_mat

    def similarity(self, left_tokens, right_tokens):
        token_sim = self.token_sim_matrix(left_tokens, right_tokens)

        left_maxes = np.argmax(token_sim, 1)
        left_idf = [self.idf[t] for t in left_tokens]
        left_scores = token_sim[(range(len(left_maxes)), left_maxes)]
        left_half = np.sum(left_idf * left_scores) / np.sum(left_idf)

        right_maxes = np.argmax(token_sim, 0)
        right_idf = [self.idf[t] for t in right_tokens]
        right_scores = token_sim[(right_maxes, range(len(right_maxes)))]
        right_half = np.sum(right_idf * right_scores) / np.sum(right_idf)

        return (left_half + right_half) * 0.5
