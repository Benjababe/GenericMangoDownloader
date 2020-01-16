from functions import Functions
from urllib.parse import urlparse

class Template:
    def __init__(self, argv, input_str):
        self.link = ""
        self.run_main = False
        self.input_str = input_str

        if len(argv) > 1:
            self.link = argv[1]
        if len(argv) > 2:
            self.run_main = argv[2]

    def set_functions(self, post_request_link):
        self.post_request_link = post_request_link

    def request_link(self):
        if self.link == "":
            self.link = input(self.input_str)
        return self.link
    #end_request_link

    def restart_app(self):
        self.link = ""
        self.run_main = False
        self.request_link()

    #either runs .main.py or requests for URL again depending on arguments on launch
    def end(self, run_main, restart):
        if self.run_main:
            run_main()
        else:
            restart()