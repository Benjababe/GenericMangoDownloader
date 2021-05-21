import argparse
import asyncio
import bs4
import html
import json
import math
import os
import pickle
import re
import requests
import sys
import time

from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, quote

#local libs
from template import Template
from functions import Functions
import constants as const

#session > basic requests
session = requests.Session()

# type(chapter/manga), chapter/mango id		eg. /api/chapter/12345
api_format = const.DEX + "/api/v2/{}/{}"
# server, hash, filename						eg. s5.mangadex.org/data/1c94608f80871458ece9f5decdc7481d/X1.png
img_format = "{}/{}/{}"
# action, mango_id, type, UNIX time
# only unfollowing will use "manga_unfollow" for action. The rest will use "manga_follow"
# type => mango_id = unfollow, 1 = reading/follow, 2 = completed, 3 = on hold, 4 = plan to read, 5 = dropped, 6 = plan to read
ajax_format = const.DEX + "/ajax/actions.ajax.php?function={}&id={}&type={}&_={}"

#see functions.py
f = Functions()

#callback on response for requests library
session.hooks["response"] = f.res_hook

#setups script with template of generic functions
dex_template = Template("Please enter MangoDex URL: ", resume_pickle = "dex_resume", cookies_pickle = "dex_cookies")

#file to keep data saver option
data_saver_pickle = const.PICKLE_PATH + "/dex_saver.pckl"

#needed to do ajax calls with mangodex. haven't tried if other methods work with this header
ajax_headers = { "X-Requested-With": "XMLHttpRequest" }

#Dex class is mainly for communicating with __main and gui files and keeping constants
class Dex:
	COMMENT_MANGA = "11"
	COMMENT_CHAPTER = "12"
	SITE = const.DEX
	ABBR = const.DEX_ABBR
	RANDOM = SITE + "/manga"

	# uses POST
	LOGIN = const.DEX_API + "auth/login"

	# use search query
	SEARCH = const.DEX_API + "manga/?title={}&limit=20"

	# use manga id
	FIND_MANGO_ID = const.DEX_API + "chapter/?manga={}&limit=100&translatedLanguage={}"

	# use chapter id
	FIND_CHAPTER_ID = const.DEX_API + "chapter/{}"

	# use group id
	FIND_GROUP_ID = const.DEX_API + "group/{}"

	# use chapter id
	FIND_AT_HOME_URL = const.DEX_API + "at-home/server/{}"

	def __init__(self):
		session.cookies = dex_template.get_pickle(dex_template.cookies_pickle, session.cookies)
		pass

	def get_chapters(self, url, disp = f.empty):
		f.set_disp(disp)
		dex_template.END = dex_template.END_CHAPTER_LIST
		mango_info = dex_parse(url)
		if mango_info == None:
			return False
		chapter_list = []
		for chapter in mango_info["chapters"]:
			chapter_dict = {
				"chapter": chapter["chapter"],
				"group": chapter["group_name"],
				"id": chapter["id"],
				"site": "https://mangadex.org"
			}
			chapter_list.append(chapter_dict)
		ret = {
			"mango_title":  mango_info["mango_title"],
			"description": mango_info["description"],
			"chapter_list": chapter_list,
			"cover_url": mango_info["cover_url"]
		}
		#resets end quota before returning info
		dex_template.END = dex_template.END_RESET
		return ret
	#end_get_chapters

    # disp and messagebox for __main_gui to pass through tkinter elements
	def download(self, id_list, disp = f.empty, messagebox = None):
		f.set_disp(disp)

		# doesn't do anything if id is already put in
		id_list = [self.get_chapter_id(url) for url in id_list]
		check_resume(messagebox = messagebox)
		dex_reader(id_list)

	#gets chapter id from chapter url
	def get_chapter_id(self, url):
		return url.split("/")[-1]

	def search(self, query):
		dex_template.END = dex_template.END_SEARCH
		ret = quick_search(query)
		dex_template.END = dex_template.END_RESET
		return ret
#end_dex_class

