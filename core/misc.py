import os
import pickle
import re

DATA_FILE = "./data.pickle"


def check_pickle(ext: str):
    """Makes sure the file exists and the dict for the extension is set

    Args:
        ext (str): Name of manga extension
    """

    # creates pickle file if it doesn't exist and stores an empty dict in it
    if not os.path.exists(DATA_FILE):
        f = open(DATA_FILE, "wb")
        pickle.dump({}, f)
        f.close()

    with open(DATA_FILE, "rb") as f:
        data = pickle.load(f)
        f.close()

    if not ext in data:
        data[ext] = {}

    with open(DATA_FILE, "wb") as f:
        pickle.dump(data, f)
        f.close()


def write_pickle(ext: str, key: str, value):
    """Writes pickle data for extension

    Args:
        ext (str): Name of manga extension
        key (str): Key for data
        value: Data to be saved
    """

    check_pickle(ext)

    with open(DATA_FILE, "rb") as f:
        data = pickle.load(f)
        f.close()

    data[ext][key] = value

    with open(DATA_FILE, "wb") as f:
        pickle.dump(data, f)
        f.close()


def read_pickle(ext: str, key: str):
    """Reads pickle data for extension

    Args:
        ext (str): Name of manga extension
        key (str): Key for data

    Returns:
        str: Data that was saved
    """

    check_pickle(ext)

    with open(DATA_FILE, "rb") as f:
        data = pickle.load(f)
        f.close()

    if key in data[ext]:
        return data[ext][key]

    else:
        return None


def delete_pickle(ext: str, key: str = "") -> bool:
    """Deletes either extension or key from pickle

    Args:
        ext (str): Name of manga extension
        key (str, optional): Key for data. Defaults to "".

    Returns:
        bool: False if not found, True if deleted successfully
    """

    if not os.path.exists(DATA_FILE):
        return False

    with open(DATA_FILE, "rb") as f:
        data = pickle.load(f)

    try:
        if key == "":
            del data[ext]

        else:
            del data[ext][key]

    except:
        return False

    with open(DATA_FILE, "wb") as f:
        pickle.dump(data, f)
        f.close()

    return True


def is_url(url: str) -> bool:
    """Checks whether string parameter is a url

    Args:
        url (str): String to check whether it is a url

    Returns:
        bool: Boolean value whether string is a url
    """
    regex = re.compile(
        r"^(?:http)s?://"  # http:// or https://
        # domain...
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    return not re.match(regex, url) == None


def is_valid_download_range(to_download: str) -> bool:
    """Checks whether download range from manga_info is valid

    Args:
        num (str): Range of chapters to download. Eg ("1-10", "1-10.5", "1,2,3,5-7", "1.5,3-8")

    Returns:
        bool: _description_
    """
    res = True
    pattern = re.compile("^\d+(\.?\d+)?$")
    dl_spl = to_download.split(",")
    num_list = []

    for i in range(len(dl_spl)):
        num_list += dl_spl[i].split("-")

    for number in num_list:
        if not bool(re.search(pattern, number.strip())):
            res = False

    return res
