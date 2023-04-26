import re
import json
import os
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from models import Books, Words, Content
from extensions import db
from application import create_app
from utilities import (
    suffixes,
    substring_around,
    text_with_query_words,
    page_match_score,
    page_match_score_v2,
    equivalent_text,
    merge_word_indices
)

app = create_app()


@app.route("/")
def index():
    # _results = Words.query.all()
    # names = sorted(list({result.name for result in _results if result.name}))
    # names = []
    return render_template("index.html", results=[], names=[])


@app.route("/results", methods=["GET"])
def results():
    # get the query
    query = request.args.get("q", default="", type=str)

    # get search results
    num_pages, data = _search(query, 10000, 0, 10000)
    return str(len(data))


@app.route("/search", methods=["POST", "GET"])
def search():
    if request.method == "GET":
        # Get the current page number from the query string
        query = request.args.get("q", default="", type=str)
        page = request.args.get("page", default=1, type=int)

    if request.method == "POST":
        query = request.form["query"]
        page = 1

    # Set the number of search results per page
    results_per_page = 5

    # Calculate the start and end indices of the search results for the current page
    start_index = (page - 1) * results_per_page
    end_index = start_index + results_per_page

    # get search results
    num_pages, data = _search(query, results_per_page, start_index, end_index)

    return render_template(
        "index.html", query=query, num_pages=num_pages, current_page=page, results=data
    )


def _search(query, results_per_page, start_index, end_index):
    # Replace all occurrences of "য়" with "য়"
    query = query.replace("য়", "য়").replace("ড়", "ড়")

    # split the query into equivalent words, e.g., separated by comma, space
    query_words_equiv = set([ equivalent_text(x, ignore_suffix=True).strip() for x in re.split(r"[,\s]+", query) if x.strip()])

    # Store the query results in an array
    query_results = []

    # create an empty set of query words
    query_words = set()
    # loop over individual query words equivalend
    for query_word in query_words_equiv:
        # get from Word table the json
        #word_rows = Words.query.filter(Words.word_equiv == query_word).limit(5).all()
        word_row = Words.query.filter(Words.word_equiv == query_word).first()

        word_index = {}
        
        if word_row:
           # if there is a result/entry for the word then get the json doc and convert to python dict
           word_index = json.loads(word_row.word_json)

        # query results for all suffixes
        query_results.append(word_index)

    # find out the set of common books (use book_id) that has all the words
    common_book_ids = set()
    for query_result in query_results:
        if common_book_ids == set():
            common_book_ids = set(list(query_result.keys()))
        else:  # keep intersecting the page numbers for each books
            common_book_ids = common_book_ids.intersection(
                set(list(query_result.keys()))
            )

    # print(common_book_ids)
    # for each books take the common pages for the words, in a book_id to set of pages
    books_pages = {}
    for book_id in common_book_ids:
        # for each book loop over each of the results, num distinct words
        for i in range(len(query_results)):
            if book_id in query_results[i]:
                if book_id not in books_pages:
                    books_pages[book_id] = set(query_results[i][book_id].keys())
                else:
                    # keep taking set intersection to find out the common pages in each of the books
                    books_pages[book_id] = books_pages[book_id].intersection(
                        set( query_results[i][book_id].keys() )
                    )

    # now retrieve the actual book title from the Books table and select with book_id
    book_title = {}
    for book_id in common_book_ids:
        book_info = Books.query.filter(Books.id == int(book_id)).first()
        book_title[book_id] = [
            re.sub("-", " ", os.path.basename(book_info.title)),
            book_info.author,
            book_info.url,
        ]

    # create the results as array of (book_id, title, author, some context text, page_no)
    results = []
    for book_id, (title, author, url) in book_title.items():
        for page_no in books_pages[book_id]:
            word_locations = []
            for query_no, query_result in enumerate(query_results):
                word_locations.append([(query_no, word_loc) for word_loc in query_result[book_id][page_no]] )

                #print(page_no, query_result[book_id][page_no])
            page_score = page_match_score_v2(word_locations)
            results.append((book_id, title, author, url, "some text", page_no, page_score))
    results.sort(key=lambda x: int(x[6]), reverse=False)

    num_pages = len(results) // results_per_page
    # data = [ (title, text, page_no) for _, title, text, page_no in results[start_index:end_index] ]

    data = []
    for book_id, title, author, url, _, page_no, page_score in results[start_index:end_index]:
        content = Content.query.filter(
            Content.book_id == book_id, Content.page_no == page_no
        ).first()
        # modified_texts = []
        # for query_word in query_words:
        #   modified_texts.append(re.sub(query_word, f"<strong>{query_word}</strong> ",  substring_around(content.text, query_word, around=150)))

        modified_texts = text_with_query_words(content.text, query_words_equiv, delta=20)
        #match_score = page_match_score(content.text, query_words_equiv)

        data.append(
            (title, author, url, "<br>...".join(modified_texts), page_no)
        )

    # sort by the match score in ascending
    #_data.sort(key=lambda x: x[5])

    #data = [(x[0], x[1], x[2], x[3], x[4]) for x in _data]

    return num_pages, data
