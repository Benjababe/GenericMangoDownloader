import core.misc as misc
import unittest


class TestMisc(unittest.TestCase):
    def test_is_url(self):
        self.assertTrue(misc.is_url("https://google.com"))
        self.assertTrue(misc.is_url("https://mangadex.org/chapter/123"))
        self.assertFalse(misc.is_url("Hello World!"))

    def test_read_write_delete_pickle(self):
        # write then read pickle
        misc.write_pickle("unittest", "testkey", "testvalue")
        val = misc.read_pickle("unittest", "testkey")
        self.assertEqual(val, "testvalue")

        # first two deletions should be successful but not the others
        self.assertTrue(misc.delete_pickle("unittest", "testkey"))
        self.assertTrue(misc.delete_pickle("unittest"))
        self.assertFalse(misc.delete_pickle("unittest", "testkey"))
        self.assertFalse(misc.delete_pickle("unittest"))
