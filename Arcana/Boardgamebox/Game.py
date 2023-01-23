import json
from datetime import datetime
from Boardgamebox.Game import Game as BaseGame
from Arcana.Boardgamebox.Player import Player
from Arcana.Boardgamebox.Board import Board

class Game(BaseGame):
	def __init__(self, cid, initiator, groupName, tipo = None, modo = None):
		BaseGame.__init__(self, cid, initiator, groupName, tipo, modo)		
	
	# Creacion de player de Say Anything.
	def add_player(self, uid, name):
		self.playerlist[uid] = Player(name, uid)
	def create_board(self):
		player_number = len(self.playerlist)
		self.board = Board(player_number, self)
	def call(self, context):
		import Arcana.Commands as ArcanaCommands
		if self.board is not None:
			ArcanaCommands.command_call(context.bot, self)