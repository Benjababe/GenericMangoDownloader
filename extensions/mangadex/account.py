from datetime import datetime
import json
import requests
from core.misc import read_pickle, write_pickle

API_URL = "https://api.mangadex.org"


def login(
    session: requests.Session,
    username: str = "",
    password: str = "",
    mark_on_dl: str = "",
):
    """Logs into MangaDex and saves the login session

    Args:
        session (requests.Session): Session object used for HTTP requests
        username (str): Login username. Defaults to "".
        password (str, optional): Login password. Defaults to "".
        mark_on_dl (str, optional): String to indicate whether to mark chapter as
        read on download. Defaults to "".
    """

    if username == "":
        username = input("Enter your username: ")

    else:
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
        update_login_session(session, data)
        print("Successfully logged in as", username)
        mark_on_dl_store = mark_on_dl

        if mark_on_dl == "":
            mark_on_dl = input(
                "Would you like to mark chapters as read when downloaded? (y/N) "
            ).lower()

            if mark_on_dl in ["y", "yes"]:
                mark_on_dl_store = True
            elif mark_on_dl in ["", "n", "no"]:
                mark_on_dl_store = False
            else:
                print("Invalid input, defaulting to no")
                mark_on_dl_store = False

        write_pickle("mangadex", "mark_on_dl", str(mark_on_dl_store))


def check_login_session(session: requests.Session):
    """Checks current session token expiry and refreshes if necessary

    Args:
        session (requests.Session): Session object used for HTTP requests
    """
    expires = -1
    for cookie in session.cookies:
        if cookie.name == "session" and cookie.expires is not None:
            expires = cookie.expires

    if datetime.now().timestamp() > expires:
        print("Login session expired, refreshing...")
        refresh_token = session.cookies.get("refresh")
        refresh_url = f"{API_URL}/auth/refresh"

        res = session.post(refresh_url, json={"token": refresh_token})
        res.close()
        data = json.loads(res.text)

        if data["result"] == "ok":
            update_login_session(session, data)
            print("Login session refreshed!")


def update_login_session(session: requests.Session, data: dict):
    """Update session information with MangaDex response on auth

    Args:
        session (requests.Session): Session object used for HTTP requests
        data (dict): JSON containing session and refresh tokens
    """

    expiry = int(datetime.now().timestamp()) + 15 * 60000
    session.cookies.set(name="Login", value="true")
    session.cookies.set(name="session", value=data["token"]["session"], expires=expiry)
    session.cookies.set(name="refresh", value=data["token"]["refresh"])
    session.headers.update({"Authorization": f"Bearer {data['token']['session']}"})

    # saving current session into a pickle
    write_pickle("mangadex", "session", session)


def toggle_data_saver():
    """Toggles data setting for MangaDex"""
    data_saver = read_pickle("mangadex", "data_saver")
    data_saver = not data_saver
    write_pickle("mangadex", "data_saver", data_saver)

    print(f"Data saver set to: {data_saver}")


def set_language(language: str):
    """Sets manga language for MangaDex

    Args:
        language (str): Language code to set to
    """

    write_pickle("mangadex", "language", language)
    print(f"Language set to: {language}")


def mark_chapter_read(
    session: requests.Session, manga_id: str, chapter_id: str
) -> bool:
    """Marks chapter as read by chapter_id parameter given

    Args:
        session (requests.Session): Session object that was used for login
        manga_id (str): Manga containing the chapter
        chapter_id (str): Chapter ID to be marked as read

    Returns:
        bool: Boolean flag to indicate whether marking was successful or not
    """
    check_login_session(session)

    mark_url = f"{API_URL}/manga/{manga_id}/read"

    res = session.post(mark_url, json={"chapterIdsRead": [chapter_id]})
    res.close()

    if res.ok:
        print("Chapter marked read")

    return res.ok


def mark_chapter_unread(
    session: requests.Session, manga_id: str, chapter_id: str
) -> bool:
    """Marks chapter as unread by chapter_id parameter given

    Args:
        session (requests.Session): Session object that was used for login
        manga_id (str): Manga containing the chapter
        chapter_id (str): Chapter ID to be marked as unread

    Returns:
        bool: Boolean flag to indicate whether marking was successful or not
    """
    check_login_session(session)

    mark_url = f"{API_URL}/manga/{manga_id}/read"

    res = session.post(mark_url, json={"chapterIdsUnread": [chapter_id]})
    res.close()

    if res.ok:
        print("Chapter marked unread")

    return res.ok


# updates reading status ["reading", "on_hold", "plan_to_read",
# "dropped", "re_reading", "completed"]
def update_reading_status(
    session: requests.Session, manga_id: str, status_index: int = -1
):
    """Updates reading status of manga by manga_id parameter given

    Args:
        session (requests.Session): Session object that was used for login
        manga_id (str): Manga ID for its status to be changed
        status_index (int): Index of status to set for manga. Defaults to -1.

    Returns:
        bool: Boolean flag to indicate whether marking was successful or not
    """
    check_login_session(session)

    msg = """Enter manga status:\n1.Reading\n2.On hold\n3.Plan to read\n4.Dropped\n\
            5.Re-reading\n6.Completed\n:"""
    while status_index < 0 or status_index > 5:
        status_index = int(input(msg)) - 1

    status_list = [
        "reading",
        "on_hold",
        "plan_to_read",
        "dropped",
        "re_reading",
        "completed",
    ]

    url = f"{API_URL}/manga/{manga_id}/status"
    res = session.post(
        url,
        headers={"Content-Type": "application/json"},
        json={"status": status_list[status_index]},
    )
    res.close()

    if res.ok:
        print("Manga status updated")
    else:
        print("Error with updating status")

    return res.ok
