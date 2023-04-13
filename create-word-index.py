import sqlite3
import csv
import argparse
import gzip
import re
import os
import json
import string
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape


# conn.commit()
# conn.close()
#


def main():
    """This script few txt file with book/pages and inserts the word index to the specified table"""
    args = create_arguments()

    book_index, word_indices, content_array = create_index(args)

    insert_books_to_db(args.db_file, book_index)

    insert_words_to_db(args.db_file, word_indices)

    insert_content_to_db(args.db_file, content_array)


def insert_books_to_db(db_file, index_array):
    conn = sqlite3.connect(db_file)

    for book_id, title, author, url, book_file_path in index_array:
        row_insert_command = f"INSERT INTO books VALUES (?, ?, ?, ?)"

        conn.execute(row_insert_command, (int(book_id), title, author, url))

    conn.commit()
    conn.close()


def insert_words_to_db(db_file, index_array):
    conn = sqlite3.connect(db_file)

    for index, word, value in index_array:
        row_insert_command = f"INSERT INTO words VALUES (?, ?, ?)"

        conn.execute(row_insert_command, (index, word, value))

    conn.commit()
    conn.close()


def insert_content_to_db(db_file, index_array):
    conn = sqlite3.connect(db_file)

    for _id, index, word, value in index_array:
        row_insert_command = f"INSERT INTO content VALUES (?,  ?, ?, ?)"

        conn.execute(row_insert_command, (_id, index, word, value))

    conn.commit()
    conn.close()


def create_index(args):
    """
    word1->{book_id1: [page list]}
          ->{book_id2: [page list]}

    word2->{book_id2: [page list]}
    """

    with open(args.books_info_file, encoding="utf-8") as f:
        book_info = {}
        for line in f:
            fields = [x.strip() for x in line.strip().split("\t")]
            if fields and len(fields) == 6:
                book_info[fields[0]] = fields[1:]

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
                    book_file_path
                )
            )
    # books text file with info
    book_text_files = [ (x[0], x[4])  for x in book_index ]

    content_array = []
    content_id = 0

    word_index = {}

    # Open the file in read-only mode with the correct encoding
    for book_id, book_file_path in book_text_files:
        print("book file", book_file_path)

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
            page_no = page.find("page_no").text.strip()
            raw_page_content = page.find("content").text
            raw_page_content = re.sub(r"\n", " ", raw_page_content)

            page_content = re.sub("[" + string.punctuation + "]", "", raw_page_content)

            # record the content
            content_id += 1
            content_array.append((content_id, book_id, int(page_no), page_content))

            # process the words in the page
            words = set(
                [
                    x.strip()
                    for x in page_content.split(" ")
                    if (x and x.strip() not in stop_words)
                ]
            )
            for word in words:
                if word not in word_index:
                    word_index[word] = {}

                if book_id not in word_index[word]:
                    word_index[word][book_id] = []

                word_index[word][book_id].append(int(page_no))

    word_indices = [
        (idx, word, json.dumps(word_idx))
        for idx, (word, word_idx) in enumerate(word_index.items())
    ]

    return book_index, word_indices, content_array


def create_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db-file",
        "-d",
        dest="db_file",
        required=True,
        help="the db file",
    )
    parser.add_argument(
        "--books",
        "-b",
        dest="books",
        nargs="+",
        required=True,
        help="list of book files",
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


stop_words = {
    "a",
    "about",
    "above",
    "after",
    "again",
    "against",
    "all",
    "am",
    "an",
    "and",
    "any",
    "are",
    "aren't",
    "as",
    "at",
    "be",
    "because",
    "been",
    "before",
    "being",
    "below",
    "between",
    "both",
    "but",
    "by",
    "can",
    "can't",
    "cannot",
    "could",
    "couldn't",
    "did",
    "didn't",
    "do",
    "does",
    "doesn't",
    "doing",
    "don't",
    "down",
    "during",
    "each",
    "few",
    "for",
    "from",
    "further",
    "had",
    "hadn't",
    "has",
    "hasn't",
    "have",
    "haven't",
    "having",
    "he",
    "he'd",
    "he'll",
    "he's",
    "her",
    "here",
    "here's",
    "hers",
    "herself",
    "him",
    "himself",
    "his",
    "how",
    "how's",
    "i",
    "i'd",
    "i'll",
    "i'm",
    "i've",
    "if",
    "in",
    "into",
    "is",
    "isn't",
    "it",
    "it's",
    "its",
    "itself",
    "let's",
    "me",
    "more",
    "most",
    "mustn't",
    "my",
    "myself",
    "no",
    "nor",
    "not",
    "of",
    "off",
    "on",
    "once",
    "only",
    "or",
    "other",
    "ought",
    "our",
    "ours",
    "ourselves",
    "out",
    "over",
    "own",
    "same",
    "shan't",
    "she",
    "she'd",
    "she'll",
    "she's",
    "should",
    "shouldn't",
    "so",
    "some",
    "such",
    "than",
    "that",
    "that's",
    "the",
    "their",
    "theirs",
    "them",
    "themselves",
    "then",
    "there",
    "there's",
    "these",
    "they",
    "they'd",
    "they'll",
    "they're",
    "they've",
    "this",
    "those",
    "through",
    "to",
    "too",
    "under",
    "until",
    "up",
    "very",
    "was",
    "wasn't",
    "we",
    "we'd",
    "we'll",
    "we're",
    "we've",
    "were",
    "weren't",
    "what",
    "what's",
    "when",
    "when's",
    "where",
    "where's",
    "which",
    "while",
    "who",
    "who's",
    "whom",
    "why",
    "why's",
    "with",
    "won't",
    "would",
    "wouldn't",
    "you",
    "you'd",
    "you'll",
    "you're",
    "you've",
    "your",
    "yours",
    "yourself",
    "yourselves",
}

if __name__ == "__main__":
    main()
