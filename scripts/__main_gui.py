import asyncio
import html
import io
import math
import Pmw
import requests
import threading
import time
from concurrent.futures import ThreadPoolExecutor

#pylint: disable=no-member, unused-wildcard-import
#why isn't messagebox in * 🤔
from tkinter import messagebox
from tkinter import *
from PIL import ImageTk as itk, Image

#my local files
import constants as const
from functions import Functions

f = Functions()
session = requests.Session()
libs = []
search_dict = image_memory = {}

#preloads images and can set the tkinter image by passing it through tk_image
def set_tk_image(url, ref, tk_image = None):
    try:
        if image_memory.get(url) != None:
            pilImg = image_memory[url]
        else:
            res = session.get(url)
            res.close()
            pilImg = Image.open(io.BytesIO(res.content))
            image_memory[url] = pilImg

        ph_image = itk.PhotoImage(pilImg.resize((math.floor(pilImg.width * ref.winfo_height() / pilImg.height), 
                                                ref.winfo_height())))
        #why does it need to set both image attributes? I will never know
        if tk_image != None:
            tk_image.config(image = ph_image)
            tk_image.image = ph_image
    except Exception as ex:
        print("Error with image" + ex.args[0])
#end_set_tk_image

#fills up image memory from list of image urls
async def populate_image_memory(url_list):
    with ThreadPoolExecutor(max_workers=5) as executor:
        loop = asyncio.get_event_loop()
		#tasks is a list filled with f.dl_mango_image promises for all page urls
        tasks = [
            loop.run_in_executor(
                executor,
                f.download,
                *(session, url)
            )
            for url in url_list
        ]
        for res in await asyncio.gather(*tasks):
            pilImg = Image.open(io.BytesIO(res.content))
            image_memory[res.url] = pilImg
#end_populate_image_memory

#for dex, only works with /title/ paths
def get_chapters(url):
    return parse_url([url], command = const.MAIN_CH)

'''
Format to get from parse_url:
{
    'mango_title': 'Protagonist x Rival',
    'description': "Short yuri manga be...ter",
    'chapter_list': [
        {
            'chapter': '1',
            'id': '601293',
            'group': 'Striptease',
            'site': 'mangadex'
        },
        {
            'chapter': '2',
            'id': '609708',
            'group': 'Striptease',
            'site': 'mangadex'
        },...],
    'cover_url': 'https://mangadex.or...571671229'
}
'''

#uses url_list in case of multichapter downloads. affects retrieving chapters as well
def parse_url(url_list, site = "", command = const.MAIN_DL, disp = None, messagebox = None):
    for lib in libs:
        #makes sure url provided is supported. refer to constants.py for list
        if site.__contains__(lib.SITE) or lib.SITE in url_list[0]:
            #downloads chapter if url to reader was directly provided or through GUI chapter selection
            if command == const.MAIN_DL:
                lib.download(url_list, disp = disp, messagebox = messagebox)
            #returns mango info to display on GUI for user selection
            if command == const.MAIN_CH:
                return lib.get_chapters(url_list[0])
#end_parse_url

def search(site, query):
    for lib in libs:
        if lib.SITE.__contains__(site):
            return lib.search(query)

#imports all library files named in constants file under the site key.
#removes clutter if more sites are added in future
for site in const.DATA["sites"]:
    site = const.DATA["sites"][site]
    file_name = list(site.keys())[0]
    class_name = list(site.values())[0]
    #eg. from dl_dex import Dex
    #    libs.append(Dex())
    exec("from {} import {}".format(file_name, class_name) + 
         "\nlibs.append({}())".format(class_name) + 
         #search_dict => {'Cafe': 'https://hentai.cafe', 'Dex': 'https://mangadex.org', ...}
         "\nsearch_dict[{}.ABBR] = {}.SITE".format(class_name, class_name)
    )
#end_import_loop

#global variables
chapter_list = []
loading = False

#----------------------------------------------------------------------------------------------------------------------#

