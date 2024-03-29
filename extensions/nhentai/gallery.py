import json
import re
import requests
from bs4 import BeautifulSoup

import core

# global variables, used when accessing the same gallery page to reduce GET requests
GALLERY_FORMAT = "https://nhentai.net/g/{}"
gallery_url = ""
res = None
soup = None
gallery_headers = {}


def favourite(session: requests.Session, manga_id: str):
    """(Un)Favourites manga by manga_id parameter given

    Args:
        session (requests.Session): Session object containing login session
        manga_id (str): Manga ID to be (un)favourited
    """
    if not manga_id in gallery_url:
        set_globals(session, manga_id)

    title = soup.find("span", "pretty").string
    btn_fav = soup.find("button", {"id": "favorite"}).find("span", "text")

    # in case it's already favourited
    if btn_fav.string == "Unfavorite":
        msg = f"Manga '{title}' is already favourited. Do you wish to unfavourite? (y/N): "
        fav = input(msg)

        if fav.lower() in ["y", "yes"]:
            res = session.post(
                f"https://nhentai.net/api/gallery/{manga_id}/unfavorite",
                headers=gallery_headers,
            )
            res.close()
            check_fav_res(res, title)

        return

    fav_res = session.post(
        f"https://nhentai.net/api/gallery/{manga_id}/favorite", headers=gallery_headers
    )
    fav_res.close()
    check_fav_res(fav_res, title)


def check_fav_res(fav_res: requests.Response, title: str):
    """Checks favourite status from HTTP Response

    Args:
        res_fav (requests.Response): HTTP Response after trying to (un)favourite a manga
        title (str): Title of manga to be (un)favourited
    """

    if fav_res.status_code == 200:
        data = json.loads(fav_res.text)
        print(title, end=" has been ")
        print("favourited" if data["favorited"] else "unfavourited")
    else:
        print("Error with request")


# comments on manga by id
def comment(session: requests.Session, manga_id: str):
    """Comments on manga by manga_id parameter given

    Args:
        session (requests.Session): Session object containing login session
        manga_id (str): Manga ID of manga to be commented
    """

    global res

    if not manga_id in gallery_url:
        set_globals(session, manga_id)

    title = soup.find("span", "pretty").string

    comment_str = input("Please enter your comment: ").strip()
    while len(comment_str) < 10 or len(comment_str) > 1000:
        print("Please lengthen this text to between 10 and 1000 characters")
        comment_str = input("Please enter your comment: ").strip()

    comment_url = f"https://nhentai.net/api/gallery/{manga_id}/comments/submit"

    res = session.post(comment_url, headers=gallery_headers, json={"body": comment_str})
    res.close()
    data = json.loads(res.text)

    if "success" in data:
        # saves last comment for undoing
        last_comment = {"manga_id": manga_id, "comment_id": data["comment"]["id"]}
        core.write_pickle("nhentai", "last_comment", last_comment)
        print(f"Successfully commented on {title}")

    elif "error" in data:
        print(f"nhentai: {data['error']}")


def undo_comment(session: requests.Session):
    """Removes last comment made"""
    last_comment = core.read_pickle("nhentai", "last_comment")
    if last_comment is None:
        return

    if not last_comment["manga_id"] in gallery_url:
        set_globals(session, last_comment["manga_id"])

    delete_url = f"https://nhentai.net/api/comments/{last_comment['comment_id']}/delete"
    _res = session.post(delete_url, headers=gallery_headers)
    _res.close()
    data = json.loads(_res.text)

    if data["success"]:
        print("Last comment deleted")
        core.delete_pickle("nhentai", "last_comment")


def set_globals(session: requests.Session, manga_id: str):
    """Sets global variables by manga_id parameter given

    Args:
        session (requests.Session): Session object containing login session
        manga_id (str): Manga ID to be based off of
    """
    global gallery_url, res, soup, gallery_headers

    gallery_url = GALLERY_FORMAT.format(manga_id)

    res = session.get(gallery_url)
    res.close()
    soup = BeautifulSoup(res.text, "html.parser")

    # searches all of html file for csrf token value
    csrf_pattern = r"csrf_token: \"([a-zA-Z0-9]*)\""
    csrf_token = re.search(csrf_pattern, res.text).group(1)
    gallery_headers = {"x-csrftoken": csrf_token, "x-requested-with": "XMLHttpRequest"}
