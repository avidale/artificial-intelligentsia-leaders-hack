import pandas as pd
from config import TOP_DOCUMENTS_DATA


class Searcher:
    def __init__(self):
        self.top_documents = pd.read_parquet(TOP_DOCUMENTS_DATA)

    def search_by_substr(self, substr):
        return self.top_documents[:10]


searcher = Searcher()
