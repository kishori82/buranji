from extensions import db

class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(40))
    lname = db.Column(db.String(40))
    pet = db.Column(db.String(40))

    def __init__(self, fname, lname, pet):
        self.fname = fname
        self.lname = lname
        self.pet = pet

class Person(db.Model):
    __tablename__ = "persons"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40))
    reference = db.Column(db.String(200))

    def __init__(self, name, reference):
        self.name = name
        self.reference = reference
