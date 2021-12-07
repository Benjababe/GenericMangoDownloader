import json
import requests

import misc

API_URL = "https://api.mangadex.org"


def login(session: requests.Session, username: str, password: str = "", mark_on_dl: str = ""):
    """Logs into MangaDex and saves the login session

    Args:
        session (requests.Session): Session object used for HTTP requests
        username (str): Login username
        password (str, optional): Login password. Defaults to "".
        mark_on_dl (str, optional): String to indicate whether to mark chapter as read on download. Defaults to "".
    """

    print("Logging in as", username)

    if password == "":
        password = input("Enter your password: ")

    login_url = f"{API_URL}/auth/login"
    login_json = {"username": username, "password": password}
    login_headers = {"Content-Type": "application/json"}

    res = session.post(login_url, json=login_json, headers=login_headers)
    res.close()
    data = json.loads(res.text)

    if data["result"] == "ok":
        # saving session information into cookies
        session.cookies.set(name="Login", value="true")
        session.cookies.set(name="session", value=data["token"]["session"])
        session.cookies.set(name="refresh", value=data["token"]["refresh"])
        session.headers.update({"Authorization": data["token"]["session"]})

        # saving current session into a pickle
        misc.write_pickle("mangadex", "session", session)
        print("Successfully logged in as", username)

        if mark_on_dl == "":
            mark_on_dl = input(
                "Would you like to mark chapters as read when downloaded? (y/N) ").lower()

            if mark_on_dl in ["y", "yes"]:
                mark_on_dl = True
            elif mark_on_dl in ["", "n", "no"]:
                mark_on_dl = False
            else:
                print("Invalid input, defaulting to no")
                mark_on_dl = False

        misc.write_pickle("mangadex", "mark_on_dl", mark_on_dl)
# end_login


def mark_chapter_read(session: requests.Session, chapter_id: str) -> bool:
    """Marks chapter as read by chapter_id parameter given

    Args:
        session (requests.Session): Session object that was used for login
        chapter_id (str): Chapter ID to be marked as read

    Returns:
        bool: Boolean flag to indicate whether marking was successful or not 
    """

    mark_url = f"{API_URL}/chapter/{chapter_id}/read"
    res = session.post(mark_url)
    res.close()
    return res.ok
# end_mark_chapter


def mark_chapter_unread(session: requests.Session, chapter_id: str) -> bool:
    """Marks chapter as unread by chapter_id parameter given

    Args:
        session (requests.Session): Session object that was used for login
        chapter_id (str): Chapter ID to be marked as unread

    Returns:
        bool: Boolean flag to indicate whether marking was successful or not 
    """

    mark_url = f"{API_URL}/chapter/{chapter_id}/read"
    res = session.delete(mark_url)
    res.close()
    return res.ok
# end_mark_chapter


# updates reading status ["reading", "on_hold", "plan_to_read", "dropped", "re_reading", "completed"]
def update_reading_status(session: requests.Session, manga_id: str, status_index: int = -1):
    """Updates reading status of manga by manga_id parameter given

    Args:
        session (requests.Session): Session object that was used for login
        manga_id (str): Manga ID for its status to be changed
        status_index (int): Index of status to set for manga. Defaults to -1.

    Returns:
        bool: Boolean flag to indicate whether marking was successful or not 
    """

    msg = "Enter manga status:\n1.Reading\n2.On hold\n3.Plan to read\n4.Dropped\n5.Re-reading\n6.Completed\n:"
    while status_index < 0 or status_index > 5:
        status_index = int(input(msg)) - 1

    status_list = ["reading", "on_hold", "plan_to_read",
                   "dropped", "re_reading", "completed"]

    url = f"{API_URL}/manga/{manga_id}/status"
    res = session.post(url, headers={
        "Content-Type": "application/json"
    }, json={
        "status": status_list[status_index]
    })
    res.close()

    if res.ok:
        print("Manga status updated")
    else:
        print("Error with updating status")

    return res.ok


# end_update_reading_status
