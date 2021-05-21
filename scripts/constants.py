import os

#sites
#abbreviation btw
NH = "https://nhentai.net"
NH_ABBR = "nH"

CAFE = "https://hentai.cafe/"
CAFE_ABBR = "Cafe"

DEX = "https://mangadex.org/"
DEX_API = "https://api.mangadex.org/"
DEX_READER = "https://mangadex.org/chapter/{}"
DEX_ABBR = "Dex"

#stuff
MAIN_DL = "download"
MAIN_CH = "chapters"

PICKLE_PATH = os.path.dirname(os.path.realpath(__file__)) + "/pickles/"

DOWNLOAD_PATH = "./downloads/"

#data
DATA = {
    "main": ".main.py",
    "sites": {
        "hentai.cafe": {
            "dl_cafe": "Cafe"
        }, 
        "nhentai.net": {
            "dl_nh": "NH"
        }, 
        "mangadex.org": {
            "dl_dex": "Dex"
        }
    }
}