from extensions import db


class Books(db.Model):
    __tablename__ = "books"
    __id = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.Integer)
    title = db.Column(db.String(400))
    author = db.Column(db.String(100))
    url = db.Column(db.String(400))

    def __init__(self, book_id,  title, author, url):
        self.id = book_id
        self.title = title
        self.author = author
        self.url = url


class Words(db.Model):
    __tablename__ = "words"
    __id = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.Integer)
    word = db.Column(db.String(100))
    word_json = db.Column(db.String(20000))

    def __init__(self, word_id, word, word_json):
        self.id = word_id
        self.word = word
        self.word_json = word_json


class Content(db.Model):
    __tablename__ = "content"
    __id = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.Integer)
    book_id = db.Column(db.String(100))
    page_no = db.Column(db.Integer)
    text = db.Column(db.String(5000))

    def __init__(self, content_id, book_id, page_no, text):
        self.id = content_id
        self.book_id = book_id
        self.page_no = page_no
        self.text = text
