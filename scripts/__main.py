#my local files
import constants as const

libs = []

def request_url():
    url = input("Enter URL of (H-)Mango: ")
    if (url.lower() == "q" or url.upper() == "Q"):
        raise SystemExit
    else:
        parse_url(url, const.DATA["sites"])

def parse_url(url, data):
    for lib in libs:
        if url.__contains__(lib.SITE):
            lib.download(url)
            request_url()
#end_parse_url

#imports all library files named in constants file under the site key.
#removes clutter if more sites are added in future
for site in const.DATA["sites"]:
    site = const.DATA["sites"][site]
    file_name = list(site.keys())[0]
    class_name = list(site.values())[0]
    #eg. from dl_dex import Dex
    #    libs.append(Dex())
    exec("from {} import {}".format(file_name, class_name) + 
         "\nlibs.append({}())".format(class_name))
#end_import_loop

print("\n")
request_url()