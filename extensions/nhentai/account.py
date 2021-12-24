import json

import requests
import core

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

    core.write_pickle("nhentai", "session", session)
    username = soup.find("span", "username").text.strip()
    print(f"Logged in as {username}")
# end_login
