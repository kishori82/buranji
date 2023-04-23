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
    equivalent_text
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
    query_words_equiv = set([ equivalent_text(x).strip() for x in re.split(r"[,\s]+", query) if x.strip()])

    words_to_bold = set()

    # Store the query results in an array
    query_results = []

    # create an empty set of query words
    query_words = set()
    # loop over individual query words equivalend
    for query_word in query_words_equiv:
        # get from Word table the json
        word_row = Words.query.filter(Words.word_equiv == query_word).first()
        if word_row:
            # if there is a result/entry for the word then get the json doc and convert to python dict
            word_index = json.loads(word_row.word_json)
            
            # stores
            query_words.add(word_row.word)
        else:
            word_index = {}

        is_assamese = all(0x0980 <= ord(c) <= 0x09FF for c in query_word)
        if is_assamese:
            # try with all suffixes
            for suffix in suffixes:
                # extend the word
                extended_query_word = word_row.word + suffix.strip()

                # get from Word table the json
                word_suffix_json = Words.query.filter(
                    Words.word == extended_query_word
                ).first()

                # merge the two word indices
                if word_suffix_json:
                    extended_word_index = json.loads(word_suffix_json.word_json)
                    words_to_bold.add(extended_query_word)
                    for book, page_array in extended_word_index.items():
                        # if book id already seen add the new page numbers, otherwise add a new entry for the book
                        if book in word_index:
                            word_index[book] = sorted(
                                list(set(word_index[book]).union(set(page_array))),
                                reverse=False,
                            )
                        else:
                            word_index[book] = page_array

        # query results for all suffixes
        query_results.append(word_index)
    # print(query_results)

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
        # for each book loop over each of the results
        for i in range(len(query_results)):
            if book_id in query_results[i]:
                if book_id not in books_pages:
                    books_pages[book_id] = set(query_results[i][book_id])
                else:
                    # keep taking set intersection to find out the common pages in each of the books
                    books_pages[book_id] = books_pages[book_id].intersection(
                        set(query_results[i][book_id])
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

    # create the results as array of (book_id, some context text, title)
    results = []
    for book_id, (title, author, url) in book_title.items():
        for page_no in books_pages[book_id]:
            results.append((book_id, title, author, url, "some text", page_no))
    results.sort(key=lambda x: int(x[5]))

    num_pages = len(results) // results_per_page
    # data = [ (title, text, page_no) for _, title, text, page_no in results[start_index:end_index] ]

    _data = []
    for book_id, title, author, url, _, page_no in results:
        content = Content.query.filter(
            Content.book_id == book_id, Content.page_no == page_no
        ).first()
        # modified_texts = []
        # for query_word in query_words:
        #   modified_texts.append(re.sub(query_word, f"<strong>{query_word}</strong> ",  substring_around(content.text, query_word, around=150)))

        modified_texts = text_with_query_words(content.text, query_words, delta=20)
        match_score = page_match_score(content.text, query_words)

        _data.append(
            (title, author, url, "<br>...".join(modified_texts), page_no, match_score)
        )

    # sort by the match score in ascending
    _data.sort(key=lambda x: x[5])

    data = [(x[0], x[1], x[2], x[3], x[4]) for x in _data][start_index:end_index]

    return num_pages, data
