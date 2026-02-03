import sqlite3
import csv
import argparse
import gzip
import re
import os
import json
import string
import psycopg2
import sys

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
from application import create_app
from extensions import db
from models import Books, Words, Content
from utilities import equivalent_text
from stop_words import stop_words


num_books_inserted = 0
num_pages_inserted = 0
num_words_inserted = 0
num_chars_inserted = 0

def main():
    """This script few txt file with book/pages and inserts the word index to the specified table"""
    args = create_arguments()
    book_index, word_indices, content_array = create_index(args)
    print(f"INFO: BOOKS CREATED : {len(book_index)}")
    print(f"INFO: WORDS CREATED : {len(word_indices)}")
    print(f"INFO: PAGES CREATED : {len(content_array)}")

    app = Flask(__name__)
    if "prod" in args.db_file:
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    elif "dev" in args.db_file:
        # Set the configuration for the app's SQLAlchemy connection
        db_file_path = os.path.join(Path(__file__).parent.absolute(), "../buranji.db")
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///{}".format(db_file_path)
    else:
        print('specify db as either "prod" or "dev"')
        print("exiting")
        return

    # db = SQLAlchemy(app)
    db.init_app(app)

    with app.app_context():
        db.create_all()
        db.session.commit()

        num_books = insert_books_to_db(db, book_index)
        print(f"INFO: INSERTED THE BOOKS :{num_books}")
        db.session.commit()

        num_words = insert_words_to_db(db, word_indices)
        print(f"INFO: INSERTED THE WORDS: {num_words}")
        db.session.commit()

        num_pages = insert_content_to_db(db, content_array)
        print(f"INFO: INSERTED THE CONTENTS: {num_pages}")
        db.session.commit()

        print(f'INFO: DATABASE URI {app.config["SQLALCHEMY_DATABASE_URI"]}')

# Define a function to replace Bengali Unicode points with their corresponding Assamese Unicode points
def convert_to_assamese(text):
    # Define a dictionary with Bengali and Assamese Unicode points as key-value pairs
    unicode_map = {
        "\u09BC": "\u0995\u09CD\u09B7",  # ়
        "\u09C1": "\u0985\u09B2",  # ু
        "\u09C2": "\u0985\u09CD\u09B7",  # ূ
        "\u09C3": "\u0986\u09CD\u09AE",  # ৃ
        "\u09E3": "\u0982",  # ৣ
    }

    # Use a regular expression to find all Bengali Unicode points in the text
    regex = "[" + re.escape("".join(unicode_map.keys())) + "]"
    matches = re.findall(regex, text)

    # Replace each Bengali Unicode point with its corresponding Assamese Unicode point
    for match in matches:
        text = text.replace(match, unicode_map[match])

    # Return the converted text
    return text


def insert_books_to_db(db, index_array):
    num_books = 0
    for book_id, title, author, url, book_file_path in index_array:
        book_file_base = os.path.basename(book_file_path)
        print(book_id, title, author, url)
        db.session.add(Books(book_id, title, author, book_file_base,  url))
        num_books += 1
    return num_books


def insert_words_to_db(db, index_array):
    i = 0
    for index, word_equiv, value in index_array:
        # print(index, word, value)

        if len(word_equiv) > 100:
            print(f"skipping long word of length {word_equiv}", len(word_equiv))
            continue

        if len(value) > 60000:
            print(f"skipping excessively popular word {word_equiv}", len(value))
            continue

        db.session.add(Words(index, word_equiv, value))
        i += 1
    return i


def insert_content_to_db(db, index_array):
    num_pages = 0
    for _id, index, word, value in index_array:
        if len(value) > 5000:
            print("skipping excessively large page text", len(value))
            continue
        db.session.add(Content(_id, index, word, value))
        num_pages += 1

    return num_pages


