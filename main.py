import os
import sys
import duckduckpy
import time
from datetime import date
import text2pdf
import threading
import bs4
import requests
import urllib.request
import json
import random
from random import uniform
from pprint import pprint
from gtts import gTTS, lang
from youtube_search import YoutubeSearch
from google_trans_new import google_translator
from json import dumps, load
from time import sleep
from io import BytesIO
from string import hexdigits
from string import punctuation
from random import choice, randint, sample
from pathlib import Path
from threading import Thread
from contextlib import suppress
from unicodedata import normalize

from pdf2image import convert_from_path
from youtube_dl import YoutubeDL
from amino.client import Client
from amino.sub_client import SubClient

# Big optimisation thanks to SempreLEGIT#1378 ♥
version = "1.6.3"
print(f"version : {version}")

path_utilities = "utilities"
path_amino = 'utilities/amino_list'
path_picture = 'utilities/pictures'
path_sound = 'utilities/sound'
path_download = 'utilities/download'
path_config = "utilities/config.json"
path_client = "client.txt"

for i in (path_utilities, path_picture, path_sound, path_download, path_amino):
	Path(i).mkdir(exist_ok=True)


class BotAmino:
	def __init__(self, client, community, inv: str = None):
		self.client = client
		self.lvl_min = 0
		self.marche = True

		if isinstance(community, int):
			self.community_id = community
			self.community = self.client.get_community_info(
			    comId=self.community_id)
			self.community_amino_id = self.community.aminoId
		else:
			self.community_amino_id = community
			self.informations = self.client.get_from_code(
			    f"http://aminoapps.com/c/{community}")
			self.community_id = self.informations.json["extensions"][
			    "community"]["ndcId"]
			self.community = self.client.get_community_info(
			    comId=self.community_id)

		self.community_name = self.community.name
		try:
			self.community_leader_agent_id = self.community.json["agent"][
			    "uid"]
		except Exception:
			self.community_leader_agent_id = "-"

		try:
			self.community_staff_list = self.community.json[
			    "communityHeadList"]
		except Exception:
			self.community_staff_list = ""

		if self.community_staff_list:
			self.community_leaders = [
			    elem["uid"] for elem in self.community_staff_list
			    if elem["role"] in (100, 102)
			]
			self.community_curators = [
			    elem["uid"] for elem in self.community_staff_list
			    if elem["role"] == 101
			]
			self.community_staff = [
			    elem["uid"] for elem in self.community_staff_list
			]

		if not Path(f'{path_amino}/{self.community_amino_id}.json').exists():
			self.create_community_file()

		old_dict = self.get_file_dict()
		new_dict = self.create_dict()

		for key, value in new_dict.items():
			if key not in old_dict:
				old_dict[key] = value

		for key, value in old_dict.items():
			if key not in new_dict:
				del old_dict[key]

		self.update_file(old_dict)

		self.subclient = SubClient(comId=self.community_id,
		                           profile=client.profile)
		self.banned_words = self.get_file_info("banned_words")
		self.message_bvn = self.get_file_info("welcome")
		self.locked_command = self.get_file_info("locked_command")
		self.admin_locked_command = self.get_file_info("admin_locked_command")
		self.welcome_chat = self.get_file_info("welcome_chat")
		self.only_view = self.get_file_info("only_view")
		self.prefix = self.get_file_info("prefix")
		self.level = self.get_file_info("level")
		self.favorite_users = self.get_file_info("favorite_users")
		self.favorite_chats = self.get_file_info("favorite_chats")
		self.subclient.activity_status("on")
		new_users = self.subclient.get_all_users(start=0,
		                                         size=30,
		                                         type="recent")
		self.new_users = [
		    elem["uid"] for elem in new_users.json["userProfileList"]
		]
		if self.welcome_chat or self.message_bvn:
			with suppress(Exception):
				Thread(target=self.check_new_member).start()

	def create_community_file(self):
		with open(f'{path_amino}/{self.community_amino_id}.json',
		          'w',
		          encoding='utf8') as file:
			dict = self.create_dict()
			file.write(dumps(dict, sort_keys=False, indent=4))

	def create_dict(self):
		return {
		    "welcome": "",
		    "banned_words": [],
		    "locked_command": [],
		    "admin_locked_command": [],
		    "prefix": "*",
		    "only_view": [],
		    "welcome_chat": "",
		    "level": 0,
		    "favorite_users": [],
		    "favorite_chats": []
		}

	def get_dict(self):
		return {
		    "welcome": self.message_bvn,
		    "banned_words": self.banned_words,
		    "locked_command": self.locked_command,
		    "admin_locked_command": self.admin_locked_command,
		    "prefix": self.prefix,
		    "only_view": self.only_view,
		    "welcome_chat": self.welcome_chat,
		    "level": self.level,
		    "favorite_users": self.favorite_users,
		    "favorite_chats": self.favorite_chats
		}

	def update_file(self, dict=None):
		if not dict:
			dict = self.get_dict()
		with open(f"{path_amino}/{self.community_amino_id}.json",
		          "w",
		          encoding="utf8") as file:
			file.write(dumps(dict, sort_keys=False, indent=4))

	def get_file_info(self, info: str = None):
		with open(f"{path_amino}/{self.community_amino_id}.json",
		          "r",
		          encoding="utf8") as file:
			return load(file)[info]

	def get_file_dict(self, info: str = None):
		with open(f"{path_amino}/{self.community_amino_id}.json",
		          "r",
		          encoding="utf8") as file:
			return load(file)

	def set_prefix(self, prefix: str):
		self.prefix = prefix
		self.update_file()

	def set_level(self, level: int):
		self.level = level
		self.update_file()

	def set_welcome_message(self, message: str):
		self.message_bvn = message.replace('"', '“')
		self.update_file()

	def set_welcome_chat(self, chatId: str):
		self.welcome_chat = chatId
		self.update_file()

	def add_locked_command(self, liste: list):
		self.locked_command.extend(liste)
		self.update_file()

	def add_admin_locked_command(self, liste: list):
		self.admin_locked_command.extend(liste)
		self.update_file()

	def add_banned_words(self, liste: list):
		self.banned_words.extend(liste)
		self.update_file()

	def add_only_view(self, chatId: str):
		self.only_view.append(chatId)
		self.update_file()

	def add_favorite_users(self, value: str):
		self.favorite_users.append(value)
		self.update_file()

	def add_favorite_chats(self, value: str):
		self.favorite_chats.append(value)
		self.update_file()

	def remove_locked_command(self, liste: list):
		[
		    self.locked_command.remove(elem) for elem in liste
		    if elem in self.locked_command
		]
		self.update_file()

	def remove_admin_locked_command(self, liste: list):
		[
		    self.admin_locked_command.remove(elem) for elem in liste
		    if elem in self.admin_locked_command
		]
		self.update_file()

	def remove_banned_words(self, liste: list):
		[
		    self.banned_words.remove(elem) for elem in liste
		    if elem in self.banned_words
		]
		self.update_file()

	def remove_favorite_users(self, value: str):
		liste = [value]
		[
		    self.favorite_users.remove(elem) for elem in liste
		    if elem in self.favorite_users
		]
		self.update_file()

	def remove_favorite_chats(self, value: str):
		liste = [value]
		[
		    self.favorite_chats.remove(elem) for elem in liste
		    if elem in self.favorite_chats
		]
		self.update_file()

	def remove_only_view(self, chatId: str):
		self.only_view.remove(chatId)
		self.update_file()

	def unset_welcome_chat(self):
		self.welcome_chat = ""
		self.update_file()

	def is_in_staff(self, uid):
		return uid in self.community_staff

	def is_leader(self, uid):
		return uid in self.community_leaders

	def is_curator(self, uid):
		return uid in self.community_curators

	def is_agent(self, uid):
		return uid == self.community_leader_agent_id

	def accept_role(self, rid: str = None, cid: str = None):
		with suppress(Exception):
			self.subclient.accept_organizer(cid)
			return True
		with suppress(Exception):
			self.subclient.promotion(noticeId=rid)
			return True
		return False

	def get_staff(self, community):
		if isinstance(community, int):
			with suppress(Exception):
				community = self.client.get_community_info(com_id=community)
		else:
			try:
				informations = self.client.get_from_code(
				    f"http://aminoapps.com/c/{community}")
			except Exception:
				return False

			community_id = informations.json["extensions"]["community"][
			    "ndcId"]
			community = self.client.get_community_info(comId=community_id)

		try:
			community_staff_list = community.json["communityHeadList"]
			community_staff = [elem["uid"] for elem in community_staff_list]
		except Exception:
			community_staff_list = ""
		else:
			return community_staff

	def get_user_id(self, user_name):
		size = self.subclient.get_all_users(
		    start=0, size=1, type="recent").json['userProfileCount']
		size2 = size

		st = 0
		while size > 0:
			value = size
			if value > 100:
				value = 100

			users = self.subclient.get_all_users(start=st, size=value)
			for user in users.json['userProfileList']:
				if user_name == user['nickname'] or user_name == user['uid']:
					return (user["nickname"], user['uid'])
			size -= 100
			st += 100

		size = size2

		st = 0
		while size > 0:
			value = size
			if value > 100:
				value = 100

			users = self.subclient.get_all_users(start=st, size=value)
			for user in users.json['userProfileList']:
				if user_name.lower() in user['nickname'].lower():
					return (user["nickname"], user['uid'])
			size -= 100
			st += 100

		return False

	def ask_all_members(self, message, lvl: int = 20, type_bool: int = 1):
		size = self.subclient.get_all_users(
		    start=0, size=1, type="recent").json['userProfileCount']
		st = 0

		while size > 0:
			value = size
			if value > 100:
				value = 100
			users = self.subclient.get_all_users(start=st, size=value)
			if type_bool == 1:
				user_lvl_list = [
				    user['uid'] for user in users.json['userProfileList']
				    if user['level'] == lvl
				]
			elif type_bool == 2:
				user_lvl_list = [
				    user['uid'] for user in users.json['userProfileList']
				    if user['level'] <= lvl
				]
			elif type_bool == 3:
				user_lvl_list = [
				    user['uid'] for user in users.json['userProfileList']
				    if user['level'] >= lvl
				]
			self.subclient.start_chat(userId=user_lvl_list, message=message)
			size -= 100
			st += 100

	def ask_amino_staff(self, message):
		self.subclient.start_chat(userId=self.community_staff, message=message)

	def get_chat_id(self, chat: str = None):
		with suppress(Exception):
			return self.subclient.get_from_code(
			    f"http://aminoapps.com/c/{chat}").objectId

		val = self.subclient.get_public_chat_threads(size=50)
		for title, chat_id in zip(val.title, val.chatId):
			if chat == title:
				return chat_id
		for title, chat_id in zip(val.title, val.chatId):
			if chat.lower() in title.lower() or chat == chat_id:
				return chat_id
		return False

	def stop_instance(self):
		self.marche = False

	def leave_community(self):
		self.client.leave_community(comId=self.community_id)
		self.marche = False
		for elem in self.subclient.get_public_chat_threads().chatId:
			with suppress(Exception):
				self.subclient.leave_chat(elem)

	def check_new_member(self):
		if not (self.message_bvn and self.welcome_chat):
			return
		new_list = self.subclient.get_all_users(start=0,
		                                        size=25,
		                                        type="recent")
		new_member = [(elem["nickname"], elem["uid"])
		              for elem in new_list.json["userProfileList"]]
		for elem in new_member:
			name, uid = elem[0], elem[1]
			try:
				val = self.subclient.get_wall_comments(
				    userId=uid, sorting='newest').commentId
			except Exception:
				val = True

			if not val and self.message_bvn:
				with suppress(Exception):
					self.subclient.comment(message=self.message_bvn,
					                       userId=uid)
			if not val and self.welcome_chat:
				with suppress(Exception):
					self.send_message(chatId=self.welcome_chat,
					                  message=f"Welcome here ‎‏‎‏@{name}!‬‭",
					                  mentionUserIds=[uid])

		new_users = self.subclient.get_all_users(start=0,
		                                         size=30,
		                                         type="recent")
		self.new_users = [
		    elem["uid"] for elem in new_users.json["userProfileList"]
		]

	def welcome_new_member(self):
		new_list = self.subclient.get_all_users(start=0,
		                                        size=25,
		                                        type="recent")
		new_member = [(elem["nickname"], elem["uid"])
		              for elem in new_list.json["userProfileList"]]

		for elem in new_member:
			name, uid = elem[0], elem[1]

			try:
				val = self.subclient.get_wall_comments(
				    userId=uid, sorting='newest').commentId
			except Exception:
				val = True

			if not val and uid not in self.new_users and self.message_bvn:
				with suppress(Exception):
					self.subclient.comment(message=self.message_bvn,
					                       userId=uid)

			if uid not in self.new_users and self.welcome_chat:
				with suppress(Exception):
					self.send_message(chatId=self.welcome_chat,
					                  message=f"Welcome here ‎‏‎‏@{name}!‬‭",
					                  mentionUserIds=[uid])

		new_users = self.subclient.get_all_users(start=0,
		                                         size=30,
		                                         type="recent")
		self.new_users = [
		    elem["uid"] for elem in new_users.json["userProfileList"]
		]

	def feature_chats(self):
		for elem in self.favorite_chats:
			with suppress(Exception):
				self.favorite(time=2, userId=elem)

	def feature_users(self):
		featured = [
		    elem["uid"] for elem in
		    self.subclient.get_featured_users().json["userProfileList"]
		]
		for elem in self.favorite_users:
			if elem not in featured:
				with suppress(Exception):
					self.favorite(time=1, userId=elem)

	def get_member_level(self, uid):
		return self.subclient.get_user_info(userId=uid).level

	def is_level_good(self, uid):
		return self.subclient.get_user_info(userId=uid).level >= self.level

	def get_member_titles(self, uid):
		with suppress(Exception):
			return self.subclient.get_user_info(userId=uid).customTitles
		return False

	def get_member_info(self, uid):
		return self.subclient.get_user_info(userId=uid)

	def get_message_info(self, chatId=None, messageId=None):
		return self.subclient.get_message_info(chatId=chatId,
		                                       messageId=messageId)

	def get_wallet_info(self):
		return self.client.get_wallet_info().json

	def ban(self, userId: str, reason: str, banType: int = None):
		self.subclient.ban(userId, reason, banType)

	def get_wallet_amount(self):
		return self.client.get_wallet_info().totalCoins

	def pay(self,
	        coins: int = 0,
	        blogId: str = None,
	        chatId: str = None,
	        objectId: str = None,
	        transactionId: str = None):
		if not transactionId:
			transactionId = f"{''.join(sample([lst for lst in hexdigits[:-6]], 8))}-{''.join(sample([lst for lst in hexdigits[:-6]], 4))}-{''.join(sample([lst for lst in hexdigits[:-6]], 4))}-{''.join(sample([lst for lst in hexdigits[:-6]], 4))}-{''.join(sample([lst for lst in hexdigits[:-6]], 12))}"
		self.subclient.send_coins(coins=coins,
		                          blogId=blogId,
		                          chatId=chatId,
		                          objectId=objectId,
		                          transactionId=transactionId)

	def edit_chat(self,
	              chatId: str,
	              doNotDisturb: bool = None,
	              pinChat: bool = None,
	              title: str = None,
	              icon: str = None,
	              backgroundImage: str = None,
	              content: str = None,
	              announcement: str = None,
	              coHosts: list = None,
	              keywords: list = None,
	              pinAnnouncement: bool = None,
	              publishToGlobal: bool = None,
	              canTip: bool = None,
	              viewOnly: bool = None,
	              canInvite: bool = None,
	              fansOnly: bool = None):
		self.subclient.edit_chat(chatId, doNotDisturb, pinChat, title, icon,
		                         backgroundImage, content, announcement,
		                         coHosts, keywords, pinAnnouncement,
		                         publishToGlobal, canTip, viewOnly, canInvite,
		                         fansOnly)

	def get_message_level(self, level: int):
		return f"You need the level {level} to do this command"

	def delete_message(self,
	                   chatId: str,
	                   messageId: str,
	                   reason: str = "Clear",
	                   asStaff: bool = False):
		self.subclient.delete_message(chatId, messageId, asStaff, reason)

	def kick(self, userId: str, chatId: str, allowRejoin: bool = True):
		self.subclient.kick(userId, chatId, allowRejoin)

	def edit_profile(self,
	                 nickname: str = None,
	                 content: str = None,
	                 icon: str = None,
	                 chatRequestPrivilege: str = None,
	                 mediaList: list = None,
	                 backgroundImage: str = None,
	                 backgroundColor: str = None,
	                 titles: list = None,
	                 defaultBubbleId: str = None):
		self.subclient.edit_profile(nickname, content, icon,
		                            chatRequestPrivilege, mediaList,
		                            backgroundImage, backgroundColor, titles,
		                            defaultBubbleId)

	def send_message(self,
	                 chatId: str = None,
	                 message: str = "None",
	                 messageType: str = None,
	                 file: str = None,
	                 fileType: str = None,
	                 replyTo: str = None,
	                 mentionUserIds: str = None):
		self.subclient.send_message(chatId=chatId,
		                            message=message,
		                            file=file,
		                            fileType=fileType,
		                            replyTo=replyTo,
		                            messageType=messageType,
		                            mentionUserIds=mentionUserIds)

	def favorite(self,
	             time: int = 1,
	             userId: str = None,
	             chatId: str = None,
	             blogId: str = None,
	             wikiId: str = None):
		self.subclient.feature(time=time,
		                       userId=userId,
		                       chatId=chatId,
		                       blogId=blogId,
		                       wikiId=wikiId)

	def unfavorite(self,
	               userId: str = None,
	               chatId: str = None,
	               blogId: str = None,
	               wikiId: str = None):
		self.subclient.unfeature(userId=userId,
		                         chatId=chatId,
		                         blogId=blogId,
		                         wikiId=wikiId)

	def join_chat(self, chat: str, chatId: str = None):
		chat = chat.replace("http:aminoapps.com/p/", "")
		if not chat:
			with suppress(Exception):
				self.subclient.join_chat(chatId)
				return ""

			with suppress(Exception):
				chati = self.subclient.get_from_code(
				    f"http://aminoapps.com/c/{chat}").objectId
				self.subclient.join_chat(chati)
				return chat

		chats = self.subclient.get_public_chat_threads()
		for title, chat_id in zip(chats.title, chats.chatId):
			if chat == title:
				self.subclient.join_chat(chat_id)
				return title

		chats = self.subclient.get_public_chat_threads()
		for title, chat_id in zip(chats.title, chats.chatId):
			if chat.lower() in title.lower() or chat == chat_id:
				self.subclient.join_chat(chat_id)
				return title

		return False

	def get_chats(self):
		return self.subclient.get_public_chat_threads()

	def join_all_chat(self):
		for elem in self.subclient.get_public_chat_threads(size=50).chatId:
			with suppress(Exception):
				self.subclient.join_chat(elem)

	def leave_chat(self, chat: str):
		self.subclient.leave_chat(chat)

	def leave_all_chats(self):
		for elem in self.subclient.get_public_chat_threads(size=100).chatId:
			with suppress(Exception):
				self.subclient.leave_chat(elem)

	def follow_user(self, uid):
		self.subclient.follow(userId=[uid])

	def unfollow_user(self, uid):
		self.subclient.unfollow(userId=uid)

	def add_title(self, uid, title: str, color: str = None):
		member = self.get_member_titles(uid)
		tlist = []
		clist = []
		with suppress(Exception):
			tlist = [elem['title'] for elem in member]
			clist = [elem['color'] for elem in member]
		tlist.append(title)
		clist.append(color)

		with suppress(Exception):
			self.subclient.edit_titles(uid, tlist, clist)
		return True

	def remove_title(self, uid, title: str):
		member = self.get_member_titles(uid)
		tlist = []
		clist = []
		for elem in member:
			tlist.append(elem["title"])
			clist.append(elem["color"])

		if title in tlist:
			nb = tlist.index(title)
			tlist.pop(nb)
			clist.pop(nb)
			self.subclient.edit_titles(uid, tlist, clist)
		return True

	def passive(self):
		i = 30
		j = 470
		k = 7170
		m = 86370
		o = 0
		activities = [
		    f"{self.prefix}𝑼 𝒔𝒐𝒖𝒏𝒅𝒔 𝒃𝒆𝒕𝒕𝒆𝒓 𝒘𝒊𝒕𝒉 𝒚𝒐𝒖𝒓 𝒎𝒐𝒖𝒕𝒉 𝒄𝒍𝒐𝒔𝒆𝒅",
		    "𝑼 𝒔𝒐𝒖𝒏𝒅𝒔 𝒃𝒆𝒕𝒕𝒆𝒓 𝒘𝒊𝒕𝒉 𝒚𝒐𝒖𝒓 𝒎𝒐𝒖𝒕𝒉 𝒄𝒍𝒐𝒔𝒆𝒅",
		    f"{self.prefix}𝑩𝒐𝒐𝒃𝒔 𝒂𝒓𝒆 𝒕𝒉𝒆 𝒑𝒓𝒐𝒐𝒇 𝒕𝒉𝒂𝒕 𝒎𝒂𝒏 𝒄𝒂𝒏 𝒇𝒐𝒄𝒖𝒔 𝒐𝒏 𝒕𝒘𝒐 𝒕𝒉𝒊𝒏𝒈𝒔 𝒂𝒕 𝒐𝒏𝒄𝒆"
		]
		while self.marche:
			if i >= 60:
				if self.welcome_chat or self.message_bvn:
					Thread(target=self.welcome_new_member).start()
				with suppress(Exception):
					self.subclient.activity_status('on')
				i = 0
				o += 1
				if o > len(activities) - 1:
					o = 0
			if j >= 500:
				if self.welcome_chat or self.message_bvn:
					with suppress(Exception):
						Thread(target=self.check_new_member).start()
				j = 0

			if k >= 7200 and self.favorite_chats:
				with suppress(Exception):
					Thread(target=self.feature_chats).start()
				k = 0

			if m >= 86400 and self.favorite_users:
				with suppress(Exception):
					Thread(target=self.feature_users).start()
				m = 0

			k += 10
			m += 10
			j += 10
			i += 10

			sleep(10)

	def run(self):
		Thread(target=self.passive).start()


