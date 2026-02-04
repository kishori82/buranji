import re
import json
import os
import threading
import xml.etree.ElementTree as ET
from flask import Flask, jsonify, redirect, render_template, request, send_from_directory, url_for
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
    merge_word_indices,
)

_BOOK_CACHE = {}
_BOOK_CACHE_LOCK = threading.Lock()

_BOOKS_LIST_CACHE = {
    "mtime": None,
    "data": None,
}
_BOOKS_LIST_CACHE_LOCK = threading.Lock()

_BOOKS_LOCK = threading.Lock()


BOOKS = None

app = create_app()
app.debug = True


@app.route("/book", methods=["GET"])
def book():
    return_to = request.referrer or url_for("index")
    return render_template("book.html", return_to=return_to)


@app.route("/book.js", methods=["GET"])
def book_js():
    return send_from_directory(os.path.dirname(__file__), "book.js")


@app.route("/book.css", methods=["GET"])
def book_css():
    return send_from_directory(os.path.dirname(__file__), "book.css")


def get_book_by_id(book_id: str):
    # NOTE: BOOKS may be rebuilt from the TSV via `get_cached_books_list(...)`.
    if not BOOKS:
        return None
    for b in BOOKS:
        if b["id"] == book_id:
            return b
    return None


def load_books_list_from_tsv(tsv_path: str):
    path_prefix = "books/"

    with open(tsv_path, encoding="utf-8") as f:
        book_info = {}
        for line in f:
            if re.search(r"^#", line):
                continue
            fields = [x.strip() for x in line.strip().split("\t")]
            if not fields or not fields[0]:
                continue
            book_info[fields[0]] = fields

    # This is the shape returned by GET /api/books (used by the frontend to render the table).
    books = []

    # This is the shape used by GET /api/book-data (used by get_book_by_id).
    books_for_reader = []
    idx = 1

    # book_id is also the base filename 
    for _, fields in book_info.items():
        title = fields[3] if len(fields) > 3 else ""
        author = fields[4] if len(fields) > 4 else ""
        url = fields[5] if len(fields) > 5 else ""
        publisher = fields[9] if len(fields) > 9 else ""

        # Treat filename as the primary id in the system.
        # (The frontend will navigate using this value as book_id.)
        assamese_filename = fields[0]
        english_filename = fields[1]

        books.append({
            "num": idx,
            "id": assamese_filename,
            "book_id": assamese_filename,
            "title": title,
            "author": author,
            "publisher": publisher,
            "url": url,
        })

        books_for_reader.append({
            "id": assamese_filename,
            "title": title,
            "en_xml_path": f"{path_prefix}{english_filename}",
            "as_xml_path": f"{path_prefix}{assamese_filename}",
        })
        idx += 1

        books.append({
            "num": idx,
            "id": english_filename,
            "book_id": english_filename,
            "title": title,
            "author": author,
            "publisher": publisher,
            "url": url,
        })

        books_for_reader.append({
            "id": english_filename,
            "title": title,
            "en_xml_path": f"{path_prefix}{english_filename}",
            "as_xml_path": f"{path_prefix}{assamese_filename}",
        })

        idx += 1
    return books, books_for_reader


def get_cached_books_list(tsv_path: str):
    mtime = os.path.getmtime(tsv_path)
    with _BOOKS_LIST_CACHE_LOCK:
        if _BOOKS_LIST_CACHE["data"] is not None and _BOOKS_LIST_CACHE["mtime"] == mtime:
            return _BOOKS_LIST_CACHE["data"]

        books, books_for_reader = load_books_list_from_tsv(tsv_path)

        # Update the global BOOKS list atomically so /api/book-data can resolve book_id.
        with _BOOKS_LOCK:
            global BOOKS
            BOOKS = books_for_reader

        _BOOKS_LIST_CACHE["mtime"] = mtime
        _BOOKS_LIST_CACHE["data"] = books
        return books


