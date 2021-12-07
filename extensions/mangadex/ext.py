# standard libraries
import json
import requests
from datetime import datetime

# local files
from classes import Chapter, Extension, Manga, Tag
import extensions.mangadex.account as account
import misc

API_URL = "https://api.mangadex.org"


class Mangadex(Extension):
    scanlators = {}
    language = "en"
    data_saver = True

    # initialises pickled variables
    stored_session = misc.read_pickle("mangadex", "session")
    session = stored_session if stored_session else requests.Session()

    stored_mark = misc.read_pickle("mangadex", "mark_on_dl")
    mark_on_dl = stored_mark if stored_mark else False

    def parse_url(self, url: str):
        MANGA_TEMPLATE = "https://mangadex.org/title/"
        CHAPTER_TEMPLATE = "https://mangadex.org/chapter/"

        if MANGA_TEMPLATE in url and url.index(MANGA_TEMPLATE) == 0:
            manga_id = url.replace(MANGA_TEMPLATE, "")
            return self.parse_url_manga(manga_id)

        elif CHAPTER_TEMPLATE in url and url.index(CHAPTER_TEMPLATE) == 0:
            chapter_id = url.replace(CHAPTER_TEMPLATE, "").split("/")[0]
            return self.parse_url_chapter(chapter_id)

    # end_parse_url

    def parse_url_manga(self, manga_id: str) -> dict:
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

    def search(self, query: str, page: int, cover: bool = False):
        search_len = 10
        search_url = f"{API_URL}/manga?title={query}&limit={search_len}&offset={(page-1) * search_len}"

        res = self.session.get(search_url)
        res.close()
        data = json.loads(res.text)

        # only reaches last page of search result when chapter offset + chapter displayed is greater of equals total search results
        last_page = (len(data["data"]) + data["offset"]) >= data["total"]

        manga_list = []

        # populate the returned list
        for item in data["data"]:
            manga = Manga()

            manga.title = item["attributes"]["title"]["en"]
            manga.id = item["id"]

            # retrieves front cover URL
            if cover:
                for rel in item["relationships"]:
                    if rel["type"] == "cover_art":
                        cover_id = rel["id"]
                        cover_url = f"{API_URL}/cover/{cover_id}"

                        res = self.session.get(cover_url)
                        res.close()

                        cover_data = json.loads(res.text)
                        cover_filename = cover_data["data"]["attributes"]["fileName"]
                        manga.cover_url = f"https://uploads.mangadex.org/covers/{manga.id}/{cover_filename}"
                    # end_if
                # end_for
            # end_if
            manga_list.append(manga)

        return {"manga_list": manga_list, "last_page": last_page}
    # end_search

    def get_manga_info(self, manga: Manga) -> Manga:
        manga_info_url = f"{API_URL}/manga/{manga.id}"
        chapter_list_url = f"{API_URL}/chapter/?manga={manga.id}&limit=100&translatedLanguage[]={self.language}"

        res = self.session.get(manga_info_url)
        res.close()
        data = json.loads(res.text)

        # variables to be returned in manga_info dict
        description = data["data"]["attributes"]["description"][self.language]
        tags = []

        for tag in data["data"]["attributes"]["tags"]:
            tags.append(Tag(
                tag["attributes"]["name"]["en"],
                tag["id"]
            ))

        res = self.session.get(chapter_list_url)
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

    def arg_handler(self, args: list) -> None:
        # pairs argument with its corresponding function
        arg_handlers = {
            "--login": account.login,
            "--mark-read": account.mark_chapter_read,
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
