from bs4 import BeautifulSoup
import argparse
import cfscrape
import json
import re
import requests
import sys

from urllib.parse import urlparse

#local lib
from functions import Functions
from template import Template
import constants as const

#setup
session = cfscrape.Session()
f = Functions()
nh_template = Template("Please enter NH URL: ", resume_pickle = "nh_resume", cookies_pickle = "nh_cookies")

class NH:
    SITE = const.NH
    THUMB = "https://t.nhentai.net"
    GALLERY = "https://i.nhentai.net/galleries/{}/"
    ABBR = const.NH_ABBR
    G_API = SITE + "/api/gallery/{}"
    RANDOM = SITE + "/random/"
    SEARCH = SITE + "/search/?q={}"

    IMG_TYPES = json.loads('{"j": ".jpg", "p": ".png", "g": ".gif"}')

    def __init__(self):
        pass

    def get_chapters(self, url):
        nh_template.END = nh_template.END_CHAPTER_LIST
        return nh_parse(url)

    def download(self, url_list, disp = None, messagebox = None):
        f.set_disp(disp)
        for url in url_list:
            nh_parse(url)

#retrieves nh_id and passes it to nh_download
def nh_parse(url):
    path = urlparse(url.strip()).path
    #arr = ["g", "nh_id", "page_if_entered"]
    arr = list(filter(len, path.split("/")))
    nh_id = arr[1]
    #returns to GUI
    if nh_template.END == nh_template.END_CHAPTER_LIST:
        return nh_info_page(arr[1])
    else:
        nh_download(nh_id)
#end_nh_parse

def nh_download(nh_id):
    api_url = NH.G_API.format(nh_id)
    res_json = json.loads(session.get(api_url).text)

    if "err" in res_json:
        print("Error with nh mango ID provided.")
        return
    
    title = res_json["title"]["english"]
    # number of pages
    pages = len(res_json["images"]["pages"])
    # jpg or png
    ext = NH.IMG_TYPES[res_json["images"]["pages"][0]["t"]]
    # https://i.nhentai.net/galleries/media_id/
    base = NH.GALLERY.format(res_json["media_id"])
    #single digit files so not have a "0" in front of it
    zero = False

    f.cf_download(session, title, zero, pages, ext, base)

    #only requests for nh links again if this was the file that the user initiated with
    if __name__ == "__main__":
        nh_template.restart_app()
#end_nh_reader

def nh_info_page(nh_id):
    url = NH.G_API.format(nh_id)
    res_json = json.loads(session.get(url).text)
    cover_type = res_json["images"]["cover"]["t"]
    data = {
        "chapter_list": [{"chapter": "1", "group": "", "id": NH.SITE + "/g/" + nh_id, "site": "nhentai.net"}],
        #raw dogging it
        "cover_url": "https://t.nhentai.net/galleries/" + res_json["media_id"] + "/cover." + NH.IMG_TYPES[cover_type],
        "description": "",
        "mango_title": res_json["title"]["english"]
    }
    #resets end quota before returning info
    nh_template.END = nh_template.END_RESET
    return data
#end_nh_info_page

def login(username, password):
    login_url = NH.SITE + "/login/"
    res = session.get(login_url)
    soup = BeautifulSoup(res.content, "html.parser")
    token = soup.find("input", {"name": "csrfmiddlewaretoken"})["value"]

    #referer header is very important in CSRF situations for this site
    res = session.post(login_url, data = {
        "csrfmiddlewaretoken": token,
        "username_or_email": username,
        "password": password,
        "next": ""
    }, headers = { "referer": login_url })
    if res.url == NH.SITE + "/":
        print("Logged in successfully")
        nh_template.update_pickle(nh_template.cookies_pickle, session.cookies)
    else:
        print("Login for " + username + " failed")
#end_login

def login_session(sessionid):
    sess_cookie = requests.cookies.create_cookie(domain="nhentai.net",name="sessionid",value=sessionid)
    session.cookies.set_cookie(sess_cookie)
    nh_template.update_pickle(nh_template.cookies_pickle, session.cookies)

    res = session.get(NH.SITE)
    soup = BeautifulSoup(res.content, "html.parser")

    sign_in_btn = soup.find("li", {"class": "menu-sign-in"})
    if sign_in_btn == None:
        print("Login session updated successfully")
    else:
        print("Imported session is invalid")
#end_login_session

