import multiprocessing
import requests
import time
from urllib.parse import urlencode



def run_process(process_num):
    # Code for the process goes here
    url = 'http://127.0.0.1:5000/search'
    url = 'https://buranji.com/search'
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
    num_queries = len(queries)

    for i in range(100):
       form_data = { 'query': queries[(i + process_num)%num_queries] }
       form_data_encoded = urlencode(form_data)
       response = requests.post(url, data=form_data)

       #print(response.text)
       print(f"process no: {process_num}, query no: {i}, response no: {len(response.text)}")


if __name__ == '__main__':
    processes = []
    for i in range(0, 10):
        process = multiprocessing.Process(target=run_process, args=(i,))
        processes.append(process)
        process.start()

    # Wait for all processes to complete
    for process in processes:
        process.join()
