from Constants.Cards import cartas_aventura

import logging as log

import copy
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update, ForceReply, Update

from Wavelength.Boardgamebox.State import State
from Boardgamebox.Board import Board as BaseBoard

from Wavelength.Constants.Cards import WAVECARDS

log.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=log.INFO)


logger = log.getLogger(__name__)

class Board(BaseBoard):
	def __init__(self, playercount, game):
		BaseBoard.__init__(self, playercount, game)
		self.wave_cards = random.sample(copy.deepcopy(WAVECARDS), len(WAVECARDS))	
		self.discarded_wave_cards = []
		# Se seteara en difficultad el doom inicial
		self.state = State()
	
	def print_board(self, bot, game):
		#import Arcana.Controller as ArcanaController
		board = ""
		board += "--- *Estado de Partida Turno {}* ---\n".format(game.turncount)		
		board += "--- *Orden de jugadores* ---\n"
		for team in game.board.state.teams:
			if game.board.state.active_team == team:
				board += "*{} ({})*: ".format(team.name, team.score)
			else:
				board += "{} ({}): ".format(team.name, team.score)
			for player in team.player_sequence:
				nombre = player.name.replace("_", " ")
				if team.active_player == player:
					board += "*" + nombre + "*" + " " + u"\u27A1\uFE0F" + " "
				else:
					board += nombre + " " + u"\u27A1\uFE0F" + " "
			board = board[:-3]
			board += u"\U0001F501"
			board += "\n\n"
		bot.send_message(game.cid, board, parse_mode=ParseMode.MARKDOWN)
	
	def new_wave_card(self):
		# I discard the previous wave_card
		if self.state.active_wave_card != None:
			self.discard_wave_card()
		# Set next wave_card, add discard and shuffle the deck
		if len(self.wave_cards) == 0:
			self.wave_cards.extend(self.discarded_wave_cards)
			self.discarded_wave_cards = []
			random.shuffle(self.wave_cards)
	
		self.state.active_wave_card = self.wave_cards.pop()
		# Set current point in wavelength Random (0 - 180)
		self.state.wavelength = random.randint(0, 180)
		self.state.reference = None
		self.state.team_choosen_grade = -1
		self.state.opponent_team_choosen_left_right = -1
		
	def discard_wave_card(self):
		self.discarded_wave_cards.append(self.state.active_wave_card)
		self.state.active_wave_card = None
