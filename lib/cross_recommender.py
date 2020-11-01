import pandas as pd
import requests

from lib.events_base import Embedder, EventSearcher
from lib import geocoder
from lib.user_model import User


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
    def __init__(self, embedder_data):
        self.embedder = Embedder(embedder_data)
        self.events_searcher = make_events_searcher(embedder=self.embedder)

    def book2vec(self, book):
        # todo: implement me
        pass

    def recommend_events(self, user: User):
        # todo: use user book vectors instead
        events = self.events_searcher.df.sample(10)
        return [
            {
                'name': e.name,
                'description': e.full_description,
                'imgUrl': e.pic_url
            }
            for i, e in events.iterrows()
        ]
