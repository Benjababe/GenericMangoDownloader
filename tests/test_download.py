import os
import re
import unittest

import core.download as download
from models import Chapter


ext_pattern = "^.*\.(\w+){1}$"


class TestDownload(unittest.TestCase):
    def setUp(self) -> None:
        self.URL = "https://filesamples.com/samples/image/jpeg/sample_640%C3%97426.jpeg"
        self.PATH = "./downloads/unittest"
        self.EXTENSION = re.search(ext_pattern, self.URL).group(1)
        return super().setUp()
    # end_setUp

    def test_single_download(self):
        download.download_page(self.URL, self.PATH, 1)
        check = os.path.exists(f"{self.PATH}/1.{self.EXTENSION}")
        self.assertTrue(check)
    # end_test_single_download

    def tearDown(self) -> None:
        os.remove(f"{self.PATH}/1.{self.EXTENSION}")
        os.rmdir(self.PATH)
        return super().tearDown()
    # end_tearDown

# end_TestDownload


class TestAsyncDownload(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.URL1 = "https://filesamples.com/samples/image/jpeg/sample_640%C3%97426.jpeg"
        self.URL2 = "https://filesamples.com/samples/image/jpeg/sample_1280%C3%97853.jpeg"
        self.PATH = "./downloads/unittest"
        self.EXTENSION = re.search(ext_pattern, self.URL1).group(1)
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
        check = all(os.path.exists(f"{self.PATH}/{i}.{self.EXTENSION}")
                    for i in range(1, 11))
        self.assertTrue(check)
    # end_test_multi_download

    def tearDown(self) -> None:
        for i in range(1, 11):
            os.remove(f"{self.PATH}/{i}.{self.EXTENSION}")
        os.rmdir(self.PATH)
        return super().tearDown()
    # end_tearDown

# end_TestAsyncDownload
