from datetime import datetime
import html
import math
import os
import re
import requests
import sys
import time

#my local constants
import constants as const

class Functions:
    def __init__(self, v = False):
        self.v = v
        self.disp = self.empty

    def empty(self, txt = ""):
        pass

    def set_v(self, v = False):
        self.v = v
        print("Verbose printing is now " + "active" if self.v else "inactive")

    def vprint(self, string):
        #only prints when set_v is passed with true
        if self.v:
            print(string)

    def set_disp(self, disp):
        self.disp = disp
    
    def display_download(self, title, progress, total):
        #adjusts max length for terminal so it doesn't fuck up the stdout flush by invading the newline
        if self.disp == self.empty:
            terminal_len = os.get_terminal_size().columns
            # prevents the string from being longer than the terminal length. 14 is for the "{}% ({}/{}) and some overhead"
            reserved_len = len("Downloading ") + (len(str(total)) * 2) + total + 14
            # -3 for the "..."
            max_len = terminal_len - reserved_len - 3
            title = title[0:max_len]

        #caps progress bar at 20 chars long
        perc_total = 20 if total > 20 else total
        perc_progress = math.ceil(progress * perc_total / total)

        #eg. Downloading Saeki-san wa Nemutteru Ch. 38 - Tokimiya's Dilemma... [====================] 100% (22/22)
        download_status = '\rDownloading "{}" [{}{}] {}% ({}/{})'.format(
            title, 
            "#" * perc_progress, 
            "=" * (perc_total - perc_progress), 
            math.ceil(progress / total * 100),
            progress, 
            total
            )

        if self.disp == self.empty:
            sys.stdout.write(download_status)
            sys.stdout.flush()
        else:
            #function passed in to display status elsewhere eg. GUI
            self.disp(download_status)
    #end_display_download

    def res_hook(self, res, *args, **kwargs):
        #writes abnormal http requests to a logfile. opens as append
        if not res.status_code == 200:
            now = datetime.now()
            date_time = now.strftime("%d/%m/%Y %H:%M:%S")
            log_str = "[{}] - HTTP status code {} returned from URL: {}\n".format(date_time, res.status_code, res.url)
            log = open(".http_log.txt", "a")
            log.write(log_str)
            log.close()
    #end_res_hook

    #TODO maybe do this in the cf_download instead?
    def has_zero(self, url):
        ext = url.split(".")[-1]
        codes = []

        #sees status code for both "1.png" and "01.png" to see which exists. 200 for OK, 404 for doesn't exist
        for name in ["1.", "01."]:
            split[-1] = name + ext
            new_url = "/".join(split)
            res = requests.get(new_url)
            codes.append(res.status_code)
        return True if codes[1] == 200 else False
    #end_has_zero

    def is_float(self, num):
        #oneshot edge case
        if num == "":
            return False
        try:
            float(num)
            return True
        except:
            return False

    def remove_backslash(self, arr):
        for i in range(0, len(arr)):
            if arr[i][-1] == "/":
                arr[i] = arr[i][:-1]
            if arr[i][0] == "/":
                arr[i] = arr[i][1:]
        return arr
    #end_remove_backslash

    def get_extension(self, filename):
        ext = filename.split(".")[1]
        return ext

    def generate_filename(self, zero, page_no, ext):
        z = ""
        if page_no < 10 and zero:
        #z is needed because files are named "01.jpg", "02.jpg"
            z = "0"
        return "{}{}{}".format(z, page_no, ext)
    #end_generate_filename

    #barebones, returns response only
    def download(self, session, url, file_path = None, display = False):
        #checks if file exists. if does, returns None and doesn't download
        if(file_path != None and os.path.isfile(file_path)):
            self.vprint(file_path + " already exists!")
            return None
        #downloads file within 5 tries
        for _ in range(5):
            try:
                with session.get(url) as res:
                    if display:
                        self.vprint("Download for {} completed".format(url))
                    if file_path != None:
                        with open(file_path, "wb") as img:
                            img.write(res.content)
                            img.close()
                    return res
            except Exception as ex:
                print("Exception caught: " + type(ex).__name__)
            else:
                break

    def cf_download(self, scraper, title, zero, pages, ext, base):
        for i in range(1, pages + 1):
            filename = self.generate_filename(zero, i, ext)
            img_url = base + "/" + filename
            # removes all folder incompatible characters
            folder_path = const.DOWNLOAD_PATH + re.sub(r"[\\/:*?\"<>|]", "", title)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            headers = {"Connection": "Keep-Alive"}

            try:
                img = scraper.get(img_url, headers = headers).content
                with open("{}/{}".format(folder_path, filename), "wb") as f:
                    f.write(img)
                    f.close()
            except KeyboardInterrupt:
                print("\nKilled it yourself")
                sys.exit(0)
            except Exception as ex:
                print("Exception caught: " + str(ex))
                print("\nProblem with download, retrying in 2 seconds...")
                time.sleep(2)
            except:
                print("Unknown Error, idk fampai")

            scraper.close()
            self.display_download(title, i, pages)
        #end_for_loop
        print("\n")
    #end_cf_download

#end_Functions_class

if __name__ == "__main__":
    print("Dont run me fool")