def favorite(mango_id):
    mango_url = NH.SITE + "/g/{}/".format(str(mango_id))
    res = session.get(mango_url)
    soup = BeautifulSoup(res.content, "html.parser")

    fav = soup.find("span", {"class": "text"}).text.lower()
    html = res.text
    post_url = NH.G_API.format(str(mango_id)) + "/{}".format(fav)

    #old
    '''
    tk_start = html.index("csrf_token: \"")
    #13 to account for the csrf_token: "
    html = html[tk_start+13:]
    token = html[:html.index("\"")]
    '''

    pattern = re.compile(r"(csrf_token: ).+?(?=\")\"")
    search = re.search(pattern, html)
    token = search.group(0)
    token = token.split(":")[1].replace("\"", "").strip()

    res = session.post(post_url, headers = {
        "referer": mango_url,
        "x-csrftoken": token,
        "x-requested-with": "XMLHttpRequest"
    }) 

    if res.status_code == 200:
        json_res = json.loads(res.text)
        print("Mango ID {} has been {}".format(mango_id, "favorited" if (json_res["favorited"]) else "unfavorited"))
#end_favorite

def comment(mango_id, comment_str):
    if len(comment_str) < 10:
        print("Commenting requires 10 or more characters!")
        return
    #similar to above
    mango_url = NH.SITE + "/g/{}/".format(str(mango_id))
    res = session.get(mango_url)
    soup = BeautifulSoup(res.content, "html.parser")

    fav = soup.find("span", {"class": "text"}).text.lower()
    html = res.text

    #ye olden method
    '''
    tk_start = html.index("csrf_token: \"")
    #+13 to account for the csrf_token: "
    html = html[tk_start+13:]
    token = html[:html.index("\"")]
    '''

    post_url = NH.G_API.format(str(mango_id)) + "/comments/submit"
    pretty_title = soup.find("span", {"class": "pretty"}).text

    #grabs "csrf_token: ..."
    pattern = re.compile(r"(csrf_token: ).+?(?=\")\"")
    search = re.search(pattern, html)
    token = search.group(0)
    token = token.split(":")[1].replace("\"", "").strip()

    res = session.post(post_url, headers = {
        "referer": mango_url,
        "x-csrftoken": token,
        "x-requested-with": "XMLHttpRequest",
    }, json = {
        "body": comment_str
    })

    if res.status_code == 200:
        json_res = json.loads(res.text)
        print("Comment {} for \"{}\"".format("successfully posted comment" \
            if json_res["success"] else "failed to post", 
            pretty_title))
    elif res.status_code == 403:
        json_res = json.loads(res.text)
        print(json_res["error"])
#end_comment

def random():
    res = session.get(NH.RANDOM)
    nh_parse(res.url)
#end_random

def check_args():
    #sets max length of printout 100 chars
    parser = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=100))
    
    parser.add_argument("-L", "--login", nargs=2, metavar=("username", "password"), dest="login", help="Passes through username, password to login")
    parser.add_argument("-LS", "--login-session", metavar="sessionid", dest="sessionid", help="Logs in via your browser's sessionid")
    parser.add_argument("-RD", "--random", action="store_true", dest="random", help="Returns a random hentei")
    parser.add_argument("-DL", "--download", metavar="url", dest="download", help="Downloads by hentei provided by the URL")
    parser.add_argument("-F", "--favorite", metavar="mango_id", dest="fav", help="Toggles favorite by mango ID")
    parser.add_argument("-CM", "--comment", nargs=2, metavar=("mango_id", "comment_string"), dest="comment", help="Submits your comment according to the mango ID provided. There is a 2 minute cooldown for every comment you make")

    for arg in parser.parse_args().__dict__:
        val = parser.parse_args().__dict__[arg]
        if (val == None):
            continue
        if (arg == "login"):
            login(*val)
            sys.exit(0)
        if (arg == "sessionid"):
            login_session(val)
            sys.exit(0)
        if (arg == "random" and val == True):
            nh_template.kill_flag = True
            random()
        if (arg == "download"):
            nh_template.kill_flag = True
            nh_parse(val)
        if (arg == "fav"):
            favorite(val)
            sys.exit(0)
        if (arg == "comment"):
            comment(*val)
            sys.exit(0)
#end_check_args

#only runs this snippet if ran by dl_nh.py
if __name__ == "__main__":
    nh_template.set_post_request(nh_parse)
    session.cookies = nh_template.get_pickle(nh_template.cookies_pickle, session.cookies)

    check_args()

    link = nh_template.request_link()
    nh_parse(link)