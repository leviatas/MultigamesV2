import json
from datetime import datetime
from random import shuffle, randint

from Boardgamebox.Game import Game as BaseGame
from Unanimo.Boardgamebox.Player import Player
from Unanimo.Boardgamebox.Board import Board
#from Boardgamebox.Board import Board
#from Boardgamebox.State import State
from Utils import get_config_data, basic_validation

class Game(BaseGame):
	def __init__(self, cid, initiator, groupName, tipo = None, modo = None):
		BaseGame.__init__(self, cid, initiator, groupName, tipo, modo)
		self.modulos = []
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
		return False

	def myturn_message(self, uid):		
		group_link_name = self.groupName if get_config_data(self, "link") is None else "[{0}]({1})".format(self.groupName, get_config_data(self, "link"))
		
		if self.board.state.fase_actual == "Set_Reference":
			msg = ""
			return msg
		if self.board.state.fase_actual == "Intercept/Decrypt":
			msg = ""
			return msg

	def print_roles(self):
		try:	
			rtext =  ""
			for uid, player in self.playerlist.items():
				name = player.name
				rol = player.rol
				afiliacion = player.afiliacion
				txt_mayor = " *y era el mayor*"	if player.is_mayor else ""
				rtext += "El rol de *{}* era *{}* con afiliacion *{}*{}.\n".format(name, rol, afiliacion, txt_mayor)
				rtext +=  "\n"
			return rtext
		except Exception as e:
			rtext += str(e)

	def validate_call_choose_lobo(self, uid):
		return basic_validation(self, uid)

	def validate_call_choose_vidente(self, uid):
		return basic_validation(self, uid) and any(player_lobo.uid == uid for player_lobo in self.get_badguys())

	def validate_call_choose_poke(self, uid):
		return basic_validation(self, uid) and self.board.state.fase_actual is None 

	def call(self, context):
		import Unanimo.Commands as UnanimoCommands
		if self.board is not None:
				UnanimoCommands.command_call(context.bot, self)
	def timer(self, update, context):
		import Unanimo.Commands as UnanimoCommands
		if self.board is not None:
			UnanimoCommands.callback_timer(update, context)
