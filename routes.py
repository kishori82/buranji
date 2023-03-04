from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from models import Student, Person
from extensions import db
from application import create_app
from batch_upload import batch_upload

app = create_app()

@app.route("/")
def index():
    _results = Person.query.all()
    names = sorted(list({result.name for result in _results if result.name}))
    
    return render_template('index.html', results=[], names = names)


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


@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']
    # Perform the search and get the results
    _results = Person.query.all()
    names = sorted(list({result.name for result in _results if result.name}))

    results = []
    for result in _results: 
      if query.strip() and query.lower() in result.name.lower().split(' '):
        results.append(result)
    # Render the template with the search results
    return render_template('index.html', results=results, names = names)

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    raw_data = file.read().decode('utf-8')
    data = [ line.split(',') for line in raw_data.split('\n') ]
    batch_upload(data)
    return f'{file.filename} File uploaded successfully!'
