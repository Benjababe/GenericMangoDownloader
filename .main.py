import os

#my local files
import constants as const

libs = []

def parse_url(url, data):
    for lib in libs:
        if url.__contains__(lib.SITE):
            lib.download(url)
            url = input("Enter URL of (H-)Mango: ")
            parse_url(url, const.DATA["sites"])
#end_parse_url

#imports all library files named in constants file under the site key.
#removes clutter if more sites are added in future
for site in const.DATA["sites"]:
    site = const.DATA["sites"][site]
    file_name = list(site.keys())[0]
    class_name = list(site.values())[0]
    exec("from {} import {}".format(file_name, class_name) + 
         "\nlibs.append({}())".format(class_name))

print("\n")
url = input("Enter URL of (H-)Mango: ")
parse_url(url, const.DATA["sites"])