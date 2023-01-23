from Boardgamebox.Player import Player as BasePlayer

class Player(BasePlayer):
	def __init__(self, name, uid):		
		BasePlayer.__init__(self, name, uid)		
		# Lost Expedition atributes
		self.puntaje = 0		

	def print_stats(self):
		board = "--- Stats Jugador %s ---\n" % self.name
		board += "--- %s 🍲 ---\n" % self.food
		
		return board
