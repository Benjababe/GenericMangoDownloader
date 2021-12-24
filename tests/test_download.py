import os
import unittest

import core.download as download
from models import Chapter


class TestDownload(unittest.TestCase):
    def setUp(self) -> None:
        self.URL = "https://file-examples-com.github.io/uploads/2017/10/file_example_JPG_100kB.jpg"
        self.PATH = "./downloads/unittest"
        return super().setUp()
    # end_setUp

    def test_single_download(self):
        download.download_page(self.URL, self.PATH, 1)
        check = os.path.exists(f"{self.PATH}/1.jpg")
        self.assertTrue(check)
    # end_test_single_download

    def tearDown(self) -> None:
        os.remove(f"{self.PATH}/1.jpg")
        os.rmdir(self.PATH)
        return super().tearDown()
    # end_tearDown

# end_TestDownload


class TestAsyncDownload(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.URL1 = "https://file-examples-com.github.io/uploads/2017/10/file_example_JPG_100kB.jpg"
        self.URL2 = "https://file-examples-com.github.io/uploads/2017/10/file_example_JPG_500kB.jpg"
        self.PATH = "./downloads/unittest"
        return super().setUp()
    # end_setUp

    async def test_multi_download(self):
        # sets up chapter object for testing
        chapter = Chapter(pre_download=False)
        chapter.page_urls = [self.URL1, self.URL2] * 5
        chapter.manga_title = "unittest"
        chapter.number = "1"

        # downloads all 10 images
        await download.download_chapter_async(chapter)

        # ensures all 10 files are downloaded
        check = all(os.path.exists(f"{self.PATH}/{i}.jpg")
                    for i in range(1, 11))
        self.assertTrue(check)
    # end_test_multi_download

    def tearDown(self) -> None:
        for i in range(1, 11):
            os.remove(f"{self.PATH}/{i}.jpg")
        os.rmdir(self.PATH)
        return super().tearDown()
    # end_tearDown

# end_TestAsyncDownload
