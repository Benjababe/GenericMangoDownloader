import math
import os
import pickle
import re
import requests
import sys
import time

from urllib.parse import urlparse

#local libs
from template import Template
from functions import Functions
import constants as const

#type(chapter/manga), chapter/mango id
api_format = const.DEX + "/api/{}/{}"
#server, hash, filename
img_format = "{}/{}/{}"
#mango id
cover_format = const.DEX + "/images/manga/{}.jpg"

functions = Functions()

class Dex:
    def __init__(self):
        self.SITE = const.DEX
        self.CHAPTER_LIST = "chapter_list"

    def get_chapters(self, url):
        mango_info = dex_parse(url, end = self.CHAPTER_LIST)
        chapter_urls = []
        for chapter in mango_info[1]["chapters"]:
            chapter_urls.append(const.DEX_READER.format(chapter["id"]))
        ret = {
            "mango_title":  mango_info[1]["mango_title"],
            "chapter_list": mango_info[0],
            "chapter_urls": chapter_urls,
            "thumb_url": cover_format.format(mango_info[1]["mango_id"])
        }

        return ret

    def download(self, url):
        check_resume()
        dex_parse(url)

#check sort url whether it is the reader or the preview page
def dex_parse(link, end = None):
    if type(link) == "str":
        link = link.strip()
    path = urlparse(link).path
    preview_pattern = r"\/title\/[0-9]{0,10}\/.*"
    reader_pattern = r"\/chapter\/[0-9]{0,10}[\/\\0-9]{0,10}"

    preview_match = re.match(preview_pattern, path)
    reader_match = re.match(reader_pattern, path)

    if preview_match and preview_match.span()[1] == len(path):
        mango_id = path.split("/")[2]
        return dex_mango_id_parser(mango_id, end = end)
    elif reader_match and reader_match.span()[1] == len(path):
        chapter_id = path.split("/")[2]
        dex_reader(chapter_id)
    else:
        dex_error()
#end_dex_parse

#handles any preview links
def dex_mango_id_parser(mango_id, dl_input = -1, end = None):
    res = requests.get(api_format.format("manga", mango_id), hooks = hooks)
    res.close()
    json = res.json()
    mango_info = { "mango_id": mango_id, "mango_title": json["manga"]["title"], "chapters": [] }
    chapters = json["chapter"]
    chapter_nums = []
    for id in chapters:
        #englando chapters
        if chapters[id]["lang_code"].upper() == const.DEX_LANG and chapters[id]["chapter"].isnumeric():
            chapter_info = chapters[id]
            chapter_info["id"] = id
            chapter_nums.append(float(chapter_info["chapter"]))
            mango_info["chapters"].insert(0, chapter_info)
    #end_for_loop
    chapter_nums.sort()
    #halts operation of the end is the desired chapter listing
    if (end == Dex().CHAPTER_LIST):
        return [chapter_nums, mango_info]
    else:
        dex_request_chapters(mango_info, chapter_nums, dl_input)
#end_dex_preview

#requests user input for which chapters to download
def dex_request_chapters(mango_info, chapter_nums, dl_input = -1):
    str_dl = "Please indicate which chapter(s) to download ({}-{}) eg. 1-14: "
    #shows first and last chapters in the list
    if dl_input == -1:
        dl_input = input(str_dl.format(chapter_nums[0], chapter_nums[-1]))
    dl = dl_input.split("-")
    #single chapter selected
    if len(dl) == 1:
        chapter = [ float(dl[0]) ]
    #multiple chapters selected
    elif len(dl) == 2:
        chapter = [ float(dl[0]), float(dl[1]) ]
    pending_downloads = mango_info_retriever(mango_info, chapter)
    dex_download(pending_downloads)

#returns mango info if so desired 
def mango_info_retriever(mango_info, chapter):
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

#handles any reader links
def dex_reader(chapter_id):
    res = requests.get(api_format.format("chapter", chapter_id), hooks = hooks)
    res.close()
    json = res.json()
    dex_mango_id_parser(json["manga_id"], dl_input = json["chapter"])
#end_dex_reader

def dex_error():
    print("Error with URL provided...")
    dex.link = ""
    link = dex.request_link()
    dex_parse(link)

