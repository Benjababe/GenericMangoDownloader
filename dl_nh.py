from bs4 import BeautifulSoup
import cfscrape
import sys

from urllib.parse import urlparse

#local lib
from functions import Functions
from template import Template

#setup
scraper = cfscrape.create_scraper()
functions = Functions()

#TODO include parsing failure on invalid URL entry

#check sort url whether it is the reader or the preview page
def nh_parse(link):
    if type(link) == type("str"):
        url = link.strip()
    path = urlparse(url).path
    #if length = 4 => gallery   if length = 5 => reader
    length = len(path.split("/"))
    is_gallery = True if length == 4 else False
    nh_download(url, is_gallery)
#end_nh_parse

def nh_download(url, is_gallery):
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

    nh.end(functions.run_main_app, nh.restart_app)
#end_nh_reader

nh = Template(sys.argv, "Please enter NH URL: ")
link = nh.request_link()
nh_parse(link)