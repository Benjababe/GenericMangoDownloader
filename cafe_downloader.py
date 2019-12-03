from bs4 import BeautifulSoup
import cfscrape
import math
import os
import re
import sys
#import tkinter as tk

scraper = cfscrape.create_scraper()
title = ""

def request_link():
    print("\n")
    link = input("Please enter Cafe URL: ")
    cafe_parse(link)
#end_request_link

def cafe_parse(e):
    if type(e) == type("str"):
        url = e.strip()
    else:
        url = txtUrl.get().strip()
    if ("cafe/manga/read" in url):
        cafe_reader(url)
    else:
        cafe_info_page(url)
#end_cafe_parse
        
def cafe_info_page(url):
    content = scraper.get(url).content
    soup = BeautifulSoup(content, "html.parser")
    cafe_url = soup.find("a", {"class": "x-btn-large"})["href"]
    if ("cafe/manga/read" in cafe_url):
        cafe_reader(cafe_url)
    else:
        print("URL is invalid")
#end_cafe_info_page

def cafe_reader(url):
    content = scraper.get(url).content
    soup = BeautifulSoup(content, "html.parser")
    title = soup.title.string
    title = title[0:title.index(":")].strip()
    src = soup.find("img")["src"]
    pages = soup.find("div", {"class": "text"}).text
    pages = int(re.sub("[^0-9]", "", pages))
    
    ext = src[src.rfind("."):len(src)]
    base = src[0:src.rfind("/")]
    zero = has_zero(src)

    for i in range(1, pages+1):
        z = ""
        if (i < 10 and zero):
            z = "0"
        filename = "{}{}{}".format(z, i, ext)
        imgUrl = base + "/" + filename        
        #print("Downloading: {}".format(imgUrl))
        folderpath = title
        if not os.path.exists(folderpath):
            print("Creating folder: {}".format(folderpath))
            os.makedirs(folderpath)
        
        cfurl = scraper.get(imgUrl).content
        with open("{}/{}".format(folderpath, filename), "wb") as f:
            f.write(cfurl)
        download_status = "\rDownloading {}... [{}{}] {}%".format(
                            title, "=" * i, " " * (pages - i), math.ceil(i / pages * 100))
        sys.stdout.write(download_status)
        sys.stdout.flush()
    #Cycles the requesting process
    request_link()
    #end_for_loop
        
#end_cafe_reader

def has_zero(url):
    check = url.rfind(".") - 2
    return (url[check] == "0")
#end_has_zero

request_link()

'''
master = tk.Tk()
master.title("Cafe Downloader")

tk.Label(master, text="URL: ").grid(row=0)
txtUrl = tk.Entry(master, width=70)
txtUrl.bind("<Return>", cafe_parse)
txtUrl.grid(row=0, column=1)
txtUrl.focus()
btnUrl = tk.Button(master, text="Download")
btnUrl.bind("<Button-1>", cafe_parse)
btnUrl.grid(row=0, column=2)

master.mainloop()
'''
