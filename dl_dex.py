from datetime import datetime
import math
import os
import re
import requests
import sys

from urllib.parse import urlparse

#local libs
from template import Template
from functions import Functions
import constants as const

#type(chapter/manga), chapter/manga id
api_format = const.DEX + "/api/{}/{}"
#server, hash, filename
img_format = "{}/{}/{}"

functions = Functions()

def res_hook(res, *args, **kwargs):
    log = open(".http_log.txt", "a")
    log_str = "{} -- HTTP Connection with : '{}' resulted in a status code of '{}'".format(
        datetime.now().strftime("%H:%M:%S"), res.url, res.status_code
    )
    if "Content-Length" in res.headers.keys():
        #shows dl size in KB
        log_str += " with a download size of {}KB".format(round(int(res.headers["Content-Length"])/1024, 1))
    log.write(log_str + "\n")
    log.close()
#end_res_hook

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
        mango_id = path.split("/")[2]
        dex_mango_id_parser(mango_id)
    elif reader_match and reader_match.span()[1] == len(path):
        chapter_id = path.split("/")[2]
        dex_reader(chapter_id)
    else:
        dex_error()
#end_dex_parse

def dex_mango_id_parser(mango_id, dl_input = -1):
    res = requests.get(api_format.format("manga", mango_id), hooks = hooks)
    res.close()
    json = res.json()
    mango_info = {"mango_title": json["manga"]["title"], "chapters": []}
    chapters = json["chapter"]
    chapter_num = []
    for id in chapters:
        #englando chapters
        if chapters[id]["lang_code"].upper() == const.DEX_LANG:
            chapter_info = chapters[id]
            chapter_info["id"] = id
            chapter_num.append(float(chapter_info["chapter"]))
            mango_info["chapters"].insert(0, chapter_info)
    #end_for_loop
    chapter_num.sort()
    str_dl = "Please indicate which chapters to download ({}-{}) eg. 1-14: "
    #shows first and last chapters in the list
    if dl_input == -1:
        dl_input = input(str_dl.format(chapter_num[0], chapter_num[-1]))
    dl = dl_input.split("-")
    #single chapter selected
    if len(dl) == 1:
        chapter = [ float(dl[0]) ]
    #multiple chapters selected
    elif len(dl) == 2:
        chapter = [ float(dl[0]), float(dl[1]) ]
    pending_downloads = manga_info_retriever(mango_info, chapter)
    dex_download(pending_downloads)
#end_dex_preview

def manga_info_retriever(mango_info, chapter):
    def chapter_filter(chapter_info):
        ch = chapter_info["chapter"]
        if len(chapter) == 1:
            if float(ch) == chapter[0]:
                return True
            else:
                return False
        elif len(chapter) == 2:
            min = chapter[0]
            max = chapter[1]
            if float(ch) >= min and float(ch) <= max:
                return True
            else:
                return False
    mango_info["chapters"] = list(filter(chapter_filter, mango_info["chapters"]))
    return mango_info
#end_manga_info_retriever

def dex_reader(chapter_id):
    res = requests.get(api_format.format("chapter", chapter_id), hooks = hooks)
    res.close()
    json = res.json()
    dex_mango_id_parser(json["manga_id"], json["chapter"])
#end_dex_reader

def dex_error():
    print("Error with URL provided...")
    dex.link = ""
    link = dex.request_link()
    dex_parse(link)

#url_list variable is only needed to retrieve title of chapters
def dex_download(pending_downloads):
    title = pending_downloads["mango_title"]
    chapters = pending_downloads["chapters"]
    #in case the ssl decides to go nuts
    headers = { "Connection": "Keep-Alive" }

    for chapter in chapters:
        res = requests.get(api_format.format("chapter", chapter["id"]), hooks = hooks)
        res.close()
        ch_data = res.json()
        #getting all the info needed to download image
        ch_server = ch_data["server"]
        ch_hash = ch_data["hash"]
        ch_page_array = ch_data["page_array"]
        ch_title = "{} Ch. {} - {}".format(title, ch_data["chapter"], ch_data["title"])
        folder_path = "./downloads/" + re.sub(r"[\\/:*?\"<>|]", "", ch_title)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        for i in range(0, len(ch_page_array)):
            src = img_format.format(ch_server, ch_hash, ch_page_array[i])
            res = requests.get(src, headers=headers, hooks = hooks)
            with open("{}/{}".format(folder_path, ch_page_array[i]), "wb") as img:
                img.write(res.content)
                img.close()
            res.close()
            functions.display_download(ch_title, i + 1, len(ch_page_array))
        #end_individual_chapter_download_loop
        print("\n")
    #end_chapter_loop
    dex.end(functions.run_main_app, dex.restart_app)
#end_dex_download

#callback on response for requests library
hooks = {"response": res_hook}

dex = Template(sys.argv, "Please enter MangoDex URL: ")
dex.set_post_request(dex_parse)
link = dex.request_link()
dex_parse(link)