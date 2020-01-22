from tkinter import *

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

#TODO KILL MYSELF WITH DESIGNING

window = Tk()
window.title("NotCafeDownloader")
window.geometry("500x400")

url_frame = Frame(window)
url_frame.pack()

lbl = Label(url_frame, text = "URL: ")
lbl.grid(column = 0, row = 0)

txt_url = Entry(url_frame, width=60)
txt_url.grid(column = 1, row = 0)

lb = Listbox(window, selectmode = SINGLE)
lb.pack(side = "left", fill = "y")

scrollbar = Scrollbar(window, orient = "vertical")
scrollbar.config(command = lb.yview)
scrollbar.pack(side = "right", fill = "y")

lb.config(yscrollcommand = scrollbar.set)

def btn_url_clicked():
    data = get_chapters(txt_url.get())
    title = data[1]["mango_title"]
    chapters = data[0]
    for i in range(0, len(chapters)):
        lb.insert(i + 1, "{} - {}".format(chapters[i], title))
        id = data[1]["chapters"][i]["id"]
        chapter_urls.append(const.DEX_READER.format(id))
    lb.config(width = 0, height = 0)
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