from tkinter import *
from PIL import ImageTk, Image
from io import BytesIO
import requests

#my local files
import constants as const

libs = []

#for dex, only works with /title/ paths
def get_chapters(url):
    return parse_url(url, const.DATA["sites"], command = const.MAIN_CH)

def parse_url(url, data, command = const.MAIN_DL):
    for lib in libs:
        if url.__contains__(lib.SITE):
            if command == const.MAIN_DL:
                lib.download(url)
            if command == const.MAIN_CH:
                return lib.get_chapters(url)
#end_parse_url

#imports all library files named in constants file under the site key.
#removes clutter if more sites are added in future
for site in const.DATA["sites"]:
    site = const.DATA["sites"][site]
    file_name = list(site.keys())[0]
    class_name = list(site.values())[0]
    #eg. from dl_dex import Dex
    #    libs.append(Dex())
    exec("from {} import {}".format(file_name, class_name) + 
         "\nlibs.append({}())".format(class_name))
#end_import_loop

chapter_urls = []

#KILL MYSELF WITH DESIGNING

window = Tk()
window.title("NotCafeDownloader")
window.config(width = 500, height = 400)
window.attributes("-fullscreen", False)

url_frame = Frame(window)
url_frame.pack()

list_frame = Frame(window)
list_frame.pack()

lbl = Label(url_frame, text = "URL: ")
lbl.grid(column = 0, row = 0)

txt_url = Entry(url_frame, width=60)
txt_url.grid(column = 1, row = 0)

img_thumb = Label(list_frame)
img_thumb.pack(side = "left")

lb = Listbox(list_frame, selectmode = SINGLE, height = 16)
lb.pack(side = "left", fill = "y")

scrollbar = Scrollbar(list_frame)
scrollbar.config(command = lb.yview)
scrollbar.pack(side = "right", fill = "y")

lb.config(yscrollcommand = scrollbar.set)

def btn_url_clicked():
    global chapter_urls
    lb.delete(0, END)
    data = get_chapters(txt_url.get())
    title = data["mango_title"]
    chapter_urls = data["chapter_urls"]
    chapter_list = data["chapter_list"]
    thumb_url = data["thumb_url"]

    res = requests.get(thumb_url)
    res.close()
    img_data = res.content
    img = PhotoImage(Image.open(BytesIO(img_data)))
    img_thumb.image = img

    for i in range(0, len(chapter_list)):
        lb.insert("end", "{} - {}".format(chapter_list[i], title))

    lb.config(width = 0)
    window.config(height = 0)

btn_url = Button(url_frame, text = "Submit", command=btn_url_clicked)
btn_url.grid(column = 2, row = 0)

#ONLY CONFIGURED FOR DEX SO FAR
def btn_chapter_clicked():
    id = list(lb.curselection())[0]
    parse_url(chapter_urls[id], const.DATA["sites"])

btn_chapter = Button(window, text = "Download Chapter", command=btn_chapter_clicked)
btn_chapter.pack()   

window.mainloop() 