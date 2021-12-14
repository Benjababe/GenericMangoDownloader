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
# end_check_pickle


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
# end_write_pickle


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
# end_read_pickle


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
    # end_delete_pickle


def is_url(url: str) -> bool:
    """Checks whether string parameter is a url

    Args:
        url (str): String to check whether it is a url

    Returns:
        bool: Boolean value whether string is a url
    """
    regex = re.compile(
        r'^(?:http)s?://'  # http:// or https://
        # domain...
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return not re.match(regex, url) == None
# end_is_url
