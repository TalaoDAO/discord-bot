# listen.py
import json
import requests

def get_stream(url):
    s = requests.Session()

    with s.get(url, headers=None, stream=True) as resp:
        for line in resp.iter_lines():
            if line:
                my_json = line.decode('utf8').replace("'", '"')
                #print(my_json)
                # Load the JSON to a Python list & dump it back out as formatted JSON
                data = json.loads(my_json[6:])
                d = json.dumps(data, indent=4, sort_keys=True)
                print(d)
                return

url = 'https://d8fa-86-229-94-232.eu.ngrok.io/bot-verifier/verifier_stream'
get_stream(url)