from extensions import db


class Books(db.Model):
    __tablename__ = "books"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(400))
    author = db.Column(db.String(100))
    url = db.Column(db.String(400))

    def __init__(self, title, author, url):
        self.title = title
        self.author = author
        self.url = url


class Words(db.Model):
    __tablename__ = "words"
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100))
    word_json = db.Column(db.String(20000))

    def __init__(self, word, word_json):
        self.word = word
        self.word_json = word_json


class Content(db.Model):
    __tablename__ = "content"
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.String(100))
    page_no = db.Column(db.Integer)
    text = db.Column(db.String(1000))

    def __init__(self, book_id, page_no, text):
        self.book_id = book_id
        self.page_no = page_no
        self.text = text