def load_book_data_from_xml(xml_path: str):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    data = {}
    for page in root.findall(".//page"):
        page_no = (page.findtext("page_no") or "").strip()
        content_el = page.find("content")
        content_text = "".join(content_el.itertext()).strip() if content_el is not None else ""

        if not page_no:
            continue

        data[page_no] = content_text

    return data


def build_bilingual_book_data(en_xml_path: str, as_xml_path: str, title="",reference_page: int | None = None):
    en_pages = load_book_data_from_xml(en_xml_path)
    as_pages = load_book_data_from_xml(as_xml_path)

    merged = {}
    all_page_nos = sorted({*en_pages.keys(), *as_pages.keys()}, key=lambda x: int(x) if x.isdigit() else x)

    for page_no in all_page_nos:
        within_window = (
            reference_page is None
            or (page_no.isdigit() and abs(int(page_no) - reference_page) <= 5)
        )
        merged[page_no] = {
            "en": {
                "pageno": page_no,
                "title": title,
                "body": en_pages.get(page_no, "") if within_window else None,
            },
            "as": {
                "pageno": page_no,
                "title": title,
                "body": as_pages.get(page_no, "") if within_window else None,
            },
        }

    return merged


def get_cached_bilingual_book_data(en_xml_path: str, as_xml_path: str, title :str= "", reference_page: int | None = None):
    en_mtime = os.path.getmtime(en_xml_path)
    as_mtime = os.path.getmtime(as_xml_path)
    cache_key = (en_xml_path, as_xml_path, title, reference_page)

    with _BOOK_CACHE_LOCK:
        cached = _BOOK_CACHE.get(cache_key)
        if cached is not None:
            cached_en_mtime, cached_as_mtime, cached_data = cached
            if cached_en_mtime == en_mtime and cached_as_mtime == as_mtime:
                return cached_data

        data = build_bilingual_book_data(en_xml_path, as_xml_path, title=title, reference_page=reference_page)
        _BOOK_CACHE[cache_key] = (en_mtime, as_mtime, data)
        return data



@app.get("/api/book-data")
def api_book_data():
    book_id = request.args.get("book_id", type=str)
    if not book_id:
        return jsonify({"error": "Missing required query param: book_id"}), 400

    # Ensure BOOKS has been loaded from TSV (so the reader can open any TSV entry).
    get_cached_books_list("books/assamese-english-book-list.tsv")

    book = get_book_by_id(book_id)
    if book is None:
        return jsonify({"error": f"Unknown book_id: {book_id}"}), 404

    en_xml_path = book["en_xml_path"]
    as_xml_path = book["as_xml_path"]
    title = book["title"]
    reference_page = request.args.get("reference_page", type=int)
    
    return jsonify(get_cached_bilingual_book_data(en_xml_path, as_xml_path, title=title, reference_page=reference_page))

@app.get("/api/books")
def api_books():
    books_info_file = "books/assamese-english-book-list.tsv"
    return jsonify(get_cached_books_list(books_info_file))


@app.get("/api/books-deprecated")
def api_books_deprecated():
    books_info = Books.query.order_by(Books.id).all()
    books = []
    for idx, b in enumerate(books_info, start=1):
        books.append(
            {
                "num": idx,
                "id": str(b.id) if b.id is not None else "",
                "book_id": str(b.id) if b.id is not None else "",
                "title": b.title or "",
                "author": b.author or "",
                "publisher": "",
                "url": b.url or "",
            }
        )
    return jsonify(books)