#check sort url whether it is the reader or the preview page
def dex_parse(link):
	if type(link) == "str":
		link = link.strip()
	path = urlparse(link).path
	preview_pattern = r"\/title\/[0-9]{0,10}.*"
	reader_pattern = r"\/chapter\/[0-9]{0,10}[\/\\0-9]*"

	preview_match = re.match(preview_pattern, path)
	reader_match = re.match(reader_pattern, path)

	f.disp("Checking out {}".format(link))
	if preview_match and preview_match.span()[1] == len(path):
		mango_id = path.split("/")[2]
		return dex_mango_id_parser(mango_id)
	elif reader_match and reader_match.span()[1] == len(path):
		chapter_id = path.split("/")[2]
		dex_reader([chapter_id])
	if link.lower() == "q":
		sys.exit(0)
	else:
		dex_error()
#end_dex_parse

#handles any reader links
def dex_reader(chapter_ids):
	pending_downloads = { "chapters": [], "mango_title": "" }
	for chapter_id in chapter_ids:
		res = session.get(api_format.format("chapter", chapter_id))
		res.close()
		if not res.status_code == 200:
			print("Problem with retrieving mango info through API. HTTP Status Code of :" + str(res.status_code))
		else:
			json = res.json()
			#sets title if haven't
			if pending_downloads["mango_title"] == "":
				reader_res = session.get(api_format.format("manga", json["manga_id"]))
				pending_downloads["mango_title"] = reader_res.json()["manga"]["title"]
			pending_downloads["chapters"].append({
				"chapter": json["chapter"],
				"id": json["id"]
			})
	dex_download(pending_downloads)
#end_dex_reader

#handles any preview links
def dex_mango_id_parser(mango_id, dl_input = -1):
	api_url = api_format.format("manga", mango_id)
	res = session.get(api_url)
	res.close()
	data = res.json()["data"]
	mango_info = { 
		"mango_id": mango_id, 
		"mango_title": data["title"], 
		"cover_url": data["mainCover"],
		"description": data["description"],
		"chapters": [] 
	}

	# in event there are no chapters at all regardless of language
	try:
		res = session.get(api_url + "/chapters")
		res.close()
		data = res.json()["data"]
		chapters = data["chapters"]
	except KeyError:
		no_chap_found()

	chapter_nums = []
	for chapter in chapters:
		# ensures chapters are in language set and chapters are numbers
		if chapter["language"].lower() in dex_template.LANG and f.is_float(chapter["chapter"]):
			chapter_nums.append(float(chapter["chapter"]))
			mango_info["chapters"].insert(0, chapter)
	#end_for_loop

	chapter_nums.sort()

	# no chapters found in englando or maybe selected language in the future :\
	if len(chapter_nums) == 0:
		no_chap_found()

	# halts operation of the end is the desired chapter listing
	if (dex_template.END == dex_template.END_CHAPTER_LIST):
		return mango_info
	else:
		dex_request_chapters(mango_info, chapter_nums, dl_input)
#end_dex_preview

def no_chap_found():
	print("No chapters found in selected language")
	if dex_template.END == dex_template.END_CHAPTER_LIST:
		return False
	else:
		dex_template.link = ""
		link = dex_template.request_link()
		dex_parse(link)
#end_no_chap_found

# requests user input for which chapters to download
def dex_request_chapters(mango_info, chapter_nums, dl_input = -1):
	str_dl = "Please indicate which chapter(s) to download ({}-{}): "

	# shows first and last chapters in the list
	while dl_input == -1 or dl_input == "":
		dl_input = input(str_dl.format(chapter_nums[0], chapter_nums[-1]))
	dl = dl_input.split("-")

	# single chapter selected
	if len(dl) == 1:
		chapter = [ float(dl[0]) ]

	# multiple chapters selected
	elif len(dl) == 2:
		chapter = [ float(dl[0]), float(dl[1]) ]
	pending_downloads = mango_chapter_filter(mango_info, chapter)
	dex_download(pending_downloads)

#returns what chapters user requested
def mango_chapter_filter(mango_info, chapter):
	def chapter_filter(chapter_info):
		ch = chapter_info["chapter"]

		# only allows 1 chapter number through if only 1 chapter was selected
		if len(chapter) == 1:
			if float(ch) == chapter[0]:
				return True
			else:
				return False

		# allows all chapters in range if given so. eg. if 1-5 was given, every chapter between including 1.2, 2.5 will be returned
		elif len(chapter) == 2:
			min = chapter[0]
			max = chapter[1]
			if float(ch) >= min and float(ch) <= max:
				return True
			else:
				return False
	mango_info["chapters"] = list(filter(chapter_filter, mango_info["chapters"]))
	mango_info = check_mango_duplicates(mango_info)
	return mango_info
