import json
import re
from typing import List

from models import Chapter


def parse_gallery(self, query: str) -> Chapter:
    """Parses URL fully and returns models.Chapter object with all necessary attributes populated

    Args:
        self (Hitomi): Hitomi object passed from ext.py
        query (str): URL string to be parsed

    Returns:
        Chapter: Fully populated models.Chapter object to be downloaded
    """

    chapter = Chapter(pre_download=False)
    chapter.number = 1

    res = self.session.get(query)
    res.close()

    id_pattern = r"var galleryid = ([0-9]{1,});"
    chapter.id = re.search(id_pattern, res.text).group(1)

    # js file contains json for page information
    gallery_url = f"https://ltn.hitomi.la/galleries/{chapter.id}.js"
    res = self.session.get(gallery_url)
    txt = res.text.replace("var galleryinfo = ", "")
    data = json.loads(txt)

    chapter.page_urls = get_page_urls(self, data)
    chapter.title = data["title"]
    chapter.manga_title = data["title"]

    # essential for downloading else you'll get a 403 error
    chapter.headers = {"referer": f"https://hitomi.la/reader/{chapter.id}.html"}

    return chapter


def get_page_urls(self, data: dict) -> List[dict]:
    """Gets page URLs for downloading

    Args:
        self (Hitomi): Hitomi object passed from ext.py
        data (dict): JSON object obtained from chapter.id.js file

    Returns:
        List[dict]: List of page URLs
    """

    pages = []

    for file in data["files"]:
        no_webp = file["haswebp"] == 0
        no_avif = file["hasavif"] == 0

        hash = file["hash"]
        tmp_ext = file["name"].split(".")[-1]

        # will use ".(jpg|png) if either image doesn't have webp or user chooses not to use webp"
        ext = tmp_ext if no_webp or not self.always_webp else "webp"
        path = "images" if no_webp or not self.always_webp else "webp"

        # decrypting hash to obtain full image path
        first_subdom = first_subdom_from_hash(self.gg, hash)
        second_subdom = "b" if no_webp and no_avif or not self.always_webp else "a"
        hash_path = full_path_from_hash(self.gg, hash)

        page_url = (
            f"https://{first_subdom}{second_subdom}.hitomi.la/{path}/{hash_path}.{ext}"
        )
        pages.append(page_url)

    return pages


def full_path_from_hash(gg: dict, hash: str) -> str:
    """Gets image path from gg object and hash

    Args:
        gg (dict): gg object obtained from gg.js file
        hash (str): Generated hash for the image

    Returns:
        str: Full pathname for the image
    """

    # finds "b: '123456789/'" in gg
    p1 = r"b: ('|\")(.*\/)('|\")"
    m1 = re.search(p1, gg).group(2)

    # reorders last 3 digits of hash and returns
    # "abcde12" -> "2e1" -> "737"
    hash_int = str(int(hash[-1] + hash[-3:][:2], 16))

    # full pathname: "123456879/737/abcde12"
    return f"{m1}{hash_int}/{hash}"


def first_subdom_from_hash(gg: dict, hash: str) -> str:
    """Gets first subdomain from the hash value

    Args:
        gg (dict): gg object obtained from gg.js file
        hash (str): Generated hash for the image

    Returns:
        str: First subdomain for the page URL
    """

    # reorders last 3 digits of hash into int
    # "abcde12" -> 737
    g = int(hash[-1] + hash[-3:][:2], 16)

    # finds "case 737: o = (0|1); break;" in gg
    p2 = r"case " + str(g) + r": o = ([01]); break;"
    o = int(re.search(p2, gg).group(1))

    # returns "a" or "b" depending on o value
    return chr(97 + o)
