import re
from typing import Set, AnyStr
from typing.re import Pattern
from nltk import word_tokenize, pos_tag

bad_chars: Pattern
idf_keys: Set[AnyStr]


def init_worker():
    global bad_chars, idf_keys
    bad_chars = re.compile('[^A-Za-z0-9]+')
    idf_keys = set()
    with open('/app/data/bnc.ic', 'r') as bnc_idf:
        for line in bnc_idf:
            word, score = line.split(',')
            idf_keys.add(word)


def clean_string(key, text):
    global bad_chars, idf_keys
    return key, [t[0].lower() for t in pos_tag(word_tokenize(bad_chars.sub(' ', text))) if t[1][0] in ('N', 'V', 'J', 'R') and t[0].lower() in idf_keys]