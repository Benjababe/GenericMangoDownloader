from bs4 import BeautifulSoup
import cfscrape
import sys

from urllib.parse import urlparse

#local lib
from functions import Functions
from template import Template
import constants as const

#setup
scraper = cfscrape.create_scraper()
functions = Functions()

class NH:
    def __init__(self):
        self.SITE = const.NH

    def download(self, url):
        nh_parse(url)

#check sort url whether it is the reader or the preview page
def nh_parse(link):
    if type(link) == type("str"):
        url = link.strip()
    path = urlparse(url).path
    #arr = ["g", "nh_id", "page_if_entered"]
    arr = list(filter(len, path.split("/")))
    #if length = 2 => gallery   if length = 3 => reader
    if arr[0] == "g" and len(arr) == 2:
        nh_download(url, True)
    elif arr[0] == "g" and len(arr) == 3:
        nh_download(url, False)
    else:
        print("Error with URL provided...")
#end_nh_parse

def nh_download(url, is_gallery):
    if is_gallery:
        #throws to reader, subject to change
        url += "1"
    content = scraper.get(url).content
    soup = BeautifulSoup(content, "html.parser")
    title = soup.title.string
    title = title[0:title.index("- Page")].strip()
    pages = int(soup.find("span", {"class": "num-pages"}).text)
    src = soup.find("section", {"id": "image-container"}).find("img")["src"]

    #image extension
    ext = src[src.rfind("."):len(src)]
    #entire url of image before the actual file name
    base = src[0:src.rfind("/")]
    #single digit files so not have a "0" in front of it
    zero = False

    functions.cf_download(scraper, title, zero, pages, ext, base)

    if __name__ == "__main__":
        nh.restart_app()
#end_nh_reader

#only runs this snippet if ran by dl_nh.py
if __name__ == "__main__":
    nh = Template("Please enter NH URL: ")
    nh.set_post_request(nh_parse)
    link = nh.request_link()
    nh_parse(link)