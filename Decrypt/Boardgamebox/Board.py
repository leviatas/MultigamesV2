import logging as log

import copy
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update, ForceReply, Update

from Decrypt.Boardgamebox.State import State
from Boardgamebox.Board import Board as BaseBoard

log.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=log.INFO)


logger = log.getLogger(__name__)

class Board(BaseBoard):
	def __init__(self, playercount, game):
		BaseBoard.__init__(self, playercount, game)
		self.cards = None
		self.discard = None
		# Se seteara en difficultad el doom inicial
		self.state = State()
	
	def print_board(self, bot, game):
		#import Arcana.Controller as ArcanaController
		board = ""
		board += "--- *Estado de Partida Turno {}* ---\n".format(game.turncount)		
		board += "--- *Orden de jugadores* ---\n"
		for team in game.board.state.teams:
			if game.board.state.active_team == team:
				board += "*‼️{}‼️️ (I = {} M = {})*: ".format(team.name, team.interceptions, team.miscommunications)
			else:
				board += "{} (I = {} M = {}): ".format(team.name, team.interceptions, team.miscommunications)
			for player in self.starting_with(team.player_sequence, team.player_counter):
				nombre = player.name.replace("_", " ")
				if team.active_player == player:
					board += "‼️*" + nombre + "*‼️" + " " + u"\u27A1\uFE0F" + " "
				else:
					board += nombre + " " + u"\u27A1\uFE0F" + " "
			board = board[:-3]
			board += u"\U0001F501"
			board += "\n\n"
		if game.turncount == 8:
			board += "‼️Este es el ultimo turno‼️\n\n"
		bot.send_message(game.cid, board, parse_mode=ParseMode.MARKDOWN)
	
	def new_round(self, game):
		# Create Decrypt card for both teams and set choosen variables to none
		for team in game.board.state.teams:
			team.generate_decrypt_card(5)	

	def starting_with(self, lst, start):
		for idx in range(len(lst)):
			yield  lst[(idx + start) % len(lst)]