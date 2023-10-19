from typing import List, Union

from models.manga import Chapter, Manga


class ParseResult:
    """Class containing results of parsing either manga or chapter"""

    MANGA = 0
    CHAPTER = 1

    def __init__(self, res_type: int, item: Union[Manga, Chapter]):
        """Constructor for ParseResult class

        Args:
            type (int): Either the _MANGA or _CHAPTER constants depending on parsing results
            item (Union[Manga, Chapter]): Manga/Chapter object retrieved from parsing the webpage
        """

        super().__init__()
        self.type = res_type
        self.item = item


class SearchResult:

    """Class containing search results from extension"""

    def __init__(self, manga_list: List[Manga], last_page: bool):
        """Constructor for SearchResult class

        Args:
            manga_list (List[Manga]): List of Manga objects from searching
            last_page (bool): Boolean flag to indicate whether search result is at the last page
        """

        super().__init__()

        self.manga_list = manga_list
        self.last_page = last_page
        self.length = len(manga_list)
