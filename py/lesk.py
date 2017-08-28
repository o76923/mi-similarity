import difflib
from uuid import uuid4
from nltk.corpus.reader.wordnet import Synset
from nltk.corpus import stopwords

sw = set(stopwords.words('english'))


def lesk_sim(left_syn: Synset, right_syn: Synset):
    left_data = {
        "also": ' #{}# '.format(uuid4()).join(left_syn.also_sees()),
        "attr": ' #{}# '.format(uuid4()).join(left_syn.also_sees()),
        "example": ' #{}# '.format(uuid4()).join(left_syn.examples()),
        "glos": left_syn.definition(),
        "holo": ' #{}# '.format(uuid4()).join([l.definition() for l in
                                               left_syn.member_holonyms()
                                               + left_syn.part_holonyms()
                                               + left_syn.substance_holonyms()]),
        "hype": ' #{}# '.format(uuid4()).join([l.definition() for l in left_syn.hypernyms()]),
        "hypo": ' #{}# '.format(uuid4()).join([l.definition() for l in left_syn.hyponyms()]),
        "mero": ' #{}# '.format(uuid4()).join([l.definition() for l in
                                               left_syn.member_meronyms()
                                               + left_syn.part_meronyms()
                                               + left_syn.substance_meronyms()]),
        "pert": ' #{}# '.format(uuid4()).join([' #{}# '.format(uuid4()).join(
                l.pertainyms()) for l in left_syn.lemmas()]),
        "sim": ' #{}# '.format(uuid4()).join(left_syn.similar_tos()),
        "syns": ' #{}# '.format(uuid4()).join(set([l.name() for l in left_syn.lemmas()]))
    }
    left_data = {k:  [t for t in v.split(' ') if len(t) > 0] for (k, v) in left_data.items()}
    right_data = {
        "also": ' #{}# '.format(uuid4()).join(right_syn.also_sees()),
        "attr": ' #{}# '.format(uuid4()).join(right_syn.also_sees()),
        "example": ' #{}# '.format(uuid4()).join(right_syn.examples()),
        "glos": right_syn.definition(),
        "holo": ' #{}# '.format(uuid4()).join([l.definition() for l in
                                               right_syn.member_holonyms()
                                               + right_syn.part_holonyms()
                                               + right_syn.substance_holonyms()]),
        "hype": ' #{}# '.format(uuid4()).join([l.definition() for l in right_syn.hypernyms()]),
        "hypo": ' #{}# '.format(uuid4()).join([l.definition() for l in right_syn.hyponyms()]),
        "mero": ' #{}# '.format(uuid4()).join([l.definition() for l in
                                               right_syn.member_meronyms()
                                               + right_syn.part_meronyms()
                                               + right_syn.substance_meronyms()]),
        "pert": ' #{}# '.format(uuid4()).join([' #{}# '.format(uuid4()).join(
                l.pertainyms()) for l in right_syn.lemmas()]),
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
            if not all([o in sw for o in overlap]):
                print(left_data[left_key], right_data[right_key])
                print(overlap)