#end_manga_info_retriever

#weed out duplicate chapters. SURELY THERE HAS TO BE AN CLEANER OR EASIER WAY WTFF
def check_mango_duplicates(mango_info):
	f.vprint("Checking for chapter duplicates...")
	# to_keep is a list of indexes of mango_info["chapters"] to keep after dupe check, chapter_storage is direct data from mangodex
	to_keep, chapter_storage = [], {}
	# for keeping group names
	groups = {}
	# organising chapters
	for i in range(0, len(mango_info["chapters"])):
		chapter = mango_info["chapters"][i]
		g_id = chapter["groups"][0]
		if not g_id in list(groups.keys()):
			res = session.get(api_format.format("chapter", chapter["id"])).json()
			group_name = res["data"]["groups"][0]["name"]
			groups[g_id] = group_name
		if chapter["chapter"] in chapter_storage:
			chapter_storage[chapter["chapter"]].append(str(i) + "_" + groups[g_id])
		else:
			chapter_storage[chapter["chapter"]] = [str(i) + "_"+ groups[g_id]]
	# goes through every chapter and queries for which translation to keep if there are dupes
	for ch in chapter_storage:
		# if there are duplicate chapters by different sub groups
		if len(chapter_storage[ch]) > 1:
			# indexes keeps the index of the chapter of the mango_info["chapters"] list accordingly
			# eg. indexes[1] = 5, indexes[2] = 6...
			indexes = [""]
			prompt = "There are {} duplicate uploads for chapter {}. Please choose a sub group to download from :\n".format(
				len(chapter_storage[ch]), ch)
			for j in range(0, len(chapter_storage[ch])):
				entry = chapter_storage[ch][j]
				split = entry.split("_")
				indexes.append(int(split[0]))
				if j == 0:
					prompt += "{}.{}(default)\t".format(j + 1, split[1])
				else:
					prompt += "{}.{}\t".format(j + 1, split[1])
			index = input(prompt.strip() + "\tN.Download all: ")
			if index == "": 
				to_keep.append(indexes[1])
			elif index.upper() == "N":
				del indexes[0]
				to_keep += indexes
			else: 
				to_keep.append(indexes[int(index)])
		# no duplicates of chapter
		else:
			entry = chapter_storage[ch][0]
			to_keep.append(int(entry.split("_")[0]))
	# filters chapters by their indexes in to_keep list
	mango_info["chapters"] = [mango_info["chapters"][i] for i in to_keep]
	return mango_info
#end_check_duplicates

def dex_error():
	print("Error with URL provided... (Q to quit)")
	f.disp("Error with URL provided...")
	dex_template.link = ""
	link = dex_template.request_link()
	dex_parse(link)

'''
pending_downloads = {
	"chapters": [
		{
			"chapter": "44",
			"id": "747038"
		},
		{
			"chapter": "44.5",
			"id": "67036"
		}
	],
	"mango_title": "Houseki no Cunny"
}
'''
def dex_download(pending_downloads, resume = False):
	title = pending_downloads["mango_title"]
	chapters = pending_downloads["chapters"]

	# where dl stopped if resume exists
	resume_ch = -1

	# creates temp file
	if not os.path.exists(dex_template.resume_pickle):
		dex_template.update_pickle(dex_template.resume_pickle, [resume_ch, pending_downloads])
	else:
		resume_ch, pending_downloads = dex_template.get_pickle(dex_template.resume_pickle)

	session.cookies = dex_template.get_pickle(dex_template.cookies_pickle, session.cookies)

	# uses index to keep track of what is currently being download for the pickle
	for i in range(0, len(chapters)):
		chapter = chapters[i]
		if i >= resume_ch:
			prepare_chapter_download(title, chapter, [i, pending_downloads])
	#end_chapter_loop
	on_end()
#end_dex_download

def on_end():
	# deletes resume pickle when program ends naturally
	if os.path.exists(dex_template.resume_pickle):
		os.remove(dex_template.resume_pickle)
	print("Download completed")

	# returns after downloads finish. used in GUI and arg_parse
	if dex_template.END == dex_template.END_DOWNLOAD:
		dex_template.END = dex_template.END_RESET
		return
	if __name__ == "__main__":
	# quits app if download was started with an argument D:
		dex_template.restart_app()
#end_end(lol)

