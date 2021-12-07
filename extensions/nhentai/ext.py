import re
from typing import List
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# local files
from classes import Chapter, Extension, Manga, Tag
import extensions.nhentai.account as account
import extensions.nhentai.gallery as gallery
import misc


class NHentai(Extension):
    # initialises pickled variables
    stored_session = misc.read_pickle("nhentai", "session")
    session = stored_session if stored_session else requests.Session()

    def parse_url(self, query: str) -> dict:
        return super().parse_url(query)

    def search(self, query: str, page: int, cover: bool = False):
        search_url = f"https://nhentai.net/search/?q={query}+language%3Aenglish&page={page}"

        res = self.session.get(search_url)
        res.close()
        soup = BeautifulSoup(res.text, "html.parser")

        last_btn = soup.find("a", "last")
        last_string = re.search(r"page=([0-9]{1,})", last_btn["href"]).group(1)
        last_page = page >= int(last_string)

        manga_list = []

        gallery = soup.find_all("div", "gallery")

        for item in gallery:
            # gets id from "/g/{id}"
            id = re.search(r"\/g\/([0-9]{1,})\/",
                           item.find("a")["href"]).group(1)
            title = item.find("div", "caption").string

            manga = Manga()
            manga.id = id
            manga.title = title

            if cover:
                manga.cover_url = item.find("img", "lazyload")["data-src"]

            manga_list.append(manga)

        return {"manga_list": manga_list, "last_page": last_page}
    # end_search

    def get_manga_info(self, manga: Manga):
        res = self.session.get(f"https://nhentai.net/g/{manga.id}/")
        res.close()
        soup = BeautifulSoup(res.text, "html.parser")

        tags = []
        scanlators = []
        tag_containers = soup.find_all("div", "tag-container")

        for tag_container in tag_containers:
            category = tag_container.next.strip()
            if "Tags:" in category:
                tag_doms = tag_container.find_all("a")

                for tag_dom in tag_doms:
                    tags.append(Tag(
                        tag_dom.find("span", "name").string,
                        tag_dom["class"][1].split("-")[-1]
                    ))

            elif "Groups:" in category:
                tag_doms = tag_container.find_all("a")

                for tag_dom in tag_doms:
                    scanlators.append(tag_dom.find("span", "name").string)

        date = soup.find("time")["datetime"]
        date = get_formatted_date(date)

        chapter = Chapter(pre_download=False)

        chapter.number = "1"
        chapter.id = manga.id
        chapter.manga_title = manga.title
        chapter.scanlator = ", ".join(scanlators)
        chapter.date = date
        chapter.foldername = chapter.title

        thumbnail_container = soup.find_all("div", "thumb-container")

        for tb in thumbnail_container:
            thumbnail_pattern = r"(https://)(t)(.nhentai.net/galleries/[0-9]{1,}/[0-9]{1,})(t.[a-zA-Z]{1,})"
            img = tb.find("img")
            src = img["data-src"]

            groups = list(re.search(thumbnail_pattern, src).groups())
            # replaces t in hostname with i
            groups[1] = "i"
            # removes t from filename: 12t.png -> 12.png
            groups[3] = groups[3][1:]

            chapter.page_urls.append("".join(groups))

        manga.chapters.append(chapter)
        manga.tags = tags

        return manga
    # end_get_manga_info

    def arg_handler(self, args: List[str]):
        # pairs argument with its corresponding function
        arg_handlers = {
            "--login": account.login,
            "--favorite": gallery.favourite,
            "--favourite": gallery.favourite,
            "--comment": gallery.comment
        }

        for arg in args:
            arg = arg.split(" ")

            if arg[0] in arg_handlers:
                arg_handlers[arg.pop(0)](self.session, *arg)
    # end_arg_handler
# end_NHentai_class


def get_formatted_date(date: str) -> str:
    """Converts ISO8601 datetime format to DD/MM/YYYY

    Args:
        date (str): Datetime in ISO8601 format

    Returns:
        str: Date in DD/MM/YYYY format
    """
    upload_date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%f%z")
    upload_date = upload_date.strftime("%d/%m/%Y")
    return upload_date
# end_get_formatted_date