def is_it_bot(uid):
	return uid == botId


def is_it_me(uid):
	return uid in ('d656e556-57ba-4f69-8c1c-07848e7800d8',
	               'e123f164-2e43-4ec7-96ee-36c121977f9e')


def is_it_admin(uid):
	return uid in perms_list


def join_community(comId: str = None, inv: str = None):
	with suppress(Exception):
		client.join_community(comId=comId, invitationId=inv)
		return 1

	if inv:
		with suppress(Exception):
			client.request_join_community(comId=comId,
			                              message='ass for everyone!!')
			return 2


def join_amino(subClient=None,
               chatId=None,
               authorId=None,
               author=None,
               message=None,
               messageId=None):
	invit = None
	if taille_commu >= 20 and not (is_it_me(authorId)
	                               or is_it_admin(authorId)):
		subClient.send_message(chatId,
		                       "The bot has joined too many communities!")
		return

	staff = subClient.get_staff(message)
	if not staff:
		subClient.send_message(chatId, "Wrong amino ID!")
		return

	try:
		test = message.strip().split()
		amino_c = test[0]
		invit = test[1]
		invit = invit.replace("http://aminoapps.com/invite/", "")
	except Exception:
		amino_c = message
		invit = None

	try:
		val = subClient.client.get_from_code(
		    f"http://aminoapps.com/c/{amino_c}")
		comId = val.json["extensions"]["community"]["ndcId"]
	except Exception:
		val = ""

	isJoined = val.json["extensions"]["isCurrentUserJoined"]
	if not isJoined:
		join_community(comId, invit)
		val = client.get_from_code(f"http://aminoapps.com/c/{amino_c}")
		isJoined = val.json["extensions"]["isCurrentUserJoined"]
		if isJoined:
			communaute[comId] = BotAmino(client=client, community=message)
			communaute[comId].run()
			subClient.send_message(chatId, "Joined!")
			return
		subClient.send_message(chatId, "Waiting for join!")
		return
	else:
		subClient.send_message(chatId, "Allready joined!")
		return

	subClient.send_message(chatId, "Waiting for join!")


