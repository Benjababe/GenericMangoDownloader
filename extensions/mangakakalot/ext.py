# standard libraries
from typing import List
import bs4
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# local files
from classes import Chapter, Extension, Manga, Tag


class Mangakakalot(Extension):
    session = requests.Session()

    def parse_url(self, query: str) -> dict:
        return super().parse_url(query)

    # search_len is unapplicable here
    def search(self, query: str, page: int, cover: bool = False):
        # mangakakalot replaces spaces with underscores
        query = query.replace(" ", "_")

        search_url = f"https://mangakakalot.com/search/story/{query}?page={page}"

        res = self.session.get(search_url)
        res.close()
        soup = BeautifulSoup(res.text, "html.parser")

        paging_elem = soup.find("a", "page_last")

        # if paging cannot be found, there's only 1 page of search results
        if paging_elem == None:
            last_page = True
        else:
            paging_string = paging_elem.string.strip()
            paging_string = re.search(
                r"Last\(([0-9]{1,})\)", paging_string).group(1)
            last_page = page >= int(paging_string)

        manga_list = []

        story_items = soup.find_all("div", "story_item")

        for story_item in story_items:
            url = story_item.find("a", {"href": True})["href"]
            story_name = story_item.find("h3", "story_name")
            title = story_name.text.strip()

            manga = Manga()
            # mangakakalot is special and uses more than 1 domain, so we use url as the id
            manga.id = url
            manga.title = title

            if cover:
                cover_url = story_item.find("img", {"src": True})["src"]
                manga.cover_url = cover_url

            manga_list.append(manga)

        return {"manga_list": manga_list, "last_page": last_page}
    # end_search

    def get_manga_info(self, manga: Manga):
        res = self.session.get(manga.id)
        res.close()
        soup = BeautifulSoup(res.text, "html.parser")

        description = soup.find("div", {"id": "noidungm"})
        description = description.contents[2].strip()

        tags = []
        manga_info_dom = soup.find("ul", "manga-info-text")

        for el in list(manga_info_dom.children):
            if isinstance(el, str):
                continue

            if "Genres" in el.text:
                tag_dom = el
                break

        for tag in tag_dom.contents:
            if isinstance(tag, bs4.element.Tag):
                tags.append(Tag(
                    tag.string,
                    tag["href"]
                ))

        chapter_list_dom = soup.find("div", "chapter-list")

        for chapter_item in chapter_list_dom.find_all("div", "row"):
            chapter = self.get_chapter(chapter_item)
            chapter.manga_title = manga.title
            manga.chapters.append(chapter)

        manga.description = description
        manga.tags = tags

        return manga
    # end_get_manga_info

    def get_chapter(self, chapter_item: bs4.element.Tag) -> Chapter:
        """Generates Chapter object with attributes populated

        Args:
            chapter_item (bs4.element.Tag): HTML element for chapter

        Returns:
            Chapter: Chapter object with attributes populated
        """

        chapter_name = chapter_item.find("a")
        chapter_time = chapter_item.contents[-2]

        chapter = Chapter(pre_download=True)

        chapter_num_pattern = r"Chapter ([0-9.]{1,})"
        matched = re.search(chapter_num_pattern,
                            chapter_name["title"], flags=re.IGNORECASE)
        chapter.number = matched.group(1)

        # ID will be page 1 of chapter, will be used in pre_download
        chapter.id = chapter_name["href"]
        chapter.date = chapter_time.string

        title = chapter_name["title"]
        # because chapter titles are formatted like
        # Chapter <chapter_num> : <chapter_title>
        if ":" in title:
            chapter.title = title[title.index(":")+1:].strip()

        return chapter
    # end_get_chapter

    def pre_download(self, chapter: Chapter) -> Chapter:
        """Preprocessing done before chapter download, retrieves full url for page downloads and sets cloudflare headers

        Args:
            chapter (Chapter): Chapter object to be downloaded

        Returns:
            Chapter: Chapter object with page_urls populated and cloudflare headers set
        """

        # accesses page 1 of chapter
        res = self.session.get(chapter.id)
        res.close()
        soup = BeautifulSoup(res.text, "html.parser")

        # find URLs of all other pages
        chapter_container = soup.find("div", "container-chapter-reader")
        images = chapter_container.find_all("img")
        chapter.page_urls = [image["src"] for image in images]

        # downloading requires cloudflare bypass
        chapter.cloudflare = True
        chapter.headers = generate_headers(chapter)

        return chapter
    # end_pre_download

    def get_random(self):
        return
    # end_get_random

    def arg_handler(self, args: List[str]):
        return
    # end_arg_handler

# end_Mangakakalot_class


def generate_headers(chapter: Chapter) -> dict:
    """Generate cloudflare headers for chapter downloads

    Args:
        chapter (Chapter): Chapter object to be downloaded

    Returns:
        dict: Headers to be used with cloudflare scraper 
    """

    temp_host_url = urlparse(chapter.id)
    temp_image_url = urlparse(chapter.page_urls[0])

    cf_headers = {
        "authority": temp_image_url.hostname,
        "method": "GET",
        "path": temp_image_url.path,
        "scheme": "https",
        "accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
        "referer": f"{temp_host_url.scheme}://{temp_host_url.hostname}",
        "sec-fetch-dest": "image",
        "sec-fetch-mode": "no-cors",
        "sec-fetch-site": "cross-site",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.115 Safari/537.36"
    }

    return cf_headers
# end_generate_headers
