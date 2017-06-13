import re
import string
import numpy as np
import nltk
from itertools import combinations, product
from nltk.corpus import wordnet as wn
from nltk.corpus import wordnet_ic
from nltk.corpus.reader.wordnet import WordNetError
from py.utils import memoize

PUNCTUATION_PATTERN = re.compile('[%s]' % re.escape(string.punctuation))


class MiSim(object):

    def __init__(self):
        self._load_idf()
        self.bnc_ic = wordnet_ic.ic('ic-bnc.dat')
        self.sim_functions = [
            wn.wup_similarity,
            wn.path_similarity,
            # self.lin_similarity,
        ]

    def _load_idf(self):
        self.idf = {}
        with open('../data/bnc.ic', 'r') as bnc_idf:
            for line in bnc_idf:
                word, score = line.split(',')
                self.idf[word] = float(score)

    def clean_string(self, text):
        return [t.lower() for t in nltk.word_tokenize(text)
                if t.lower() in self.idf and self.get_synset(t)]

    def lin_similarity(self, left_syn, right_syn):
        try:
            return wn.lin_similarity(left_syn, right_syn, self.bnc_ic)
        except WordNetError:
            return None

    @memoize
    def get_synset(self, word):
        try:
            return [s for s in wn.synsets(word) if s.pos() in ('n', 'v', 'j')][0]
        except IndexError:
            return None

    @memoize
    def average_syn_score(self, left_syn, right_syn):
        # If words are same, return 1.0
        if left_syn == right_syn:
            return 1.0

        try:
            return np.nanmean([fn(left_syn, right_syn) for fn in self.sim_functions])
        except TypeError:
            for fn in self.sim_functions:
                print(fn, left_syn, right_syn, fn(left_syn, right_syn))
            exit()

    @memoize
    def average_word_score(self, left_word, right_word):
        if left_word == right_word:
            return 1.0
        left_syn = self.get_synset(left_word)
        right_syn = self.get_synset(right_word)
        if left_syn == right_syn:
            return 1.0

        if left_syn.pos() == right_syn.pos():
            return self.average_syn_score(left_syn, right_syn)
        else:
            return 0.0

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
        print(left_tokens, right_tokens)
        token_sim = self.token_sim_matrix(left_tokens, right_tokens)
        print(token_sim)
        
        left_maxes = np.argmax(token_sim, 1)

        for left_index, right_index in enumerate(left_maxes):
            print(left_index,
                  right_index,
                  left_tokens[left_index],
                  right_tokens[right_index],
                  self.get_synset(left_tokens[left_index]),
                  self.get_synset(right_tokens[right_index]),
                  token_sim[left_index, right_index])

        left_idf = [self.idf[left_tokens[m][0]] for m in left_maxes]
        left_scores = token_sim[(range(len(left_maxes)), left_maxes)]
        left_half = np.sum(left_idf * left_scores)/np.sum(left_idf)

        # right_maxes = np.argmax(token_sim, 0)
        # right_idf = [self.idf[right_tokens[m][0]] for m in right_maxes]
        # right_scores = token_sim[(right_maxes, range(len(right_maxes)))]
        # right_half = np.sum(right_idf * right_scores)/np.sum(right_idf)
        #
        # for right_index, left_index in enumerate(right_maxes):
        #     print(left_index,
        #           right_index,
        #           left_tokens[left_index],
        #           right_tokens[right_index],
        #           self.get_synset(left_tokens[left_index]),
        #           self.get_synset(right_tokens[right_index]),
        #           token_sim[left_index, right_index])

        print(' '.join(left_tokens), '\t', ' '.join(right_tokens))
        print(token_sim)
        print(left_maxes, right_maxes)
        print((left_half + right_half) * 0.5)
        input()

        return (left_half + right_half) * 0.5

if __name__ == "__main__":
    from functools import partial
    mi = MiSim()
    s1 = mi.get_synset("store")
    s2 = mi.get_synset("customer")
    functions = {
        "jcn": partial(wn.jcn_similarity, ic=mi.bnc_ic),
        "res": partial(wn.res_similarity, ic=mi.bnc_ic),
        "lin": partial(wn.lin_similarity, ic=mi.bnc_ic),
        "wup": wn.wup_similarity,
        "lch": wn.lch_similarity,
        "path": wn.path_similarity
    }
    for name, fn in functions.items():
        print(name, fn(s1, s2))

