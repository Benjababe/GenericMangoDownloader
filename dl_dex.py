from bs4 import BeautifulSoup
import requests
import os
import re
import sys

from urllib.parse import urlparse

#local libs
from template import Template
from functions import Functions

#chapter_id
api_format = "https://mangadex.org/api/?id={}&type=chapter"
#hash, filename
img_format = "https://s5.mangadex.org/data/{}/{}"

functions = Functions()

#check sort url whether it is the reader or the preview page
def dex_parse(link):
    if type(link) == "str":
        link = link.strip()
    path = urlparse(link).path
    preview_pattern = r"\/title\/[0-9]{0,10}\/.*"
    reader_pattern = r"\/chapter\/[0-9]{0,10}[\/\\0-9]{0,10}"

    preview_match = re.match(preview_pattern, path)
    reader_match = re.match(reader_pattern, path)

    if preview_match and preview_match.span()[1] == len(path):
        dex_preview(link)
    elif reader_match and reader_match.span()[1] == len(path):
        dex_reader(link, path)
    else:
        print("Error with URL provided...")
        link = dex.request_link()
        dex_parse(link)
#end_dex_parse

def dex_preview(url):
    #filtering language to englando
    jar = requests.cookies.RequestsCookieJar()
    jar.set("mangadex_filter_langs", "1")
    res = requests.get(url, cookies=jar).text
    soup = BeautifulSoup(res, "html.parser")
    chapter_array = soup.findAll("div", {"class": "chapter-row"})[1:]
    chapter_dict = filter_chapters(chapter_array)
    chapter_no_arr = list(chapter_dict.keys())

    str_dl = "Please indicate which chapters to download ({}-{}) eg. 4-10: "
    u_input = input(str_dl.format(chapter_no_arr[0], chapter_no_arr[-1]))
    dex_parse_input(u_input, chapter_dict)
#end_dex_preview

def dex_reader(url, path):
    title = BeautifulSoup(requests.get(url).text, "html.parser").title.string
    mango_id = path.split("/")[2]
    res = requests.get(api_format.format(mango_id)).json()
    hash = res["hash"]
    page_array = res["page_array"]
    headers = {"Connection": "Keep-Alive"}

    folder_path = re.sub(r"[\\/:*?\"<>|]", "", title)

    if not os.path.exists(folder_path):
                os.makedirs(folder_path)

    for i in range(0, len(page_array)):
        img_url = img_format.format(hash, page_array[i])
        res = requests.get(img_url, headers=headers, stream=True)
        with open("{}/{}".format(folder_path, page_array[i]), "wb") as f:
            f.write(res.content)
            f.close()
        res.close()
        functions.display_download(title, i, len(page_array) - 1)
    #end_for_loop
    print("\n")
#end_dex_reader

def filter_chapters(chapter_array):
    chapter_dict = {}
    chapter_array = chapter_array[::-1]
    for i in range(0, len(chapter_array)):
        chapter_no = chapter_array[i]["data-chapter"]
        chapter_url = chapter_array[i].find("a")["href"]
        #{ 1: chapter_url, 2: chapter_url, ... }
        chapter_dict[chapter_no] = chapter_url
    return chapter_dict
#end_filter_chapters

def dex_parse_input(u_input, chapter_dict):
    chapters = u_input.split("-")
    if len(chapters) == 1:
        path = chapter_dict[chapters[0]]
        dex_reader("https://mangadex.org" + path, path)
    elif len(chapters) == 2:
        for i in range(int(chapters[0]), int(chapters[1]) + 1):
            path = chapter_dict[str(i)]
            dex_reader("https://mangadex.org" + path, path)
        #end_for_loop
    #end_if_else
    dex.end(functions.run_main_app, dex.restart_app)
#end_dex_parse_input

dex = Template(sys.argv, "Please enter MangoDex URL: ")
link = dex.request_link()
dex_parse(link)