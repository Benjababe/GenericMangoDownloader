import os
import unittest

import core
import extensions.mangakakalot.ext as mangakakalotExt
from models import Chapter, Manga, Tag, SearchResult, ParseResult


# testing methods defined in Mangakakalot class
class TestExtension(unittest.TestCase):
    # variables used in test cases
    def setUp(self) -> None:
        self.mangakakalot = mangakakalotExt.Mangakakalot()
        return super().setUp()

    def test_search(self):
        query = "Umineko Tsubasa"
        res = self.mangakakalot.search(query, 1)

        # ensures output is a SearchResult object
        self.assertTrue(isinstance(res, SearchResult))

        # checks all items in manga_list is a models.Manga object
        all_manga = all(
            isinstance(manga, Manga) and len(manga.id) > 0 and len(manga.title) > 0
            for manga in res.manga_list
        )
        self.assertTrue(all_manga and isinstance(res.last_page, bool))

        # checks last_page value is a boolean
        self.assertTrue(isinstance(res.last_page, bool))

    def test_get_manga_info(self):
        manga = Manga()
        manga.title = "Umineko no Naku Koro ni Tsubasa"
        manga.id = "https://mangakakalot.com/manga/umineko_no_naku_koro_ni_tsubasa"

        manga = self.mangakakalot.get_manga_info(manga)

        # checks all items in 'chapters' key is a models.Chapter object
        allChapters = all(isinstance(item, Chapter) for item in manga.chapters)

        # checks all items in 'tags' key is a Tag object
        allTags = all(isinstance(tag, Tag) for tag in manga.tags)

        self.assertTrue(allChapters and allTags)

    def test_pre_download(self):
        # only populating id since it's all we need for predownload
        chapter = Chapter(pre_download=True)
        chapter.id = (
            "https://mangakakalot.com/chapter/umineko_no_naku_koro_ni_tsubasa/chapter_1"
        )
        chapter = self.mangakakalot.pre_download(chapter)

        # ensure cloudflare settings are set
        self.assertTrue(chapter.cloudflare)
        self.assertTrue(isinstance(chapter.headers, dict))

        # ensure all page_urls are valid
        page_check = all(core.is_url(url) for url in chapter.page_urls)
        self.assertTrue(page_check)

    def test_download(self):
        DOWNLOAD_PATH = "./downloads/unittest"

        manga = Manga()
        manga.id = "https://mangakakalot.com/manga/umineko_no_naku_koro_ni_tsubasa"
        manga = self.mangakakalot.get_manga_info(manga)

        # downloads only chapter 1
        chapter = list(filter(lambda x: x.number == "1", manga.chapters))[0]
        chapter = self.mangakakalot.pre_download(chapter)

        # downloads only 1 page from that chapter
        page = chapter.page_urls[0]
        cf = chapter.cloudflare
        headers = chapter.headers
        core.download_page(page, DOWNLOAD_PATH, 1, cloudflare=cf, headers=headers)

        # gets filesize of page
        size = os.path.getsize(f"{DOWNLOAD_PATH}/1.{page.split('.')[-1]}")

        self.assertEqual(size, 130200)

        os.remove(f"{DOWNLOAD_PATH}/1.{page.split('.')[-1]}")
        os.rmdir(DOWNLOAD_PATH)


if __name__ == "__main__":
    unittest.main()
