import os

#my local files
import constants as const

from dl_cafe import Cafe
from dl_dex import Dex
from dl_nh import NH

libs = [Cafe(), Dex(), NH()]

query = "Enter URL of (H-)Mango: "

def parse_url(url, data):
    for lib in libs:
        if url.__contains__(lib.SITE):
            lib.download(url)
            url = input(query)
            parse_url(url, const.DATA["sites"])
#end_parse_url

print("\n")
url = input(query)
parse_url(url, const.DATA["sites"])