# standard libraries
import argparse
import sys
from models import Manga

# local files
import download
import misc
from manga_info import get_manga_info
from random_manga import random_manga
from search import search

# extensions
import extensions.mangadex.ext as mangadexExt
import extensions.mangakakalot.ext as mangakakalotExt
import extensions.nhentai.ext as nhentaiExt


# to match the object via string
ext_dict = {
    "mangadex": mangadexExt.Mangadex(),
    "mangakakalot": mangakakalotExt.Mangakakalot(),
    "nhentai": nhentaiExt.NHentai()
}


# keeps the active extension
ext_active = None


def main_parse_url(url: str):
    """Parse URL string given and proceeds accordingly either as a whole manga or single chapter

    Args:
        url (str): URL string to be parsed
    """

    if not misc.is_url(url):
        print("A URL was not provided")
        return

    global ext_active

    parsed_url = ext_active.parse_url(url)

    # if type if manga, output should be a dict with keys "title" and "manga_id"
    if parsed_url["type"] == "manga":
        main_get_manga_info(parsed_url["item"])

    # if type is chapter, output should be a regular chapter object
    elif parsed_url["type"] == "chapter":
        download.download_chapters(ext_active, [parsed_url["item"]])
# end_parse_url


def main_search(query: str):
    """Searches for a manga by the given query string

    Args:
        query (str): Query string to search for manga
    """

    global ext_active

    manga = search(ext_active, query)

    if manga:
        main_get_manga_info(manga)
# end_main_search


def main_random():
    global ext_active

    manga = random_manga(ext_active)

    if manga:
        main_get_manga_info(manga)
# end_main_random


def main_get_manga_info(manga: Manga):
    """Gets chapters available for download and proceeds to downloading them

    Args:
        manga (Manga): Manga object with only id and title attributes populated
    """

    global ext_active

    valid_chapters = get_manga_info(ext_active, manga)

    if valid_chapters:
        download.download_chapters(ext_active, valid_chapters)
# end_main_get_manga_info


parser = argparse.ArgumentParser(
    formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=100))

# extension argument parsing
parser.add_argument("--mangadex", action="store_true",
                    dest="mangadex", help="Sets active extension as MangaDex")
parser.add_argument("--mangakakalot", action="store_true",
                    dest="mangakakalot", help="Sets active extension as Mangakakalot")
parser.add_argument("--nhentai", action="store_true",
                    dest="nhentai", help="Sets active extension as nHentai")

# standardised functions for every extension
parser.add_argument("-S", "--search", metavar="query", dest="search",
                    help="Calls the search function of the active extension")

parser.add_argument("-RD", "--random", action="store_true", dest="random",
                    help="Finds a random manga")

parser.add_argument("-U", "--url", metavar="url", dest="parse_url",
                    help="Retrieves manga/chapter directly from a provided URL")

parser.add_argument("ext_args", nargs=argparse.REMAINDER,
                    help="Reserved for extension's custom arguments, use after the reserved arguments")


def check_extension():
    """Checks whether an active extension has been set
    """

    global ext_active

    if ext_active == None:
        print("You have no initialised the program with an extension (i.e. mangadex)")
        sys.exit(0)
# end_check_extension


def parse_arguments():
    """Parses arguments from argparse
    """

    global ext_active

    args, unknown_args = parser.parse_known_args()
    args = args.__dict__

    for arg in args:
        val = args[arg]

        if not val == None:
            # sets active extension
            if arg in ext_dict.keys() and val == True:
                # ensures pickle has key for active extension
                misc.check_pickle(arg)
                ext_active = ext_dict[arg]
                # ext_active.arg_handler(unknown_args)

            # catch and runs standardised functions
            elif arg == "search":
                check_extension()
                main_search(val)

            elif arg == "random" and val == True:
                check_extension()
                main_random()

            elif arg == "parse_url":
                check_extension()
                main_parse_url(val.strip())

            # if it's the remaining arguments, treat them as custom extension arguments
            elif arg == "ext_args":
                check_extension()
                ext_active.arg_handler(val)

# end_parse_arguments


if __name__ == "__main__":
    parse_arguments()
