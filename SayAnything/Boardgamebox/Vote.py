from SayAnything.Boardgamebox.Player import Player

class Vote():
	# Init with one key and value
	def __init__(self, player, key, value):
		self.player = player		
		self.content = {}
		self.content[key] = value
		
	def add(self, key, value):
		self.content[key] = value
