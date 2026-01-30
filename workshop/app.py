import xml.etree.ElementTree as ET

import os
import threading

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder=None)

_BOOK_CACHE = {}
_BOOK_CACHE_LOCK = threading.Lock()


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
    cache_key = (en_xml_path, as_xml_path, reference_page)

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
    en_xml_path = "books/an-account-of-assam-francis-hamilton-english.txt"
    as_xml_path = "books/an-account-of-assam-francis-hamilton-english-to-assamese.txt"

    #en_xml_path = request.args.get("en_xml_path", type=str)
    #as_xml_path = request.args.get("as_xml_path", type=str)
    en_xml_path = "books/political-history-of-assam-english.txt"
    as_xml_path = "books/political-history-of-assam-english-to-assamese.txt"
    title = "Political History of Assam"

    reference_page = request.args.get("reference_page", type=int)
    print("reference page:", reference_page)
    return jsonify(get_cached_bilingual_book_data(en_xml_path, as_xml_path, title=title, reference_page=reference_page))


@app.get("/<path:filename>")
def files(filename: str):
    return send_from_directory(".", filename)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
