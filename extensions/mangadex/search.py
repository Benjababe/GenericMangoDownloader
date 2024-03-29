from typing import List
import json
import requests

from models import Manga, Tag
from models.results import SearchResult

API_URL = "https://api.mangadex.org"

# only show 10 manga in search results at a time
SEARCH_LEN = 10


def search(
    self, query: str, page: int, cover: bool = False, search_tags: List[str] = None
) -> SearchResult:
    """Searches for manga in MangaDex

    Args:
        query (str): Text query to search with
        page (int): Current page of results
        cover (bool, optional): Flag whether to show cover. Defaults to False.
        search_tags (List[str], optional): Manga tags to include with search. Defaults to [].

    Returns:
        SearchResult
    """

    search_url = f"{API_URL}/manga"

    # query Mangadex with proper parameters
    res = self.session.get(
        search_url,
        params={
            "title": query,
            "limit": SEARCH_LEN,
            "offset": (page - 1) * SEARCH_LEN,
            "includedTags[]": search_tags,
        },
    )
    res.close()
    data = json.loads(res.text)

    # only reaches last page of search result when chapter offset + chapter
    # displayed is greater of equals total search results
    last_page = (len(data["data"]) + data["offset"]) >= data["total"]

    manga_list = []

    # populate the returned list
    for item in data["data"]:
        manga = Manga()

        manga.title = item["attributes"]["title"][self.language]
        manga.id = item["id"]
        cover = True

        # retrieves front cover URL
        if cover:
            for rel in item["relationships"]:
                if rel["type"] == "cover_art":
                    cover_id = rel["id"]
                    cover_url = f"{API_URL}/cover/{cover_id}"

                    res = self.session.get(cover_url)
                    res.close()

                    cover_data = json.loads(res.text)
                    cover_filename = cover_data["data"]["attributes"]["fileName"]
                    manga.cover_url = f"https://uploads.mangadex.org/covers/{manga.id}/{cover_filename}"

        manga_list.append(manga)

    return SearchResult(manga_list, last_page)


def query_tags(session: requests.Session) -> List[str]:
    """Retrieves tags to use for manga query

    Args:
        session (requests.Session): Session object used for HTTP requests

    Returns:
        List[str]: List of tag ids used to querying
    """

    tag_query = ""
    while tag_query.lower() != "y":
        tag_query = input("Do you wish to search with tags? (y/N): ") or "N"

        if tag_query.lower() == "n":
            return []

    tags = get_tags(session)
    print("Choose tags by number:")

    # print all available tags
    double_format = "{}. {:<25}\t\t{}. {:<25}"
    for i in range(0, len(tags), 2):
        if len(tags) - i > 1:
            print(double_format.format(i + 1, tags[i].name, i + 2, tags[i + 1].name))
        else:
            print(f"{i+1}. {tags[i].name}")

    tag_query = ""
    tags_used = []
    while tag_query.lower() != "s":
        query = f"Enter ID of tag to include (1-{len(tags)}, s to stop): "
        tag_query = input(query) or ""

        # skip if input is not a number
        if not tag_query.isnumeric():
            continue

        i = int(tag_query) - 1

        if 0 <= i < len(tags):
            if tags[i] in tags_used:
                tags_used.remove(tags[i])
            else:
                tags_used.append(tags[i])

        print("Currently using: ", end="" if len(tags_used) > 0 else "\n")

        for i, tag in enumerate(tags_used):
            if i < len(tags_used) - 1:
                print(f"{tag.name}", end=", ")
            else:
                print(tag.name)

    # we only want the ids of the tags for querying
    tag_ids_used = list(map(lambda x: x.id, tags_used))
    return tag_ids_used


def get_tags(session: requests.Session) -> List[Tag]:
    """Retrieve list of tags supported by Mangadex

    Args:
        session (requests.Session): Session object used for HTTP requests

    Returns:
        List[Tag]: List of Mangadex Tag objects
    """

    res = session.get(f"{API_URL}/manga/tag")
    res.close()
    data = json.loads(res.text)

    tags = []

    for tag in data["data"]:
        name = tag["attributes"]["name"]["en"]
        tag_id = tag["id"]
        tags.append(Tag(name, tag_id))

    # sort tags in alphabetical order
    tags.sort(key=lambda x: x.name)
    return tags