# getting all the info needed to download image
def get_chapter_info(ch_data, title):
	'''
	# ends app if chapter isn't available on main site
	if ch_data["status"] == "external":
		print("Mango is currently only available on: {}".format(ch_data["external"]))
		on_end()
	'''

	data = ch_data["data"]["attributes"]

	saver = dex_template.get_pickle(data_saver_pickle, False)
	if saver == True:
		ch_page_array = data["dataSaver"] if saver else data["data"]

	ch_quality = "data-saver" if saver else "data"
	ch_hash = data["hash"]
	ch_title = "Ch. " + data["chapter"].strip() +  (" - " + data["title"] if (data["title"].strip() != "") else "")
	ch_group_id = ""
	ch_group_name = ""

	for item in ch_data["relationships"]:
		if item["type"] == "scanlation_group":
			f.vprint("Fetching group info...")

			ch_group_id = item["id"]
			res = session.get(Dex.FIND_GROUP_ID.format(ch_group_id))
			res.close()
			ch_group_name = json.loads(res.text)["data"]["attributes"]["name"]
			break

	# retrieves MangaDex@Home server url
	res = session.get(Dex.FIND_AT_HOME_URL.format(ch_data["data"]["id"]))
	res.close()
	ch_server = json.loads(res.text)["baseUrl"]

	# creates folder path based off chapter title, chapter name and scanlator
	folder_path = const.DOWNLOAD_PATH + title + "/" + re.sub(r"[\\/:*?\"<>|]", "", "[{}] {}".format(ch_group_name, ch_title)).strip()
	return [ch_server, ch_quality, ch_hash, ch_page_array, ch_title, folder_path]

def prepare_chapter_download(title, chapter, pickle_info):
	f.vprint("Fetching chapter info...")
	res = session.get(Dex.FIND_CHAPTER_ID.format(chapter["id"]))
	res.close()

	if res.ok:
		ch_data = json.loads(res.text)

		loop = asyncio.get_event_loop()
		future = asyncio.ensure_future(dl_chapter_async(title, ch_data))
		# will hold on this line until all downloads in download_async are completed
		loop.run_until_complete(future)

		# marks chapter as read if logged in and indicated so
		if "mark_on_dl" in session.cookies.keys() and session.cookies.get("mark_on_dl"):
			chapter_mark("read", chapter["id"])

		# updates pickle on download status every chapter dl completion
		dex_template.update_pickle(dex_template.resume_pickle, [pickle_info[0], pickle_info[1]])
#end_handle_chapter_download

async def dl_chapter_async(title, ch_data):
	f.vprint("Loading downloads...")
	ch_server, ch_quality, ch_hash, ch_page_array, ch_title, folder_path = get_chapter_info(ch_data, title)
	urls = []
	file_paths = []
	# urls = [img_format.format(ch_server, ch_hash, pg) for pg in ch_page_array]
	display = [ch_title, 0, len(ch_page_array)]

	# creates download folder if doesn't exist
	if not os.path.exists(folder_path):
		os.makedirs(folder_path)

	# file_paths = [(folder_path + "/" + page) for page in ch_page_array]

	for i in range(len(ch_page_array)):
		url = f"{ch_server}/{ch_quality}/{ch_hash}/{ch_page_array[i]}"
		urls.append(url)
		dl_filename = f"{str(i+1)}.{f.get_extension(ch_page_array[i])}"
		file_paths.append(html.unescape(f"{folder_path}/{dl_filename}"))

	# credits to https://bit.ly/2WT52U5
	with ThreadPoolExecutor(max_workers=10) as executor:
		loop = asyncio.get_event_loop()
		#tasks is a list filled with f.dl_mango_image promises for all page urls
		tasks = []
		for i in range(0, len(urls)):
			tasks.append(
				loop.run_in_executor(
					executor,
					f.download,
					*(session, urls[i], file_paths[i], True)
				)
			)

		# below will be called when individual download has been completed.
		# waits for all tasks before ending end_download_async function
		for res in await asyncio.gather(*tasks):
			display[1] += 1
			f.display_download(*display)
#end_download_async

# queries if user wants to continue previous halted dl
def check_resume(messagebox = None):
	dex_template.check_resume(dex_download, messagebox = messagebox)
#end_check_resume

def set_data_saver():
	saver = dex_template.get_pickle(data_saver_pickle, None)
	if saver == None:
		saver = True
	else:
		saver = not saver
	dex_template.update_pickle(data_saver_pickle, saver)
	print("Data saver set to " + str(saver))
	sys.exit(0)