def title(subClient=None,
          chatId=None,
          authorId=None,
          author=None,
          message=None,
          messageId=None):
	if subClient.is_in_staff(botId):
		color = None
		try:
			elem = message.strip().split("color=")
			message, color = elem[0], elem[1].strip()
			if not color.startswith("#"):
				color = "#" + color
			val = subClient.add_title(authorId, message, color)
		except Exception:
			val = subClient.add_title(authorId, message)

		if val:
			subClient.send_message(chatId,
			                       f"The titles of {author} has changed")
		else:
			subClient.send_mesubClient.send_message(
			    chatId, subClient.get_message_level(subClient.lvl_min))


def cus_k(subClient=None,
          chatId=None,
          authorId=None,
          author=None,
          message=None,
          messageId=None):
	subClient.send_message(chatId, f"Here is a {message} for {author} ")


def hh(subClient=None,
       chatId=None,
       authorId=None,
       author=None,
       message=None,
       messageId=None):
	subClient.subclient.accept_organizer(chatId)
	subClient.send_message(chatId, "accepted")


def dice(subClient=None,
         chatId=None,
         authorId=None,
         author=None,
         message=None,
         messageId=None):
	if not message:
		subClient.send_message(chatId, f"🎲 -{randint(1, 20)},(1-20)- 🎲")
		return

	with suppress(Exception):
		pt = message.split('d')
		val = ''
		cpt = 0
		if int(pt[0]) > 20:
			pt[0] = 20
		if int(pt[1]) > 1000000:
			pt[1] = 1000000
		for _ in range(int(pt[0])):
			ppt = randint(1, int(pt[1]))
			cpt += ppt
			val += str(ppt) + " "
		print(f'🎲 -{cpt},[ {val}](1-{pt[1]})- 🎲')
		subClient.send_message(chatId, f'🎲 -{cpt},[ {val}](1-{pt[1]})- 🎲')


def join(subClient=None,
         chatId=None,
         authorId=None,
         author=None,
         message=None,
         messageId=None):
	val = subClient.join_chat(message, chatId)
	if val or val == "":
		subClient.send_message(chatId, f"Chat {val} joined".strip())
	else:
		subClient.send_message(chatId, "No chat joined")


def join_all(subClient=None,
             chatId=None,
             authorId=None,
             author=None,
             message=None,
             messageId=None):
	if subClient.is_in_staff(authorId) or is_it_me(authorId) or is_it_admin(
	    authorId):
		subClient.join_all_chat()
		subClient.send_message(chatId, "All chat joined")


def leave_all(subClient=None,
              chatId=None,
              authorId=None,
              author=None,
              message=None,
              messageId=None):
	if subClient.is_in_staff(authorId) or is_it_me(authorId) or is_it_admin(
	    authorId):
		subClient.send_message(chatId, "Leaving all chat...")
		subClient.leave_all_chats()


def leave(subClient=None,
          chatId=None,
          authorId=None,
          author=None,
          message=None,
          messageId=None):
	if message and (is_it_me(authorId) or is_it_admin(authorId)):
		chat_ide = subClient.get_chat_id(message)
		if chat_ide:
			chatId = chat_ide
	subClient.leave_chat(chatId)


def clear(subClient=None,
          chatId=None,
          authorId=None,
          author=None,
          message=None,
          messageId=None):
	if (subClient.is_in_staff(authorId) or is_it_me(authorId)
	    or is_it_admin(authorId)) and subClient.is_in_staff(botId):
		size = 1
		msg = ""
		val = ""
		subClient.delete_message(chatId, messageId, asStaff=True)
		if "chat=" in message and (is_it_me(authorId)
		                           or is_it_admin(authorId)):
			chat_name = message.rsplit("chat=", 1).pop()
			chat_ide = subClient.get_chat_id(chat_name)
			if chat_ide:
				chatId = chat_ide
			message = " ".join(message.strip().split()[:-1])

		with suppress(Exception):
			size = int(message.strip().split(' ').pop())
			msg = ' '.join(message.strip().split(' ')[:-1])

		if size > 50 and not is_it_me(authorId):
			size = 50

		if msg:
			try:
				val = subClient.get_user_id(msg)
			except Exception:
				val = ""

		messages = subClient.subclient.get_chat_messages(chatId=chatId,
		                                                 size=size)

		for message, authorId in zip(messages.messageId,
		                             messages.author.userId):
			if not val:
				subClient.delete_message(chatId, message, asStaff=True)
			elif authorId == val[1]:
				subClient.delete_message(chatId, message, asStaff=True)


def spam(subClient=None,
         chatId=None,
         authorId=None,
         author=None,
         message=None,
         messageId=None):
	try:
		size = int(message.strip().split().pop())
		msg = " ".join(message.strip().split()[:-1])
	except ValueError:
		size = 1
		msg = message

	if size > 3:
		size = 3

	for _ in range(size):
		with suppress(Exception):
			subClient.send_message(chatId, msg)


def mention(subClient=None,
            chatId=None,
            authorId=None,
            author=None,
            message=None,
            messageId=None):
	if "chat=" in message and (is_it_me(authorId) or is_it_admin(authorId)):
		chat_name = message.rsplit("chat=", 1).pop()
		chat_ide = subClient.get_chat_id(chat_name)
		if chat_ide:
			chatId = chat_ide
		message = " ".join(message.strip().split()[:-1])
	try:
		size = int(message.strip().split().pop())
		message = " ".join(message.strip().split()[:-1])
	except ValueError:
		size = 1

	val = subClient.get_user_id(message)
	if not val:
		subClient.send_message(chatId=chatId, message="Username not found")
		return

	if size > 5 and not (is_it_me(authorId) or is_it_admin(authorId)):
		size = 5

	if val:
		for _ in range(size):
			with suppress(Exception):
				subClient.send_message(chatId=chatId,
				                       message=f"‎‏‎‏@{val[0]}‬‭",
				                       mentionUserIds=[val[1]])


def mentionall(subClient=None,
               chatId=None,
               authorId=None,
               author=None,
               message=None,
               messageId=None):
	if subClient.is_in_staff(authorId) or is_it_me(authorId) or is_it_admin(
	    authorId):
		if message and is_it_me(authorId):
			chat_ide = subClient.get_chat_id(message)
			if chat_ide:
				chatId = chat_ide
			message = " ".join(message.strip().split()[:-1])

		mention = [
		    userId for userId in subClient.subclient.get_chat_users(
		        chatId=chatId).userId
		]
		test = "".join([
		    "‎‏‎‏‬‭" for user in subClient.subclient.get_chat_users(
		        chatId=chatId).userId
		])

		with suppress(Exception):
			subClient.send_message(chatId=chatId,
			                       message=f"@everyone{test}",
			                       mentionUserIds=mention)


def join_vc(subClient=None,
            chatId=None,
            authorId=None,
            author=None,
            message=None,
            messageId=None):
	client.join_voice_chat2(chatId=chatId, comId=subClient.community_id)


def msg(subClient=None,
        chatId=None,
        authorId=None,
        author=None,
        message=None,
        messageId=None):
	value = 0
	size = 1
	ment = None
	with suppress(Exception):
		try:
			subClient.delete_message(chatId, messageId, asStaff=True)
		except:
			subClient.delete_message(chatId, messageId)

	if "chat=" in message and (is_it_me(authorId) or is_it_admin(authorId)):
		chat_name = message.rsplit("chat=", 1).pop()
		chat_ide = subClient.get_chat_id(chat_name)
		if chat_ide:
			chatId = chat_ide
		message = " ".join(message.strip().split()[:-1])

	try:
		size = int(message.split().pop())
		message = " ".join(message.strip().split()[:-1])
	except ValueError:
		size = 0

	try:
		value = int(message.split().pop())
		message = " ".join(message.strip().split()[:-1])
	except ValueError:
		value = size
		size = 1

	if not message and value == 1:
		message = f"‎‏‎‏@{author}‬‭"
		ment = authorId

	if size > 3:
		size = 3

	for _ in range(size):
		with suppress(Exception):
			subClient.send_message(chatId=chatId,
			                       message=f"{message}",
			                       messageType=value,
			                       mentionUserIds=ment)


def add_banned_word(subClient=None,
                    chatId=None,
                    authorId=None,
                    author=None,
                    message=None,
                    messageId=None):
	if subClient.is_in_staff(authorId) or is_it_me(authorId) or is_it_admin(
	    authorId):
		if not message or message in subClient.banned_words:
			return
		try:
			message = message.lower().strip().split()
		except Exception:
			message = [message.lower().strip()]
		subClient.add_banned_words(message)
		subClient.send_message(chatId, "Banned word list updated")


def remove_banned_word(subClient=None,
                       chatId=None,
                       authorId=None,
                       author=None,
                       message=None,
                       messageId=None):
	if subClient.is_in_staff(authorId) or is_it_me(authorId) or is_it_admin(
	    authorId):
		if not message:
			return
		try:
			message = message.lower().strip().split()
		except Exception:
			message = [message.lower().strip()]
		subClient.remove_banned_words(message)
		subClient.send_message(chatId, "Banned word list updated")


def start_vc(subClient=None,
             chatId=None,
             authorId=None,
             author=None,
             message=None,
             messageId=None):
	sleep(1)
	client.start_vc(chatId=chatId, comId=subClient.community_id, role=message)


def end_vc(subClient=None,
           chatId=None,
           authorId=None,
           author=None,
           message=None,
           messageId=None):
	client.end_vc(chatId=chatId, comId=subClient.community_id)


