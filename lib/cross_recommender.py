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
        pass
    items_df = pd.DataFrame(items)
    s150 = EventSearcher(items_df, embedder=embedder, title_column='name', desc_column='full_description')
    s150.prepare_embeddings()
    return s150


class CrossRecommender:
    def __init__(self, embedder_data, ann_data):
        self.embedder = Embedder(embedder_data)
        self.events_searcher = make_events_searcher(embedder=self.embedder)
        self.ann_df = pd.read_parquet(ann_data)

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
        # todo: use user book vectors instead
        events = self.events_searcher.df.sample(10)
        return [
            {
                'name': e.name,
                'description': e.full_description,
                'imgUrl': e.pic_url,
                'type': 'event',
            }
            for i, e in events.iterrows()
        ]
