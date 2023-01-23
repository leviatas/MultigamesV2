from Boardgamebox.Player import Player as BasePlayer
from Arcana.Constants.Cards import PLAYERFATETOKENS
import copy

class Player(BasePlayer):
	def __init__(self, name, uid):		
		BasePlayer.__init__(self, name, uid)		
		# Tokens que el jugador modificara cuando el resto de jugadores le diga. Marca que posible Fate tiene en mano
		self.playerFateTokens = copy.deepcopy(PLAYERFATETOKENS)
		# Fate Tokens que tiene el jugador en mano
		self.fateTokens = []
		self.last_chosen_fate = None
		self.amount_tokens_draw = 0
		
	def get_private_info(self, game):
		board = "--- Info del Jugador {} ---\n".format(self.name)    
		board += "--- Tokens en mano ---\n"
		for fateToken in self.fateTokens:
			board += "{0}({1}) ".format(fateToken["Texto"], fateToken["TimeSymbols"])
		board = board[:-1]
		return board
