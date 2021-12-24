class Manga():
    """
    This is the basic Manga class to be used to obtain chapters.
    Any attributes not included can be added via the extension itself with add_attribute.
    """

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
# end_Manga


class Chapter():
    """
    This is the basic Chapter class to be used for downloading
    Any attributes not included can be added via the extension itself with add_attribute
    """

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
        """Allow for additional attributes to be added to models.Chapter object upon extension's needs

        Args:
            name (str): Name of new attribute
            value (str): Value of new attribute
        """
        setattr(self, name, value)
# end_Chapter


class Tag():
    """This is the basic Tag class for manga tags, could be used for a GUI in the future
    """

    def __init__(self, name: str, id: str):
        """Constructor for Tag class

        Args:
            name (str): Name of tag
            id (str): ID of tag
        """

        self.name = name
        self.id = id
# end_Tag
