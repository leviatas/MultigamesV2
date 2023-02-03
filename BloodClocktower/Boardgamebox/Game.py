import json
from datetime import datetime
from random import shuffle, randint

from Boardgamebox.Game import Game as BaseGame
from BloodClocktower.Boardgamebox.Player import Player
from BloodClocktower.Boardgamebox.Board import Board
#from Boardgamebox.Board import Board
#from Boardgamebox.State import State
from Utils import get_config_data, basic_validation

class Game(BaseGame):
	def __init__(self, cid, initiator, groupName):
		BaseGame.__init__(self, cid, initiator, groupName, None, None)
		
		self.using_timer = False	
	
	def get_rules(self):
		return ["""El juego es una combinacion de Werewolf y Preguntas para adivinar una o mas palabras
Un jugador, el mayor, responderá las preguntas y sabrá la respuesta.

Los jugadores, o el mayor, pueden tener estos roles:
Aldeano = No conoce la palabra y tiene que adivinarla.
Lobo = Conoce la palabra y quiere que *NO* se adivine.
Vidente = Conoce la palabra y quiere que se adivine.

El mayor si es:
Vidente = Tiene que ver de escoger una palabra fácil ya que no hay vidente.
Lobo = Tiene que desviar de la palabra pero no ser muy obvio porque sino lo descubren.

Al final del partido (cuando se adivina la palabra o el equipo se queda sin preguntas) pasa lo siguiente:

Si se adivino la palabra, se revelan los hombres lobo y estos señalan a un jugador, *si adivinan a la vidente*, ellos ganan.

Si NO se adivino la palabra, los aldeanos votan a ver quien es el lobo. *Si un lobo le dan la mayoria, o empata en mayoria de votos*, los lobos pierden."""]
		
		
	# Creacion de player de juego.	
	def add_player(self, uid, name):
		self.playerlist[uid] = Player(name, uid)

	def create_board(self):
		player_number = len(self.playerlist)
		self.board = Board(player_number, self)
	
	def verify_turn(self, uid):
		if self.board.state.fase_actual == "Proponiendo Pistas":
			return uid not in self.board.state.last_votes
		else:
			return False

	def myturn_message(self, uid):
		try:
			group_link_name = self.groupName if get_config_data(self, "link") is None else "[{0}]({1})".format(self.groupName, get_config_data(self, "link"))
			if self.board.state.fase_actual == "Proponiendo Pistas":
				mensaje_clue_ejemplo = "Ejemplo: Si la palabra fuese (Fiesta)\n/words Cumpleaños, Torta, Decoracion, Musica, Rock, Infantil, Luces, Velas"
				return f"Partida: {group_link_name} debes dar {mensaje_clue_ejemplo}. \nLa palabra es : *{self.board.state.acciones_carta_actual}* propone tus palabras!."
		except Exception as e:
			return str(e)

	def resetPlayerPoints(self):
		for player in self.playerlist.values():
			player.points = 0

	def call(self, context):
		import BloodClocktower.Commands as BloodClocktowerCommands
		if self.board is not None:
				BloodClocktowerCommands.command_call(context.bot, self)
				
	def timer(self, update, context):
		import BloodClocktower.Commands as BloodClocktowerCommands
		if self.board is not None:
			BloodClocktowerCommands.callback_timer(update, context)
