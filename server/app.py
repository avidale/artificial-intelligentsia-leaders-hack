
from flask import Flask, request, jsonify, abort
from src.models import rec_model
from src.searcher import searcher
from config import DEBUG, SERVER_PORT, TEXT_EMBEDDER_MODEL
import sys
sys.path.append('..')
from lib.user_model import User, UserStorage
from lib.cross_recommender import CrossRecommender

import logging
logging.basicConfig(level=logging.DEBUG)


app = Flask(__name__)
user_storage = UserStorage()
cross_recommender = CrossRecommender(TEXT_EMBEDDER_MODEL)

logger = logging.getLogger(__name__)


def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Origin, X-Requested-With, Content-Type, Accept"
    response.headers['Access-Control-Allow-Methods'] = "DELETE, GET, POST, PUT, OPTIONS"
    return response


app.after_request(add_cors_headers)


@app.route('/')
def salam():
    return "Salam aleikum"


@app.route('/recommend', methods=["POST"])
def recommend():
    # doc_ids = request.json["doc_ids"]
    user = user_storage.get_user(uid=request.json['uid'])
    logger.debug('recommending for user {}'.format(request.json['uid']))
    books = recommend_books(user)
    events = cross_recommender.recommend_events(user)
    return jsonify(books + events)


def recommend_books(user: User):
    doc_ids = user.book_ids
    if not doc_ids:
        recommendations = rec_model.random_books(10)
    else:
        recommendations = rec_model.recommend_by_history(doc_ids, 20)
        recommendations = rec_model.get_book_info(recommendations)
        recommendations = recommendations.drop_duplicates(['title']).head(10)
    res = [{
        "title": cand["title"],
        "author": cand["author"],
        "doc_id": cand["doc_id"],
        'type': 'book',
        'name': cand['title'],
        'description': cand['author'],
    } for i, cand in recommendations.iterrows()]
    return res


@app.route('/search', methods=["POST"])
def handle_search():
    if "search_str" not in request.json:
        abort(401)

    search_res = searcher.search_by_substr(request.json['search_str'])

    res = [{
        "title": cand["title"],
        "author": cand["author"],
        "doc_id": cand["doc_id"],
    } for i, cand in search_res.iterrows()]

    return jsonify(res)


@app.route('/add-book', methods=["POST"])
def add_book():
    # expects json like {'uid': str, 'book': object}
    if "uid" not in request.json or 'book' not in request.json:
        abort(401)
    logger.debug('adding a book {} for user {}'.format(request.json['book'], request.json['uid']))
    user = user_storage.get_user(uid=request.json['uid'])
    user.add_book(request.json['book'])
    user_storage.save_user(user)
    return jsonify({'result': 'OK'})


@app.route('/profile', methods=["POST"])
def get_profile():
    # expects json like {'uid': str, 'book': object}
    if "uid" not in request.json:
        abort(401)
    user = user_storage.get_user(uid=request.json['uid'])
    logger.debug('user : {}'.format(user.to_dict()))
    return jsonify(user.to_dict())


@app.route('/setUserData', methods=["POST"])
def set_user_data():
    # expects json like {'uid': str, 'book': object}
    if "uid" not in request.json:
        abort(401)
    user = user_storage.get_user(uid=request.json['uid'])
    user_data = request.json
    logger.debug('user data: {}'.format(user_data))
    if user_data.get('address'):
        user.address = user_data['address']
    if user_data.get('location'):
        user.location = user_data['location']
    if user_data.get('age'):
        user.age = user_data['age']
    user_storage.save_user(user)
    return jsonify({'result': 'OK'})


if __name__ == '__main__':
    app.run(
        debug=DEBUG,
        port=SERVER_PORT
    )
