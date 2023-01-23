from Constants.Cards import cartas_aventura

import logging as log

import copy
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update, ForceReply, Update

from Arcana.Boardgamebox.State import State
from Boardgamebox.Board import Board as BaseBoard

from Arcana.Constants.Cards import FATETOKENS, ARCANACARDS, LASHORAS

log.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=log.INFO)


logger = log.getLogger(__name__)

class Board(BaseBoard):
	def __init__(self, playercount, game):
		BaseBoard.__init__(self, playercount, game)
		self.arcanaCards = random.sample(copy.deepcopy(ARCANACARDS), len(ARCANACARDS))
		self.fateTokens = random.sample(copy.deepcopy(FATETOKENS), len(FATETOKENS))		
		# Se seteara en difficultad el doom inicial
		self.state = State()
		
	def draw_fate_token(self):		
		# Los tokens son siempre los mismos. Mezclo cada vez que saco.
		random.shuffle(self.fateTokens)
		return self.fateTokens.pop()
	
	def print_board(self, bot, game):
		#import Arcana.Controller as ArcanaController
		
		bot.send_message(game.cid, "--- *Estado de Partida* ---\nCondena: {}/7.\nPuntaje {}/7\nCartas en mazo/descarte {}/{}"
				 .format(self.state.doom, self.state.score, len(self.arcanaCards), len(self.state.discardedArcanas)), parse_mode=ParseMode.MARKDOWN, timeout=30)
		btns = []
		btns.append([self.create_arcana_button(game.cid, self.arcanaCards[len(self.arcanaCards)-1])])
		btnMarkup = InlineKeyboardMarkup(btns)
		bot.send_message(game.cid, "*Arcana de arriba del mazo:*", 
				 parse_mode=ParseMode.MARKDOWN, reply_markup=btnMarkup, timeout=30)
		board = "*Arcanas Activas*:\n"
		btns = []
		i = 0
		for arcana_on_table in game.board.state.arcanasOnTable:
			btns.append([self.create_arcana_button(game.cid, arcana_on_table, i)])
			i += 1
		btnMarkup = InlineKeyboardMarkup(btns)
		bot.send_message(game.cid, "*Arcanas Activas*:", parse_mode=ParseMode.MARKDOWN, reply_markup=btnMarkup, timeout=30)
		
		if len(game.board.state.fadedarcanasOnTable) > 0:
			btns = []
			i = 0
			for arcana_on_table in game.board.state.fadedarcanasOnTable:
				btns.append([self.create_arcana_button(game.cid, arcana_on_table, -2)])
				i += 1
			btnMarkup = InlineKeyboardMarkup(btns)
			bot.send_message(game.cid, "*Arcanas desvanecidas* para usar /remove N:", 
					 parse_mode=ParseMode.MARKDOWN, reply_markup=btnMarkup, timeout=30)
		
		board = ""		
		board += "--- *Orden de jugadores* ---\n"
		for player in game.player_sequence:
			nombre = ""
			if self.state.active_player == player:
				nombre += "*{}({})*".format(player.name.replace("_", " "), len(player.fateTokens))
			else:
				nombre += "{}({})".format(player.name.replace("_", " "), len(player.fateTokens))
			board += "{}".format(nombre) + " " + u"\u27A1\uFE0F" + " "
		board = board[:-3]
		board += u"\U0001F501"
		board += "\n\nEl jugador *{0}* es el jugador activo".format(game.board.state.active_player.name)
		bot.send_message(game.cid, board, parse_mode=ParseMode.MARKDOWN, timeout=30)
		#ArcanaController.show_player_fate_tokens_active_player(bot, game)
	
	def create_arcana_button(self, cid, arcana, index = '-1', comando_callback = 'txtArcanaAR'):
		if 'tokens' not in arcana:
			arcana['tokens'] = []
		
		faded = "faded" in arcana and arcana["faded"]
		
		lunas = arcana["Lunas"]
		if faded:
			titulo = arcana["Título reverso"]
		else:
			texto = arcana["Texto"]
			titulo = arcana["Título"]
			
		#if len(tokens) > 0:
		txt_tokens = ""
		if len(arcana['tokens']) > 0:
			for fate in arcana['tokens']:
				txt_tokens += "{}, ".format(fate["Texto"])
			txt_tokens = "[{}]".format(txt_tokens[:-2])
		tokens_lunas = "" if (titulo == "Las horas" or faded) else "({}/{})".format(self.count_fate_tokens(arcana), lunas) 
		txtBoton = "{} {} {}".format(titulo, txt_tokens, tokens_lunas)
		comando_callback = comando_callback
		datos = str(cid) + "*" + comando_callback + "*" + str(titulo) + "*" + str(index)
		#log.info(datos)
		return InlineKeyboardButton(txtBoton, callback_data=datos)

	def print_arcana_front(self, arcana):
		return "*{}*\n{}\nCantidad de lunas: {}\n".format(arcana["Título"], arcana["Texto"], arcana["Lunas"])
	
	def print_arcana_back(self, arcana):
		return "*{}*\n{}\n".format(arcana["Título reverso"], arcana["Texto reverso"])
	
	def print_result(self, game):		
		resultado = ""
		if game.board.state.score > 6:
			resultado = "Han ganado!"
		else:
			resultado = "Han perdido!"
		return resultado
	def count_fate_tokens(self, arcana):
		i = 0
		for fate in arcana['tokens']:
			i += int(fate["TimeSymbols"])
		return i
	
	def is_legal_arcana(self, arcana, chosen_fate, unchosen_fate):
		if arcana["Título"] == "Las horas":
			arcana_db = copy.deepcopy(LASHORAS)
		else:
			arcana_db = copy.deepcopy(next((item for item in ARCANACARDS if item["Título"] == arcana["Título"]), -1))
		if 'tokens' not in arcana:
			arcana['tokens'] = []
		my_tokens = [int(item['Texto']) for item in arcana['tokens']]
		
		all_tokens = [int(item['Texto']) 
				 for sublist in [arcana['tokens'] 
						 for arcana in self.state.arcanasOnTable ] 
				 for item in sublist]
		#log.info(all_tokens)
		#log.info( 'En el medio de is legal arcana {} {} {} {}'.format(int(unchosen_fate["Texto"]),
		#	int(chosen_fate["Texto"]), my_tokens, all_tokens))
		int_unchosen_fate, int_chosen_fate = int(unchosen_fate["Texto"]), int(chosen_fate["Texto"])
		is_legal_arcana = arcana_db["Legal"](int_unchosen_fate, int_chosen_fate, my_tokens, all_tokens)
		#log.info('Finalizando is legal arcana {}'.format(is_legal_arcana))
		
		# Excepciones Sacar es la unica al momento. 
		if self.state.used_sacar and arcana["Título"] == "Sacar":
			is_legal_arcana = False
		
		return is_legal_arcana
		
	def get_valid_arcanas(self, fate_token1, fate_token2):
		valid_arcanas_fates = []
		for arcana in (arcana for arcana in self.state.arcanasOnTable if arcana["Título"] != "Las horas"):
			if(self.is_legal_arcana(arcana, fate_token1, fate_token2)):
				valid_arcanas_fates.append([arcana, fate_token1, fate_token2])
			if(self.is_legal_arcana(arcana, fate_token2, fate_token1)):
				valid_arcanas_fates.append([arcana, fate_token2, fate_token1])
		return valid_arcanas_fates
