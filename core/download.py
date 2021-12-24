import asyncio
import cfscrape
import os
import re
import requests
from concurrent.futures import ThreadPoolExecutor

from models import Chapter, Extension

DOWNLOAD_PATH = "./downloads/"

session = requests.Session()
cf_scraper = cfscrape.create_scraper()


def download_chapters(ext_active: Extension, valid_chapters: list):
    """[summary]

    Args:
        ext_active (Extension): Subclass of Extension class the site extension creates
        valid_chapters (list): List of Chapter objects with attributes populated
    """

    for chapter in valid_chapters:

        # runs the pre_download for the extension if needed
        # most likely used to retrieve page_urls for the chapter
        if chapter.pre_download == True:
            chapter = ext_active.pre_download(chapter)

        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(download_chapter_async(chapter))
        loop.run_until_complete(future)
    # end_chapter_loop
# end_download_chapters


async def download_chapter_async(chapter: Chapter):
    """Downloads a chapter in an asynchronous thread, 10 pages at once

    Args:
        chapter (Chapter): Chapter object with attributes populated
    """

    # find and remove all invalid characters from folder pathname
    remove_char = '[<>:"\/|?*]'
    chapter_path = f"{DOWNLOAD_PATH}{re.sub(remove_char, '', chapter.manga_title)}/"

    if not chapter.foldername == "":
        chapter_path += f"{re.sub(remove_char, '', chapter.foldername)}/"

    # blatantly copied off https://bit.ly/2WT52U5
    with ThreadPoolExecutor(max_workers=10) as executor:
        loop = asyncio.get_event_loop()
        tasks = []

        for i in range(len(chapter.page_urls)):
            dl_print = f"{chapter.manga_title}: Chapter {chapter.number} page {i} download complete"

            if not os.path.exists(chapter_path):
                os.makedirs(chapter_path)

            tasks.append(
                loop.run_in_executor(
                    executor,
                    download_page,
                    *(chapter.page_urls[i], chapter_path, i+1, dl_print, chapter.cloudflare, chapter.headers)
                )
            )
        # end_for_page_loop
    # end_multithread

# end_download_chapter


# basic download function from the given image url
def download_page(url: str, chapter_path: str, page_num: int, dl_print: str = "", cloudflare: bool = False, headers: dict = {}):
    """Downloads manga image from URL

    Args:
        url (str): Manga image URL
        chapter_path (str): Directory path to save chapter
        page_num (int): Page number of image
        dl_print (str): String to print upon download completion
        cloudflare (bool, optional): Boolean flag to indicate whether cloudflare bypass is required. Defaults to False.
        headers (dict, optional): Dict of http headers for cloudflare bypass. Defaults to {}.
    """

    # if somehow folder hasn't been made yet
    if not os.path.exists(chapter_path):
        os.makedirs(chapter_path)

    # Use either cloudflare bypass or regular http requests depending on extension requirements
    if cloudflare:
        res = cf_scraper.get(url, headers=headers)
    else:
        res = session.get(url)

    # URL should always end with a .(jpg/png/gif)
    extension = url.split(".")[-1]

    # reference path for the downloaded image
    page_path = f"{chapter_path}/{page_num}.{extension}"

    # save data stream into reference path
    with open(page_path, "wb") as page:
        page.write(res.content)
        page.close()

    res.close()
    print(dl_print)
# end_download_page
