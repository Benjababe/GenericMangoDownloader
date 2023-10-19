import asyncio
from typing import List
import os
import re
from concurrent.futures import ThreadPoolExecutor
import requests
import cfscrape
from tqdm.asyncio import tqdm

from models import Chapter, Extension

DOWNLOAD_PATH = "./downloads/"

session = requests.Session()
cf_scraper = cfscrape.create_scraper()


def download_chapters(ext: Extension, valid_chapters: List[Chapter]):
    """[summary]

    Args:
        ext (Extension): Subclass of Extension class the site extension creates
        valid_chapters (list): List of models.Chapter objects with attributes populated
    """

    for chapter in valid_chapters:
        # runs the pre_download for the extension if needed
        # most likely used to retrieve page_urls for the chapter
        if chapter.pre_download is True:
            chapter = ext.pre_download(chapter)

        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(download_chapter_async(chapter))
        loop.run_until_complete(future)


async def download_chapter_async(chapter: Chapter):
    """Downloads a chapter in an asynchronous thread, 10 pages at once

    Args:
        chapter (Chapter): models.Chapter object with attributes populated
    """

    # find and remove all invalid characters from folder pathname
    remove_char = r'[<>:"/|?*]'
    chapter_path = f"{DOWNLOAD_PATH}{re.sub(remove_char, '', chapter.manga_title)}/"

    if not chapter.foldername == "":
        chapter_path += f"{re.sub(remove_char, '', chapter.foldername)}/"

    with tqdm(total=len(chapter.page_urls)) as progress:
        # blatantly copied off https://bit.ly/2WT52U5
        with ThreadPoolExecutor(max_workers=10) as executor:
            loop = asyncio.get_event_loop()
            tasks = []

            for i, page_url in enumerate(chapter.page_urls):
                # dl_print = f"{chapter.manga_title}: Chapter {chapter.number} page {i} download complete"
                progress.update()

                if not os.path.exists(chapter_path):
                    os.makedirs(chapter_path)

                tasks.append(
                    loop.run_in_executor(
                        executor,
                        download_page,
                        *(
                            page_url,
                            chapter_path,
                            i + 1,
                            "",
                            chapter.cloudflare,
                            chapter.headers,
                        ),
                    )
                )


# basic download function from the given image url
def download_page(
    url: str,
    chapter_path: str,
    page_num: int,
    dl_print: str = "",
    cloudflare: bool = False,
    headers: dict = None,
):
    """Downloads manga image from URL

    Args:
        url (str): Manga image URL
        chapter_path (str): Directory path to save chapter
        page_num (int): Page number of image
        dl_print (str): String to print upon download completion
        cloudflare (bool, optional): Boolean flag to indicate whether cloudflare bypass is required.
                                     Defaults to False.
        headers (dict, optional): Dict of http headers for cloudflare bypass. Defaults to {}.
    """

    # if somehow folder hasn't been made yet
    if not os.path.exists(chapter_path):
        os.makedirs(chapter_path)

    # in case url has spaces
    url = re.sub(r"\s", "", url)

    # Use either cloudflare bypass or regular http requests depending on extension requirements
    if cloudflare:
        res = cf_scraper.get(url, headers=headers)
    else:
        res = session.get(url, headers=headers)

    # URL should always end with a .(jpg/png/gif)
    extension = url.split(".")[-1]

    # reference path for the downloaded image
    page_path = f"{chapter_path}/{page_num}.{extension}"

    # save data stream into reference path
    if res.ok:
        with open(page_path, "wb") as page:
            page.write(res.content)
            page.close()

        if dl_print.strip() != "":
            print(dl_print)

    else:
        print(f"Page {page_num}: {res.url} failed...")

    res.close()