#end_set_data_saver

# remember is true because login is separate from the main runtime
def login(username, password, two_factor = "", remember = 1):
	print("Logging in...")

	res = session.post(Dex.LOGIN, headers = ajax_headers, json = { "username": username, "password": password })
	res.close()
	data = json.loads(res.text)

	# site only spits out text response when there's an error
	if data["result"] == "ok":
		session.cookies = res.cookies

		mark_on_dl = input("Would you like to mark chapters as read when downloaded? (y/N) ").lower()
		if mark_on_dl in ["y", "yes"]:
			mark_on_dl = "True"
		elif mark_on_dl in ["", "n", "no"]:
			mark_on_dl = "False"

		else:
			print("Invalid input, defaulting to no :)")
		session.cookies.set(name = "mark_on_dl", value = mark_on_dl)
		session.cookies.set(name = "session", value = data["token"]["session"])

		# storing login cookies into pickle file
		dex_template.update_pickle(dex_template.cookies_pickle, session.cookies)
		
		print("Login successful")
	else:
		print("Login unsuccessful: {}".format(data["errors"][0]["title"]))
#end_login


def quick_search(query):
	print("Searching for: " + query + "...")
	res = session.get(Dex.SEARCH.format(quote(query)))
	data = json.loads(res.text)

	results = {}
	if len(data["results"]) > 0:
		for i in range(0, len(data["results"])):
			mango_data = data["results"][i]["data"]

			results[str(i+1)] = { 
				"title": html.unescape(mango_data["attributes"]["title"]["en"]), 
				"description": mango_data["attributes"]["description"]["en"], 
				"mango_id": mango_data["id"]
			}
			print("{}. {}".format(i+1, results[str(i+1)]["title"]))

	if dex_template.END == dex_template.END_SEARCH:
		return results
	choice = input("Please choose which mango you wish to download (1-{}): ".format(len(results))).strip()
	dex_get_id(results[choice]["title"], results[choice]["mango_id"])

# chapters are limited to 100
def dex_get_id(title, mango_id):
	url = Dex.FIND_MANGO_ID.format(mango_id, "en")
	res = session.get(url)

	data = json.loads(res.text)
	pending_downloads = {"chapters": [], "mango_title": title}

	for i in range(data["total"]):
		result = data["results"][i]
		chapter_data = {
			"chapter": result["data"]["attributes"]["chapter"],
			"id": result["data"]["id"]
		}
		pending_downloads["chapters"].append(chapter_data)

	res.close()
	dex_download(pending_downloads)
#end_dex_get_id

def random():
	res = session.get(Dex.RANDOM)
	soup = BeautifulSoup(res.text, "html.parser")
	link = soup.find("link", rel = "canonical")
	title = link.find("title")
	title =  "" if (title == None) else title.text
	print("You have randomed: " + title + " URL: " + link["href"])
	dex_parse(link["href"])
# end_random

def dex_ajax_call(action, _id, _type = 1, time = str(math.floor(time.time())), data = {}):
	url = ajax_format.format(action, _id, _type, time)
	print("\nProcessing GET request for URL: " + url)

	res = session.get(url, headers = ajax_headers, data = data)
	res.close()

	if res.ok:
		f.vprint("Action completed...")
		if not res.text == "":
			f.vprint(res.text)
	else:
		f.vprint("Error with your request")
		print(str(res.status_code) + " " + res.text)
#end_dex_ajax_call

# action has to be either "read" or "unread"
def chapter_mark(action, chapter_id):
	dex_ajax_call("chapter_mark_" + action, chapter_id)
#end_chapter_mark

def create_comment_thread(ajax_id, chapter_id):
	# type = 11 for manga comments, 12 for chapter comments
	create_thread_uri = "https://mangadex.org/ajax/actions.ajax.php?function=start_empty_thread&id=" + ajax_id

	#type value = 1 for manga thread, 3 for chapter thread.
	res = session.post(create_thread_uri, headers = ajax_headers, data = {
		"type": 3 if (ajax_id == Dex.COMMENT_CHAPTER) else 1, 
		"type_id": str(chapter_id)
	})
	if res.text == "":
		f.vprint("Thread created")
		return True
	return False
#end_create_comment_thread

