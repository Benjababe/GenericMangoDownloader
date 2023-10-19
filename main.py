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


def main_parse_url(ext: Extension, url: str):
    """Parse URL string given and proceeds accordingly either as a whole manga or single chapter

    Args:
        url (str): URL string to be parsed
    """

    if not core.is_url(url):
        print("A URL was not provided")
        return

    parse_result = ext.parse_url(url)

    # if type is manga, output should be a dict with keys "title" and "manga_id"
    if parse_result.type == ParseResult.MANGA:
        main_get_manga_info(ext, parse_result.item)

    # if type is chapter, output should be a regular chapter object
    elif parse_result.type == ParseResult.CHAPTER:
        core.download_chapters(ext, [parse_result.item])


def main_search(ext: Extension, query: str):
    """Searches for a manga by the given query string

    Args:
        query (str): Query string to search for manga
    """

    manga = core.search(ext, query)

    if manga:
        main_get_manga_info(ext, manga)


def main_random(ext: Extension):
    """Retrieves a random manga from the extension's website, not compatible with all extensions"""

    manga = core.random_manga(ext)

    if manga:
        main_get_manga_info(ext, manga)


def main_get_manga_info(ext: Extension, manga: Manga):
    """Gets chapters available for download and proceeds to downloading them

    Args:
        manga (Manga): models.Manga object with only id and title attributes populated
    """

    valid_chapters = core.get_manga_info(ext, manga)

    if valid_chapters:
        core.download_chapters(ext, valid_chapters)


def check_extension(ext: Extension):
    """Checks whether an active extension has been set"""

    if ext is None:
        print("You have no initialised the program with an extension (i.e. --mangadex)")
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
    ext = None

    parser = generate_arg_parser()
    args, unknown_args = parser.parse_known_args()
    args = args.__dict__

    for arg in args:
        val = args[arg]

        if val is not None:
            # sets active extension
            if arg in ext_dict and val is True:
                # ensures pickle has key for active extension
                core.check_pickle(arg)
                ext = ext_dict[arg]
                ext.arg_handler(unknown_args)

            # catch and runs standardised functions
            elif arg == "search":
                check_extension(ext)
                main_search(ext, val)

            elif arg == "random" and val is True:
                check_extension(ext)
                main_random(ext)

            elif arg == "parse_url":
                check_extension(ext)
                main_parse_url(ext, val.strip())

            # if it's the remaining arguments, treat them as custom extension arguments
            elif arg == "ext_args":
                check_extension(ext)
                ext.arg_handler(val)


if __name__ == "__main__":
    parse_arguments()
