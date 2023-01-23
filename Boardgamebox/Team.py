import logging as log

import copy
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update, ForceReply, Update
from Utils import player_call
log.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=log.INFO)


logger = log.getLogger(__name__)

class Team(object):
	def __init__(self, name):
		self.name = name
		self.player_sequence = []
	# Returns true if uid belong to team 
	def belongs(self, uid):
		for player in self.player_sequence:
			if player.uid == uid:
				return True
		return False

	def getPlayer(self, uid):
		for player in self.player_sequence:
			if player.uid == uid:
				return player
		return None

	def generate_call_team_players(self, exclude = []):
		call_other_players = ""
		for player in self.player_sequence:
			if player.uid not in exclude:
				call_other_players += "{} ".format(player_call(player))
		return call_other_players
	
	def communicate_team(self, bot, message, exclude = [], messanger = "", groupName = ""):		
		final_message = "{}{}".format("*{} ({})*: ".format(messanger,groupName) if messanger != "" else "", message)
		for player in self.player_sequence:
			if player.uid not in exclude:
				bot.send_message(player.uid, final_message, ParseMode.MARKDOWN)