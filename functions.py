import math
import json
import os
import re
import sys

class Functions:
    def display_download(self, title, progress, total):
        download_status = "\rDownloading {}... [{}{}] {}%".format(
                            title, "=" * progress, " " * (total - progress), math.ceil(progress / total * 100))
        sys.stdout.write(download_status)
        sys.stdout.flush()
    #end init

    def has_zero(self, url):
        check = url.rfind(".") - 2
        return (url[check] == "0")
    #end_has_zero

    def generate_filename(self, zero, page_no, ext):
        z = ""
        if (page_no < 10 and zero):
        #z is needed because files are named "01.jpg", "02.jpg"
            z = "0"
        return "{}{}{}".format(z, page_no, ext)
    #end_generate_filename

    def cf_download(self, scraper, title, zero, pages, ext, base):
        for i in range(1, pages+1):
            filename = self.generate_filename(False, i, ext)
            img_url = base + "/" + filename
            folder_path = re.sub(r"[\\/:*?\"<>|]", " ", title)

            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            cfurl = scraper.get(img_url).content
            with open("{}/{}".format(folder_path, filename), "wb") as f:
                f.write(cfurl)
            self.display_download(title, i, pages)
        #end_for_loop
    #end_cf_download

    def run_main(self):
        with open(".data.json") as data_file:
            cmd = "python " + json.load(data_file)["main"]
            os.system(cmd)
    #end_run_main


