from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from models import Student
from extensions import db
from application import create_app


app = create_app()

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit():
    fname = request.form["fname"]
    lname = request.form["lname"]
    pet = request.form["pets"]

    student = Student(fname, lname, pet)
    db.session.add(student)
    db.session.commit()

    # fetch a certain student2
    studentResult = db.session.query(Student).filter(Student.id == 1)
    for result in studentResult:
        print(result.fname)

    return render_template("success.html", data=fname)