#KILL MYSELF WITH DESIGNING. or will I?
#GOD IT'S A FUCKING MESS
root = Tk()
root.title("NotCafeDownloader")
root.config(width = 1000, height = 700)
root.resizable(False, False)
root.attributes("-fullscreen", False)

Pmw.initialise(root)

url_frame = Frame(root)
url_frame.pack()

list_frame = Frame(root)
list_frame.pack()

lbl = Label(url_frame, text = "URL: ")
lbl.grid(column = 0, row = 1)

txt_url = Entry(url_frame, width=80)
txt_url.grid(column = 1, row = 1)

btn_url = Button(url_frame, text = "Submit")
btn_url.grid(column = 2, row = 1)

lbl_title = Label(url_frame, text = "")
lbl_title.grid(column = 1, row = 2)

img_thumb = Label(list_frame)
img_thumb.pack(side = "left")

lb_chapters = Listbox(list_frame, selectmode = MULTIPLE, height = 16)
lb_chapters.pack(side = "left", fill = "y")

scrollbar = Scrollbar(list_frame)
scrollbar.config(command = lb_chapters.yview)
scrollbar.pack(side = "right", fill = "y")

lb_chapters.config(yscrollcommand = scrollbar.set)

lbl_progress = Label(root, text = "", anchor = W, justify = LEFT)
lbl_progress.pack()

def btn_url_clicked():
    global loading, chapter_list
    if loading:
        print("It's currently fetching the mango info. Please do not overload the app")
        return
    #prevents url fetching when currently processing a job
    loading = True
    #clears any previous mangoes from listbox
    lb_chapters.delete(0, END)
    data = get_chapters(txt_url.get())

    #on the event an error occurs midway
    if data == False:
        loading = False
        return 

    try:
        title = html.unescape(data["mango_title"])
        description = data["description"]
        chapter_list = data["chapter_list"]
        cover_url = data["cover_url"]

        #formatting, adjusting tooltip width and removing other languages
        #most descriptions use \r and \n to separate languages so it may face complications in some mangoes
        description = html.unescape(description[0:description.find("\r")])
        description = fit_description(description, 120)

        for chapter in chapter_list:
            lb_chapters.insert(END, "   Ch {} | {}   ".format(chapter["chapter"], 
                                             html.unescape(chapter["group"])))
        lbl_title.config(text = title)
        lb_chapters.config(width = 0)
    except Exception as ex:
        print("Error with fetching mango info")
        print(ex)
        loading = False
    
    try:
        set_tk_image(cover_url, lb_chapters, img_thumb)
        balloon = Pmw.Balloon(root)
        balloon.bind(img_thumb, description if description else "Description would've gone here if it existed")
    except Exception as ex:
        print("Error with image: " + ex.args[0])
        loading = False

    root.config(height = 0)
    #reallows url fetching upon finishing
    loading = False
#end_btn_url_clicked

#negative of top down programming
btn_url.config(command = btn_url_clicked)
txt_url.bind("<Return>", lambda e: btn_url_clicked())

#updates label for download progress
def update_lbl(progress):
    lbl_progress.config(text = progress)
    root.update()

#DOESN'T WORK WITH NH YET. DEX AND CAFE WORKS
def btn_chapter_clicked():
    global chapter_list
    chapters_selected = []
    selected = list(lb_chapters.curselection())
    for i in selected:
        chapters_selected.append(chapter_list[i]["id"])
    parse_url(chapters_selected, chapter_list[0]["site"], disp = update_lbl, messagebox = messagebox)
    update_lbl("Downloads for {} completed!".format(lbl_title.cget("text")))

def fit_description(description, width):
    words = description.split(" ")
    temp_str = []
    description = ""
    for word in words:
        temp_str.append(word)
        #adds new line when character limit is exceeded
        if len(" ".join(temp_str)) > width:
            temp_str.pop()
            description += " ".join(temp_str) + "\n"
            temp_str = [word]
        if word == words[-1]:
            description += " ".join(temp_str)
    return description
#end_fit_description

btn_chapter = Button(root, text = "Download Chapter", command=btn_chapter_clicked)
btn_chapter.pack()

