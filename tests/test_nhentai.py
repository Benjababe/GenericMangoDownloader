import os
import unittest

import download
import extensions.nhentai.ext as nhentai
from classes import Chapter, Manga, Tag


class TestExtension(unittest.TestCase):
    def setUp(self) -> None:
        self.nhentai = nhentai.NHentai()
        return super().setUp()

    def test_search(self):
        query = "Umineko"
        res = self.nhentai.search(query, 1)

        # checks all items in manga_list is a Manga object and attributes are populated
        all_manga = all(isinstance(manga, Manga) and
                        len(manga.id) > 0 and len(manga.title) > 0 for manga in res["manga_list"])
        self.assertTrue(all_manga)

        # checks last_page value is a boolean
        self.assertTrue(isinstance(res["last_page"], bool))
    # end_test_search

    def test_get_manga_info(self):
        manga = self.get_manga()

        # checks all items in 'chapters' key is a Chapter object
        allChapters = all(isinstance(chapter, Chapter)
                          for chapter in manga.chapters)

        # checks all items in 'tags' key is a Tag object
        allTags = all(isinstance(tag, Tag) for tag in manga.tags)

        self.assertTrue(allChapters and allTags)
    # end_test_get_manga_info

    def test_download(self):
        DOWNLOAD_PATH = "./downloads/unittest"

        # retrieves chapter with all information needed to download
        manga = self.get_manga()
        chapter = manga.chapters[0]

        # downloads only 1 page to sample
        page = chapter.page_urls[0]
        download.download_page(page, DOWNLOAD_PATH, 1)

        # gets filesize of page
        size = os.path.getsize(f"{DOWNLOAD_PATH}/1.{page.split('.')[-1]}")

        self.assertEqual(size, 394241)

        os.remove(f"{DOWNLOAD_PATH}/1.{page.split('.')[-1]}")
        os.rmdir(DOWNLOAD_PATH)
    # end_test_download

    def test_get_random(self):
        manga = self.nhentai.get_random()

        self.assertIsNotNone(manga.title)
        self.assertIsNotNone(manga.id)
    # end_test_get_random

    def test_get_formatted_date(self):
        date = "2020-10-27T01:13:39.218505+00:00"
        date = nhentai.get_formatted_date(date)
        self.assertEqual(date, "27/10/2020")
    # end_test_get_formatted_date

    def get_manga(self) -> Manga:
        """ Helper method for retrieving an attribute-populated Manga object

        Returns:
            Manga: Populated Manga object
        """

        manga = Manga()
        manga.title = "(C78) The World My Little Sister Only Knows 2 (Umineko no Naku Koro ni)"
        manga.id = "333998"

        manga = self.nhentai.get_manga_info(manga)
        return manga
    # end_get_manga

# end_TestExtension
