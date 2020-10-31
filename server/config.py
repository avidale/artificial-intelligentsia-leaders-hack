import os

PROJECT_PATH = os.path.dirname(__file__)
DATA_PATH = os.path.join(PROJECT_PATH, "data")

MAPPERS_PATH = os.path.join(DATA_PATH, "mappers.pkl")
MODEL_PATH = os.path.join(DATA_PATH, "model.pkl")
ITEM_USER_DATA = os.path.join(DATA_PATH, "item_user_data.pkl")

TOP_DOCUMENTS_DATA = os.path.join(DATA_PATH, "top_documents.parquet")
ALL_DOCUMENTS_DATA = os.path.join(DATA_PATH, "all_documents.parquet")

SERVER_PORT = 3228
DEBUG = True