def banned_word_list(subClient=None,
                     chatId=None,
                     authorId=None,
                     author=None,
                     message=None,
                     messageId=None):
	val = ""
	if subClient.banned_words:
		for elem in subClient.banned_words:
			val += elem + "\n"
	else:
		val = "No words in the list"
	subClient.send_message(chatId, val)


def sw(subClient=None,
       chatId=None,
       authorId=None,
       author=None,
       message=None,
       messageId=None):
	if subClient.is_in_staff(authorId) or is_it_me(authorId) or is_it_admin(
	    authorId):
		subClient.set_welcome_message(message)
		subClient.send_message(chatId, "Welcome message changed")


def get_chats(subClient=None,
              chatId=None,
              authorId=None,
              author=None,
              message=None,
              messageId=None):
	val = subClient.get_chats()
	for title, _ in zip(val.title, val.chatId):
		subClient.send_message(chatId, title)


def chat_id(subClient=None,
            chatId=None,
            authorId=None,
            author=None,
            message=None,
            messageId=None):
	if is_it_me(authorId) or is_it_admin(authorId):
		val = subClient.get_chats()
		for title, chat_id in zip(val.title, val.chatId):
			if message.lower() in title.lower():
				subClient.send_message(chatId, f"{title} | {chat_id}")


def leave_amino(subClient=None,
                chatId=None,
                authorId=None,
                author=None,
                message=None,
                messageId=None):
	if subClient.is_in_staff(authorId) or is_it_me(authorId) or is_it_admin(
	    authorId):
		subClient.send_message(chatId, "Leaving the amino!")
		subClient.leave_community()
	del communaute[subClient.community_id]


def src(subClient=None,
        chatId=None,
        authorId=None,
        author=None,
        message=None,
        messageId=None):
	value = 0
	size = 1
	ment = None
	with suppress(Exception):
		try:
			subClient.delete_message(chatId, messageId, asStaff=True)
		except:
			subClient.delete_message(chatId, messageId)

	try:
		size = int(message.split().pop())
		message = " ".join(message.strip().split()[:-1])
	except ValueError:
		size = 0

	try:
		value = int(message.split().pop())
		message = " ".join(message.strip().split()[:-1])
	except ValueError:
		value = size
		size = 1

	if not message and value == 1:
		message = f"‎‏‎‏@{author}‬‭"
		ment = authorId

	if size > 10 and not (is_it_me(authorId) or is_it_admin(authorId)):
		size = 10

	search_word = message
	response = duckduckpy.query(message, container='dict')
	answer = response['abstract_text']
	if len(answer) < 5:
		answer = "Refer Below Link"
	answer_url = response['abstract_url']
	if len(answer_url):
		reply = "-----------------------------------------------------------------\n[BC]Search Result\n-----------------------------------------------------------------\nWord: " + str(
		    search_word
		) + "\nResult: " + str(answer) + "\nSoucre URL: " + str(
		    answer_url
		) + "\n-----------------------------------------------------------------"
	if len(answer_url) == 0:
		reply = "[C] No Result Found"
	print("reply", reply)
	for _ in range(size):
		with suppress(Exception):
			subClient.send_message(chatId=chatId,
			                       message=f"{reply}",
			                       messageType=value,
			                       mentionUserIds=ment)


def img_search(subClient=None,
               chatId=None,
               authorId=None,
               author=None,
               message=None,
               messageId=None):
	search_phrase = message
	with suppress(Exception):
		try:
			subClient.delete_message(chatId, messageId, asStaff=True)
		except:
			subClient.delete_message(chatId, messageId)
	path = "https://www.google.co.in/search?q={0}&source=lnms&tbm=isch"
	path1 = path.format(search_phrase)
	requete = requests.get(path1)
	page = requete.content
	soup = bs4.BeautifulSoup(page, "html.parser")
	# print("\n\n",soup.find_all("img"),"\n\n")
	propriete = soup.find_all("img")[1]
	# Ketan Edit 1.23
	propriete = str(propriete).split("src=")[1][:-2]
	print("propriete", propriete)
	image = propriete + ".jpg"
	image = (image.replace('"', ''))
	if image is not None:
		print(image)
		filename = image.split("tbn:")[-1]
		urllib.request.urlretrieve(image, filename)
		with open(filename, 'rb') as fp:
			with suppress(Exception):
				subClient.send_message(chatId, file=fp, fileType="image")
				print(os.remove(filename))


def gif_search(subClient=None,
               chatId=None,
               authorId=None,
               author=None,
               message=None,
               messageId=None):
	search = message
	with suppress(Exception):
		try:
			subClient.delete_message(chatId, messageId, asStaff=True)
		except:
			subClient.delete_message(chatId, messageId)
	response = requests.get(
	    'http://api.giphy.com/v1/gifs/search?q=' + search +
	    '&api_key=1jdqvfFwB2Vf12z6ZJ72sqkYm1yz0VVM&limit=10')
	# print(response.text)
	data = json.loads(response.text)
	gif_choice = random.randint(0, 9)
	image = data['data'][gif_choice]['images']['original']['url']
	print("URL", image)
	if image is not None:
		print(image)
		filename = image.split("/")[-1]
		urllib.request.urlretrieve(image, filename)
		with open(filename, 'rb') as fp:
			with suppress(Exception):
				subClient.send_message(chatId, file=fp, fileType="gif")
				print(os.remove(filename))


def prank(subClient=None,
          chatId=None,
          authorId=None,
          author=None,
          message=None,
          messageId=None):
	coins_val = (message)
	with suppress(Exception):
		try:
			subClient.delete_message(chatId, messageId, asStaff=True)
		except:
			subClient.delete_message(chatId, messageId)

	transactionId = "d656e556-57ba-4f69-8c1c-07848e7800d8"
	old_chat = None
	if message and is_it_me(authorId):
		chat_ide = subClient.get_chat_id(message)
		if chat_ide:
			old_chat = chatId
			chatId = chat_ide
	for _ in range(1):
		subClient.subclient.send_coins(coins=int(coins_val),
		                               chatId=chatId,
		                               transactionId=transactionId)

	if old_chat:
		chatId = old_chat
		subClient.send_message(chatId, "Done")


def image(subClient=None,
          chatId=None,
          authorId=None,
          author=None,
          message=None,
          messageId=None):
	val = os.listdir("pictures")
	if val:
		file = choice(val)
		with suppress(Exception):
			with open(path_picture + file, 'rb') as fp:
				subClient.send_message(chatId, file=fp, fileType="image")
	else:
		subClient.send_message(chatId, "Error! No file")


def audio(subClient=None,
          chatId=None,
          authorId=None,
          author=None,
          message=None,
          messageId=None):
	val = os.listdir(path_sound)
	print("VAL:", val)
	if val:
		file = choice(val)
		print("File", file)
		with suppress(Exception):
			with open(path_sound + "/" + file, 'rb') as fp:
				subClient.send_message(chatId, file=fp, fileType="audio")
	else:
		subClient.send_message(chatId, "Error! No file")


def telecharger(url):
	music = None
	if ("=" in url and "/" in url and " " not in url) or ("/" in url
	                                                      and " " not in url):
		if "=" in url and "/" in url:
			music = url.rsplit("=", 1)[-1]
		elif "/" in url:
			music = url.rsplit("/")[-1]

		if music in os.listdir(path_sound):
			return music

		ydl_opts = {
		    'format':
		    'bestaudio/best',
		    'postprocessors': [{
		        'key': 'FFmpegExtractAudio',
		        'preferredcodec': 'mp3',
		        'preferredquality': '192',
		    }],
		    'extract-audio':
		    True,
		    'outtmpl':
		    f"{path_download}/{music}.webm",
		}

		with YoutubeDL(ydl_opts) as ydl:
			video_length = ydl.extract_info(url, download=True).get('duration')
			ydl.cache.remove()

		url = music + ".mp3"

		return url, video_length
	return False, False


def decoupe(musical, temps):
	size = 170
	with open(musical, "rb") as fichier:
		nombre_ligne = len(fichier.readlines())

	if temps < 180 or temps > 540:
		return False

	decoupage = int(size * nombre_ligne / temps)

	t = 0
	file_list = []
	for a in range(0, nombre_ligne, decoupage):
		b = a + decoupage
		if b >= nombre_ligne:
			b = nombre_ligne

		with open(musical, "rb") as fichier:
			lignes = fichier.readlines()[a:b]

		with open(musical.replace(".mp3", "PART" + str(t) + ".mp3"),
		          "wb") as mus:
			for ligne in lignes:
				mus.write(ligne)

		file_list.append(musical.replace(".mp3", "PART" + str(t) + ".mp3"))
		t += 1
	return file_list


def convert(subClient=None,
            chatId=None,
            authorId=None,
            author=None,
            message=None,
            messageId=None):
	music, size = telecharger(message)
	if music:
		music = f"{path_download}/{music}"
		val = decoupe(music, size)

		if not val:
			try:
				with open(music, 'rb') as fp:
					subClient.send_message(chatId, file=fp, fileType="audio")
			except Exception:
				subClient.send_message(chatId,
				                       "Error! File too heavy (9 min max)")
			os.remove(music)
			return

		os.remove(music)
		for elem in val:
			with suppress(Exception):
				with open(elem, 'rb') as fp:
					subClient.send_message(chatId, file=fp, fileType="audio")
			os.remove(elem)
		return
	subClient.send_message(chatId, "Error! Wrong link")


def helper(subClient=None,
           chatId=None,
           authorId=None,
           author=None,
           message=None,
           messageId=None):
	if not message:
		subClient.send_message(chatId, helpMsg)
	elif message == "staff":
		subClient.send_message(chatId, staff)
	elif message == "ask":
		subClient.send_message(chatId, helpAsk)
	else:
		subClient.send_message(chatId, "No help is available for this command")


def reboot(subClient=None,
           chatId=None,
           authorId=None,
           author=None,
           message=None,
           messageId=None):
	if is_it_me(authorId) or is_it_admin(authorId):
		subClient.send_message(chatId, "Restarting Bot")
		os.execv(sys.executable, ["None", os.path.basename(sys.argv[0])])



def chat_copy(subClient=None, chatId=None, authorId=None, author=None, message=None, messageId=None):
	id=client.get_from_code(message). objectId
	i=subClient.subclient.get_chat_thread(chatId=id).icon
	c=subClient.subclient.get_chat_thread(chatId=id).content
	t=subClient.subclient.get_chat_thread(chatId=id).title
	bg=subClient.subclient.get_chat_thread(chatId=id).backgroundImage
	a=subClient.subclient.get_chat_thread(chatId=id).announcement
	subClient.subclient.edit_chat(chatId=chatId,title=t,content=c,icon=i,announcement=a)
	subClient.subclient.edit_chat(chatId=chatId,backgroundImage=bg)

def stop(subClient=None,
         chatId=None,
         authorId=None,
         author=None,
         message=None,
         messageId=None):
	if is_it_me(authorId) or is_it_admin(authorId):
		subClient.send_message(chatId, "Stopping Bot")
		os.execv(sys.executable, ["None", "None"])


def day(subClient=None,
        chatId=None,
        authorId=None,
        author=None,
        message=None,
        messageId=None):
	try:
		today = date.today()
		G = today.strftime("%A")
		d = time.strftime("%b %d %Y \n %-I:%M %p")
		subClient.send_message(chatId=chatId, message=f"{G}  {d}")
	except:
		pass