def comment(ajax_id, _id, text):
	url = Dex.SITE
	# flag = 11 for manga, 12 for chapter
	if ajax_id == Dex.COMMENT_MANGA:
		url += "/title/{}/filler/comments".format(_id)
	elif ajax_id == Dex.COMMENT_CHAPTER:
		# filler can be anything. server doesn't care
		url += "/chapter/{}/comments".format(_id)
	data = { "text": text }
	res = session.get(url)
	res.close()
	soup = BeautifulSoup(res.content, "html.parser")

	# finding if thread exists
	btn = soup.find("button", {"id": "post_reply_button"})
	if btn == None:
		input_str = "There is no comment thread for this {}. Would you like to create one? (Y/n) ".format(\
			"manga" if ajax_id == Dex.COMMENT_MANGA else "chapter")
		create = input(input_str).lower()
		if create in ["", "y", "yes"]:
			x = create_comment_thread(ajax_id, _id)
			# gives a second for thread creation
			time.sleep(1)
			# re-retrieving comment page for thread id
			if x:
				res = session.get(url)
				res.close()
				soup = BeautifulSoup(res.content, "html.parser")
			else:
				print("Thread creation failed. Are you currently logged in?")
				return
		else:
			return
	# everything below is some hardcoding shit. any change in dex will ruin it
	# finding comment thread id -> posting comment
	js = res.text

	# looking for script text in the html " var button = $("#post_reply_button") "
	# it will only exist if logged in
	x = js.find("#post_reply_button")
	if x == -1:
		print("Error with comment creation. Are you currently logged in?")
	elif x > 0:
		js = js[x:]
		key_start = js.find("url: '")

		# I want the start of the value instead of the key
		js = js[key_start + len("url: '"):]
		reply_path = js[0:js.find("'")]
		reply_uri = Dex.SITE + reply_path
		res = session.post(reply_uri, headers = ajax_headers, data = data)
		if res.ok and res.text == "":
			print("Comment successfully posted")
			return

		# problems with posting comment. only one I know of is if your account is too new / commenting too recently
		else:
			#soup to remove html tags from text attribute
			soup = BeautifulSoup(res.text, "html.parser")
			print(soup.text)
#end_comment

def set_language(lang = "idk_fam", default = False):
	lang_dict = dex_template.get_pickle(dex_template.site_info_pickle)
	# run from main, getting language set or defaulting to englando
	if default:
		if len(lang_dict["dex"]["user_language"]) > 0:
			dex_template.LANG = lang_dict["dex"]["user_language"]
		return
	user_language, added, prompt, index = None, False, "", 1
	while(user_language == None):
		reset = input("Do you want to clear all saved languages? (Y/n) ").lower()
		if reset in ["y", "yes", ""]:
			user_language = []
		elif reset in ["n", "no"]:
			user_language = lang_dict["dex"]["user_language"]
	languages = lang_dict["dex"]["language_list"]
	for language in languages:
		if language[0].lower() == lang.lower() or language[1].lower() == lang.lower():
			user_language.append(language[0])
			print("Set language: " + language[1])
			added = True
		prompt += "{}. {}\t".format(str(index), language[1])
		prompt += "\n" if (index % 4 == 0 and index > 3) else ""
		index += 1
	if not added:
		print("No languages have been added yet... please choose from the displayed below:\n")
		lang_input = input(prompt + "\nSeparate each selection with a [space] (1-" + str(len(languages)) + "): ")
		nums = lang_input.split(" ")
		for num in nums:
			if not num.isnumeric():

				# resets language setting
				print("The numbers only please...")
				set_language(lang, default)
				return
			user_language.append(languages[int(num) - 1][0])
			print("Set language: " + languages[int(num) - 1][1])
	lang_dict["dex"]["user_language"] = user_language
	dex_template.update_pickle(dex_template.site_info_pickle, lang_dict)
#end_set_language

