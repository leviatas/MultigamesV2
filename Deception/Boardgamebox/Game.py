import json
from datetime import datetime
from random import shuffle, randint

from Boardgamebox.Game import Game as BaseGame
from Deception.Boardgamebox.Player import Player
from Deception.Boardgamebox.Board import Board
#from Boardgamebox.Board import Board
#from Boardgamebox.State import State
from Utils import (player_call, get_config_data, basic_validation)

class Game(BaseGame):
	def __init__(self, cid, initiator, groupName, tipo = None, modo = None):
		BaseGame.__init__(self, cid, initiator, groupName, tipo, modo)
		self.modulos = []
		self.using_timer = False
	
	def get_forense(self):
		for uid in self.playerlist:
			if self.playerlist[uid].is_forense():
				return self.playerlist[uid]
		return None

	def get_asesino(self):
		for uid in self.playerlist:
			if self.playerlist[uid].is_asesino():
				return self.playerlist[uid]
		return None

	def get_rol(self, role_name):
		for uid in self.playerlist:
			if self.playerlist[uid].is_role(role_name):
				return self.playerlist[uid]
		return None

	def get_complice(self):
		for uid in self.playerlist:
			if self.playerlist[uid].is_complice():
				return self.playerlist[uid]
		return None

	def get_testigo(self):
		for uid in self.playerlist:
			if self.playerlist[uid].is_testigo():
				return self.playerlist[uid]
		return None

	def get_masones(self):
		masones = []
		for uid, player in self.playerlist.items():
			if (player == "Mason" or player.dople_rol == "Mason"):
				masones.append(player)
		return masones

	def get_oracles(self):
		oraculos = []
		for uid, player in self.playerlist.items():
			if (player == "Oraculo" or player.dople_rol == "Oraculo"):
				oraculos.append(player)
		return oraculos

	def get_rules(self):
		return ["""Deception es un juego de roles ocultos cuyo objetivo es descubrir al asesino de un asesinato.
*Objetivo team policia:* (Asesino y cómplice (6+ jugadores)) Encontrar al asesino, su medio y su pista vital.

*Objetivo team asesino:* (Policias, Forense y Testigo(6+ jugadores)) Evitar que se encuentre el asesino, su medio y pista vital.

Cada jugador recibe una cantidad de cartas de pista y de medios

El asesino eligira una pista y un medio de sus cartas como forma de realizar su asesinato.

El cómplice sabrá quien es el asesino y la forma que realizó el asesinato.

El testigo sabrá los nombres de las dos personas que pueden ser el asesino y el cómplice, pero no sabrá quien es quien.

El forense ira poniendo balas en unas tarjetas para ir dando pistas de como ha sido el asesinato.

Los jugadores irán charlando sobre el asesinato e iran acusando a los otros de ser los asesinos.

*ACUSAR:* En cualquier momento un jugador puede señalar a un jugador y acusarle de ser el asesino, mencionará que pista y medio ha usado.
Si su *acusación es falsa*, el jugador sigue jugando pero no podra acusar. Si todos los jugadores, excepto el forense, han acusado
y no se ha encontrado el asesino, el *team asesino gana*.
Si su *acusación es correta* y no hay testigo. El team policia gana. Si hay testigo, el asesino y el complice se ponen de acuerdo y señalan a un
jugador, si es el testigo, el *team asesino gana* en vez del *team policia*.

Cuando el forense haya puesto la *6ta bala* y la charla haya finalizado hará los siguientes pasos *A) B) A) B) A)*
A) Exposición: Los jugadores iran dando sus posibles teorias de quien es el asesino, su pista clave y su medio.

B) Nueva evidencia: Luego de esta exposición el forense hará /newevidence para dar nueva evidencia y reemplazara una carta de escena por otra
poniendo una bala sobre la nueva.

Si para la ultima exposicion del ultimo jugador nadie ha hecho un acusación correcta el *team asesino gana*"""]
		
		
	# Creacion de player de juego.	
	def add_player(self, uid, name):
		self.playerlist[uid] = Player(name, uid)

	def create_board(self):
		player_number = len(self.playerlist)
		self.board = Board(player_number, self)
	
	def verify_turn(self, uid):
		return False

	def myturn_message(self, uid):		
		group_link_name = self.groupName if get_config_data(self, "link") is None else "[{0}]({1})".format(self.groupName, helper.get_config_data(self, "link"))
		
		if self.board.state.fase_actual == "Set_Reference":
			msg = ""
			return msg
		if self.board.state.fase_actual == "Intercept/Decrypt":
			msg = ""
			return msg

	def print_roles(self):
		try:	
			rtext =  ""
			for player in self.playerlist.values():
				name = player.name
				rol = player.rol
				afiliacion = player.afiliacion				
				rtext += "El rol de *{}* era *{}* con afiliacion *{}*.\n".format(name, rol, afiliacion)
				rtext +=  "\n"
			return rtext
		except Exception as e:
			rtext += str(e)

	def validate_call_choose_lobo(self, uid):
		return basic_validation(self, uid)
	
	def validate_call_choose_pista_mean(self, jugador_ejecutor):
		return basic_validation(self, jugador_ejecutor.uid) and self.board.state.fase_actual is None and jugador_ejecutor.is_asesino

	def validate_call_choose_continue(self, jugador_ejecutor):
		return basic_validation(self, jugador_ejecutor.uid) and self.board.state.fase_actual is None and jugador_ejecutor.is_forense
	
	def call(self, context):
		import Deception.Commands as DeceptionCommands
		if self.board is not None:
    			DeceptionCommands.command_call(context.bot, self)
	
	def timer(self, update, context):
		import Deception.Commands as DeceptionCommands
		if self.board is not None:
			DeceptionCommands.callback_timer(update, context)
