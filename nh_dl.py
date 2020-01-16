from bs4 import BeautifulSoup
import cfscrape
import json
import os
import re
import sys

from functions import Functions
from urllib.parse import urlparse

#basic setup
scraper = cfscrape.create_scraper()
functions = Functions()
link = ""
run_main = False

if len(sys.argv) > 1:
    link = sys.argv[1]

if len(sys.argv) > 2:
    run_main = sys.argv[2]

def request_link():
    print("\n")
    global link
    if link == "":
        link = input("Please enter NH URL: ")
    nh_parse(link)
#end_request_link

#check sort url whether it is the reader or the preview page
def nh_parse(e):
    if type(e) == type("str"):
        url = e.strip()
    path = urlparse(url).path
    #if length = 4 => gallery   if length = 5 => reader
    length = len(path.split("/"))
    is_gallery = True if length == 4 else False
    nh_download(url, is_gallery)
#end_nh_parse

def nh_download(url, is_gallery):
    global run_main
    if is_gallery:
        #throws to gallery, subject to change
        url += "1"
    content = scraper.get(url).content
    soup = BeautifulSoup(content, "html.parser")
    title = soup.title.string
    title = title[0:title.index("- Page 1 »")].strip()
    pages = int(soup.find("span", {"class": "num-pages"}).text)
    src = soup.find("section", {"id": "image-container"}).find("img")["src"]

    #image extension
    ext = src[src.rfind("."):len(src)]
    #entire url of image before the actual file name
    base = src[0:src.rfind("/")]
    #single digit files so not have a "0" in front of it
    zero = False

    functions.cf_download(scraper, title, zero, pages, ext, base)

    if run_main:
        functions.run_main()
    else:
        restart()
#end_nh_reader

def restart():
    global link, run_main
    link = ""
    run_main = False
    request_link()

request_link()