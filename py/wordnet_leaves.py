from nltk.corpus import wordnet as wn
from nltk.corpus import wordnet_ic
from nltk.corpus.reader.wordnet import information_content, _INF

max_ic = 0.0
ic = wordnet_ic.ic('ic-bnc.dat')


def get_max_leaf_ic(syn):
    global max_ic, ic
    hyponyms = syn.hyponyms()
    if len(hyponyms) == 0:
        syn_ic = information_content(syn, ic)
        if syn_ic > max_ic and syn_ic != _INF:
            max_ic = syn_ic
    else:
        for h in hyponyms:
            get_max_leaf_ic(h)

if __name__ == "__main__":
    root = wn.synset('entity.n.01').root_hypernyms()[0]
    get_max_leaf_ic(root)
    print(max_ic)
