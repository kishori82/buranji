import requests
import time
from urllib.parse import urlencode

if __name__ == "__main__":
    #url = "http://127.0.0.1:5000/results"
    url = 'http://buranji.com/results'
    queries = [
        " চুকাফা   ",
        "Assam,Sibsagar",
        " জয়মতী    ",
      "  জয়মতী কুৱঁৰী    ",
        "কছাৰী ৰাজ্য  ",
        " নৰা ৰাজ্য  ",
        "   মোলা গাভৰু   ",
        "    মুলা গাভৰু  ",
        "    মূলা গাভৰু  ",
        "মেচাগড়",
        " চেতিয়া  ",
        "  চেটীয়া ",
    ]

    for query in queries:
        query_params = {"q": query}
        response = requests.get(url, params=query_params)
        print("Query: ", query, "  num results:", response.text)
