import logging as log

import itertools
import copy
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update, ForceReply, Update

from Boardgamebox.Team import Team as BaseTeam
from Utils import player_call

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
		self.code = None
		self.clue = None
		self.team_choosen_code = None
		self.opponent_team_choosen_code = None
		# Palabras del equipo que se usan para asociar los numeros del codigo para generar la pista (clue)
		self.cards = []
		self.miscommunications = 0
		self.interceptions = 0
		self.half_gueses = 0
		self.history = ["*Key 1*\n","*Key 2*\n","*Key 3*\n","*Key 4*\n"]
		self.round_history = []
	
	def generate_decrypt_card(self, n = 5):
		lista = [x for x in range(n) if x != 0]
		a = list(itertools.permutations(lista, len(lista)-1))
		self.code = "".join(map(str, a[random.randint(1,len(a))])) 
		self.clue = None
		self.team_choosen_code = None
		self.opponent_team_choosen_code = None
	
	def increment_player_counter(self):
		if self.player_counter < len(self.player_sequence) - 1:
			self.player_counter += 1			
		else:
			self.player_counter = 0
		self.active_player = self.player_sequence[self.player_counter]
	
	def count_points(self, value_intercept, value_miscommunication, allow_half_guess, value_half_guess):
		total = (value_intercept * self.interceptions) + (value_miscommunication * self.miscommunications) 		
		if allow_half_guess:
			total += self.half_gueses * value_half_guess
		return total
	
	def saveHistory(self, clue, code):
		if not hasattr(self, 'round_history'):
			self.round_history = []
		self.round_history.append("{}:{}".format(code, clue))
		clues = clue.split(',')		
		for idx, numero in enumerate(code):
			self.history[int(numero)-1] += "{}\n".format(clues[idx].strip())
			
	def printHistory(self, show_words = False):
		result = "*Historial del equipo {}*\n".format(self.name)			
		keys_text = ""
		i = 1
		for keys in self.history:
			#if len(keys) > 8:
			# Si es del equipo muestra la palabra en vez de KEY X
			if show_words:
				#log.info("{} {}".format("Key {}".format(i), self.cards[i-1]))
				keys = keys.replace("Key {}".format(i), self.cards[i-1].title())
			#log.info(keys)
			keys_text += keys
			i += 1
		if (len(keys_text) > 0):
			return result + keys_text
		else:
			return ""
	
	def generate_decrypt_message(self, groupName):
		call_other_players = self.generate_call_team_players([self.active_player.uid])	
		message = "Partida en el grupo *{}* con la referencia dada por {} con tus compañeros {}\n\nLas palabras son *{}*.\nLa referencia es {}\nUsa /team MSG para comunicarte y /decrypt XXX para desencriptar".format(groupName, 
														player_call(self.active_player), call_other_players,", ".join(self.cards), self.clue)
		return message
	def generate_intercept_message(self, groupName, clue):
		call_other_players = self.generate_call_team_players()
		message = "Partida en el grupo *{}* con tus compañeros {}\n\nLas referencia es *{}*\n Usen comando /team MSG para comunicarse y /intercept XXX para interceptar".format(groupName, call_other_players, clue)
		return message

	def generate_code_message(self, groupName):
		call_other_players = self.generate_call_team_players([self.active_player.uid])
		message = "Partida en el grupo *{}* con tus compañeros {}\n\nLa carta que te ha tocado es: *{}*.\nLas palabras son *{}*\nPone tu pista con /code PISTA2, PISTA4, PISTA3.\n{}".format(
			groupName, call_other_players, self.code, ", ".join(self.cards), self.printHistory(True))
		return message	
	


