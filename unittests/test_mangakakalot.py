import json
import unittest

import misc
import extensions.mangakakalot.ext as mangakakalotExt
from classes import Chapter, Manga, Tag

# testing methods defined in Mangakakalot class


class TestExtension(unittest.TestCase):

    # variables used in test cases
    def setUp(self) -> None:
        self.mangakakalot = mangakakalotExt.Mangakakalot()
        return super().setUp()

    def test_search(self):
        QUERY = "Umineko Tsubasa"
        res = self.mangakakalot.search(QUERY, 1)

        # checks all items in manga_list is a Manga object
        allManga = all(isinstance(manga, Manga) for manga in res["manga_list"])
        self.assertTrue(allManga)

        # checks last_page value is a boolean
        self.assertTrue(isinstance(res["last_page"], bool))
    # end_test_search

    def test_get_manga_info(self):
        manga = Manga()
        manga.title = "Umineko no Naku Koro ni Tsubasa"
        manga.id = "https://mangakakalot.com/manga/umineko_no_naku_koro_ni_tsubasa"

        manga = self.mangakakalot.get_manga_info(manga)

        # checks all items in 'chapters' key is a Chapter object
        allChapters = all(isinstance(item, Chapter)
                          for item in manga.chapters)

        # checks all items in 'tags' key is a Tag object
        allTags = all(isinstance(tag, Tag) for tag in manga.tags)

        self.assertTrue(allChapters and allTags)
    # end_test_get_manga_info

    def test_pre_download(self):
        # only populating id since it's all we need for predownload
        chapter = Chapter(pre_download=True)
        chapter.id = "https://mangakakalot.com/chapter/umineko_no_naku_koro_ni_tsubasa/chapter_1"
        chapter = self.mangakakalot.pre_download(chapter)

        # ensure cloudflare settings are set
        self.assertTrue(chapter.cloudflare)
        self.assertTrue(isinstance(chapter.headers, dict))

        # ensure all page_urls are valid
        page_check = all(misc.is_url(url) for url in chapter.page_urls)
        self.assertTrue(page_check)
    # end_test_pre_download


# end_TestExtension


if __name__ == "__main__":
    unittest.main()
