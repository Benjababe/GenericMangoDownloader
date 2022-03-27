import re
from typing import List
import requests

# local files
from models import Chapter, Extension, Manga, Tag
import core

import extensions.hitomi.parse as parse

NAME = "hitomi"


class Hitomi(Extension):
    session = requests.Session()
    always_webp = True

    def __init__(self):
        super().__init__()
        res = self.session.get("https://ltn.hitomi.la/gg.js")
        res.close()
        self.gg = res.text

    def parse_url(self, query: str) -> dict:
        pattern = r"https:\/\/hitomi.la\/(gamecg|cg|manga|doujinshi){1}\/"
        matches = re.search(pattern, query)

        if matches == None:
            return None

        chapter = parse.parse_gallery(self, query)
        return {"type": "chapter", "item": chapter}
    # end_parse_url

    def search(self, query: str, page: int, cover: bool = False) -> dict:
        return {}

    def get_manga_info(self, manga: Manga) -> Manga:
        return Manga(pre_download=False)

    def get_random(self) -> Manga:
        return Manga(pre_download=False)

    def arg_handler(self, args: List[str]):
        return
# end_Hitomi_class
