import json
import os

data = {}

def parse_url(url, data):
    sites = data.keys()
    for site in sites:
        if (url.__contains__(site)):
            py_file = data[site]
            #run command eg. "python dl_cafe.py True {cafe_url}"
            cmd = "python {} {} True".format(py_file, url)
            print("Running Command: '{}'". format(cmd))
            os.system(cmd)
#end_parse_url

with open(".data.json") as data_file:
    data = json.load(data_file)["sites"]
print("\n")
url = input("Enter URL of (H-)Mango: ")
parse_url(url, data)