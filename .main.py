import os

#my local constants
import constants as const

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

print("\n")
url = input("Enter URL of (H-)Mango: ")
parse_url(url, const.DATA["sites"])