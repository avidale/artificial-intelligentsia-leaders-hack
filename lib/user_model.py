import os
import pickle

from lib.scraping import google_img


class User:
    def __init__(self, uid, age=None, location=None, address=None, books=None):
        self.uid = uid
        self.age = age
        self.location = location
        self.address = address
        self.books = books or []
        self.book_vectors = []

    def add_book(self, book):
        # if book.get('title'):
        #     gi = google_img(book['title'])
        #     if gi:
        #         book['img_url'] = gi
        self.books.append(book)

    def add_book_vector(self, book_vector):
        self.book_vectors.append(book_vector)

    @property
    def book_ids(self):
        return [b['doc_id'] for b in self.books]

    @property
    def book_titles(self):
        return {b['title'] for b in self.books}

    def to_dict(self):
        return {
            'uid': self.uid,
            'age': self.age,
            'address': self.address,
            'location': self.location,
            'books': self.books,
            'book_vectors': self.book_vectors,
        }


class UserStorage:
    def __init__(self, filename=None):
        self.users = {}
        self.filename = filename
        if self.filename and os.path.exists(self.filename):
            with open(self.filename, 'rb') as f:
                self.users = pickle.load(f)

    def get_user(self, uid):
        return self.users.get(uid) or User(uid=uid)

    def save_user(self, user: User):
        self.users[user.uid] = user
        if self.filename:
            with open(self.filename, 'wb') as f:
                pickle.dump(self.users, f)
