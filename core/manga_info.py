from typing import List
from models import Chapter, Extension, Manga


def get_manga_info(ext_active: Extension, manga: Manga) -> List[Chapter]:
    """Retrieves all available chapters for download

    Args:
        ext_active (Extension): Instantiated object of an Extension subclass
        manga (Manga): Manga object with only id and title attributes populated

    Returns:
        List[Chapter]: List of Chapter objects available to be downloaded
    """

    manga_info = ext_active.get_manga_info(manga)
    to_download, valid_chapters = [], {}

    # if no available chapters, exit
    if len(manga_info.chapters) == 0:
        print("There are no chapters for this manga in english")
        return

    # if only 1 available chapter, no need to process
    if len(manga_info.chapters) == 1:
        return manga_info.chapters

    # sorts chapters by number
    manga.chapters.sort(key=lambda x: float(x.number))

    for chapter in manga_info.chapters:
        scanlator = f"[{chapter.scanlator}] " if chapter.scanlator else ""
        foldername = f"{scanlator}Ch.{chapter.number}{'' if chapter.title == '' else ' - '}{chapter.title}"

        chapter_float = round(float(chapter.number), 3)
        chapter.foldername = foldername
        valid_chapters[chapter_float] = chapter

        print(foldername)

    while True:
        query_str = f"Which chapters do you wish to download (1-{manga_info.chapters[-1].number}, q to quit): "
        to_download = (input(query_str).lower().strip() or "q")

        if to_download == "q":
            return

        to_download = parse_to_download(to_download, valid_chapters)

        # keeps asking for chapters until a valid input is given
        if len(to_download) > 0:
            break
        else:
            print("Error with input, please try again.")

    # only keeps the keys that are requested to be downloaded in valid_chapters
    valid_chapters = [valid_chapters[chapter_num]
                      for chapter_num in to_download]

    return valid_chapters
# end_get_manga_info


def parse_to_download(to_download: str, valid_chapters: List[Chapter]) -> List[Chapter]:
    """Retrieves a list of chapters to be downloaded

    Args:
        to_download (str): String range of chapters to be downloaded
        valid_chapters (List[Chapter]): List of Chapter objects

    Returns:
        List[Chapter]: List of Chapter objects with chapter numbers in range of 'to_download' parameter
    """

    new_to_download = []

    to_download = to_download.split(",")

    for chapters in to_download:
        chapters = chapters.strip().split("-")

        # if only 1 chapter from the comma split
        if len(chapters) == 1 and int(chapters[0]) in valid_chapters:
            new_to_download.append(int(chapters[0]))

        # range of chapters from the comma split
        elif len(chapters) == 2:
            chapters = [float(chapter) for chapter in chapters]

            # in any case first num is bigger
            if chapters[0] < chapters[1]:
                i = chapters[0]
                # loop in increments of 0.1 for chapters like 10.1 or 9.5
                while i <= chapters[1]:
                    if i in valid_chapters:
                        new_to_download.append(i)

                    # round to mitigate floating point errors
                    i = round(i + 0.1, 4)

            # left number is larger than right
            else:
                return []

    return new_to_download
# end_parse_to_download
