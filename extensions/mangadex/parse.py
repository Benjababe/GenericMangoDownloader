import json
from typing import Dict

from models import Manga, Chapter

API_URL = "https://api.mangadex.org"


def parse_url(self, url: str) -> Dict:
    """Feeds URL into parser for either manga or chapter page

    Args:
        url (str): URL given by user

    Returns:
        Dict: {
            "type": ("manga"|"chapter"),
            "item": Manga or models.Chapter object
        }
    """
    MANGA_TEMPLATE = "https://mangadex.org/title/"
    CHAPTER_TEMPLATE = "https://mangadex.org/chapter/"

    if MANGA_TEMPLATE in url and url.index(MANGA_TEMPLATE) == 0:
        manga_id = url.replace(MANGA_TEMPLATE, "")
        # in case last char is /, will cause error in querying
        if manga_id[-1] == "/":
            manga_id = manga_id[:-1]
        return parse_url_manga(self, manga_id)

    elif CHAPTER_TEMPLATE in url and url.index(CHAPTER_TEMPLATE) == 0:
        chapter_id = url.replace(CHAPTER_TEMPLATE, "").split("/")[0]
        return parse_url_chapter(self, chapter_id)
# end_parse_url


def parse_url_manga(self, manga_id: str) -> dict:
    """Parses manga url string and returns dict for type manga

    Args:
        manga_id (str): Manga ID

    Returns:
        dict: Dict for type manga
    """

    manga_info_url = f"{API_URL}/manga/{manga_id}"

    res = self.session.get(manga_info_url)
    res.close()
    data = json.loads(res.text)

    manga = Manga()
    manga.title = data["data"]["attributes"]["title"][self.language]
    manga.id = manga_id

    return {
        "type": "manga",
        "item": manga
    }
# end_parse_url_manga


def parse_url_chapter(self, chapter_id: str) -> dict:
    """Parses chapter url string and returns dict for type chapter

    Args:
        chapter_id (str): Chapter ID

    Returns:
        dict: Dict for type chapter
    """

    chapter_info_url = f"{API_URL}/chapter/{chapter_id}"

    res = self.session.get(chapter_info_url)
    res.close()
    data = json.loads(res.text)

    chapter = Chapter(pre_download=True)

    chapter.id = chapter_id
    chapter.title = data["data"]["attributes"]["title"]
    chapter.number = data["data"]["attributes"]["chapter"]
    chapter.page_urls = data["data"]["attributes"]["dataSaver" if self.data_saver else "data"]
    chapter.scanlator = self.get_scanlator(data["data"]["relationships"])
    chapter.add_attribute("hash", data["data"]["attributes"]["hash"])

    for rel in data["data"]["relationships"]:
        if rel["type"] == "manga":
            manga_info_url = f"{API_URL}/manga/{rel['id']}"
            chapter_lang = data["data"]["attributes"]["translatedLanguage"]

            res = self.session.get(manga_info_url)
            res.close()
            data = json.loads(res.text)

            chapter.manga_title = data["data"]["attributes"]["title"][chapter_lang]
            chapter.foldername = f"[{chapter.scanlator}] Ch.{chapter.number}{'' if chapter.title == '' else ' - '}{chapter.title}"

    return {
        "type": "chapter",
        "item": chapter
    }
# end_parse_url_chapter
