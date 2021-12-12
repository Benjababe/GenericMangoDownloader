# standard libraries
import json
from typing import Dict
import requests
from datetime import datetime

# local files
from classes import Chapter, Extension, Manga, Tag
import extensions.mangadex.account as account
import extensions.mangadex.search as search
import extensions.mangadex.parse as parse
import misc

API_URL = "https://api.mangadex.org"


class Mangadex(Extension):
    scanlators = {}

    # initialises pickled variables
    language = misc.read_pickle("mangadex", "language")
    if language == None:
        language = "en"
        misc.write_pickle("mangadex", "language", language)

    data_saver = misc.read_pickle("mangadex", "data_saver")
    if data_saver == None:
        data_saver = True
        misc.write_pickle("mangadex", "data_saver", data_saver)

    stored_session = misc.read_pickle("mangadex", "session")
    session = stored_session if stored_session else requests.Session()

    stored_mark = misc.read_pickle("mangadex", "mark_on_dl")
    mark_on_dl = stored_mark if stored_mark else False

    def parse_url(self, url: str):
        return parse.parse_url(self, url)
    # end_parse_url

    def search(self, query: str, page: int, cover: bool = False, tag=False) -> Dict:
        return search.search(self, query, page, cover, tag=False)
    # end_search

    def get_manga_info(self, manga: Manga) -> Manga:
        manga_info_url = f"{API_URL}/manga/{manga.id}"
        chapter_list_url = f"{API_URL}/chapter"

        res = self.session.get(manga_info_url)
        res.close()
        data = json.loads(res.text)

        # variables to be returned in manga_info dict
        description = data["data"]["attributes"]["description"][self.language]
        tags = []

        for tag in data["data"]["attributes"]["tags"]:
            name = tag["attributes"]["name"][self.language]
            id = tag["id"]
            tags.append(Tag(name, id))

        res = self.session.get(chapter_list_url, params={
            "manga": manga.id,
            "limit": 100,
            "translatedLanguage[]": self.language
        })
        res.close()
        data = json.loads(res.text)

        for res_results in data["data"]:
            chapter = self.get_chapter(res_results)
            chapter.manga_title = manga.title
            manga.chapters.append(chapter)

        manga.description = description
        manga.tags = tags

        return manga
    # end_get_manga_info

    def get_chapter(self, res_results: dict) -> Chapter:
        """Returns Chapter object from API call results

        Args:
            res_results (dict): Results from API call receiving list of chapters

        Returns:
            Chapter: Chapter object parsed from API call results
        """

        # only return page_urls as filenames for now as it takes a GET request for the full URL
        # which would take too much time and probably exceed the API limit if done prior to download
        # full url will be handled in pre_download, "hash" is also a non-mandatory key for retrieving the full url
        chapter = Chapter(pre_download=True)

        chapter.number = res_results["attributes"]["chapter"]
        chapter.id = res_results["id"]
        chapter.title = res_results["attributes"]["title"]
        chapter.page_urls = res_results["attributes"]["dataSaver" if self.data_saver else "data"]
        chapter.scanlator = self.get_scanlator(res_results["relationships"])
        chapter.date = get_formatted_date(
            res_results["attributes"]["updatedAt"])
        chapter.add_attribute(
            "hash", res_results["attributes"]["hash"]
        )

        return chapter
    # end_get_chapter

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

                    self.scanlators[scanlator_id] = tmp_data["data"]["attributes"]["name"]
                # end_if_scanlator_id

                return self.scanlators[scanlator_id]
            # end_if_rel_type
        # end_for_rel
    # end_get_scanlator

    # gets the full list of image urls before download

    def pre_download(self, chapter: Chapter) -> Chapter:
        """Preprocessing done before chapter download, retrieves full url for page downloads

        Args:
            chapter (Chapter): Chapter object to be downloaded

        Returns:
            Chapter: Chapter object with page_urls populated
        """
        at_home_url = f"{API_URL}/at-home/server/{chapter.id}"

        res = self.session.get(at_home_url)
        res.close()
        tmp_data = json.loads(res.text)

        # image url without the filename
        base_url = f"{tmp_data['baseUrl']}/{'data-saver' if self.data_saver else 'data'}/{chapter.hash}"

        # constructs full image url
        chapter.page_urls = [
            f"{base_url}/{filename}" for filename in chapter.page_urls
        ]

        if self.mark_on_dl and self.session.cookies.get("Login"):
            account.mark_chapter_read(self.session, chapter.id)

        return chapter
    # end_pre_download

    def get_random(self):
        res = self.session.get(f"{API_URL}/manga/random")
        res.close()
        data = json.loads(res.text)

        manga = Manga()
        manga.title = data["data"]["attributes"]["title"][self.language]
        manga.id = data["data"]["id"]

        return manga
    # end_get_random

    def arg_handler(self, args: list) -> None:
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
            "--reading-status": account.update_reading_status
        }

        for arg in args:
            arg = arg.split(" ")

            if arg[0] in arg_handlers:
                arg_handlers[arg.pop(0)](self.session, *arg)
# end_arg_handler
# end_Mangadex_class


def get_formatted_date(upload_date: str) -> str:
    """Converts ISO8601 datetime format that MangaDex provides to DD/MM/YYYY

    Args:
        upload_date (str): Datetime in ISO8601 format

    Returns:
        str: Date in DD/MM/YYYY format
    """
    upload_date = datetime.strptime(upload_date, "%Y-%m-%dT%H:%M:%S%z")
    upload_date = upload_date.strftime("%d/%m/%Y")
    return upload_date
# end_get_formatted_date
