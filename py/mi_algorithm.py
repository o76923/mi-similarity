import re
import string
import nltk
from nltk.corpus import wordnet as wn

PUNCTUATION_PATTERN = re.compile('[%s]' % re.escape(string.punctuation))


def clean_string(text):
    clean_sentence = text
    tokens = nltk.word_tokenize(clean_sentence.lower())
    punct_less_tokens = [PUNCTUATION_PATTERN.sub('', t).strip() for t in tokens]
    return punct_less_tokens


class MihalceaSentSimBNC(object):
    """
    @author CH Bong
    Implemented Mihalcea's sentence similarity measure
    BNC, version
    """
    ic = None
    #information content holder
    #tc = None #term count?
    idf = {}
    debug = False
    idf_file = '/app/data/bnc.ic'

    def __init__(self):
        '''
        Constructor
        '''
        #print 'Loading Brown information content ...'
        #wnic = WordNetICCorpusReader(nltk.data.find('corpora/wordnet_ic'), '.*\.dat')
        #self.ic = wnic.ic('ic-brown.dat')

        '''
        Load bnc idf
        '''
        # print 'Loading BNC Information Content dictionary ...'
        with open(self.idf_file, 'r', encoding="utf-8") as bnc_idf:
            for line in bnc_idf:
                word, score = line.split(',')
                self.idf[word] = float(score)
                # print 'Total of item:',len(self.idf)

    def find_the_most_similar_word(self, term, tokenized_list):
        best_score = 0
        best_term = ''

        for compared_term in tokenized_list:
            score = self.average_score(term, compared_term)
            # print 'score:',score
            if score >= best_score:
                best_score = score
                best_term = compared_term

        return best_term, best_score

    def average_score(self, word1, word2, verbose=False):
        '''
        Compute average of WSD scores using the most common synset
        '''
        #msg = ''
        #if self.debug: msg += 'Working on [%s] and [%s].' % (word1, word2)

        if word1 == word2:
            #if self.debug: print ' Identical words, return 1.'
            #print msg
            return 1

        else:
            #Use common synset
            synset1 = wn.synsets(word1)
            synset2 = wn.synsets(word2)
            if len(synset1) ==0 or len(synset2)==0:
                #if self.debug: print ' Empty synsets, return 0.'
                #print msg
                return 0
            else:
                com_synset1 = wn.synsets(word1)[0]
                com_synset2 = wn.synsets(word2)[0]

                if com_synset1.pos != com_synset2.pos:
                    #if self.debug: print ' Incompatible pos, return 0.'
                    #print msg
                    return 0

                score = 0
                count = 0

                #word similarity scoring functions
                sim = 0
                functions = [wn.wup_similarity, wn.path_similarity, wn.lin_similarity, wn.jcn_similarity]
                for func in functions:
                    if func == wn.lin_similarity or func == wn.res_similarity:
                        try:
                            sim = func(com_synset1, com_synset2, self.ic)
                            if sim is not None:
                                score = score + sim
                                count = count + 1
                        except:
                            None
                    else:
                        try:
                            sim = func(com_synset1, com_synset2)
                            if sim is not None:
                                score = score + sim
                                count = count + 1
                        except:
                            None

                            #if self.debug: msg += ' Sim: %s,%s,%s,%s' % (sim, func, com_synset1, com_synset2)

                if score == 0 or count ==0:
                    #if self.debug: print '0 score, 0 count'
                    #print msg
                    return 0
                else:
                    #if self.debug: print 'Average Sim: %s/%s=%s' % (score, count, score/count)
                    #print msg
                    return score/count

    def similarity(self, sentence1, sentence2):
        '''
        Similarity function
        '''
        #sentence1 = self.clean_string(sentence1)
        #sentence2 = self.clean_string(sentence2)

        # list1 = clean_string(sentence1)
        # list2 = clean_string(sentence2)
        list1 = sentence1
        list2 = sentence2

        '''
        First half
        '''
        totalTerm1Score = 0
        totalTerm1IDF = 0
        best_term = ''
        idf = 0
        for term1 in list1:
            if term1 in self.idf:
                idf = self.idf[term1]
            else:
                idf = 0

            best_term, score = self.find_the_most_similar_word(term1, list2)

            #print '%s vs %s: %s' % (term1, best_term, score)
            totalTerm1IDF += idf
            totalTerm1Score += score*idf

        '''
        Second half
        '''
        if self.debug: print('Second half ..\n\n')

        totalTerm2Score = 0
        totalTerm2IDF = 0
        for term2 in list2:
            if term2 in self.idf:
                idf = self.idf[term2]
            else:
                idf = 0
            # print 'idf',idf
            best_term, score = self.find_the_most_similar_word(term2, list1)

            # print '%s vs %s: %s' % (term2, best_term, score)

            totalTerm2IDF += idf
            # print totalTerm2IDF
            totalTerm2Score += score*idf

        #first_half = 0

        if totalTerm1Score==0 or totalTerm1IDF==0:
            first_half = 0
        else:
            first_half = totalTerm1Score/totalTerm1IDF
            if self.debug:
                print('first_half: %s/%s = %s' % (totalTerm1Score,totalTerm1IDF,totalTerm1Score/totalTerm1IDF))

        #second_half = 0
        if totalTerm2Score==0 or totalTerm2IDF==0:
            second_half = 0
        else:
            second_half = totalTerm2Score/totalTerm2IDF
            if self.debug:
                print('second_half: %s/%s = %s' % (totalTerm2Score,totalTerm2IDF,totalTerm2Score/totalTerm2IDF))

        #sim_score = (first_half + second_half)*0.5
        #sim_score = (first_half + second_half)*0.5

        return (first_half + second_half)*0.5