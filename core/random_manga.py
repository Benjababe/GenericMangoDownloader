from models import Extension, Manga


def random_manga(ext: Extension) -> Manga:
    """Retrieves random manga

    Args:
        ext (Extension): Subclass of Extension class the site extension creates

    Returns:
        Manga: models.Manga object with only id and title attributes populated
    """

    manga = ext.get_random()

    while True:
        query = (
            f'Found random manga "{manga.title}". Do you wish to download it? (Y/n): '
        )
        dl = input(query) or "Y"

        if dl.upper() == "N":
            return None

        if dl.upper() == "Y":
            break

    return manga
