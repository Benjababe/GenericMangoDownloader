from models import Extension, Manga


def random_manga(ext_active: Extension) -> Manga:
    """Retrieves random manga

    Args:
        ext_active (Extension): Subclass of Extension class the site extension creates

    Returns:
        Manga: models.Manga object with only id and title attributes populated
    """

    manga = ext_active.get_random()

    while True:
        query = (
            f'Found random manga "{manga.title}". Do you wish to download it? (Y/n): '
        )
        dl = input(query) or "Y"

        if dl.upper() == "N":
            return

        elif dl.upper() == "Y":
            break

    return manga
