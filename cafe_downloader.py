from bs4 import BeautifulSoup
import cfscrape
import os
import re
import tkinter as tk

scraper = cfscrape.create_scraper()
title = ""

def download(e):
    url = txtUrl.get().strip()
    content = scraper.get(url).content
    soup = BeautifulSoup(content, "html.parser")
    title = soup.title.string
    title = title[0:title.index(":")].strip()
    src = soup.find("img")["src"]
    pages = soup.find("div", {"class": "text"}).text
    pages = int(re.sub("[^0-9]", "", pages))
    
    ext = src[src.rfind("."):len(src)]
    base = src[0:src.rfind("/")]
    zero = hasZero(src)

    for i in range(1, pages+1):
        z = ""
        if (i < 10 and zero):
            z = "0"
        filename = "{}{}{}".format(z, i, ext)
        imgUrl = base + "/" + filename
        print("Downloading: {}".format(imgUrl))
        cfurl = scraper.get(imgUrl).content
        folderpath = title
        if not os.path.exists(folderpath):
            print("Creating folder: {}".format(folderpath))
            os.makedirs(folderpath)
        with open("{}/{}".format(folderpath, filename), "wb") as f:
            f.write(cfurl)

def hasZero(url):
    check = url.rfind(".") - 2
    return (url[check] == "0") 

master = tk.Tk()
master.title("Cafe Downloader")

tk.Label(master, text="URL: ").grid(row=0)
txtUrl = tk.Entry(master, width=70)
txtUrl.bind("<Return>", download)
txtUrl.grid(row=0, column=1)
txtUrl.focus()
btnUrl = tk.Button(master, text="Download")
btnUrl.bind("<Button-1>", download)
btnUrl.grid(row=0, column=2)

master.mainloop()
