from typing import List


class Manga:
    """
    This is the basic Manga class to be used to obtain chapters.
    Any attributes not included can be added via the extension itself with add_attribute.
    """

    def __init__(self):
        """Constructor for Manga class"""

        super().__init__()
        self.title: str = ""
        self.id: str = ""
        self.cover_url: str = ""
        self.description: str = ""
        self.tags: List[Tag] = []
        self.chapters: List[Chapter] = []

    def add_attribute(self, name: str, value: str):
        """Adds attribute tag to Manga object

        Args:
            name (str): Attribute name
            value (str): Attribute value
        """
        setattr(self, name, value)


class Chapter:
    """
    This is the basic Chapter class to be used for downloading
    Any attributes not included can be added via the extension itself with add_attribute
    """

    def __init__(self, pre_download: bool):
        """Constructor for Chapter class

        Args:
            pre_download (bool): Boolean flag indicate segment of code
                                should be run before downloading
        """

        self.pre_download = pre_download
        self.number: str = ""
        self.id: str = ""
        self.title: str = ""
        self.scanlator: str = ""
        self.date: str = ""
        self.manga_id: str = ""
        self.manga_title: str = ""
        self.foldername: str = ""
        self.page_urls: List[str] = []

        # headers for http request if the site's a fucking piece of shit
        self.headers = {}
        self.cloudflare = False

    def add_attribute(self, name: str, value: str):
        """Allow for additional attributes to be added to models.
            Chapter object upon extension's needs

        Args:
            name (str): Name of new attribute
            value (str): Value of new attribute
        """
        setattr(self, name, value)


class Tag:
    """This is the basic Tag class for manga tags, could be used for a GUI in the future"""

    def __init__(self, name: str, tag_id: str):
        """Constructor for Tag class

        Args:
            name (str): Name of tag
            id (str): ID of tag
        """

        self.name = name
        self.id = tag_id
