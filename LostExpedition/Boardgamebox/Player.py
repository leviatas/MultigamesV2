from Boardgamebox.Player import Player as BasePlayer

class Player(BasePlayer):
	def __init__(self, name, uid):		
		BasePlayer.__init__(self, name, uid)
		# Lost Expedition atributes
		self.hand = []
		self.food = 3
		self.bullets = 3
		self.vida_explorador_campero = 3
		self.vida_explorador_brujula = 3
		self.vida_explorador_hoja = 3
		self.skills = []

	def print_stats(self):
		board = "--- Stats Jugador %s ---\n" % self.name
		board += "--- %s 🍲 ---\n" % self.food
		board += "--- %s 🔫 ---\n" % self.bullets
		board += "--- %s ❤️ Explorador Campero  ---\n" % self.vida_explorador_campero
		board += "--- %s ❤️ Explorador Brujula  ---\n" % self.vida_explorador_brujula
		board += "--- %s ❤️ Explorador Hoja  ---\n" % self.vida_explorador_hoja

		'''for uid in player_list:
		board += "%s tiene " % (player_list[uid].name)
		for i in range(player_list[uid].tokens_posesion):
		board += "\U0001F47F"            
		board += "\n"  
		'''
		return board
