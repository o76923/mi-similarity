from nltk.corpus.reader.bnc import BNCCorpusReader

bnc = BNCCorpusReader('data/2554/download/Texts', fileids=r'[a-z]{3}/\w*\.xml')

print(len(bnc))
print(len(bnc.sents()))
print(len(bnc.words()))