@app.get("/api/book-data-deprecated")
def api_book_data_deprecated():
    book_id = request.args.get("book_id", type=str)
    if not book_id:
        return jsonify({"error": "Missing required query param: book_id"}), 400

    reference_page = request.args.get("reference_page", type=int)

    book = Books.query.filter(Books.id == int(book_id)).first()
    if book is None:
        return jsonify({"error": f"Unknown book_id: {book_id}"}), 404

    pages = Content.query.filter(Content.book_id == book_id).order_by(Content.page_no).all()
    data = {}
    for p in pages:
        page_no = p.page_no
        within_window = (
            reference_page is None
            or (isinstance(page_no, int) and abs(int(page_no) - int(reference_page)) <= 5)
        )

        body = p.text if within_window else None

        key = str(page_no)
        data[key] = {
            "en": {
                "pageno": key,
                "title": book.title or "",
                "body": body,
            },
            "as": {
                "pageno": key,
                "title": book.title or "",
                "body": body,
            },
        }

    return jsonify(data)

@app.route("/")
def index():
    return render_template("index.html", results=[], names=[])


@app.route("/references", methods=["GET"])
def references():
    # get the books
    books_info = Books.query.order_by(Books.id).all()

    references = []
    for num, book_info in enumerate(books_info):
        references.append(
            (
                num + 1,
                book_info.title,
                book_info.author,
                "To be added",
                "To be added",
                book_info.url,
            )
        )

    # render the list of references
    return render_template("references.html", references=references)


@app.route("/team", methods=["GET"])
def team():
    # render the list of team members
    return render_template("team.html")


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
        return redirect(url_for("search", q=query, page=1))
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
    # query = query.replace("য়", "য়").replace("ড়", "ড়")
    query = (
        query.replace("য়", "য়").replace("ড়", "ড়").replace("র", "ৰ").replace("ঢ়", "ঢ়")
    )

    # split the query into equivalent words, e.g., separated by comma, space
    query_words_equiv = set(
        [
            equivalent_text(x, ignore_suffix=True).strip()
            for x in re.split(r"[,\s]+", query)
            if x.strip()
        ]
    )

    # Store the query results in an array
    query_results = []

    # create an empty set of query words
    query_words = set()
    # loop over individual query words equivalend
    for query_word in query_words_equiv:
        # get from Word table the json
        # word_rows = Words.query.filter(Words.word_equiv == query_word).limit(5).all()
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
        # print('books', list((query_result.keys())))
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
                        set(query_results[i][book_id].keys())
                    )

    # now retrieve the actual book title from the Books table and select with book_id
    book_title = {}
    for book_id in common_book_ids:
        book_info = Books.query.filter(Books.id == int(book_id)).first()
        book_title[book_id] = [
            re.sub("-", " ", os.path.basename(book_info.title)),
            book_info.author,
            book_info.book_file_path,
            book_info.url,
        ]

    # print(book_title)
    # create the results as array of (book_id, title, author, some context text, page_no)
    results = []
    for book_id, (title, author, book_file_path, url) in book_title.items():
        for page_no in books_pages[book_id]:
            word_locations = []
            for query_no, query_result in enumerate(query_results):
                # print(book_id, type(book_id),  page_no, type(book_id))
                word_locations.append(
                    [
                        (query_no, word_loc)
                        for word_loc in query_result[book_id][page_no]
                    ]
                )

                # print(page_no, query_result[book_id][page_no])
            page_score = page_match_score_v2(word_locations)
            results.append(
                (book_id, title, author, book_file_path,  url, "some text", page_no, page_score)
            )
    results.sort(key=lambda x: int(x[6]), reverse=False)

    num_pages = len(results) // results_per_page

    data = []
    for book_id, title, author, book_file_path,  url, _, page_no, page_score in results[
        start_index:end_index
    ]:
        content = Content.query.filter(
            Content.book_id == book_id, Content.page_no == page_no
        ).first()

        modified_texts = text_with_query_words(
            content.text, query_words_equiv, delta=20
        )
        # match_score = page_match_score(content.text, query_words_equiv)
        url = f"/book#/book/{book_file_path}?page={page_no}&lang=en"

        data.append(
            (title, author, url, "...<br><br>...".join(modified_texts), page_no)
        )

    return num_pages, data
