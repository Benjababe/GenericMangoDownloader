from bs4 import BeautifulSoup
import cfscrape
import re
import sys

#local lib
from functions import Functions
from template import Template
import constants as const

#setup
scraper = cfscrape.create_scraper()
functions = Functions()

class Cafe:
    def __init__(self):
        self.SITE = const.CAFE

    def download(self, url):
        cafe_parse(url)

#check sort url whether it is the reader or the preview page
def cafe_parse(link):
    if type(link) == type("str"):
        url = link.strip()
    if ("cafe/manga/read" in url):
        cafe_reader(url)
    else:
        cafe_info_page(url)
#end_cafe_parse
        
def cafe_info_page(url):
    #Checks if URL provided was the preview page before quitting
    content = scraper.get(url).content
    soup = BeautifulSoup(content, "html.parser")
    cafe_url = soup.find("a", {"class": "x-btn-large"})["href"]
    if ("cafe/manga/read" in cafe_url):
        cafe_reader(cafe_url)
    else:
        print("URL is invalid")
        #requests for user input after failure
        link = cafe.request_link()
        cafe_parse(link)
#end_cafe_info_page

def cafe_reader(url):
    content = scraper.get(url).content
    soup = BeautifulSoup(content, "html.parser")
    #title will be the folder name of download
    title = soup.title.string
    title = title[0:title.index(":")].strip()
    src = soup.find("img")["src"]
    pages = soup.find("div", {"class": "text"}).text
    pages = int(re.sub("[^0-9]", "", pages))
    
    #image extension
    ext = src[src.rfind("."):len(src)]
    #entire url of image before the actual file name
    base = src[0:src.rfind("/")]
    #check if pages less than 10 have a 0 on the front of their filename
    zero = functions.has_zero(src)

    functions.cf_download(scraper, title, zero, pages, ext, base)
    
    if __name__ == "__main__":
        cafe.restart_app()
#end_cafe_reader

#only runs this snippet if ran by dl_cafe.py
if __name__ == "__main__":
    cafe = Template("Please enter Cafe URL: ")
    cafe.set_post_request(cafe_parse)
    link = cafe.request_link()
    cafe_parse(link)
