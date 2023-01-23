import json
from datetime import datetime
from random import shuffle

from Boardgamebox.Game import Game as BaseGame
from SayAnything.Boardgamebox.Player import Player
from SayAnything.Boardgamebox.Board import Board
#from Boardgamebox.Board import Board
#from Boardgamebox.State import State

class Game(BaseGame):
	def __init__(self, cid, initiator, groupName, tipo = None, modo = None):
		BaseGame.__init__(self, cid, initiator, groupName, tipo, modo)		
	
	# Creacion de player de Say Anything.
	def add_player(self, uid, name):
		player = Player(name, uid)
		self.playerlist[uid] = player
		return player
	def create_board(self):
		player_number = len(self.playerlist)
		self.board = Board(player_number, self)
	def call(self, context):
		import SayAnything.Commands as SayAnythingCommands
		if self.board is not None:
    			SayAnythingCommands.command_call(context.bot, self)
