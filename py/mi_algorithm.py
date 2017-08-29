import math
import numpy as np
from itertools import product, groupby
from collections import defaultdict
from functools import partial
from nltk.corpus import wordnet as wn
from nltk.corpus import wordnet_ic
from nltk.corpus import stopwords
from nltk.corpus.reader.wordnet import Synset, _lcs_ic
from py.utils import *


class MiSim(object):

    # Based on all leaf nouns that didn't have an IC of 1e+300
    MAX_ICx2 = 19.05665959003492 ** 2.0

    # Based on lorthographic word count from http://www.natcorp.ox.ac.uk/corpus/index.xml?ID=numbers
    LN_SYN_COUNT = math.log(96986707.0)

    # The max depth based on wn._compute_max_depth('n', False) is 19
    LCH_MAX = -math.log(1.0 / (2.0 * 19.0))

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
            self.sim_functions.append(partial(wn.jcn_similarity, ic=self.ic))
        if COMPONENT_ALGORITHM.LIN in algs:
            self.sim_functions.append(partial(wn.lin_similarity, ic=self.ic))
        if COMPONENT_ALGORITHM.WUP in algs:
            self.sim_functions.append(wn.wup_similarity)
        if COMPONENT_ALGORITHM.LCH in algs:
            self.sim_functions.append(self.lch_sim)
        if COMPONENT_ALGORITHM.PATH in algs:
            self.sim_functions.append(wn.path_similarity)

    def svh_sim(self, left_syn, right_syn):
        # Normalized Jiang & Conrath similarity based on forumla 6 in Seco, Veale, and Hayes
        left_ic, right_ic, lcs_ic = _lcs_ic(left_syn, right_syn, self.ic)
        return 1.0 - ((left_ic + right_ic - 2.0 * wn.res_similarity(left_syn, right_syn, self.ic))/2.0)

    def res_sim(self, left_syn, right_syn):
        raw_sim = wn.res_similarity(left_syn, right_syn, self.ic)
        scaled_sim = raw_sim / self.LN_SYN_COUNT
        return scaled_sim

    def lch_sim(self, left_syn, right_syn):
        raw_sim = wn.lch_similarity(left_syn, right_syn)
        scaled_sim = raw_sim / self.LCH_MAX
        return scaled_sim

    @memoize
    def get_synsets(self, word):
        ret = defaultdict(list)
        group = {k: list(i[1] for i in v) for k, v in groupby([(s.pos(), s) for s in wn.synsets(word)],
                                                              key=lambda x: x[0])}
        ret.update(group)
        return ret

    @memoize
    def average_syn_score(self, left_syn, right_syn):
        if left_syn == right_syn:
            return 1.0
        sims = [fn(left_syn, right_syn) for fn in self.sim_functions]
        return np.nanmean(sims)

    @memoize
    def average_word_score(self, left_word, right_word):
        if left_word == right_word:
            return 1.0

        left_syns = self.get_synsets(left_word)
        right_syns = self.get_synsets(right_word)

        best_sim = -0.01
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