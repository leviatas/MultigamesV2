import json
import random
from datetime import datetime
from random import shuffle

from Constants.Cards import cartas_aventura

from Boardgamebox.Game import Game as BaseGame
from LostExpedition.Boardgamebox.Player import Player
from LostExpedition.Boardgamebox.Board import Board
#from Boardgamebox.Board import Board
#from Boardgamebox.State import State

class Game(BaseGame):
	def __init__(self, cid, initiator, groupName, tipo = None, modo = None):
		BaseGame.__init__(self, cid, initiator, groupName, tipo, modo)
		self.cartasAventura = random.sample([*cartas_aventura], len([*cartas_aventura]))
		self.cartasExplorationActual = []
	
	# Creacion de player de Say Anything.
	def add_player(self, uid, name):
		self.playerlist[uid] = Player(name, uid)
	def create_board(self):
		player_number = len(self.playerlist)
		self.board = Board(player_number, self)
