import numpy as np
import pandas as pd
import requests

from lib.events_base import Embedder, EventSearcher, unit_norm
from lib import geocoder
from lib.user_model import User
from lib.text_search import normalize_text


EVENTS_URL = 'https://www.mos.ru/afisha/tickets/_next/data/fI_e03_EFY6-2Yur4wNIE/events.json?page=1&page_size=500'


def make_events_searcher(embedder):
    data = requests.get(EVENTS_URL).json()
    items = data['pageProps']['items']
    for item in items:
        item['address'] = geocoder.Address(lat=item['latitude'], lon=item['longitude'], text=item['spot_name'])
    items_df = pd.DataFrame(items)
    s150 = EventSearcher(items_df, embedder=embedder, title_column='name', desc_column='full_description')
    s150.prepare_embeddings()
    return s150


def load_clubs_searcher(embedder, path):
    result = EventSearcher.from_pickle(path, embedder)
    return result


class CrossRecommender:
    def __init__(self, embedder_data, ann_data, clubs_model):
        self.embedder = Embedder(embedder_data)
        self.events_searcher = make_events_searcher(embedder=self.embedder)
        self.ann_df = pd.read_parquet(ann_data)

        self.clubs_searcher = load_clubs_searcher(self.embedder, clubs_model)

    def find_annotation(self, title, author=None):
        title_norm = normalize_text(title)
        chosen = self.ann_df[self.ann_df.title_norm == title_norm].copy()
        if chosen.shape[0] == 0:
            return None
        if chosen.shape[0] > 1:
            if author:
                author_norm = set(normalize_text(author).split())

                def auth_intersection(text):
                    return len(set(text.split()).intersection(author_norm))

                chosen['auth_match'] = chosen.author_norm.apply(auth_intersection)
                chosen.sort_values('auth_match', ascending=False, inplace=True)
        return chosen.iloc[0].annotation or None

    def book2vec(self, book, annotation_weight=10):
        e = self.embedder(book['title'])
        if book.get('annotation'):
            e = unit_norm(e + self.embedder(book['annotation']) * annotation_weight)
        return e

    def recommend_events(self, user: User):
        if len(user.book_vectors) == 0:
            events = self.events_searcher.df.copy()
            events['score'] = 1
        else:
            vec = np.mean(user.book_vectors, axis=0)
            found = self.events_searcher.match_vector(vec, n=30)
            events = self.events_searcher.df.iloc[found.idx].copy()
            events['score'] = 1 - found.d
        if user.location and user.location.get('lat'):
            addr = geocoder.Address(lat=user.location['lat'], lon=user.location['lng'])
            events['distance'] = events.address.apply(lambda a: geocoder.geo_distance(addr, a))
            events['total_score'] = events.score * np.exp(- events['distance'] / 20)
            events.sort_values('total_score', inplace=True, ascending=False)
        events = events.head(10)
        return [
            {
                'name': e['name'],
                'description': e.full_description,
                'imgUrl': e.pic_url,
                'type': 'event',
            }
            for i, e in events.iterrows()
        ]

    def recommend_clubs(self, user: User):
        if len(user.book_vectors) == 0:
            clubs = self.clubs_searcher.df.copy()
            clubs['score'] = 1
        else:
            vec = np.mean(user.book_vectors, axis=0)
            found = self.clubs_searcher.match_vector(vec, n=30)
            clubs = self.clubs_searcher.df.iloc[found.idx].copy()
            clubs['score'] = 1 - found.d
        # todo: use address
        clubs = clubs.head(10)
        return [
            {
                'name': e['title'],
                'description': e['text'],
                'type': 'club',
            }
            for i, e in clubs.iterrows()
        ]
