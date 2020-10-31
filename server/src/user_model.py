

class User:
    def __init__(self, uid, age=None, address=None, books=None):
        self.uid = uid
        self.age = age
        self.address = address
        self.books = books or []

    def add_book(self, book):
        self.books.append(book)

    @property
    def book_ids(self):
        return [b['doc_id'] for b in self.books]

    def to_dict(self):
        return {
            'uid': self.uid,
            'age': self.age,
            'address': self.address,
            'books': self.books,
        }


class UserStorage:
    def __init__(self):
        self.users = {}

    def get_user(self, uid):
        return self.users.get(uid) or User(uid=uid)

    def save_user(self, user: User):
        self.users[user.uid] = user
