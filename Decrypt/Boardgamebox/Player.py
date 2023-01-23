from Boardgamebox.Player import Player as BasePlayer
import copy

class Player(BasePlayer):
	def __init__(self, name, uid):		
		BasePlayer.__init__(self, name, uid)
		
	