txt_url.focus_set()

menubar = Menu(root)

def open_search():
    search_window = Toplevel(root)
    search_window.title("NotCafeDownloader Search")
    search_window.config(height = 600)
    search_window.resizable(height = True, width = True)
    
    search_frame = Frame(search_window)
    search_frame.pack()
    search_bar_frame = Frame(search_frame)
    search_bar_frame.grid(row = 0, column = 0, sticky = W)
    ddl_options = StringVar(root)
    sites = { "Cafe", "Dex", "nH" }
    ddl_options.set("Dex")
    option_site = OptionMenu(search_bar_frame, ddl_options, *sites)
    option_site.grid(row = 0, column = 0)

    txt_search = Entry(search_bar_frame, width=60)
    txt_search.grid(column = 1, row = 0)
    txt_search.focus_set()

    results_frame = Frame(search_frame)
    results_frame.grid(row = 1, column = 0)

    def btn_search_clicked():
        for widget in results_frame.winfo_children():
            widget.destroy()
        short = ddl_options.get()
        results = search(search_dict[short], txt_search.get())

        lb_frame = Frame(results_frame)
        lb_frame.grid(row = 0, column = 0)
        lb_search = Listbox(lb_frame, selectmode = SINGLE, height = 11)
        lb_search.grid(row = 0, column = 0, padx = (10, 0), sticky = E)

        search_y = Scrollbar(lb_frame, orient = VERTICAL)
        search_y.config(command = lb_search.yview)
        search_y.grid(row = 0, column = 1, sticky = NS)
        search_x = Scrollbar(lb_frame, orient = HORIZONTAL)
        search_x.config(command = lb_search.xview)
        search_x.grid(row = 1, column = 0, sticky = EW)

        lb_search.config(xscrollcommand = search_x.set, yscrollcommand = search_y.set, 
                        height = 16, width = 35)

        search_thumb = Label(results_frame)
        search_thumb.grid(row = 0, column = 1)

        lbl_search = Label(results_frame)
        lbl_search.grid(row = 0, column = 2, padx = (0, 10), sticky = N)

        url_list = []

        for i in range(1, len(results) + 1):
            mango = results[str(i)]
            url_list.append(mango["cover_url"])
            lb_search.insert(END, " {} ".format(mango["title"]))
        
        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(populate_image_memory(url_list))
        loop.run_until_complete(future)

        def lb_callback(e, load_url = False):
            res = list(results.values())
            if lb_search.curselection() == ():
                return
            selected_title = lb_search.get(lb_search.curselection()).strip()
            for mango in res:
                if selected_title == mango["title"]:
                    if load_url:
                        txt_url.delete(0, END)
                        txt_url.insert(END, mango["url"])
                        search_window.destroy()
                        btn_url_clicked()
                        return
                    set_tk_image(mango["cover_url"], lb_search, search_thumb)
                    description = mango["description"].strip()
                    description = "No description provided" if description == "" else description
                    lbl_text = "Artist: {}\n\nDescription\n\n{}".format(mango["mangaka"], description) 
                    lbl_search.config(text = lbl_text, wraplength = 300)

        lb_search.bind("<<ListboxSelect>>", lambda e: lb_callback(e))
        lb_search.bind("<Double-Button-1>", lambda e: lb_callback(e, load_url = True))
    #end_btn_search_clicked

    btn_search = Button(search_bar_frame, text = "Search")
    btn_search.grid(column = 2, row = 0)
    btn_search.config(command = btn_search_clicked)
    txt_search.bind("<Return>", lambda event: btn_search_clicked())
#end_open_search

search_menu = Menu(menubar, tearoff = 0)
search_menu.add_command(label = "Search", command = open_search)
menubar.add_cascade(label = "Options", menu = search_menu)

root.config(menu = menubar)
root.mainloop()

#TODO FIX FREEZING WHEN DISPLAYING DOWNLOAD STATUS ON LABEL WITH ASYNC DOWNLOADS
#PRESSING BUTTON FREEZES MAIN THREAD UNTIL IT RETURNS A VALUE