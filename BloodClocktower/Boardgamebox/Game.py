import json
from datetime import datetime
from random import shuffle, randint

from Boardgamebox.Game import Game as BaseGame
from BloodClocktower.Boardgamebox.Player import Player
from BloodClocktower.Boardgamebox.Board import Board
#from Boardgamebox.Board import Board
#from Boardgamebox.State import State

class Game(BaseGame):
	def __init__(self, cid, initiator, groupName):
		BaseGame.__init__(self, cid, initiator, groupName, None, None)		
		self.using_timer = False
		self.storyteller = None
		self.board_message_id = None
		self.tipo = "blood"
	
	def add_note(self, uid, notas):
		player = self.find_player_by_id(uid)
		player.notes.append(notas)

	def find_player(self, name):
		for uid in self.playerlist:
			player = self.find_player_by_id(uid)
			if player.name == name or player.nick == name.replace("@",""):
				return player
		for player in self.player_sequence:
			if player.name == name:
				return player
		return None

	def find_player_by_id(self, uid) -> Player:
		return self.playerlist[uid]

	def clear_nomination(self):
		state = self.board.state
		state.accuser = None # Jugador que acuso
		state.defender = None # Jugador que fue acusado
		state.accusation = None # Acusacion del acusador
		state.defense = None # Defenss del acusado
		state.votes = {}
		state.clock = -1
	
	def set_night(self):
		state = self.board.state
		state.phase = "Noche"
		state.day += 1
		self.history.append(f"*Noche {state.day}*")
		# Limpio el chopping block
		state.chopping_block_votes = 0
		state.chopping_block = None
		state.can_nominate = False

	def set_day(self):
		state = self.board.state
		state.phase = "Día"
		self.history.append(f"*Día {state.day}*")

	def get_current_voter(self):
		state = self.board.state
		# Si no se esta votando devolver vacio
		# Si el clock no comenzo tampoco hay current voter
		if state.accuser is None or state.clock == -1:
			return None
		# Obtengo la lista con el defensor al final
		lista = self.board.starting_with(self.player_sequence, state.defender)
		# Valido
		return list(lista)[state.clock]

	def can_modify_vote(self, uid):
		state = self.board.state
		# Si no se esta votando devolver vacio
		# Si el clock no comenzo tampoco hay current voter
		if state.accuser is None or state.clock == -1:
			return False
		# Obtengo la lista con el defensor al final
		lista = self.board.starting_with(self.player_sequence, state.defender)
		
		uid_player_index = next((i for i, item in enumerate(lista) if item.uid == uid), -1)
		# Valido
		return uid_player_index >= state.clock

	def toggle_nominations(self):
		state = self.board.state
		state.can_nominate = not state.can_nominate
	
	def player_call(self, player):
		return "[{0}](tg://user?id={1})".format(player.name, player.uid)

	def advance_clock(self) -> str:
		state = self.board.state
		state.clock += 1
		# Si estoy haciendo tick desde el ultimo jugador (que es normalmente el defensor)
		# Aviso al ST que debe decidir que pasa
		if state.clock == len(self.player_sequence):
			storyteller = Player("Storyteller", self.storyteller)
			return f"The clock rings the time has ended!\n{self.player_call(storyteller)}: Usa /chopping para mandarlo al chopping block si lo merece, luego Usa /clear para limpiar la nominación"
		else:
			current_voter = self.get_current_voter()
			return f"The clock goes forward {self.player_call(current_voter)} te toca!"
									
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
			group_link_name = self.groupName
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
