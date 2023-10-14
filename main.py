# standard libraries
import argparse
import sys
from models import Manga, Extension, ParseResult

# local files
import core

# extensions
import extensions.mangadex.ext as mangadexExt
import extensions.mangakakalot.ext as mangakakalotExt
import extensions.nhentai.ext as nhentaiExt
import extensions.hitomi.ext as hitomiExt


# to match the object via string
ext_dict = {
    mangadexExt.NAME: mangadexExt.Mangadex(),
    mangakakalotExt.NAME: mangakakalotExt.Mangakakalot(),
    nhentaiExt.NAME: nhentaiExt.NHentai(),
    hitomiExt.NAME: hitomiExt.Hitomi(),
}


# keeps the active extension
ext_active: Extension = None


def main_parse_url(url: str):
    """Parse URL string given and proceeds accordingly either as a whole manga or single chapter

    Args:
        url (str): URL string to be parsed
    """

    if not core.is_url(url):
        print("A URL was not provided")
        return

    global ext_active

    parse_result = ext_active.parse_url(url)

    # if type is manga, output should be a dict with keys "title" and "manga_id"
    if parse_result.type == ParseResult._MANGA:
        main_get_manga_info(parse_result.item)

    # if type is chapter, output should be a regular chapter object
    elif parse_result.type == ParseResult._CHAPTER:
        core.download_chapters(ext_active, [parse_result.item])


def main_search(query: str):
    """Searches for a manga by the given query string

    Args:
        query (str): Query string to search for manga
    """

    global ext_active

    manga = core.search(ext_active, query)

    if manga:
        main_get_manga_info(manga)


def main_random():
    """Retrieves a random manga from the extension's website, not compatible with all extensions"""

    global ext_active

    manga = core.random_manga(ext_active)

    if manga:
        main_get_manga_info(manga)


def main_get_manga_info(manga: Manga):
    """Gets chapters available for download and proceeds to downloading them

    Args:
        manga (Manga): models.Manga object with only id and title attributes populated
    """

    global ext_active

    valid_chapters = core.get_manga_info(ext_active, manga)

    if valid_chapters:
        core.download_chapters(ext_active, valid_chapters)


def check_extension():
    """Checks whether an active extension has been set"""

    global ext_active

    if ext_active == None:
        print("You have no initialised the program with an extension (i.e. mangadex)")
        sys.exit(0)


def generate_arg_parser() -> argparse.ArgumentParser:
    """Generates argument parser to handle inputs

    Returns:
        argparse.ArgumentParser: Parser for main.py arguments
    """
    parser = argparse.ArgumentParser(
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=100)
    )

    # extension argument parsing
    parser.add_argument(
        f"--{mangadexExt.NAME}",
        action="store_true",
        dest=f"{mangadexExt.NAME}",
        help="Sets active extension as MangaDex",
    )
    parser.add_argument(
        f"--{mangakakalotExt.NAME}",
        action="store_true",
        dest=f"{mangakakalotExt.NAME}",
        help="Sets active extension as Mangakakalot",
    )
    parser.add_argument(
        f"--{nhentaiExt.NAME}",
        action="store_true",
        dest=f"{nhentaiExt.NAME}",
        help="Sets active extension as nHentai",
    )
    parser.add_argument(
        f"--{hitomiExt.NAME}",
        action="store_true",
        dest=f"{hitomiExt.NAME}",
        help="Sets active extension as Hitomi.la",
    )

    # standardised functions for every extension
    parser.add_argument(
        "-S",
        "--search",
        metavar="query",
        dest="search",
        help="Calls the search function of the active extension",
    )

    parser.add_argument(
        "-RD",
        "--random",
        action="store_true",
        dest="random",
        help="Finds a random manga",
    )

    parser.add_argument(
        "-U",
        "--url",
        metavar="url",
        dest="parse_url",
        help="Retrieves manga/chapter directly from a provided URL",
    )

    parser.add_argument(
        "ext_args",
        nargs=argparse.REMAINDER,
        help="Reserved for extension's custom arguments, use after the reserved arguments",
    )

    return parser


def parse_arguments():
    """Parses arguments from argparse"""

    global ext_active

    parser = generate_arg_parser()
    args, unknown_args = parser.parse_known_args()
    args = args.__dict__

    for arg in args:
        val = args[arg]

        if not val == None:
            # sets active extension
            if arg in ext_dict.keys() and val == True:
                # ensures pickle has key for active extension
                core.check_pickle(arg)
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


if __name__ == "__main__":
    parse_arguments()