def uinfo(subClient=None,
          chatId=None,
          authorId=None,
          author=None,
          message=None,
          messageId=None):
	if is_it_me(authorId) or is_it_admin(authorId):
		val = ""
		val2 = ""
		uid = ""
		with suppress(Exception):
			val = subClient.client.get_user_info(message)

		with suppress(Exception):
			val2 = subClient.subclient.get_user_info(message)

		if not val:
			uid = subClient.get_user_id(message)
			if uid:
				val = subClient.client.get_user_info(uid[1])
				val2 = subClient.subclient.get_user_info(uid[1])
			print(val, val2)

		if not val:
			with suppress(Exception):
				lin = subClient.client.get_from_code(
				    f"http://aminoapps.com/u/{message}"
				).json["extensions"]["linkInfo"]["objectId"]
				val = subClient.client.get_user_info(lin)

			with suppress(Exception):
				val2 = subClient.subclient.get_user_info(lin)

		with suppress(Exception):
			with open("elJson.json", "w") as file_:
				file_.write(dumps(val.json, sort_keys=True, indent=4))

		with suppress(Exception):
			with open("elJson2.json", "w") as file_:
				file_.write(dumps(val2.json, sort_keys=True, indent=4))

		for i in ("elJson.json", "elJson2.json"):
			if os.path.getsize(i):
				txt2pdf.callPDF(i, "result.pdf")
				pages = convert_from_path('result.pdf', 150)
				file = 'result.jpg'
				for page in pages:
					page.save(file, 'JPEG')
					with open(file, 'rb') as fp:
						subClient.send_message(chatId,
						                       file=fp,
						                       fileType="image")
					os.remove(file)
				os.remove("result.pdf")

		if not os.path.getsize("elJson.json") and not os.path.getsize(
		    "elJson.json"):
			subClient.send_message(chatId, "Error!")


def cinfo(subClient=None,
          chatId=None,
          authorId=None,
          author=None,
          message=None,
          messageId=None):
	if is_it_me(authorId) or is_it_admin(authorId):
		val = ""
		with suppress(Exception):
			val = subClient.client.get_from_code(message)

		with suppress(Exception):
			with open("elJson.json", "w") as file_:
				file_.write(dumps(val.json, sort_keys=True, indent=4))

		if os.path.getsize("elJson.json"):
			txt2pdf.callPDF("elJson.json", "result.pdf")
			pages = convert_from_path('result.pdf', 150)
			for page in pages:
				file = 'result.jpg'
				page.save(file, 'JPEG')
				with open(file, 'rb') as fp:
					subClient.send_message(chatId, file=fp, fileType="image")
				os.remove(file)
			os.remove("result.pdf")

		if not os.path.getsize("elJson.json"):
			subClient.send_message(chatId, "Error!")


def sendinfo(subClient=None,
             chatId=None,
             authorId=None,
             author=None,
             message=None,
             messageId=None):
	if (is_it_admin(authorId) or is_it_me(authorId)) and message != "":
		arguments = message.strip().split()
		for eljson in ('elJson.json', 'elJson2.json'):
			if Path(eljson).exists():
				arg = arguments.copy()
				with open(eljson, 'r') as file:
					val = load(file)
				try:
					memoire = val[arg.pop(0)]
				except Exception:
					subClient.send_message(chatId, 'Wrong key!')
				if arg:
					for elem in arg:
						try:
							memoire = memoire[str(elem)]
						except Exception:
							subClient.send_message(chatId, 'Wrong key 1!')
				subClient.send_message(chatId, memoire)


def get_global(subClient=None,
               chatId=None,
               authorId=None,
               author=None,
               message=None,
               messageId=None):
                 mention = subClient.get_message_info(chatId=chatId, messageId=messageId).mentionUserIds
                 for user in mention:
                   AId = client.get_user_info(userId=str(user)).aminoId
                   subClient.send_message(chatId,
		                       message="https://aminoapps.com/u/" + str(AId))


def follow(subClient=None,
           chatId=None,
           authorId=None,
           author=None,
           message=None,
           messageId=None):
	subClient.follow_user(authorId)
	subClient.send_message(chatId, "Now following you!")


def unfollow(subClient=None,
             chatId=None,
             authorId=None,
             author=None,
             message=None,
             messageId=None):
	subClient.unfollow_user(authorId)
	subClient.send_message(chatId, "Unfollow!")


def stop_amino(subClient=None,
               chatId=None,
               authorId=None,
               author=None,
               message=None,
               messageId=None):
	if is_it_me(authorId) or is_it_admin(authorId):
		subClient.stop_instance()
		del communaute[subClient.community_id]


def block(subClient=None,
          chatId=None,
          authorId=None,
          author=None,
          message=None,
          messageId=None):
            mention = subClient.get_message_info(chatId=chatId, messageId=messageId).mentionUserIds
            for user in mention:
              subClient.client.block(str(user))
              subClient.send_message(chatId," blocked!")


def unblock(subClient=None,
            chatId=None,
            authorId=None,
            author=None,
            message=None,
            messageId=None):
	if is_it_me(authorId) or is_it_admin(authorId):
		val = subClient.client.get_blocked_users()
		for aminoId, userId in zip(val.aminoId, val.userId):
			if message in aminoId:
				subClient.client.unblock(userId)
				subClient.send_message(chatId, f"User {aminoId} unblocked!")


def accept(subClient=None,
           chatId=None,
           authorId=None,
           author=None,
           message=None,
           messageId=None):
	if subClient.is_in_staff(authorId) or is_it_me(authorId) or is_it_admin(
	    authorId):
		val = subClient.subclient.get_notices(start=0, size=25)
		ans = None
		res = None
		if subClient.accept_role("host", chatId):
			subClient.send_message(chatId, "Accepted!")
			return

		for elem in val:
			if 'become' in elem['title'] or "host" in elem['title']:
				res = elem['noticeId']
			if res:
				ans = subClient.accept_role(res)
			if ans:
				subClient.send_message(chatId, "Accepted!")
		else:
			subClient.send_message(chatId, "Error!")


def hh(subClient=None,
       chatId=None,
       authorId=None,
       author=None,
       message=None,
       messageId=None):
	subClient.subclient.accept_organizer(chatId)
	subClient.send_message(chatId, "accept")


def say(subClient=None,
        chatId=None,
        authorId=None,
        author=None,
        message=None,
        messageId=None):
	audio_file = f"{path_download}/ttp{randint(1,500)}.mp3"
	langue = list(lang.tts_langs().keys())
	if not message:
		message = subClient.subclient.get_chat_messages(chatId=chatId,
		                                                size=2).content[1]
	gTTS(text=message, lang='en', slow=False).save(audio_file)
	try:
		with open(audio_file, 'rb') as fp:
			subClient.send_message(chatId, file=fp, fileType="audio")
	except Exception:
		subClient.send_message(chatId, "Too heavy!")
	os.remove(audio_file)


def ask_thing(subClient=None,
              chatId=None,
              authorId=None,
              author=None,
              message=None,
              messageId=None):
	if subClient.is_in_staff(authorId) or is_it_me(authorId) or is_it_admin(
	    authorId):
		lvl = ""
		boolean = 1
		if "lvl=" in message:
			lvl = message.rsplit("lvl=", 1)[1].strip().split(" ", 1)[0]
			message = message.replace("lvl=" + lvl, "").strip()
		elif "lvl<" in message:
			lvl = message.rsplit("lvl<", 1)[1].strip().split(" ", 1)[0]
			message = message.replace("lvl<" + lvl, "").strip()
			boolean = 2
		elif "lvl>" in message:
			lvl = message.rsplit("lvl>", 1)[1].strip().split(" ", 1)[0]
			message = message.replace("lvl>" + lvl, "").strip()
			boolean = 3
		try:
			lvl = int(lvl)
		except ValueError:
			lvl = 20

		subClient.ask_all_members(
		    message +
		    f"\n[CUI]This message was sent by {author}\n[CUI]I am a bot and have a nice day^^",
		    lvl, boolean)
		subClient.send_message(chatId, "Asking...")


def new_mention_all(subClient=None,
                    chatId=None,
                    authorId=None,
                    author=None,
                    message=None,
                    messageId=None):
	i = 0
	count = 0
	breakflag = 0
	mes = ""
	userar = []
	while True:
		users = subClient.subclient.get_chat_users(chatId=chatId,
		                                           start=i,
		                                           size=100)
		print("users", users.nickname)
		j = 0
		for j in range(100):
			try:
				mes = mes + f"‎‏‎‏@{users.nickname[j]}\n"
				userar.append(users.userId[j])
				count += 1
				print("mess", mes)
			except IndexError:
				breakflag = 1
				break
			except:
				pass
		i += 100
		if breakflag == 1:
			break

	userar = [
	    userId
	    for userId in subClient.subclient.get_chat_users(chatId=chatId).userId
	]
	subClient.send_message(chatId=chatId, message=mes, mentionUserIds=userar)


def ask_staff(subClient=None,
              chatId=None,
              authorId=None,
              author=None,
              message=None,
              messageId=None):
	if is_it_me(authorId) or is_it_admin(authorId):
		amino_list = client.sub_clients()
		for commu in amino_list.comId:
			communaute[commu].ask_amino_staff(message=message)
		subClient.send_message(chatId, "Asking...")


def bot_clear(subClient=None,
              chatId=None,
              authorId=None,
              author=None,
              message=None,
              messageId=None):

	if (is_it_me(authorId) or is_it_admin(authorId)):
		print("clearing")
		size = 1
		msg = ""
		val = ""
		subClient.delete_message(chatId, messageId)
		if "chat=" in message and (is_it_me(authorId)
		                           or is_it_admin(authorId)):
			chat_name = message.rsplit("chat=", 1).pop()
			chat_ide = subClient.get_chat_id(chat_name)
			if chat_ide:
				chatId = chat_ide
			message = " ".join(message.strip().split()[:-1])

		with suppress(Exception):
			size = int(message.strip().split(' ').pop())
			msg = ' '.join(message.strip().split(' ')[:-1])

		if size > 50 and not is_it_me(authorId):
			size = 50

		if msg:
			try:
				val = subClient.get_user_id(msg)
			except Exception:
				val = ""

		messages = subClient.subclient.get_chat_messages(chatId=chatId,
		                                                 size=size)
		# print("clearing")
		for message, authorId in zip(messages.messageId,
		                             messages.author.userId):
			if not val:
				if authorId == botId:
					subClient.delete_message(chatId, message)
			elif authorId == val[1]:
				subClient.delete_message(chatId, message)


def prefix(subClient=None,
           chatId=None,
           authorId=None,
           author=None,
           message=None,
           messageId=None):
	if message:
		subClient.set_prefix(message)
		subClient.send_message(chatId, f"prefix set as {message}")


def lock_command(subClient=None,
                 chatId=None,
                 authorId=None,
                 author=None,
                 message=None,
                 messageId=None):
	if subClient.is_in_staff(authorId) or is_it_me(authorId) or is_it_admin(
	    authorId):
		if not message or message in subClient.locked_command or message in (
		    "lock", "unlock"):
			return
		try:
			message = message.lower().strip().split()
		except Exception:
			message = [message.lower().strip()]
		subClient.add_locked_command(message)
		subClient.send_message(chatId, "Locked command list updated")


