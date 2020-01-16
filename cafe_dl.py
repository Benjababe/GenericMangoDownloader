from bs4 import BeautifulSoup
import cfscrape
import json
import os
import re
import sys

from functions import Functions

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
        link = input("Please enter Cafe URL: ")
    cafe_parse(link)
#end_request_link

#check sort url whether it is the reader or the preview page
def cafe_parse(e):
    if type(e) == type("str"):
        url = e.strip()
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
        request_link()
#end_cafe_info_page

def cafe_reader(url):
    global run_main
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
    
    if run_main:
        functions.run_main()
    else:
        restart()
#end_cafe_reader

def restart():
    global link, run_main
    link = ""
    run_main = False
    request_link()

request_link()