import constants as const
import os
import sys
import pickle

class Template:
    def __init__(self, input_str, resume_pickle = False, cookies_pickle = False):
        if resume_pickle:
            self.resume_pickle = const.PICKLE_PATH + "/{}.pckl".format(resume_pickle)
        #mainly to store login session cookies
        if cookies_pickle:
            self.cookies_pickle = const.PICKLE_PATH + "/{}.pckl".format(cookies_pickle)
        self.site_info_pickle = const.PICKLE_PATH + "/site_info.pckl"
        #list of language codes. englando as default language (probably only used for dex)
        self.LANG = ["gb"]
        self.link = ""

        #code to run app as per normal
        self.END_RESET = "0x00"
        #ends app when chapter data is retrieved, should be for gui
        self.END_CHAPTER_LIST = "0x01"
        #ends app on download finish, should be for downloading with arguments
        self.END_DOWNLOAD = "0x02"
        #ends app when search is completed
        self.END_SEARCH = "0x03"

        #current end goal is initialised as running as per normal
        self.END = "0x00"
        #if true, restart_app will end instead of requesting again
        self.kill_flag = False
        #string for requesting site url
        self.input_str = input_str
    #end_init

    #sets what function to run after re-requesting for URL if script is ran without .main.py. 
    #should be parsing function
    #must be set before running restart_app()
    def set_post_request(self, post_request_link):
        self.post_request_link = post_request_link
    #end_set_post_request

    def request_link(self):
        if self.link == "":
            self.link = input(self.input_str)
        elif self.link.lower() == "q":
            exit()
        return self.link
    #end_request_link

    def update_pickle(self, pickle_dir, data):
        f = open(pickle_dir, "wb")
        pickle.dump(data, f)
        f.close()
    #end_update_pickle

    def get_pickle(self, pickle_dir, default = None):
        if os.path.exists(pickle_dir):
            f = open(pickle_dir, "rb")
            res = pickle.load(f)
            f.close()
            return res
        else:
            return default
    #end_get_pickle

    def check_resume(self, download_func, messagebox = None):
        #Y/n to download based on existing download pickle file
        if os.path.exists(self.resume_pickle):
            f_pickle = open(self.resume_pickle, "rb")
            chapter_loop, pending_downloads = pickle.load(f_pickle)
            f_pickle.close()

            user_input = ""
            prompt_str = "There is an unfinished download for {} at Chapter {}. Would you like to resume?".format(
                        pending_downloads["mango_title"], pending_downloads["chapters"][chapter_loop]["chapter"])
            #if messagebox is given, will pop it up and query. Else will ask in the terminal instead
            user_input = input(prompt_str + " (Y/n) ").upper() if messagebox == None\
            else messagebox.askquestion("Resume Download", prompt_str).upper()
            if (user_input == "Y" or user_input == "YES" or user_input == ""):
                download_func(pending_downloads, True)
            elif (user_input == "N" or user_input == "NO"):
                os.remove(self.resume_pickle)
            else:
                print("Only accepting 'y', 'yes, 'n', 'no' or defaults to yes if left empty dummy :P")
                #BEHOLD THE POWER OF RECURSIVENESSMEN
                self.check_resume(download_func, messagebox = messagebox)
    #end_check_resume

    def restart_app(self):
        if self.kill_flag:
            sys.exit(0)
        self.link = ""
        self.post_request_link(self.request_link())
    #end_restart_app