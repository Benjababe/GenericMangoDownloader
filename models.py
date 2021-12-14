from abc import ABC, abstractmethod
from typing import List


class Manga():
    def __init__(self):
        """Constructor for Manga class

        """
        self.title = ""
        self.id = ""
        self.cover_url = ""
        self.description = ""
        self.tags = ""
        self.chapters = []

    def add_attribute(self, name: str, value: str):
        setattr(self, name, value)


class Tag():
    def __init__(self, name: str, id: str):
        """Constructor for Tag class

        Args:
            name (str): Name of tag
            id (str): ID of tag
        """

        self.name = name
        self.id = id


class Chapter():
    def __init__(self, pre_download: bool):
        """Constructor for Chapter class

        Args:
            pre_download (bool): Boolean flag indicate segment of code should be run before downloading
        """

        self.pre_download = pre_download
        self.number = ""
        self.id = ""
        self.title = ""
        self.scanlator = ""
        self.date = ""
        self.manga_title = ""
        self.foldername = ""
        self.page_urls = []

        # headers for http request if the site's a fucking piece of shit
        self.headers = {}
        self.cloudflare = False

    def add_attribute(self, name: str, value: str):
        setattr(self, name, value)


class Extension(ABC):
    @abstractmethod
    def parse_url(self, query: str) -> dict:
        """Checks URL string whether it is a manga or chapter page

        Args:
            query (str): URL string to parse

        Raises:
            NotImplementedError: When method isn't implemented by the subclass

        Returns:
            dict: {
                "type": "manga" or "chapter",
                "item": classes.Manga object or classes.Chapter object depending on type value
            }
        """

        raise NotImplementedError("parse_url method has not been implemented")

    @abstractmethod
    def search(self, query: str, page: int, cover: bool = False) -> dict:
        """Search the extension's website using the query string

        Args:
            query (str): Query string to search for manga
            page (int): Page of search results
            cover (bool, optional): Boolean flag to indicate whether cover page should be retrieved to Manga object. Defaults to False.

        Raises:
            NotImplementedError: When method isn't implemented by the subclass

        Returns:
            dict: {
                "manga_list": [...classes.Manga object with only id and title attributes populated]
                "last_page":  Boolean flag to indicate whether it's the last page
            }
        """

        raise NotImplementedError("search method has not been implemented")

    @abstractmethod
    def get_manga_info(self, manga: Manga) -> Manga:
        """Populates Manga object with required attributes for downloading

        Args:
            manga (Manga): Manga object with only id and title attributes populated

        Raises:
            NotImplementedError: When method isn't implemented by the subclass

        Returns:
            Manga: Manga object with all applicable attributes populated
        """

        raise NotImplementedError(
            "get_manga_info method has not been implemented")

    @abstractmethod
    def get_random(self) -> Manga:
        """Retrieves Manga object from extension's website

        Raises:
            NotImplementedError: When method isn't implemented by the subclass

        Returns:
            Manga: Random Manga object
        """

        raise NotImplementedError("get_random method has not been implemented")

    @abstractmethod
    def arg_handler(self, args: List[str]):
        """Handling of custom arguments

        Args:
            args (List[str]): Arguments to be parsed by the extension

        Raises:
            NotImplementedError: When method isn't implemented by the subclass
        """

        raise NotImplementedError(
            "arg_handler method has not been implemented")
