import numpy as np
import pickle

from collections import defaultdict, Counter
from razdel import tokenize
from tqdm.auto import tqdm

import re


def normalize_text(text):
    text = re.sub('[^a-zа-яё0-9]+', ' ', text.lower())
    text = re.sub('\\s+', ' ', text).strip()
    text = re.sub('ё', 'е', text)
    return text


class Porter:
    # taken from https://gist.github.com/Kein1945/9111512
    PERFECTIVEGROUND =  re.compile(u"((ив|ивши|ившись|ыв|ывши|ывшись)|((?<=[ая])(в|вши|вшись)))$")
    REFLEXIVE = re.compile(u"(с[яь])$")
    ADJECTIVE = re.compile(u"(ее|ие|ые|ое|ими|ыми|ей|ий|ый|ой|ем|им|ым|ом|его|ого|ему|ому|их|ых|ую|юю|ая|яя|ою|ею)$")
    PARTICIPLE = re.compile(u"((ивш|ывш|ующ)|((?<=[ая])(ем|нн|вш|ющ|щ)))$")
    VERB = re.compile(u"((ила|ыла|ена|ейте|уйте|ите|или|ыли|ей|уй|ил|ыл|им|ым|ен|ило|ыло|ено|ят|ует|уют|ит|ыт|ены|ить|ыть|ишь|ую|ю)|((?<=[ая])(ла|на|ете|йте|ли|й|л|ем|н|ло|но|ет|ют|ны|ть|ешь|нно)))$")
    NOUN = re.compile(u"(а|ев|ов|ие|ье|е|иями|ями|ами|еи|ии|и|ией|ей|ой|ий|й|иям|ям|ием|ем|ам|ом|о|у|ах|иях|ях|ы|ь|ию|ью|ю|ия|ья|я)$")
    RVRE = re.compile(u"^(.*?[аеиоуыэюя])(.*)$")
    DERIVATIONAL = re.compile(u".*[^аеиоуыэюя]+[аеиоуыэюя].*ость?$")
    DER = re.compile(u"ость?$")
    SUPERLATIVE = re.compile(u"(ейше|ейш)$")
    I = re.compile(u"и$")
    P = re.compile(u"ь$")
    NN = re.compile(u"нн$")

    def stem(word):
        word = word.lower()
        word = word.replace(u'ё', u'е')
        m = re.match(Porter.RVRE, word)
        if m and m.groups():
            pre = m.group(1)
            rv = m.group(2)
            temp = Porter.PERFECTIVEGROUND.sub('', rv, 1)
            if temp == rv:
                rv = Porter.REFLEXIVE.sub('', rv, 1)
                temp = Porter.ADJECTIVE.sub('', rv, 1)
                if temp != rv:
                    rv = temp
                    rv = Porter.PARTICIPLE.sub('', rv, 1)
                else:
                    temp = Porter.VERB.sub('', rv, 1)
                    if temp == rv:
                        rv = Porter.NOUN.sub('', rv, 1)
                    else:
                        rv = temp
            else:
                rv = temp
            
            rv = Porter.I.sub('', rv, 1)

            if re.match(Porter.DERIVATIONAL, rv):
                rv = Porter.DER.sub('', rv, 1)

            temp = Porter.P.sub('', rv, 1)
            if temp == rv:
                rv = Porter.SUPERLATIVE.sub('', rv, 1)
                rv = Porter.NN.sub(u'н', rv, 1)
            else:
                rv = temp
            word = pre+rv
        return word
    stem=staticmethod(stem)


class TextSearcher:
    def __init__(self, inverse_index=None, doc_sizes=None, stem=False):
        self.inverse_index = inverse_index or {}
        self.doc_sizes = doc_sizes or {}
        self.stem = stem
        self.avg_doc_len = sum(doc_sizes.values()) / len(doc_sizes) if doc_sizes else 1

    def get_tokens(self, text):
        toks = [t.text.lower().replace('ё', 'е') for t in tokenize(text)]
        if self.stem:
            toks = [Porter.stem(t) for t in toks]
        return toks

    def fit(self, texts, indices=None):
        ii = defaultdict(list)
        doc_sizes = Counter()
        for i, text in enumerate(tqdm(texts)):
            if not isinstance(text, str):
                continue
            toks = self.get_tokens(text)
            idx = i if indices is None else indices[i]
            doc_sizes[idx] = len(toks)
            for token in toks:
                ii[token].append(idx)
        self.inverse_index = ii
        self.doc_sizes = doc_sizes
        self.avg_doc_len = sum(doc_sizes.values()) / len(doc_sizes) if doc_sizes else 1

    def bm25(self, text, max_df=0.1, k=1.5, b=0.75):
        toks = self.get_tokens(text)
        result = Counter()
        n_docs = len(self.doc_sizes)
        for t in toks:
            docs = self.inverse_index.get(t, [])
            if len(t) > max_df * n_docs:
                continue
            idf = np.log((n_docs - len(docs) + 0.5) / (len(docs) + 0.5) + 1)
            tf = 1
            score = tf * idf
            for doc in docs:
                result[doc] += idf * tf * (k + 1) / (tf + k * (1 - b + b * self.doc_sizes[doc] / self.avg_doc_len))
        return result

    def save(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump({'inverse_index': self.inverse_index, 'doc_sizes': self.doc_sizes, 'stem': self.stem}, f)

    @classmethod
    def load(cls, filename):
        with open(filename, 'rb') as f:
            return cls(**pickle.load(f))
