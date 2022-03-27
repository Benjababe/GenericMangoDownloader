from abc import ABC, abstractmethod
from typing import List

from models import Manga


class Extension(ABC):
    """ 
    This will be the parent class of all extensions for this program
    Ensure all methods that can be implemented are done so
    """

    # TODO return a ParseResult class instead of a generic dict
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
                "item": models.Manga object or models.Chapter object depending on type value
            }
        """

        msg = "parse_url method has not been implemented"
        raise NotImplementedError(msg)

    # TODO return a new SearchResult class instead of a generic dict
    @abstractmethod
    def search(self, query: str, page: int, cover: bool = False) -> dict:
        """Search the extension's website using the query string

        Args:
            query (str): Query string to search for manga
            page (int): Page of search results
            cover (bool, optional): Boolean flag to indicate whether cover page should be retrieved to models.Manga object. Defaults to False.

        Raises:
            NotImplementedError: When method isn't implemented by the subclass

        Returns:
            dict: {
                "manga_list": [...models.Manga object with only id and title attributes populated]
                "last_page":  Boolean flag to indicate whether it's the last page
            }
        """

        msg = "search method has not been implemented"
        raise NotImplementedError(msg)

    @abstractmethod
    def get_manga_info(self, manga: Manga) -> Manga:
        """Populates models.Manga object with required attributes for downloading

        Args:
            manga (Manga): models.Manga object with only id and title attributes populated

        Raises:
            NotImplementedError: When method isn't implemented by the subclass

        Returns:
            Manga: models.Manga object with all applicable attributes populated
        """

        msg = "get_manga_info method has not been implemented"
        raise NotImplementedError(msg)

    @abstractmethod
    def get_random(self) -> Manga:
        """Retrieves models.Manga object from extension's website

        Raises:
            NotImplementedError: When method isn't implemented by the subclass

        Returns:
            Manga: Random models.Manga object
        """

        msg = "get_random method has not been implemented"
        raise NotImplementedError(msg)

    @abstractmethod
    def arg_handler(self, args: List[str]):
        """Handling of custom arguments

        Args:
            args (List[str]): Arguments to be parsed by the extension

        Raises:
            NotImplementedError: When method isn't implemented by the subclass
        """

        msg = "arg_handler method has not been implemented"
        raise NotImplementedError(msg)
# end_Extension
