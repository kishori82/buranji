import re
import json
import os
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from models import Books, Words, Content
from extensions import db
from application import create_app
from batch_upload import batch_upload
from utilities import substring_around, text_with_query_words

app = create_app()



@app.route("/")
def index():
    _results = Words.query.all()
    #names = sorted(list({result.name for result in _results if result.name}))
    names = []

    return render_template("index.html", results=[], names=names)


@app.route("/submit", methods=["POST"])
def submit():
    fname = request.form["fname"]
    lname = request.form["lname"]
    pet = request.form["pets"]

    student = Books(fname, lname, pet)
    db.session.add(student)
    db.session.commit()

    # fetch a certain student2
    studentResult = db.session.query(Books).filter(Books.id == 1)
    for result in studentResult:
        print(result.fname)

    return render_template("success.html", data=fname)


@app.route("/search", methods=["POST", "GET"])
def search():

    if request.method=="GET":
      # Get the current page number from the query string
      query = request.args.get('q', default='', type=str)
      page = request.args.get('page', default=1, type=int )

    if request.method=="POST":
      query = request.form["query"]
      page = 1

    # Set the number of search results per page
    results_per_page = 5

    # Calculate the start and end indices of the search results for the current page
    start_index = (page - 1) * results_per_page
    end_index = start_index + results_per_page


    # split the query into words, e.g., separated by comma, space
    query_words = set([ x.strip() for x in re.split(r'[,\s]+', query) if x.strip() ])

    # Store the query results in an array
    query_results = []
    
    # loop over individual query words
    for query_word in query_words: 
       # get from Word table the json 
       word_json = Words.query.filter(Words.word == query_word).first()
       
       if word_json:
          # if there is a result/entry for the word then get the json doc and convert to python dict
          word_index = json.loads(word_json.word_json)
          query_results.append(word_index)
       else:
          query_results.append({})

    # find out the set of common books (use book_id) that has all the words
    common_book_ids = set()
    for query_result in query_results:
       if common_book_ids==set():
         common_book_ids = set(list(query_result.keys()))
       else:  # keep intersecting the page numbers for each books
         common_book_ids = common_book_ids.intersection(set(list(query_result.keys())))

    # for each books take the common pages for the words, in a book_id to set of pages
    books_pages = {}
    
    for book_id in common_book_ids:
      # for each book loop over each of the results 
      for i in range(len(query_results)):
        if book_id in query_results[i]:
          if book_id not in books_pages:
             books_pages[book_id] = set(query_results[i][book_id])
          else:
             # keep taking set intersection to find out the common pages in each of the books
             books_pages[book_id] = books_pages[book_id].intersection(set(query_results[i][book_id]))
          
    # now retrieve the actual book title from the Books table and select with book_id
    book_title = {}
    for book_id in common_book_ids: 
       book_info = Books.query.filter(Books.id == int(book_id)).first()
       book_title[book_id] = [ re.sub("-", ' ', os.path.basename(book_info.title)), book_info.author, book_info.url ]

    # create the results as array of (book_id, some context text, title)  
    results = []
    for book_id, (title, author, url) in book_title.items():
       for page_no in books_pages[book_id]:  
          results.append((book_id, title, author, url, "some text", page_no))

    results.sort(key = lambda x: int(x[5]))
      
    num_pages = len(results)//results_per_page
    #data = [ (title, text, page_no) for _, title, text, page_no in results[start_index:end_index] ]

    data = []
    for book_id, title, author, url, _, page_no in results[start_index:end_index]:  
       content = Content.query.filter(Content.book_id == book_id, Content.page_no==page_no).first()
       #modified_texts = []
       #for query_word in query_words:
       #   modified_texts.append(re.sub(query_word, f"<strong>{query_word}</strong> ",  substring_around(content.text, query_word, around=150)))

       modified_texts = text_with_query_words(content.text, query_words, delta=20)
       data.append((title, author, url, '<br>...'.join(modified_texts), page_no))
       
    return render_template("index.html", query=query, num_pages=num_pages, current_page=page, results=data)


@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files["file"]
    raw_data = file.read().decode("utf-8")
    data = [line.split(",") for line in raw_data.split("\n")]
    batch_upload(data)
    return f"{file.filename} File uploaded successfully!"
