from Boardgamebox.State import State as BaseState

class State(BaseState):
	def __init__(self):
		BaseState.__init__(self)
		self.doom = None
		self.score = 0
		self.topArcana = None
		self.arcanasOnTable = []
		self.fadedarcanasOnTable = []
		self.discardedArcanas = []
		self.plusOneEnable = False
		self.extraGuess = 0
		self.used_fate_power = False
		# Variables que se usan para el reubicar
		self.indexArcanaOrigen = -99
		self.indexFateArcanaOrigen = -99
		self.used_sacar = False
