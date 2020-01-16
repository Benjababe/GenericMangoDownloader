import cfscrape
import json
import os

data = {}

def parse_url(url, data):
    sites = data.keys()
    for site in sites:
        if (url.__contains__(site)):
            py_file = data[site]
            cmd = "python {} {} True".format(py_file, url)
            print("Running Command: '{}'". format(cmd))
            os.system(cmd)

with open(".data.json") as data_file:
    data = json.load(data_file)["sites"]
print("\n")
url = input("Enter URL of (H-)Mango: ")
parse_url(url, data)