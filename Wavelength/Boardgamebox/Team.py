import logging as log

import copy
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update, ForceReply

from Boardgamebox.Team import Team as BaseTeam

log.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=log.INFO)


logger = log.getLogger(__name__)

class Team(BaseTeam):
	def __init__(self, name, members):
		BaseTeam.__init__(self, name)
		self.score = 0
		self.player_sequence = members
		self.player_counter = -1
		self.active_player = None
		
	def increment_player_counter(self):
		if self.player_counter < len(self.player_sequence) - 1:
			self.player_counter += 1			
		else:
			self.player_counter = 0
		self.active_player = self.player_sequence[self.player_counter]