#actual cancer to format out
def check_args():
	manga_status_list = ["u", "f", "c", "h", "p", "d", "r"]
	# sets max length of printout 100 chars
	parser = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=100))
	parser.add_argument("-V", "--verbose", action="store_true", dest="verbose", help="Increase output verbosity")
	parser.add_argument("-DS", "--data-saver", action="store_true", dest="d_saver", help="Downloads compressed images instead")
	
	# login will take priority over all others
	parser.add_argument("-L", "--login", nargs="*", dest="login_data", help="Passes through username, password and 2FA to login")
	parser.add_argument("-QS", "--quick-search", metavar="query", dest="qsearch", help="Searches the MangoDex database for your query")
	parser.add_argument("-RD", "--random", action="store_true", dest="random", help="Returns a random mango")
	parser.add_argument("-LANG", "--language", dest="lang", nargs="?", metavar="lang_code", const="idk_fam", help="Sets language for mango reading")
	parser.add_argument("-DL", "--download", metavar="url", dest="url", help="Downloads by mango provided by the URL")

	parser.add_argument("-U", "--unfollow", metavar="mango_id", dest="u_func", help="Unfollows mango by ID")
	parser.add_argument("-F", "--follow", metavar="mango_id", dest="f_func", help="Adds mango to follow list by ID")
	parser.add_argument("-C", "--complete", metavar="mango_id", dest="c_func", help="Adds mango to complete list by ID")
	parser.add_argument("-H", "--hold", metavar="mango_id", dest="h_func", help="Adds mango to on-hold list by ID")
	parser.add_argument("-P", "--plan-to-read", metavar="mango_id", dest="p_func", help="Adds mango to plan to read list by ID")
	parser.add_argument("-D", "--drop", metavar="mango_id", dest="d_func", help="Adds mango to dropped list by ID")
	parser.add_argument("-R", "--reread", metavar="mango_id", dest="r_func", help="Adds mango to rereading list by ID")

	parser.add_argument("-MR", "--mark-read", metavar="chapter_id", dest="mr_func", help="Marks chapter as read by ID")
	parser.add_argument("-MU", "--mark-unread", metavar="chapter_id", dest="mu_func", help="Marks chapter as unread by ID")
	parser.add_argument("-CMM", "--comment-manga", nargs=2, metavar=("manga_id", "comment_string"), dest="cm_mnga_func", 
						help="Adds comment into manga thread, creates new thread if non-existent")
	parser.add_argument("-CMC", "--comment-chapter", nargs=2, metavar=("chapter_id", "comment_string"), dest="cm_chpt_func", 
						help="Adds comment into chapter thread, creates new thread if non-existent")

	exit_after_running = False

	for arg in parser.parse_args().__dict__:
		global f

		# checks through values for each argument for non empty ones
		val = parser.parse_args().__dict__[arg]
		if val == True:
			if arg == "verbose":
				f.set_v(val)
			elif arg == "d_saver":
				set_data_saver()
			elif arg == "random":
				exit_after_running = True
				dex_template.END = dex_template.END_DOWNLOAD
				random()

		# type(val)==list is for login and language
		elif type(val) is str or type(val) is list:

			# exits after running single use functions except for verbose
			exit_after_running = True

			# download
			if arg == "lang":
				set_language(val)
			if arg == "qsearch":
				dex_template.END = dex_template.END_DOWNLOAD
				quick_search(val)
			if arg == "url":
				dex_template.END = dex_template.END_DOWNLOAD
				dex_parse(val)
			if arg == "login_data":
				# the * is to spread the list into the method
				login(*val)
			elif arg.split("_")[0] in manga_status_list:
				_type = manga_status_list.index(arg[0])
				if _type == 0:
					dex_ajax_call("manga_unfollow", val, val)
				else:
					dex_ajax_call("manga_follow", val, _type)
			elif arg[0:7] == "cm_mnga":
				comment(Dex.COMMENT_MANGA, val[0], val[1])
			elif arg[0:7] == "cm_chpt":
				comment(Dex.COMMENT_CHAPTER ,val[0], val[1])
			elif arg[0:2] == "mr" or arg[0:2] == "mu":
				mark = "read" if arg[0:2] == "mr" else "unread"
				chapter_mark(mark, val)
	if exit_after_running:
		sys.exit(0)
#end_check_args


#only runs this snippet if ran by dl_dex.py
if __name__ == "__main__":

	# dex_parse runs immediately after user URL input
	# honestly can't remember why it had to be done like this.
	# it was initially for the app to continue running in the main file but idk anymore
	dex_template.set_post_request(dex_parse)

	# sets any languages given through --languages argument
	set_language(default = True)

	# checks if session cookies exist
	session.cookies = dex_template.get_pickle(dex_template.cookies_pickle, session.cookies)

	# runs through list of preset arguments
	check_args()

	#checks if resume.pckl exists
	check_resume()

	# app runs, starts by requesting link
	link = dex_template.request_link()
	dex_parse(link)