if __name__ == "profile":
    import cProfile
    import pstats
    from itertools import combinations
    mi = MiSim()
    sentences = [
        "Store manager evaluation of the hair stylist.",
        "Average customer intention to maintain service relationship with the stylist.",
        "Behavior that is generally appreciated by others (although it may take time and effort  the social costs are usually low and the social rewards high).",
        "Voluntary and constructive efforts  by individual employees  to effect organizationally functional change with respect to how work is executed.",
        "Whether the participant regards helping behaviors as part of one's job.",
        "Whether one perceives a relationship between performance of a helping behavior and outcomes such as rewards and punishment.",
        "An individual’s perception of his or her competence in performing helping behaviors.",
        "An individual’s perception of his or her competence in performing taking charge behaviors.",
        "The extent to which an individual perceives choice with respect to performing helping behaviors.",
        "The tendency to expect favorable outcomes.",
        "Include but are not limited to theft  white collar crime  absenteeism  tardiness  drug and alcohol abuse  disciplinary problems accidents  sabotage  sexual harassment  and violence.",
        "The extent to which members of a collective view the group’s needs and obligations as superordinate to individual needs and desires and the extent to which members wish to maintain strong  harmonious relationships with other group members.",
        "Generalized beliefs about the capabilities of the team across tasks and contexts.",
        "The extent to which people regard unequal status differences as legitimate.",
        "Immediate supervisor of each branch's team effectiveness rating.",
        "Decision latitude.",
        "A group of separate but interconnected human resources (HR) practices designed to enhance employees' skills and effort.",
        "Managers' assessment of the average level of human capital for the employees in their unit.",
        "Indicates an emotional bond between the employee and the organization that is based on identification with the organization's goals and values.",
        "Reflects commitment based on the perceived costs of leaving the organization.",
        "The loyalty driven by a sense of moral obligation toward the organization.",
        "The extent to which customers perceive employees as performing a series of service behaviors.",
        "Should reflect a mindset of desire to pursue a course of action of relevance to customers  such as exerting extra effort to satisfy their expectations.",
        "Refer to a loyalty driven by a sense of moral obligation towards the customer.",
        "Behaviors directed at others in the organization that go beyond one's immediate role requirements.",
        "Behaviors that go against the legitimate interests of another individual in the organization.",
        "Exists between two persons  X and Y  when they truly like each other  are concerned about one another  and have similar perspectives and outlooks on the importance of their relationship.",
        "Strong negative affective relationships are characterized by dislike  animosity  and avoidance of the other person.",
        "Exists when two individuals (say X and Y) who may or may not be positively connected to each other are connected to a common third party (say Z) through positive affective relationships.",
        "A third-party negative relationship exists when two people (X and Y) who may or may not be directly linked to each other have a common negative affective relationship with a third person (Z  i.e both dislike Z).",
        "The extent to which they generally experienced positive emotional descriptors.",
        "Reflects the evaluation that one is part of an organization.",
        "Perception of ones own position within an organization.",
        "Refers to a sense of emotional attachment to the organization.",
        "Refers to a feeling of responsibility to stay with the organization.",
    ]
    tokens = [mi.clean_string(s) for s in sentences]
    cmd = """
for (left_tokens, right_tokens) in combinations(tokens, 2):
    print(mi.similarity(left_tokens, right_tokens))
"""
    for (left_tokens, right_tokens) in combinations(tokens, 2):
        print(mi.similarity(left_tokens, right_tokens))
    # cProfile.run(cmd, 'restats')
    # p = pstats.Stats('restats')
    # p.strip_dirs().sort_stats('tottime').print_stats()

if __name__ == "timeit":
    import timeit
    setup = """
from itertools import combinations
from py.mi_algorithm2 import MiSim
mi = MiSim()
sentences = [
        "Store manager evaluation of the hair stylist."
        "Average customer intention to maintain service relationship with the stylist."
        "Behavior that is generally appreciated by others (although it may take time and effort  the social costs are usually low and the social rewards high)."
        "Voluntary and constructive efforts  by individual employees  to effect organizationally functional change with respect to how work is executed."
        "Whether the participant regards helping behaviors as part of one's job."
        "Whether one perceives a relationship between performance of a helping behavior and outcomes such as rewards and punishment."
        "An individual’s perception of his or her competence in performing helping behaviors."
        "An individual’s perception of his or her competence in performing taking charge behaviors."
        "The extent to which an individual perceives choice with respect to performing helping behaviors."
        "The tendency to expect favorable outcomes."
        "Include but are not limited to theft  white collar crime  absenteeism  tardiness  drug and alcohol abuse  disciplinary problems accidents  sabotage  sexual harassment  and violence."
        "The extent to which members of a collective view the group’s needs and obligations as superordinate to individual needs and desires and the extent to which members wish to maintain strong  harmonious relationships with other group members."
        "Generalized beliefs about the capabilities of the team across tasks and contexts."
        "The extent to which people regard unequal status differences as legitimate."
        "Immediate supervisor of each branch's team effectiveness rating."
        "Decision latitude."
        "A group of separate but interconnected human resources (HR) practices designed to enhance employees' skills and effort."
        "Managers' assessment of the average level of human capital for the employees in their unit."
        "Indicates an emotional bond between the employee and the organization that is based on identification with the organization's goals and values."
        "Reflects commitment based on the perceived costs of leaving the organization."
        "The loyalty driven by a sense of moral obligation toward the organization."
        "The extent to which customers perceive employees as performing a series of service behaviors."
        "Should reflect a mindset of desire to pursue a course of action of relevance to customers  such as exerting extra effort to satisfy their expectations."
        "Refer to a loyalty driven by a sense of moral obligation towards the customer."
        "Behaviors directed at others in the organization that go beyond one's immediate role requirements."
        "Behaviors that go against the legitimate interests of another individual in the organization."
        "Exists between two persons  X and Y  when they truly like each other  are concerned about one another  and have similar perspectives and outlooks on the importance of their relationship."
        "Strong negative affective relationships are characterized by dislike  animosity  and avoidance of the other person."
        "Exists when two individuals (say X and Y) who may or may not be positively connected to each other are connected to a common third party (say Z) through positive affective relationships."
        "A third-party negative relationship exists when two people (X and Y) who may or may not be directly linked to each other have a common negative affective relationship with a third person (Z  i.e both dislike Z)."
        "The extent to which they generally experienced positive emotional descriptors."
        "Reflects the evaluation that one is part of an organization."
        "Perception of ones own position within an organization."
        "Refers to a sense of emotional attachment to the organization."
        "Refers to a feeling of responsibility to stay with the organization."
    ]
tokens = [mi.clean_string(s) for s in sentences]
"""
    cmd = """
for (left_tokens, right_tokens) in combinations(tokens, 2):
    mi.similarity(left_tokens, right_tokens)
    """
    print(timeit.timeit(cmd, setup, number=1))