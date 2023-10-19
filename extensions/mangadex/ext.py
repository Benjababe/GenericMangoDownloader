# standard libraries
from datetime import datetime
import json
from typing import List
import requests

# local files
from models import Chapter, Extension, Manga, Tag, ParseResult
from extensions.mangadex import account, search, parse
import core

NAME = "mangadex"
API_URL = "https://api.mangadex.org"


class Mangadex(Extension):
    """Extension for https://mangadex.org"""

    def __init__(self):
        super().__init__()

        self.scanlators = {}
        self.tags = None

        # initialises pickled variables
        self.language = core.read_pickle("mangadex", "language")
        if self.language is None:
            self.language = "en"
            core.write_pickle("mangadex", "language", self.language)

        self.data_saver = core.read_pickle("mangadex", "data_saver")
        if self.data_saver is None:
            self.data_saver = True
            core.write_pickle("mangadex", "data_saver", self.data_saver)

        # restoring previous login session if available
        stored_session = core.read_pickle("mangadex", "session")
        self.session = stored_session if stored_session else requests.Session()

        # to mark chapter as read upon downloading or not
        stored_mark = core.read_pickle("mangadex", "mark_on_dl")
        self.mark_on_dl = stored_mark if stored_mark else False

    def parse_url(self, url: str) -> ParseResult:
        """Parses URL, MangaDex URL should be passed as argument

        Returns:
            ParseResult: Parsed result of manga or chapter
        """
        return parse.parse_url(self, url)

    def search(self, query: str, page: int, cover: bool = False, prompt_tag=True):
        # if tag search, ask for tags only once and save it locally
        if prompt_tag and self.tags is None:
            self.tags = search.query_tags(self.session)

        return search.search(self, query, page, cover, self.tags)

    def get_manga_info(self, manga: Manga) -> Manga:
        manga_info_url = f"{API_URL}/manga/{manga.id}"
        chapter_list_url = f"{API_URL}/chapter"

        res = self.session.get(manga_info_url)
        res.close()
        data = res.json()["data"]

        # variables to be returned in manga_info dict
        if self.language in data["attributes"]["description"]:
            manga.description = data["attributes"]["description"][self.language]
        else:
            manga.description = "No description in your preferred language"

        for tag in data["attributes"]["tags"]:
            name = tag["attributes"]["name"][self.language]
            tag_id = tag["id"]
            manga.tags.append(Tag(name, tag_id))

        # retrieves list of chapters for the current manga
        res = self.session.get(
            chapter_list_url,
            params={
                "manga": manga.id,
                "limit": 100,
                "translatedLanguage[]": self.language,
            },
        )
        res.close()
        data = res.json()["data"]

        for res_results in data:
            chapter = self.get_chapter(res_results)
            chapter.manga_title = manga.title
            manga.chapters.append(chapter)

        return manga

    def set_tags(self, tags: List[str]):
        """Sets to query with

        Args:
            tags (List[str]): Tags to use in search query
        """
        self.tags = tags

    def get_chapter(self, res_results: dict) -> Chapter:
        """Returns models.Chapter object from API call results

        Args:
            res_results (dict): Results from API call receiving list of chapters

        Returns:
            Chapter: models.Chapter object parsed from API call results
        """

        # only return page_urls as filenames for now as it takes a GET request for the full URL
        # which would take too much time and probably exceed the API limit if done prior to download
        # full url will be handled in pre_download, "hash" is also a non-mandatory
        # key for retrieving the full url
        chapter = Chapter(pre_download=True)

        chapter.number = res_results["attributes"]["chapter"]
        chapter.id = res_results["id"]
        chapter.title = res_results["attributes"]["title"]
        chapter.scanlator = self.get_scanlator(res_results["relationships"])
        chapter.date = format_date(res_results["attributes"]["updatedAt"])

        return chapter

    def get_scanlator(self, relationships: dict) -> str:
        """Retrieves scanlator name from chapter API call results

        Args:
            relationships (dict): relationships dict from API call receiving list of chapters

        Returns:
            str: Scanlator name for the chapter
        """

        for rel in relationships:
            if rel["type"] == "scanlation_group":
                scanlator_id = rel["id"]

                # if scanlator isn't currently stored, retrieve scanlator's name then stores it
                if not scanlator_id in self.scanlators:
                    scanlator_info_url = f"{API_URL}/group/{scanlator_id}"

                    res = self.session.get(scanlator_info_url)
                    res.close()
                    tmp_data = json.loads(res.text)

                    self.scanlators[scanlator_id] = tmp_data["data"]["attributes"][
                        "name"
                    ]

                return self.scanlators[scanlator_id]
        return ""

    # gets the full list of image urls before download

    def pre_download(self, chapter: Chapter) -> Chapter:
        """Preprocessing done before chapter download, retrieves full url for page downloads

        Args:
            chapter (Chapter): models.Chapter object to be downloaded

        Returns:
            Chapter: models.Chapter object with page_urls populated
        """
        at_home_url = f"{API_URL}/at-home/server/{chapter.id}"

        res = self.session.get(at_home_url)
        res.close()
        tmp_data = res.json()

        # image url without the filename
        base_url = f"{tmp_data['baseUrl']}/{'data-saver' if self.data_saver else 'data'}/{tmp_data['chapter']['hash']}"

        # constructs full image url
        chapter.page_urls = [
            f"{base_url}/{filename}"
            for filename in tmp_data["chapter"][
                "dataSaver" if self.data_saver else "data"
            ]
        ]

        if self.mark_on_dl and self.session.cookies.get("Login"):
            account.mark_chapter_read(self.session, chapter.manga_id, chapter.id)

        return chapter

    def get_random(self):
        res = self.session.get(f"{API_URL}/manga/random")
        res.close()
        data = json.loads(res.text)

        manga = Manga()
        manga.title = data["data"]["attributes"]["title"][self.language]
        manga.id = data["data"]["id"]

        return manga

    def arg_handler(self, args: List[str]) -> None:
        # pairs argument with its corresponding function
        arg_handlers = {
            "-L": account.login,
            "--login": account.login,
            "-DS": account.toggle_data_saver,
            "--data-saver": account.toggle_data_saver,
            "-LANG": account.set_language,
            "--language": account.set_language,
            "-MR": account.mark_chapter_read,
            "--mark-read": account.mark_chapter_read,
            "-MU": account.mark_chapter_unread,
            "--mark-unread": account.mark_chapter_unread,
            "--reading-status": account.update_reading_status,
        }

        for arg in args:
            arg = arg.split(" ")

            if arg[0] in arg_handlers:
                arg_handlers[arg.pop(0)](self.session, *arg)


def format_date(upload_date: str) -> str:
    """Converts ISO8601 datetime format that MangaDex provides to DD/MM/YYYY

    Args:
        upload_date (str): Datetime in ISO8601 format

    Returns:
        str: Date in DD/MM/YYYY format
    """
    upload_date = datetime.strptime(upload_date, "%Y-%m-%dT%H:%M:%S%z")
    upload_date = upload_date.strftime("%d/%m/%Y")
    return upload_date
