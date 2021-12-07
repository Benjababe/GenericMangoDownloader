import json

import requests
import misc
import re

from bs4 import BeautifulSoup

SITE_URL = "https://nhentai.net"

csrf_pattern = r"csrf_token: \"([a-zA-Z0-9]*)\""


def login(session: requests.Session, session_id: str = ""):
    """Logs in via already existing session cookie

    Args:
        session (requests.Session): Session object to contain login session
        session_id (str, optional): Already existing session ID. Defaults to "".
    """
    if session_id == "":
        session_id = input("Please enter session ID: ")

    session.cookies.set(name="sessionid", value=session_id,
                        domain="nhentai.net")

    res = session.get(SITE_URL)
    res.close()
    soup = BeautifulSoup(res.text, "html.parser")

    misc.write_pickle("nhentai", "session", session)
    username = soup.find("span", "username").text.strip()
    print(f"Logged in as {username}")
# end_login


'''
def favourite(session: requests.Session, manga_id: str):
    """(Un)Favourites manga by manga_id parameter given

    Args:
        session (requests.Session): Session object containing login session
        manga_id (str): Manga ID to be (un)favourited
    """

    gallery_url = f"{SITE_URL}/g/{manga_id}/"

    res = session.get(gallery_url)
    res.close()
    soup = BeautifulSoup(res.text, "html.parser")

    # searches all of html file for csrf token value
    csrf_token = re.search(csrf_pattern, res.text).group(1)
    title = soup.find("span", "pretty").string
    btn_fav = soup.find("button", {"id": "favorite"}).find("span", "text")

    fav_headers = {
        "x-csrftoken": csrf_token,
        "x-requested-with": "XMLHttpRequest"
    }

    # in case it's already favourited
    if btn_fav.string == "Unfavorite":
        msg = f"Manga '{title}' is already favourited. Do you wish to unfavourite? (y/N): "
        fav = input(msg)

        if fav.lower() in ["y", "yes"]:
            res = session.post(
                f"{SITE_URL}/api/gallery/{manga_id}/unfavorite", headers=fav_headers)
            res.close()
            check_fav_res(res, title)

        return

    res = session.post(
        f"{SITE_URL}/api/gallery/{manga_id}/favorite", headers=fav_headers)
    res.close()
    check_fav_res(res, title)
# end_favourite


# checks favourite status
def check_fav_res(res: requests.Response, title: str):
    """Checks favourite status from HTTP Response

    Args:
        res (requests.Response): HTTP Response after trying to (un)favourite a manga
        title (str): Title of manga to be (un)favourited
    """

    if (res.status_code == 200):
        data = json.loads(res.text)
        print(title, end=" has been ")
        print("favourited" if data["favorited"] else "unfavourited")
    else:
        print("Error with request")
# end_check_fav_res
'''
