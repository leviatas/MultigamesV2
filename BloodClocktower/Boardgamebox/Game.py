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
		self.storyteller = None
	
	def clear_nomination(self):
		state = self.board.state
		state.accuser = None # Jugador que acuso
		state.defender = None # Jugador que fue acusado
		state.accusation = None # Acusacion del acusador
		state.defense = None # Defenss del acusado
		state.votes = {}
		
	def count_alive(self):
		return sum(not p.dead for p in self.player_sequence)
	
	def count_votes(self):
		return sum(not p.dead or p.has_last_vote for p in self.player_sequence)
	
	def set_playerorder(self, playerorder):
	     new_list = []
	     for name in playerorder:
	     	player = self.find_player(name)
	     	new_list.append(player)
	     	self.player_sequence = new_list
        
	def startgame(self):
		self.board = Board(len(self.playerlist))

	def get_rules(self):
		return ["""El juego es Blood on the clocktower"""]		
		
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
