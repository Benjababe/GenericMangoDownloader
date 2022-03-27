import json
import os
import requests
import unittest

import core
import extensions.mangadex.account as account
import extensions.mangadex.ext as mangadexExt
from models import Chapter, Manga, Tag, SearchResult, ParseResult


# testing methods defined in Mangadex class
class TestExtension(unittest.TestCase):

    # variables used in test cases
    def setUp(self) -> None:
        self.mangadex = mangadexExt.Mangadex()
        self.session = core.read_pickle("mangadex", "session")
        self.API_URL = "https://api.mangadex.org"
        self.manga_id = "fe5b40a2-061e-4f09-8f04-86e26aae5649"
        self.chapter_id = "1f9b078c-27b2-4abf-8ddd-7e08f835d202"

        if self.session == None:
            self.session = requests.Session()

        return super().setUp()

    def test_parse_url(self):
        MANGA_URL = f"https://mangadex.org/title/{self.manga_id}"
        CHAPT_URL = f"https://mangadex.org/chapter/{self.chapter_id}"

        # tests manga url parsing
        res = self.mangadex.parse_url(MANGA_URL)
        check_type = res.type == ParseResult._MANGA
        check_item = isinstance(res.item, Manga)
        self.assertTrue(check_type and check_item)

        # tests chapter url parsing
        res = self.mangadex.parse_url(CHAPT_URL)
        check_type = res.type == ParseResult._CHAPTER
        check_item = isinstance(res.item, Chapter)
        self.assertTrue(check_type and check_item)
    # end_test_parse

    def test_search(self):
        query = "Umineko Tsubasa"
        res = self.mangadex.search(query, 1, prompt_tag=False)

        # ensures output is a SearchResult object
        self.assertTrue(isinstance(res, SearchResult))

        # checks all items in manga_list is a models.Manga object and attributes are populated
        all_manga = all(isinstance(manga, Manga) and
                        len(manga.id) > 0 and len(manga.title) > 0 for manga in res.manga_list)
        self.assertTrue(all_manga)

        # checks last_page value is a boolean
        self.assertTrue(isinstance(res.last_page, bool))
    # end_test_search

    def test_get_manga_info(self):
        manga = Manga()
        manga.title = "Umineko no Naku Koro ni Tsubasa"
        manga.id = self.manga_id

        manga = self.mangadex.get_manga_info(manga)

        # checks all items in 'chapters' key is a models.Chapter object
        allChapters = all(isinstance(chapter, Chapter)
                          for chapter in manga.chapters)

        # checks all items in 'tags' key is a Tag object
        allTags = all(isinstance(tag, Tag) for tag in manga.tags)

        self.assertTrue(allChapters and allTags)
    # end_test_get_manga_info

    def test_get_chapter(self):
        chapter_list_url = f"{self.API_URL}/chapter/?manga={self.manga_id}&limit=100&translatedLanguage[]=en"
        res = self.session.get(chapter_list_url)
        res.close()

        data = json.loads(res.text)
        data = data["data"][0]
        chapter = self.mangadex.get_chapter(data)

        self.assertEqual(chapter.date, "11/04/2018")
        self.assertEqual(chapter.id, self.chapter_id)
        self.assertEqual(chapter.number, "1")
        self.assertEqual(chapter.pre_download, True)
        self.assertEqual(chapter.title, "The Witches' Tanabata isn't Sweet")
    # end_test_get_chapter

    def test_get_scanlator(self):
        chapter_list_url = f"{self.API_URL}/chapter/{self.chapter_id}"
        res = self.session.get(chapter_list_url)
        res.close()

        data = json.loads(res.text)
        scanlator = self.mangadex.get_scanlator(data["data"]["relationships"])

        # tests with known scanlator of chapter
        self.assertEqual(scanlator, "WTDND Group")
    # end_test_get_scanlator

    def test_pre_download(self):
        # models.Chapter object that has been processed with pre_download
        chapter = self.get_chapter()

        # ensures all page_urls are valid
        check = all(core.is_url(url) for url in chapter.page_urls)
        self.assertTrue(check)
    # end_test_pre_download

    def test_download(self):
        DOWNLOAD_PATH = "./downloads/unittest"

        # get chapter with all information needed to download
        chapter = self.get_chapter()

        # downloads only 1 page to sample
        page = chapter.page_urls[0]
        core.download_page(page, DOWNLOAD_PATH, 1)

        # gets filesize of page
        size = os.path.getsize(f"{DOWNLOAD_PATH}/1.{page.split('.')[-1]}")

        self.assertEqual(size, 290716)

        os.remove(f"{DOWNLOAD_PATH}/1.{page.split('.')[-1]}")
        os.rmdir(DOWNLOAD_PATH)
    # end_test_download

    def test_get_random(self):
        manga = self.mangadex.get_random()

        self.assertIsNotNone(manga.title)
        self.assertIsNotNone(manga.id)
    # end_test_get_random

    def test_get_formatted_date(self):
        DATETIME = "2018-04-11T20:23:32+00:00"
        date = mangadexExt.format_date(DATETIME)

        self.assertEquals(date, "11/04/2018")
    # end_test_get_formatted_date

    def get_chapter(self) -> Chapter:
        """ Helper method for retrieving an attribute-populated models.Chapter object

        Returns:
            Chapter: Populated models.Chapter object
        """

        chapter_list_url = f"{self.API_URL}/chapter/?manga={self.manga_id}&limit=100&translatedLanguage[]=en"
        res = self.session.get(chapter_list_url)
        res.close()

        data = json.loads(res.text)
        data = data["data"][0]

        chapter = self.mangadex.get_chapter(data)
        chapter = self.mangadex.pre_download(chapter)
        return chapter
    # end_get_chapter

# end_TestExtension


# tests methods in account.py
class TestAccount(unittest.TestCase):
    def setUp(self) -> None:
        # reads login session for every test in this class
        self.session = core.read_pickle("mangadex", "session")

        if self.session == None:
            self.session = requests.Session()

        return super().setUp()

    def test_login(self):
        USERNAME = "unittestusername"
        PASSWORD = "password"

        # self.session's cookies should update after calling login
        account.login(self.session, USERNAME, PASSWORD, None)
        self.assertTrue("Login" in self.session.cookies._cookies[""]["/"])
    # end_test_login

    def test_mark_chapter(self):
        # mark chapter read and unread
        # Umineko Tsubasa Ch. 1
        CHAPTER_ID = "1f9b078c-27b2-4abf-8ddd-7e08f835d202"
        marked = account.mark_chapter_read(self.session, CHAPTER_ID)
        unmarked = account.mark_chapter_unread(self.session, CHAPTER_ID)

        self.assertTrue(marked and unmarked)
    # end_test_mark_chapter

    def test_update_reading_status(self):
        # Umineko Tsubasa
        MANGA_ID = "fe5b40a2-061e-4f09-8f04-86e26aae5649"
        results = []

        # cycle through indexes 0-5
        for index in range(6):
            res = account.update_reading_status(self.session, MANGA_ID, index)
            results.append(res)

        self.assertTrue(all(res == True for res in results))
    # end_test_update_reading_status
# end_TestAccount


if __name__ == "__main__":
    unittest.main()
