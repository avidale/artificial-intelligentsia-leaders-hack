import pandas as pd
from config import TOP_DOCUMENTS_DATA, BOOKS_SEARCHER_MODEL

import sys
sys.path.append("..")

from lib.text_search import TextSearcher


class Searcher:
    def __init__(self):
        self.top_documents = pd.read_parquet(TOP_DOCUMENTS_DATA)
        self.top_documents.set_index('doc_id', inplace=True)
        self.index = TextSearcher.load(BOOKS_SEARCHER_MODEL)

    def search_by_substr(self, substr, top=10):
        result = self.index.bm25(substr)
        return self.top_documents.loc[[id for id, count in result.most_common(top)]].reset_index()


searcher = Searcher()