def unlock_command(subClient=None,
                   chatId=None,
                   authorId=None,
                   author=None,
                   message=None,
                   messageId=None):
	if subClient.is_in_staff(authorId) or is_it_me(authorId) or is_it_admin(
	    authorId):
		if message:
			try:
				message = message.lower().strip().split()
			except Exception:
				message = [message.lower().strip()]
			subClient.remove_locked_command(message)
			subClient.send_message(chatId, "Locked command list updated")


def locked_command_list(subClient=None,
                        chatId=None,
                        authorId=None,
                        author=None,
                        message=None,
                        messageId=None):
	val = ""
	if subClient.locked_command:
		for elem in subClient.locked_command:
			val += elem + "\n"
	else:
		val = "No locked command"
	subClient.send_message(chatId, val)


def admin_lock_command(subClient=None,
                       chatId=None,
                       authorId=None,
                       author=None,
                       message=None,
                       messageId=None):
	if is_it_me(authorId) or is_it_admin(authorId):
		if not message or message not in commands_dict.keys(
		) or message == "alock":
			return

		command = subClient.admin_locked_command
		message = [message]

		if message[0] in command:
			subClient.remove_admin_locked_command(message)
		else:
			subClient.add_admin_locked_command(message)

		subClient.send_message(chatId, "Locked command list updated")


def locked_admin_command_list(subClient=None,
                              chatId=None,
                              authorId=None,
                              author=None,
                              message=None,
                              messageId=None):
	if is_it_me(authorId) or is_it_admin(authorId):
		val = ""
		if subClient.admin_locked_command:
			for elem in subClient.admin_locked_command:
				val += elem + "\n"
		else:
			val = "No locked command"
		subClient.send_message(chatId, val)


def read_only(subClient=None,
              chatId=None,
              authorId=None,
              author=None,
              message=None,
              messageId=None):
	if subClient.is_in_staff(botId) and (subClient.is_in_staff(authorId)
	                                     or is_it_me(authorId)
	                                     or is_it_admin(authorId)):
		chats = subClient.only_view
		if chatId not in chats:
			subClient.add_only_view(chatId)
			subClient.send_message(chatId,
			                       "This chat is now in only-view mode")
		else:
			subClient.remove_only_view(chatId)
			subClient.send_message(chatId,
			                       "This chat is no longer in only-view mode")
		return
	elif not subClient.is_in_staff(botId):
		subClient.send_message(chatId, "The bot need to be in the staff!")


def keep_favorite_users(subClient=None,
                        chatId=None,
                        authorId=None,
                        author=None,
                        message=None,
                        messageId=None):
	if subClient.is_in_staff(botId) and (subClient.is_in_staff(authorId)
	                                     or is_it_me(authorId)
	                                     or is_it_admin(authorId)):
		users = subClient.favorite_users
		try:
			val = subClient.get_user_id(message)
			user, userId = val[0], val[1]
		except Exception:
			subClient.send_message(chatId, "Error, user not found!")
			return
		if userId not in users:
			subClient.add_favorite_users(userId)
			subClient.send_message(chatId, f"Added {user} to favorite users")
			with suppress(Exception):
				subClient.favorite(time=1, userId=userId)
		return
	elif not subClient.is_in_staff(botId):
		subClient.send_message(chatId, "The bot need to be in the staff!")


def profile(subClient=None,
            chatId=None,
            authorId=None,
            author=None,
            message=None,
            messageId=None):
	mention = subClient.get_message_info(chatId=chatId,
	                                     messageId=messageId).mentionUserIds
	print("mention", mention)
	for user in mention:
		gg = subClient.subclient.get_user_info(userId=str(user)).icon
		u = subClient.subclient.get_user_info(userId=str(user)).mediaList
		for mediaList in u:
			for L in mediaList:
				if L != None and L != 100 and len(L):
					for image in gg, L:
						print(image)
						filename = image.split("/")[-1]
						filetype = image.split(".")[-1]
						filetype = filetype.replace(" ", "")
						# print("filetype",filetype)
						if filetype != "gif":
							filetype = "image"
						urllib.request.urlretrieve(image, filename)
						with open(filename, 'rb') as fp:
							with suppress(Exception):
								subClient.send_message(chatId,
								                       file=fp,
								                       fileType=filetype)
								print(os.remove(filename))


def edit_icon(subClient=None,
              chatId=None,
              authorId=None,
              author=None,
              message=None,
              messageId=None):
	if is_it_me(authorId) or is_it_admin(authorId):
		data = subClient.get_message_info(chatId=chatId, messageId=messageId)
		reply_message = data.json['extensions']
		if reply_message:
			image = data.json['extensions']['replyMessage']['mediaValue']
			for i in range(1, 5):
				subClient.edit_profile(icon=image)

		subClient.send_message(chatId, message="Done")


def edit_bio(subClient=None,
             chatId=None,
             authorId=None,
             author=None,
             message=None,
             messageId=None):
	if is_it_me(authorId) or is_it_admin(authorId):
		subClient.edit_profile(content=message)
		subClient.send_message(chatId, f"Bio changed to {message} by {author}")


def edit_name(subClient=None,
              chatId=None,
              authorId=None,
              author=None,
              message=None,
              messageId=None):
	if is_it_me(authorId) or is_it_admin(authorId):
		subClient.edit_profile(nickname=message)
		subClient.send_message(chatId,
		                       f"Name changed to {message} by {author}")


def ban(subClient=None,
        chatId=None,
        authorId=None,
        author=None,
        message=None,
        messageId=None):
	if subClient.is_in_staff(authorId) or is_it_me(authorId) or is_it_admin(
	    authorId):
		mention = subClient.get_message_info(
		    chatId=chatId, messageId=messageId).mentionUserIds
		for user in mention:
			subClient.ban(userId=str(user), reason=f"{author}:{message}")
		subClient.delete_message(chatId, messageId, asStaff=True)
		try:
			subClient.send_message(chatId, message="Hogya lodu ban")
		except Exception:
			subClient.send_message(
			    chatId,
			    "Error Bhosdike check kr leader ko to nahi kar raha ban")


def unkeep_favorite_users(subClient=None,
                          chatId=None,
                          authorId=None,
                          author=None,
                          message=None,
                          messageId=None):
	if subClient.is_in_staff(botId) and (subClient.is_in_staff(authorId)
	                                     or is_it_me(authorId)
	                                     or is_it_admin(authorId)):
		users = subClient.favorite_users
		try:
			val = subClient.get_user_id(message)
			user, userId = val[0], val[1]
		except Exception:
			subClient.send_message(chatId, "Error, user not found!")
			return
		if userId in users:
			subClient.remove_favorite_users(userId)
			subClient.send_message(chatId, f"Removed {user} to favorite users")
			with suppress(Exception):
				subClient.unfavorite(userId=userId)
		return
	elif not subClient.is_in_staff(botId):
		subClient.send_message(chatId, "The bot need to be in the staff!")


def keep_favorite_chats(subClient=None,
                        chatId=None,
                        authorId=None,
                        author=None,
                        message=None,
                        messageId=None):
	if subClient.is_in_staff(botId) and (subClient.is_in_staff(authorId)
	                                     or is_it_me(authorId)
	                                     or is_it_admin(authorId)):
		chats = subClient.favorite_chats
		val = subClient.get_chats()

		for title, chatId in zip(val.title, val.chatId):
			if message == title and chatId not in chats:
				subClient.add_favorite_chats(chatId)
				subClient.send_message(chatId,
				                       f"Added {title} to favorite chats")
				with suppress(Exception):
					subClient.favorite(time=1, chatId=chatId)
				return

		for title, chatId in zip(val.title, val.chatId):
			if message.lower() in title.lower() and chatId not in chats:
				subClient.add_favorite_chats(chatId)
				subClient.send_message(chatId,
				                       f"Added {title} to favorite chats")
				with suppress(Exception):
					subClient.favorite(time=1, chatId=chatId)
				return
	elif not subClient.is_in_staff(botId):
		subClient.send_message(chatId, "The bot need to be in the staff!")


def vc_com(subClient=None,
           chatId=None,
           authorId=None,
           author=None,
           message=None,
           messageId=None):
	info = client.get_from_code(message).objectId
	nm = 0
	c = 0
	while True:
		try:
			aa = subClient.subclient.get_all_users(start=nm, size=1)
			for userId, nickname in zip(aa.profile.userId,
			                            aa.profile.nickname):
				subClient.subclient.invite_to_vc2(userId=userId,
				                                  chatId=info,
				                                  comId='x226547416')
				nm = nm + 1
				c = int(c + 1)
				print(nickname + 'invited')
				if nm == 1000:
					nm = 0
		except:
			nm = nm + 1


def unkeep_favorite_chats(subClient=None,
                          chatId=None,
                          authorId=None,
                          author=None,
                          message=None,
                          messageId=None):
	if subClient.is_in_staff(botId) and (subClient.is_in_staff(authorId)
	                                     or is_it_me(authorId)
	                                     or is_it_admin(authorId)):
		chats = subClient.favorite_chats
		val = subClient.get_chats()

		for title, chatid in zip(val.title, val.chatId):
			if message == title and chatid in chats:
				subClient.remove_favorite_chats(chatid)
				subClient.unfavorite(chatId=chatid)
				subClient.send_message(chatId,
				                       f"Removed {title} to favorite chats")
				return

		for title, chatid in zip(val.title, val.chatId):
			if message.lower() in title.lower() and chatid in chats:
				subClient.remove_favorite_chats(chatid)
				subClient.unfavorite(chatId=chatid)
				subClient.send_message(chatId,
				                       f"Removed {title} to favorite chats")
				return


def global_invite(subClient=None,
                  chatId=None,
                  authorId=None,
                  author=None,
                  message=None,
                  messageId=None):
	nm = 0
	c = 0
	while True:
		try:
			aa = client.get_all_users(start=nm, size=1)
			for userId, nickname in zip(aa.profile.userId,
			                            aa.profile.nickname):
				subClient.subclient.invite_to_vc2(userId=userId,
				                                  chatId=chatId,
				                                  comId='x226547416')
				nm = nm + 1
				c = int(c + 1)
				print(nickname + 'invited to a voice chat')
				if nm == 1000:
					nm = 0

		except:
			nm = nm + 1


def pvp(subClient=None,
        chatId=None,
        authorId=None,
        author=None,
        message=None,
        messageId=None):
	msg = message + " null null "
	msg = msg.split(" ")
	try:
		rounds = int(msg[0])
	except (TypeError, ValueError):
		rounds = 5
		msg[2] = msg[1]
		msg[1] = msg[0]
		msg[0] = 5
	subClient.send_message(chatId=chatId,
	                       message=f"fighting {msg[1]} e {msg[2]}...")
	win1 = 0
	win2 = 0
	round = 0
	agess = ''
	defens = ''
	for pvp in range(0, rounds):
		round = round + 1
		subClient.send_message(chatId=chatId,
		                       message=f"[bc]Round {round}/{rounds}")
		punch = randint(0, 1)
		if punch == 0:
			win1 = win1 + 1
			agress = msg[1]
			defens = msg[2]
		else:
			win2 = win2 + 1
			agress = msg[2]
			defens = msg[1]
		time.sleep(4)
		subClient.send_message(chatId=chatId,
		                       message=f"[ic] {agress} winner°° {defens}!")
	if win1 > win2:
		subClient.send_message(chatId=chatId, message=f"[bcu]{msg[1]} winnerr")
	elif win1 < win2:
		subClient.send_message(chatId=chatId,
		                       message=f"[bcu]{msg[2]} winnerrrr!!")
	elif win1 == win2:
		subClient.send_message(chatId=chatId, message=f"[iC]victory.")


