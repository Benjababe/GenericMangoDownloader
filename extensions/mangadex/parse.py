import json

from models import Manga, Chapter, ParseResult

API_URL = "https://api.mangadex.org"
MANGA_TEMPLATE = "https://mangadex.org/title/"
CHAPTER_TEMPLATE = "https://mangadex.org/chapter/"


def parse_url(self, url: str) -> ParseResult:
    """Feeds URL into parser for either manga or chapter page

    Args:
        url (str): URL given by user

    Returns:
        ParseResult: ParseResult object containing information on parsed webpage
    """

    if MANGA_TEMPLATE in url and url.index(MANGA_TEMPLATE) == 0:
        manga_id = url.replace(MANGA_TEMPLATE, "")
        # in case last char is /, will cause error in querying
        if manga_id[-1] == "/":
            manga_id = manga_id[:-1]
        return parse_url_manga(self, manga_id)

    if CHAPTER_TEMPLATE in url and url.index(CHAPTER_TEMPLATE) == 0:
        chapter_id = url.replace(CHAPTER_TEMPLATE, "").split("/")[0]
        return parse_url_chapter(self, chapter_id)

    return None


def parse_url_manga(self, manga_id: str) -> ParseResult:
    """Parses manga url string and returns ParseResult object for type manga

    Args:
        manga_id (str): Manga ID

    Returns:
        ParseResult: ParseResult object for type manga
    """

    manga_info_url = f"{API_URL}/manga/{manga_id}"

    res = self.session.get(manga_info_url)
    res.close()
    data = json.loads(res.text)

    manga = Manga()
    manga.title = data["data"]["attributes"]["title"][self.language]
    manga.id = manga_id

    return ParseResult(ParseResult.MANGA, manga)


def parse_url_chapter(self, chapter_id: str) -> ParseResult:
    """Parses chapter url string and returns ParseResult object for type chapter

    Args:
        chapter_id (str): Chapter ID

    Returns:
        ParseResult: ParseResult object for type chapter
    """

    chapter_info_url = f"{API_URL}/chapter/{chapter_id}"

    res = self.session.get(chapter_info_url)
    res.close()
    data = res.json()["data"]

    chapter = Chapter(pre_download=True)

    chapter.number = data["attributes"]["chapter"]
    chapter.id = data["id"]
    chapter.title = data["attributes"]["title"]
    chapter.scanlator = self.get_scanlator(data["relationships"])

    for rel in data["relationships"]:
        if rel["type"] == "manga":
            manga_info_url = f"{API_URL}/manga/{rel['id']}"
            chapter_lang = data["attributes"]["translatedLanguage"]

            res = self.session.get(manga_info_url)
            res.close()
            data = res.json()["data"]

            chapter.manga_title = data["attributes"]["title"][chapter_lang]
            chapter.foldername = f"[{chapter.scanlator}] Ch.{chapter.number}{'' if chapter.title == '' else ' - '}{chapter.title}"

    return ParseResult(ParseResult.CHAPTER, chapter)
