import multiprocessing
import requests
import time
from urllib.parse import urlencode



def run_process(process_num):
    # Code for the process goes here
    url = 'http://127.0.0.1:5000/search'
    url = 'https://buranji.onrender.com/search'
    form_data = {
       'query': 'King,queen'
    }

    form_data_encoded = urlencode(form_data)

    for i in range(10000):
       time.sleep(300)
       response = requests.post(url, data=form_data)
       #print(response.text)
       print(f"process no: {process_num}, query no: {i}, response no: {len(response.text)}")


if __name__ == '__main__':
    processes = []
    for i in range(1, 2):
        process = multiprocessing.Process(target=run_process, args=(i,))
        processes.append(process)
        process.start()

    # Wait for all processes to complete
    for process in processes:
        process.join()