def ship(subClient=None,
         chatId=None,
         authorId=None,
         author=None,
         message=None,
         messageId=None):
	casal = message + " null null "
	pessoas = casal.split(" ")
	porcentagem = uniform(0, 100)
	quote = ' '
	if porcentagem <= 10:
		quote = 'Sem chance.'
	elif 10 <= porcentagem <= 25:
		quote = 'Eh...'
	elif 25 <= porcentagem <= 50:
		quote = 'zada nahi chalega'
	elif 50 <= porcentagem <= 75:
		quote = 'bonds ❤'
	elif 75 <= porcentagem <= 100:
		quote = 'pure love❤'
	subClient.send_message(
	    chatId=chatId,
	    message=f"{pessoas[0]} x {pessoas[1]} tem {porcentagem:.2f}% "
	    f"chances of getting in relation.")
	subClient.send_message(chatId=chatId, message=quote)
	try:
		value = int(''.join(open("value", 'r').readlines()))
	except:
		pass
	try:
		value = value + 1
	except:
		pass


def Youtube(subClient=None,
            chatId=None,
            authorId=None,
            author=None,
            message=None,
            messageId=None):
	try:
		size = int(message.strip().split().pop())
		msg = " ".join(message.strip().split()[:-1])
		search = msg
	except ValueError:
		size = 1
		search = message
	if size > 5:
		size = 5
	results = YoutubeSearch(search, max_results=size).to_json()
	# pprint(results)
	results = YoutubeSearch(search, max_results=size).to_dict()
	yt_reply = ""
	pprint(results)
	for result in results:
		title = result['title']
		thumbnails = result['thumbnails'][0]
		yt_url = 'https://youtu.be/' + result['url_suffix']
		dr = result['duration']
		views = result['views']
		yt_reply = yt_reply + str(title) + "\nViews: " + str(
		    views) + "\nDuration: " + str(dr) + "\n" + str(yt_url) + "\n\n"
	with suppress(Exception):
		subClient.send_message(chatId=chatId, message=yt_reply)
	for result in results:
		yt_url = 'https://youtu.be/' + result['url_suffix']
		convert(subClient, chatId, authorId, author, message=yt_url)


def welcome_channel(subClient=None,
                    chatId=None,
                    authorId=None,
                    author=None,
                    message=None,
                    messageId=None):
	if subClient.is_in_staff(authorId) or is_it_me(authorId) or is_it_admin(
	    authorId):
		subClient.set_welcome_chat(chatId)
		subClient.send_message(chatId, "Welcome channel set!")


def get_stick(subClient=None,
              chatId=None,
              authorId=None,
              author=None,
              message=None,
              messageId=None):
	data = subClient.get_message_info(chatId=chatId,
	                                  messageId=messageId)  # message

	reply_message = data.json['extensions']
	if reply_message:
		image = data.json['extensions']['replyMessage']['extensions'][
		    'sticker']['icon']
		print("\n\nurl", image)
		filename = image.split("/")[-1]
		filetype = image.split(".")[-1]
		if filetype != "gif":
			filetype = "image"
		urllib.request.urlretrieve(image, filename)
		with open(filename, 'rb') as fp:
			with suppress(Exception):
				subClient.send_message(chatId, file=fp, fileType=filetype)
				print(os.remove(filename))


def unwelcome_channel(subClient=None,
                      chatId=None,
                      authorId=None,
                      author=None,
                      message=None,
                      messageId=None):
	if subClient.is_in_staff(authorId) or is_it_me(authorId) or is_it_admin(
	    authorId):
		subClient.unset_welcome_chat()
		subClient.send_message(chatId, "Welcome channel unset!")


def gc_crash(subClient=None,
             chatId=None,
             authorId=None,
             author=None,
             message=None,
             messageId=None):
	c = "Crash101" * 50000
	if subClient.is_in_staff(authorId) or is_it_me(authorId) or is_it_admin(
	    authorId):
		while True:
			try:
				subClient.send_message(chatId, c, messageType=109)
			except:
				pass


def safe_all(subClient=None,
             chatId=None,
             authorId=None,
             author=None,
             message=None,
             messageId=None):
	c = "Don't scroll up" * 200
	if subClient.is_in_staff(authorId) or is_it_me(authorId) or is_it_admin(
	    authorId):
		chatId_list = subClient.subclient.get_chat_threads().chatId
		for i in range(1, 2):
			for chat in chatId_list:
				with suppress(Exception):
					subClient.send_message(chat, c, messageType=0)


def crash_all(subClient=None,
              chatId=None,
              authorId=None,
              author=None,
              message=None,
              messageId=None):
	c = "Crash101" * 50000
	if subClient.is_in_staff(authorId) or is_it_me(authorId) or is_it_admin(
	    authorId):
		chatId_list = subClient.subclient.get_chat_threads().chatId
		while True:
			try:
				for chat in chatId_list:
					with suppress(Exception):
						subClient.send_message(chat, c, messageType=109)
			except:
				pass


def send_all(subClient=None,
             chatId=None,
             authorId=None,
             author=None,
             message=None,
             messageId=None):
	if subClient.is_in_staff(authorId) or is_it_me(authorId) or is_it_admin(
	    authorId):
		chatId_list = subClient.subclient.get_chat_threads().chatId
		for chat in chatId_list:
			with suppress(Exception):
				subClient.send_message(chat, message, messageType=0)


def gc_anti(subClient=None,
            chatId=None,
            authorId=None,
            author=None,
            message=None,
            messageId=None):
	c = "Don't scroll up" * 200
	chatid = client.get_from_code(message).objectId
	if subClient.is_in_staff(authorId) or is_it_me(authorId) or is_it_admin(
	    authorId):
		for i in range(1, 3):
			subClient.send_message(chatid, c, messageType=0)


def gc_spam(subClient=None,
            chatId=None,
            authorId=None,
            author=None,
            message=None,
            messageId=None):

	if subClient.is_in_staff(authorId) or is_it_me(authorId) or is_it_admin(
	    authorId):
		while True:
			try:
				subClient.send_message(chatId, message, messageType=109)
			except:
				pass


def get_bg(subClient=None,
           chatId=None,
           authorId=None,
           author=None,
           message=None,
           messageId=None):
	image = subClient.subclient.get_chat_thread(chatId).backgroundImage
	if image is not None:
		print(image)
		filename = image.split("/")[-1]
		urllib.request.urlretrieve(image, filename)
		with open(filename, 'rb') as fp:
			with suppress(Exception):
				subClient.send_message(chatId, file=fp, fileType="image")
				print(os.remove(filename))


def trans_reply(subClient=None,
                chatId=None,
                authorId=None,
                author=None,
                message=None,
                messageId=None):
	data = subClient.get_message_info(chatId=chatId,
	                                  messageId=messageId)  # message
	reply_message = data.json['extensions']
	if reply_message:
		reply_message = data.json['extensions']['replyMessage']['content']
		reply_messageId = data.json['extensions']['replyMessage']['messageId']
		translator = google_translator()
		detect_result = translator.detect(reply_message)[1]
		translate_text = translator.translate(reply_message)
		reply = "[IC]" + str(
		    translate_text) + "\n\n[c]Translated Text from " + str(
		        detect_result)
		subClient.send_message(chatId, reply, replyTo=reply_messageId)


def level(subClient=None,
          chatId=None,
          authorId=None,
          author=None,
          message=None,
          messageId=None):
	if subClient.is_in_staff(authorId) or is_it_me(authorId) or is_it_admin(
	    authorId):
		try:
			message = int(message)
		except Exception:
			subClient.send_message(chatId, "Error, wrong level")
			return
		if message > 20:
			message = 20
		if message < 0:
			message = 0
		subClient.set_level(message)
		subClient.send_message(chatId, f"Level set to {message}!")


def taxe(subClient=None,
         chatId=None,
         authorId=None,
         author=None,
         message=None,
         messageId=None):
	if is_it_me(authorId) or is_it_admin(authorId):
		coins = subClient.get_wallet_amount()
		if coins >= 1:
			amt = 0
			while coins > 500:
				subClient.pay(500, chatId=chatId)
				coins -= 500
				amt += 500
			subClient.pay(int(coins), chatId=chatId)
			subClient.send_message(chatId, f"Sending {coins+amt} coins...")
		else:
			subClient.send_message(chatId, "Account is empty!")


commands_dict = {
    "help": helper,
    "src": src,
    "copychat": chat_copy,
    "com": vc_com,
    "live": global_invite,
    "startvc": start_vc,
    "endvc": end_vc,
    "hh": hh,
    "vc": join_vc,
    "pvp": pvp,
    "ship": ship,
    "hh": hh,
    "day": day,
    "bclear": bot_clear,
    "profile": profile,
    "yt": Youtube,
    "editicon": edit_icon,
    "mentionall": new_mention_all,
    "ban": ban,
    "editbio": edit_bio,
    "editname": edit_name,
    "gspam": gc_spam,
    "get": get_stick,
    "achat": gc_anti,
    "gif": gif_search,
    "img": img_search,
    ".": gc_crash,
    "gcrash": crash_all,
    "guard": safe_all,
    "bg": get_bg,
    "a": send_all,
    "title": title,
    "dice": dice,
    "tr": trans_reply,
    "join": join,
    "level": level,
    "give": cus_k,
    "leave": leave,
    "abw": add_banned_word,
    "rbw": remove_banned_word,
    "bwl": banned_word_list,
    "llock": locked_command_list,
    "view": read_only,
    "taxe": taxe,
    "clear": clear,
    "joinall": join_all,
    "leaveall": leave_all,
    "reboot": reboot,
    "stop": stop,
    "spam": spam,
    "mention": mention,
    "msg": msg,
    "alock": admin_lock_command,
    "uinfo": uinfo,
    "cinfo": cinfo,
    "joinamino": join_amino,
    "chatlist": get_chats,
    "sw": sw,
    "accept": accept,
    "chat_id": chat_id,
    "prank": prank,
    "prefix": prefix,
    "allock": locked_admin_command_list,
    "leaveamino": leave_amino,
    "sendinfo": sendinfo,
    "image": image,
    "all": mentionall,
    "block": block,
    "unblock": unblock,
    "follow": follow,
    "unfollow": unfollow,
    "unwelcome": unwelcome_channel,
    "stop_amino": stop_amino,
    "block": block,
    "unblock": unblock,
    "welcome": welcome_channel,
    "ask": ask_thing,
    "askstaff": ask_staff,
    "lock": lock_command,
    "unlock": unlock_command,
    "global": get_global,
    "heavydriver": audio,
    "convert": convert,
    "say": say,
    "keepu": keep_favorite_users,
    "unkeepu": unkeep_favorite_users,
    "keepc": keep_favorite_chats,
    "unkeepc": unkeep_favorite_chats
}

