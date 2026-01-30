import xml.etree.ElementTree as ET
import re
import os
import threading
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder=None)

_BOOK_CACHE = {}
_BOOK_CACHE_LOCK = threading.Lock()

_BOOKS_LIST_CACHE = {
    "mtime": None,
    "data": None,
}
_BOOKS_LIST_CACHE_LOCK = threading.Lock()

_BOOKS_LOCK = threading.Lock()


BOOKS = None


def get_book_by_id(book_id: str):
    # NOTE: BOOKS may be rebuilt from the TSV via `get_cached_books_list(...)`.
    if not BOOKS:
        return None
    for b in BOOKS:
        if b["id"] == book_id:
            return b
    return None


def load_books_list_from_tsv(tsv_path: str):
    path_prefix = "../../ocr-project/books/text/"

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
    for filename, fields in book_info.items():
        title = fields[1] if len(fields) > 1 else ""
        author = fields[2] if len(fields) > 2 else ""
        url = fields[3] if len(fields) > 3 else ""
        publisher = fields[7] if len(fields) > 7 else ""

        # Treat filename as the primary id in the system.
        # (The frontend will navigate using this value as book_id.)
        book_id = filename

        books.append({
            "num": idx,
            "id": filename,
            "book_id": book_id,
            "title": title,
            "author": author,
            "publisher": publisher,
            "url": url,
        })

        books_for_reader.append({
            "id": book_id,
            "title": title,
            "en_xml_path": f"{path_prefix}{filename}",
            "as_xml_path": f"{path_prefix}{filename}",
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


@app.get("/")
def index():
    return send_from_directory(".", "book.html")


@app.get("/book")
def book():
    return send_from_directory(".", "book.html")


@app.get("/api/book-data")
def api_book_data():
    book_id = request.args.get("book_id", type=str)
    if not book_id:
        return jsonify({"error": "Missing required query param: book_id"}), 400

    # Ensure BOOKS has been loaded from TSV (so the reader can open any TSV entry).
    get_cached_books_list("../book-list.tsv")

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
    books_info_file = "../book-list.tsv"
    return jsonify(get_cached_books_list(books_info_file))

@app.get("/<path:filename>")
def files(filename: str):
    return send_from_directory(".", filename)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
