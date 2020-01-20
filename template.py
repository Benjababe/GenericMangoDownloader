class Template:
    def __init__(self, argv, input_str):
        self.link = ""
        #boolean on whether to run .main.py after finishing operation
        self.run_main = False
        self.input_str = input_str

        if len(argv) > 1:
            self.link = argv[1]
        if len(argv) > 2:
            self.run_main = argv[2]
    #end_init

    #sets what function to run after re-requesting for URL if script is ran without .main.py. 
    #should be parsing function
    def set_post_request(self, post_request_link):
        self.post_request_link = post_request_link

    def request_link(self):
        if self.link == "":
            self.link = input(self.input_str)
        return self.link
    #end_request_link

    def restart_app(self):
        self.link = ""
        self.run_main = False
        self.post_request_link(self.request_link())
    #end_restart_app

    #either runs .main.py or requests for URL again depending on arguments on launch
    #run_main argument => function to run the .main.py script
    #restart argument  => function to restart the individual site .py file, 
    #could be the restart_app function above if configured
    def end(self, run_main, restart):
        if self.run_main:
            run_main()
        else:
            restart()