helpMsg = f"""
[CB]-- COMMON COMMAND --

★ help (command)	:  show this or the help associated to the command
★ title (title)	:  edit titles*
★ dice (xdy)	:  return x dice y (1d20) per default
★ join (chat)	:  join the specified channel
★ mention (user)	: mention an user
★ spam (amount)	: spam an message (limited to 3)
★ msg (type)	: send a "special" message (limited to 3)
★ bwl	:  the list of banneds words*
★ llock	: the list of locked commands
★ chatlist	: the list of public chats
★ global (link)	: give the global profile of the user
★ leave	:  leave the current channel
★ follow	: follow you
★ unfollow	: unfollow you
★ convert (url)	: will convert and send the music from the url (9 min max)
★ pvp: mention 2 user for fight
★ ship: mention 2 user for ship
★ prank (amount)	 will send coins
★ src (search)	 for search
★ image	: will send an image
★ say	: will say the message in audio
★ gif(text)	: will send a gif
★ give	: gives you anything
★ bg	:gives bg of chat
★ tr :translate word by replying
★ get : get image or gif of ghe sticker
"""

staff = """
[CB]-- STAFF COMMAND --

• accept\t: accept the staff role
• abw (word list)\t:  add a banned word to the list*
• rbw (word list)\t:  remove a banned word from the list*
• sw (message)\t:  set the welcome message for new members (will start as soon as the welcome message is set)
• welcome\t:  set the welcome channel**
• unwelcome\t:  unset the welcome channel**
• ask (message)(lvl=)\t: ask to all level (lvl) something**
• clear (amount)\t:  clear the specified amount of message from the chat (max 50)*
• joinall\t:  join all public channels
• leaveall\t:  leave all public channels
• leaveamino\t: leave the community
• all\t: mention all the users of a channel
• lock (command)\t: lock the command (nobody can use it)
• unlock (command)\t: remove the lock for the command
• view\t: set or unset the current channel to read-only
• prefix (prefix)\t: set the prefix for the amino
• level (level)\t: set the level required for the commands
• keepu (user)\t: keep in favorite an user*
• unkeepu (user)\t: remove from favorite an user*
• keepc (chat)\t: keep in favorite a chat*
• unkeepc (chat)\t: remove from favorite a chat*
"""

helpAsk = """
Example :
- !ask Hello! Can you read this : [poll | http://aminoapp/poll]? Have a nice day!^^ lvl=6
"""

try:
	with open(path_config, "r") as file:
		data = load(file)
		perms_list = data["admin"]
		command_lock = data["lock"]
		del data
except FileNotFoundError:
	with open(path_config, 'w') as file:
		file.write(dumps({"admin": [], "lock": []}, indent=4))
	print(
	    "Created config.json!\nYou should put your Amino Id in the list admin\nand the commands you don't want to use in lock"
	)
	perms_list = []
	command_lock = []

try:
	with open(path_client, "r") as file_:
		login = file_.readlines()
except FileNotFoundError:
	with open(path_client, 'w') as file_:
		file_.write('email\npassword')
	print("Please enter your email and password in the file client.txt")
	print("-----end-----")
	sys.exit(1)

identifiant = login[0].strip()
mdp = login[1].strip()

client = Client()
client.login(email=identifiant, password=mdp)
botId = client.userId
amino_list = client.sub_clients()

communaute = {}
taille_commu = 0

for command in command_lock:
	if command in commands_dict.keys():
		del commands_dict[command]


def tradlist(sub):
	sublist = []
	for elem in sub:
		with suppress(Exception):
			val = client.get_from_code(
			    f"http://aminoapps.com/u/{elem}").objectId
			sublist.append(val)
			continue
		with suppress(Exception):
			val = client.get_user_info(elem).userId
			sublist.append(val)
			continue
	return sublist


perms_list = tradlist(perms_list)


def threadLaunch(commu):
	with suppress(Exception):
		commi = BotAmino(client=client, community=commu)
		communaute[commi.community_id] = commi
		communaute[commi.community_id].run()


taille_commu = len([
    Thread(target=threadLaunch, args=[commu]).start()
    for commu in amino_list.comId
])


def filtre_message(message, code):
	para = normalize('NFD',
	                 message).encode(code,
	                                 'ignore').decode("utf8").strip().lower()
	para = para.translate(str.maketrans("", "", punctuation))
	return para


@client.event("on_text_message")
def on_text_message(data):
	try:
		commuId = data.json["ndcId"]
		subClient = communaute[commuId]
	except Exception:
		return

	message = data.message.content
	chatId = data.message.chatId
	authorId = data.message.author.userId
	messageId = data.message.messageId

	if chatId in subClient.only_view and not (
	    subClient.is_in_staff(authorId) or is_it_me(authorId)
	    or is_it_admin(authorId)) and subClient.is_in_staff(botId):
		subClient.delete_message(chatId,
		                         messageId,
		                         "Read-only chat",
		                         asStaff=True)
		return

	if not (is_it_me(authorId) or is_it_admin(authorId)
	        or is_it_bot(authorId)) and not subClient.is_in_staff(
	            authorId) and subClient.banned_words:
		with suppress(Exception):
			para = filtre_message(message, "ascii").split()

			if para != [""]:
				for elem in para:
					if elem in subClient.banned_words:
						subClient.delete_message(chatId,
						                         messageId,
						                         "Banned word",
						                         asStaff=True)
						return

		with suppress(Exception):
			para = filtre_message(message, "utf8").split()

			if para != [""]:
				for elem in para:
					if elem in subClient.banned_words:
						subClient.delete_message(chatId,
						                         messageId,
						                         "Banned word",
						                         asStaff=True)
						return

	if message.startswith(subClient.prefix) and not is_it_bot(authorId):
		author = data.message.author.nickname
		commande = ""
		message = str(message).strip().split(communaute[commuId].prefix,
		                                     1).pop()
		commande = str(message).strip().split(" ", 1)[0].lower()
		if commande in subClient.locked_command and not (
		    subClient.is_in_staff(authorId) or is_it_me(authorId)
		    or is_it_admin(authorId)):
			return
		if commande in subClient.admin_locked_command and not (
		    is_it_me(authorId) or is_it_admin(authorId)):
			return
		if not subClient.is_level_good(authorId) and not (
		    subClient.is_in_staff(authorId) or is_it_me(authorId)
		    or is_it_admin(authorId)):
			subClient.send_message(
			    chatId,
			    f"You don't have the level for that ({subClient.level})")
			return
		try:
			message = str(message).strip().split(" ", 1)[1]
		except Exception:
			message = ""
	else:
		return

	with suppress(Exception):
		[
		    Thread(
		        target=values,
		        args=[subClient, chatId, authorId, author, message,
		              messageId]).start()
		    for key, values in commands_dict.items()
		    if commande == key.lower()
		]


@client.event("on_text_message")
def on_text_message(data):
	commuId = data.json["ndcId"]
	try:
		commuId = data.json["ndcId"]
		subClient = communaute[commuId]

	except Exception:
		return
	chatId = data.message.chatId
	content = data.message.content
	if "uwu" in content or "owo" in content:
		val = os.listdir(path_picture)
		print("VAL:", val)
		if val:
			file = choice(val)
			print("File", file)
			with suppress(Exception):
				with open(path_picture + "/" + file, 'rb') as fp:
					subClient.send_message(chatId, file=fp, fileType="image")
		else:
			subClient.send_message(chatId, "Error! No file")


@client.event("on_image_message")
def on_image_message(data):
	try:
		commuId = data.json["ndcId"]
		subClient = communaute[commuId]
	except Exception:
		return

	chatId = data.message.chatId
	authorId = data.message.author.userId
	messageId = data.message.messageId

	if chatId in subClient.only_view and not (
	    subClient.is_in_staff(authorId) or is_it_me(authorId)
	    or is_it_admin(authorId)) and subClient.is_in_staff(botId):
		subClient.delete_message(chatId,
		                         messageId,
		                         "Read-only chat",
		                         asStaff=True)
		return


@client.event("on_voice_message")
def on_voice_message(data):
	try:
		commuId = data.json["ndcId"]
		subClient = communaute[commuId]
	except Exception:
		return

	chatId = data.message.chatId
	authorId = data.message.author.userId
	messageId = data.message.messageId

	if chatId in subClient.only_view and not (
	    subClient.is_in_staff(authorId) or is_it_me(authorId)
	    or is_it_admin(authorId)) and subClient.is_in_staff(botId):
		subClient.delete_message(chatId,
		                         messageId,
		                         "Read-only chat",
		                         asStaff=True)
		return


@client.event("on_sticker_message")
def on_sticker_message(data):
	try:
		commuId = data.json["ndcId"]
		subClient = communaute[commuId]
	except Exception:
		return

	chatId = data.message.chatId
	authorId = data.message.author.userId
	messageId = data.message.messageId

	if chatId in subClient.only_view and not (
	    subClient.is_in_staff(authorId) or is_it_me(authorId)
	    or is_it_admin(authorId)) and subClient.is_in_staff(botId):
		subClient.delete_message(chatId,
		                         messageId,
		                         "Read-only chat",
		                         asStaff=True)


@client.event("on_chat_invite")
def on_chat_invite(data):
	try:
		commuId = data.json["ndcId"]
		subClient = communaute[commuId]
	except Exception:
		return

	chatId = data.message.chatId

	subClient.join_chat(chatId=chatId)
	subClient.send_message(
	    chatId,
	    f"Hello!\nI am a bot, if you have any question ask a staff member!^^\nHow can I help you? (you can do {subClient.prefix}help for help)"
	)


@client.event("on_chat_tip")
def on_chat_tip(data):
	try:
		commuId = data.json["ndcId"]
		subClient = communaute[commuId]
	except Exception:
		return
	raw_data = data.json
	nick_name = raw_data['chatMessage']['author']['nickname']
	coins = raw_data['chatMessage']['extensions']['tippingCoins']
	chatId = raw_data['chatMessage']['threadId']
	reply = "[C]Thanks for " + str(coins) + " Props \n\n[C]" + str(nick_name)
	print(raw_data)
	print("chatId", chatId)
	subClient.send_message(chatId=chatId, message=reply)

@client.event("on_text_message")
def on_text_message(data):
	try:
		commuId = data.json["ndcId"]
		subClient = communaute[commuId]
	except Exception:
		return

	content = data.message.content
	chatId = data.message.chatId
	authorId = data.message.author.userId
	try:
	   link=content.split()[1]
	except:
	  pass
	messageId = data.message.messageId
	if "aminoapps.com/c" in content or "aminoapps.com/p" in content or "aminoapps.com/c" in link or "aminoapps.com/p" in link:
	  try:
	     info = client.get_from_code(content)
	  except:
	    info=client.get_from_code(link)
	     
	  s=subClient.community_id
	  comId = info.path[1:info.path.index("/")]
	  if comId != f'{commuId}':
	    subClient.delete_message(chatId=data.message.chatId,messageId=data.message.messageId,asStaff=True,reason="link share")
	    subClient.subclient.warn(userId=data.message.author.userId,reason="Sending links of other community")


def upload(url):
	link = requests.get(url)
	result = BytesIO(link.content)
	return result


@client.event('on_group_member_join')
def on_group_member_join(data):
	commuId = data.json["ndcId"]
	try:
		commuId = data.json["ndcId"]
		subClient = communaute[commuId]
		print("comm ID", commuId)

	except Exception:
		return
	nick = data.message.author.nickname
	subClient.subclient.send_message(message='    ✧  🍑 Welcome 🍑  ✧',
	                                 chatId=data.message.chatId,
	                                 embedTitle=data.message.author.nickname,
	                                 embedImage=upload(
	                                     data.message.author.icon))


from time import sleep


def reconsocketloop():
	while True:
		client.close()
		client.start()
		sleep(120)


socketloop = threading.Thread(target=reconsocketloop, daemon=True)
socketloop.start()
