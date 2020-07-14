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
f = Functions()
cafe_template = Template("Please enter Cafe URL: ", "cafe")

class Cafe:
    SITE = const.CAFE
    ABBR = const.CAFE_ABBR
    SEARCH = SITE + "/?s={}"
    def __init__(self):
        pass

    def get_chapters(self, url):
        cafe_template.END = cafe_template.END_CHAPTER_LIST
        return cafe_parse(url)
    #end_get_chapters

    def download(self, url_list, disp = None, messagebox = None):
        f.set_disp(disp)
        for url in url_list:
            cafe_parse(url)

#check sort url whether it is the reader or the preview page
def cafe_parse(link):
    if type(link) == type("str"):
        url = link.strip()
    if ("cafe/manga/read" in url):
        cafe_reader(url)
    else:
        return cafe_info_page(url)
#end_cafe_parse

def get_page_info(soup, cafe_url):
    data = {
        "chapter_list": [{ "chapter": "1", "group": "", "id": cafe_url, "site": "hentai.cafe" }],
        "cover_url": soup.find("img", {"class": "size-large"})["src"],
        "description": "",
        "mango_title": soup.find("h3").text
    }
    #resets end quota before returning info
    cafe_template.END = cafe_template.END_RESET
    return data
#end_get_reader_info

        
def cafe_info_page(url):
    #Checks if URL provided was the preview page before quitting
    res = scraper.get(url)
    res.close()
    soup = BeautifulSoup(res.content, "html.parser")

    try:
        cafe_url = soup.find("a", {"class": "x-btn-large"})["href"]
    except:
        print("URL is invalid")
        #returns False if request came from GUI
        if cafe_template.END == cafe_template.END_CHAPTER_LIST:
            return False
        #requests for user input after failure
        link = cafe_template.request_link()
        cafe_parse(link)

    if cafe_template.END == cafe_template.END_CHAPTER_LIST:
        return get_page_info(soup, cafe_url)
    elif ("cafe/manga/read" in cafe_url):
        cafe_reader(cafe_url)
        
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
    zero = f.has_zero(src)

    f.cf_download(scraper, title, zero, pages, ext, base)
    
    if __name__ == "__main__":
        cafe_template.restart_app()
#end_cafe_reader

#only runs this snippet if ran by dl_cafe.py
if __name__ == "__main__":
    cafe_template.set_post_request(cafe_parse)
    link = cafe_template.request_link()
    cafe_parse(link)