def create_index(args):
    """
    word1->{book_id1: [page list]}
          ->{book_id2: [page list]}

    word2->{book_id2: [page list]}
    """

    with open(args.books_info_file, encoding="utf-8") as f:
        book_info = {}
        for line in f:
            if re.search(r"^#", line):
                continue
            fields = [x.strip() for x in line.strip().split("\t")]
            if fields and len(fields) >= 7:
                book_info[fields[0]] = fields[2:]
                book_info[fields[1]] = fields[2:]

    book_index = []
    for book_id, book_file_path in enumerate(args.books):
        book_file_base = os.path.basename(book_file_path)

        if book_file_base in book_info:
            # insert the tuple (book_id, title, author, url)
            book_index.append(
                (
                    str(book_id),
                    book_info[book_file_base][0],
                    book_info[book_file_base][1],
                    book_info[book_file_base][2],
                    book_file_path,
                )
            )
        else:
            print("Missing file info ", book_file_base)

    # list the missing txt files but are in the book-list file
    print("Books in book-list.tsv but no OCR of pdf file: ")

    book_txt_files = [os.path.basename(book_file_path) for book_file_path in args.books]

    idx = 1
    for book_txt in book_info:
        if book_txt not in book_txt_files:
            print("\t Not in OCR ", idx, book_txt)
            idx += 1

    # books text file with info
    book_text_files = [(x[0], x[4]) for x in book_index]
    content_array = []
    content_id = 0

    word_index = {}

    print("Books in book-list.tsv with OCR txt file:")
    # Open the file in read-only mode with the correct encoding
    for book_id, book_file_path in book_text_files:
        # Parse the XML document
        with open(book_file_path, encoding="utf-8") as f:
            # Parse the XML file using ElementTree
            tree = ET.parse(f)

        # Get the root element
        root = tree.getroot()

        # Parse the XML document
        # root = ET.fromstring(xml_string)
        # Iterate over the child elements of the root element
        for page in root:
            # Print the tag name and text content of each child element
            page_no = int(page.find("page_no").text.strip())

            raw_page_content = page.find("content")

            # Replace all occurrences of "য়" with "য়"
            # raw_page_content = raw_page_content.replace("য়", "য়").replace("ড়", "ড়").replace("র", "ৰ")

            try:
               raw_page_content = (
                  raw_page_content.text.replace("য়", "য়")
                  .replace("ড়", "ড়")
                  .replace("র", "ৰ")
                  .replace("ঢ়", "ঢ়")
               )
            except:
               continue

            raw_page_content = re.sub(r"\n", " ", raw_page_content)

            page_content = re.sub("[" + string.punctuation + "]", "", raw_page_content)

            # record the content
            content_id += 1
            content_array.append((content_id, book_id, page_no, page_content))

            # process the words in the page
            words_equiv = [
                (equivalent_text(x.strip(), ignore_suffix=True), word_no)
                for word_no, x in enumerate(page_content.split(" "))
                if (x and x.strip() not in stop_words)
            ]

            for word_equiv, word_no in words_equiv:
                if word_equiv not in word_index:
                    word_index[word_equiv] = {}

                if book_id not in word_index[word_equiv]:
                    word_index[word_equiv][book_id] = {}

                if page_no not in word_index[word_equiv][book_id]:
                    word_index[word_equiv][book_id][page_no] = []

                word_index[word_equiv][book_id][page_no].append(word_no)

    word_indices = [
        (idx, word_equiv, json.dumps(word_idx))
        for idx, (word_equiv, word_idx) in enumerate(word_index.items())
    ]

    print('word index', len(word_index))
    return book_index, word_indices, content_array


def create_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db-file",
        "-d",
        dest="db_file",
        required=True,
        choices=["dev", "prod"],
        help="the db file locally",
    )
    parser.add_argument(
        "--books",
        "-b",
        dest="books",
        nargs="+",
        required=True,
        help="list of book files txt",
    )
    parser.add_argument(
        "--books-info-file",
        "-f",
        dest="books_info_file",
        required=True,
        help="file with book information",
    )

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main()