#url_list variable is only needed to retrieve title of chapters
def dex_download(pending_downloads, resume = False):
    title = pending_downloads["mango_title"]
    chapters = pending_downloads["chapters"]

    #where dl stopped if resume exists
    resume_pg = resume_ch = -1

    #creates temp file
    if not os.path.exists(dex.pickle):
        dex.update_pickle([resume_pg, resume_ch, pending_downloads])
    else:
        resume_pg, resume_ch, pending_downloads = dex.get_pickle()

    for i in range(0, len(chapters)):
        chapter = chapters[i]
        if i >= resume_ch:
            handle_chapter_download(title, chapter, [resume_pg, i, pending_downloads])
        #end_if_resume_chapter
    #end_chapter_loop
    #deletes resume file when dl completes
    if os.path.exists(dex.pickle):
        os.remove(dex.pickle)
    if __name__ == "__main__":
        dex.restart_app()
#end_dex_download

#getting all the info needed to download image
def get_chapter_info(ch_data, title):
    if ch_data["status"] == "external":
        print("Mango is currently only available on: {}".format(ch_data["external"]))
    ch_server = ch_data["server"]
    ch_hash = ch_data["hash"]
    ch_page_array = ch_data["page_array"]
    ch_title = "{} Ch. {} - {}".format(title, ch_data["chapter"], ch_data["title"])
    folder_path = const.DOWNLOAD_PATH + re.sub(r"[\\/:*?\"<>|]", "", ch_title).strip()
    return [ch_server, ch_hash, ch_page_array, ch_title, folder_path]

def handle_chapter_download(title, chapter, pickle_info):
    res = requests.get(api_format.format("chapter", chapter["id"]), hooks = hooks)
    res.close()
    ch_data = res.json()
    ch_server, ch_hash, ch_page_array, ch_title, folder_path = get_chapter_info(ch_data, title)

    #creates download folder if doesn't exist
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    for pg in range(0, len(ch_page_array)):
        if pg >= pickle_info[0]:
            src = img_format.format(ch_server, ch_hash, ch_page_array[pg])
            #repeats image download 5 times in event of an exception being caught
            for attempt in range(5):
            	try:
            		res = requests.get(src, headers={"Connection": "Keep-Alive"}, hooks = hooks)
            		with open("{}/{}".format(folder_path, ch_page_array[pg]), "wb") as img:
                		img.write(res.content)
                		img.close()
            		res.close()
            	except Exception as ex:
            		print("\nProblem with download, retrying in 2 seconds...")
            		time.sleep(2)
            	else:
            		break
            else:
            	print("Error with download. This will only show if image failed to download 5 times :(")
            #updates pickle on download status every page dl completion
            dex.update_pickle([pg, pickle_info[1], pickle_info[2]])
            functions.display_download(ch_title, pg + 1, len(ch_page_array))
    #end_individual_chapter_download_loop

    #updates pickle on download status every chapter dl completion
    dex.update_pickle([pg, pickle_info[1], pickle_info[2]])
    print("\n")
#end_handle_chapter_download

#queries if user wants to continue previous halted dl
def check_resume():
    if os.path.exists(dex.pickle):
        f = open(dex.pickle, "rb")
        pg, chapter_loop, pending_downloads = pickle.load(f)
        f.close()
        user_input = input("There is an unfinished download for {} at Chapter {} Page {}. Would you like to resume? (Y/N)  "
                        .format(pending_downloads["mango_title"], 
                                pending_downloads["chapters"][chapter_loop]["chapter"], 
                                pg + 1)).upper()
        if (user_input == "Y" or user_input == "YES"):
            dex_download(pending_downloads, True)
        elif (user_input == "N" or user_input == "NO"):
            os.remove(dex.pickle)

#callback on response for requests library
hooks = {"response": functions.res_hook}

#setups script with template of generic functions
dex = Template("Please enter MangoDex URL: ", "dex")

#only runs this snippet if ran by dl_dex.py
if __name__ == "__main__":
    dex.set_post_request(dex_parse)
    #checks if resume.pckl exists
    check_resume()
    link = dex.request_link()
    dex_parse(link)
