import compress_fasttext
import numpy as np
import pandas as pd
import pickle
import requests

from bs4 import BeautifulSoup
from collections import Counter
from functools import lru_cache
from razdel import tokenize
from sklearn.neighbors import KDTree
from tqdm.auto import tqdm


def annotation_from_librusec(title):
    r = requests.get('http://http.lib.rus.ec/search?ask={}'.format(title.replace(' ', '+'))).text
    soup = BeautifulSoup(r, features="lxml")

    found = soup.find('h3', string=' Найденные книги:')
    if not found:
        return
    a = found.parent.next_sibling.find('a')
    if isinstance(a, int):
        a = found.parent.find('a')
    if isinstance(a, int):
        return

    r = requests.get('http://http.lib.rus.ec' + a['href']).text
    soup = BeautifulSoup(r, features="lxml")

    ann = soup.find('h2', string='Аннотация')
    if not ann:
        return 
    ns = ann.next_sibling
    while ns and (not hasattr(ns, 'text') or ns.name == 'a'):
        ns = ns.next_sibling
    annotation = ns.text
    return annotation



def unit_norm(vec):
    return vec / np.sqrt(1e-10 + sum(vec**2))


class Embedder:
    def __init__(self, model, dim=300):
        if isinstance(model, str):
            self.model = compress_fasttext.models.CompressedFastTextKeyedVectors.load(model)
        else:
            self.model = model
        self.dim = dim

    @lru_cache(maxsize=10_000)
    def w2v(self, word):
        return self.model[word.lower()]

    def __call__(self, text):
        try:
            text = str(text).strip()
            if not text:
                return np.zeros(self.dim)
            toks = [t.text.lower() for t in tokenize(text) if len(t.text) > 1]
            if not toks:
                return np.zeros(self.dim)
            total = np.sum([self.w2v(t) for t in toks], axis=0)
            return unit_norm(total)
        except Exception as e:
            raise e


class EventSearcher:
    def __init__(self, df, embedder, tree_titl=None, tree_desc=None, title_column='Название мероприятия', desc_column='Краткое описание'):
        self.df = df
        self.embedder = embedder
        self.tree_titl = tree_titl
        self.tree_desc = tree_desc

        self.title_column = title_column
        self.desc_column = desc_column

        self.titles = self.df[self.title_column]
        if self.desc_column:
            self.desc = self.df[self.desc_column ]

    def prepare_embeddings(self):
        self.titles_emb = np.stack([
            self.embedder(text)
            for text in tqdm(self.titles)
        ])
        self.tree_titl = KDTree(self.titles_emb)
        if self.desc_column:
            self.desc_emb = np.stack([
                self.embedder(text)
                for text in tqdm(self.desc)
            ])
            self.tree_desc = KDTree(self.desc_emb)
        else:
            self.tree_desc = None

    def match_vector(self, e, n=10):
        distances, indices = self.tree_titl.query(e[np.newaxis, :], n)
        first = pd.DataFrame({'d': distances[0], 'idx': indices[0]})
        if self.desc_column:
            distances, indices = self.tree_desc.query(e[np.newaxis, :], n)
            second = pd.DataFrame({'d': distances[0], 'idx': indices[0]})
            total = pd.concat([first, second], ignore_index=True).sort_values('d')
        else:
            total = first
        total['title'] = self.titles[total.idx].values
        if self.desc_column:
            total['desc'] = self.desc[total.idx].values
        total.drop_duplicates(subset=['idx'], keep='first', inplace=True, ignore_index=True)
        return total

    def to_pickle(self, filename):
        pack = {
            'df': self.df, 
            'tree_desc': self.tree_desc,
            'tree_titl': self.tree_titl,
            'title_column': self.title_column, 
            'desc_column': self.desc_column,
        }
        with open(filename, 'wb') as f:
            pickle.dump(pack, f)

    @classmethod
    def from_pickle(cls, filename, embedder):
        with open(filename, 'rb') as f:
            pack = pickle.load(f)
        result = cls(embedder=embedder, **pack)
        return result


def embed_book(title, embedder, annotation_weight=10):
    e = embedder(title)
    annotation = annotation_from_librusec(title)
    if annotation:
        e = unit_norm(e + embedder(annotation) * annotation_weight)
    return e


if __name__ == '__main__':
    print('loading embedder...')
    embedder = Embedder('../resources/ft_freqprune_100K_20K_pq_100.bin')
    print('loading events...')
    event_searcher = EventSearcher.from_pickle('../events.pkl', embedder=embedder)
    print('searching for events...')
    while True:
        print('введите название книги: ', end='')
        text = input()
        print('рекомендуемые мероприятия:')
        print(event_searcher.match_vector(embed_book(text, embedder)).head(5))
