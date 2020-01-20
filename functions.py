import math
import os
import re
import requests
import sys

#my local constants
import constants

class Functions:
    def display_download(self, title, progress, total):
        download_status = "\rDownloading {}... [{}{}] {}% ({}/{})".format(
                            title, "=" * progress, " " * (total - progress), 
                            math.ceil(progress / total * 100), progress, total)
        sys.stdout.write(download_status)
        sys.stdout.flush()
    #end init

    def has_zero(self, url):
        check = url.rfind(".") - 2
        return (str(url[check]) == "0")
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
            filename = self.generate_filename(zero, i, ext)
            img_url = base + "/" + filename
            #removes all folder incompatible characters
            folder_path = re.sub(r"[\\/:*?\"<>|]", "", title)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            headers = {"Connection": "Keep-Alive"}
            cf_url = scraper.get(img_url, headers=headers).content
            with open("{}/{}".format(folder_path, filename), "wb") as f:
                f.write(cf_url)
                f.close()
            scraper.close()
            self.display_download(title, i, pages)
        #end_for_loop
        print("\n")
    #end_cf_download     

    def run_main_app(self):
        cmd = "python " + constants.DATA["main"]
        os.system(cmd)
    #end_run_main