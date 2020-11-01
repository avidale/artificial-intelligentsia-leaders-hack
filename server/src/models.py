from config import MAPPERS_PATH, MODEL_PATH, ITEM_USER_DATA, ALL_DOCUMENTS_DATA
import joblib
import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors


class RecModel:
    def __init__(self):
        self.user_mapping, self.doc_mapping, self.back_user_mapping, self.back_doc_mapping = joblib \
            .load(MAPPERS_PATH)
        self.model = joblib.load(MODEL_PATH)
        self.item_user_data = joblib.load(ITEM_USER_DATA)
        self.all_documents = pd.read_parquet(ALL_DOCUMENTS_DATA)
        self.knn_model = NearestNeighbors()
        self.knn_model = self.knn_model.fit(self.model.item_factors)

    def recommend_by_history(self, history, n_neighbors=5):
        history = list(map(self.doc_mapping.get, history))
        user_vector = np.mean(self.model.item_factors[history], axis=0)

        knn_result = self.knn_model.kneighbors(user_vector.reshape(1, -1), n_neighbors=n_neighbors)[1].flatten().tolist()

        return list(map(self.back_doc_mapping.get, knn_result))

    def get_book_info(self, doc_ids):
        return self.all_documents[self.all_documents.doc_id.isin(doc_ids)]

    def recommend_by_user(self):
        pass

    def random_books(self, k=10):
        # todo: use book popularity
        return self.all_documents.sample(k)


rec_model = RecModel()
