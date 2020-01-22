import constants as const
import pickle

class Template:
    def __init__(self, input_str, pickle):
        self.pickle = const.RESUME_PATH.format(pickle)
        self.link = ""
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
        return self.link
    #end_request_link

    #creates the pickle as well
    def update_pickle(self, data):
        f = open(self.pickle, "wb")
        pickle.dump(data, f)
        f.close()
    #end_update_pickle

    def get_pickle(self):
        f = open(self.pickle, "rb")
        res = pickle.load(f)
        f.close()
        return res
    #end_get_pickle

    def restart_app(self):
        self.link = ""
        self.post_request_link(self.request_link())
    #end_restart_app