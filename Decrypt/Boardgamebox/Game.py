import json
from datetime import datetime
from random import shuffle, randint

from Boardgamebox.Game import Game as BaseGame
from Decrypt.Boardgamebox.Player import Player
from Decrypt.Boardgamebox.Board import Board
from Decrypt.Boardgamebox.Team import Team
#from Boardgamebox.Board import Board
#from Boardgamebox.State import State
from Utils import get_config_data

class Game(BaseGame):
	def __init__(self, cid, initiator, groupName, tipo = None, modo = None):
		BaseGame.__init__(self, cid, initiator, groupName, tipo, modo)
		self.turncount = 0
		self.value_intercept = 1
		self.value_miscommunication = -1
		# Allow half guess and points of that
		self.allow_half_guess = False
		self.value_half_guess = 0.3
		self.code_length = 5
	# Creacion de player de juego.
	def add_player(self, uid, name):
		self.playerlist[uid] = Player(name, uid)
		#Si un jugador se une tarde lo asigno al team con menos jugadores
		if self.board:
			if len(self.board.state.teams[0].player_sequence ) > len(self.board.state.teams[1].player_sequence):
				self.board.state.teams[1].player_sequence.append(self.playerlist[uid])
			elif len(self.board.state.teams[0].player_sequence) < len(self.board.state.teams[1].player_sequence):
				self.board.state.teams[0].player_sequence.append(self.playerlist[uid])
			else:
				self.board.state.teams[randint(0, 1)].player_sequence.append(self.playerlist[uid])
							
	
	def create_board(self):
		player_number = len(self.playerlist)
		self.board = Board(player_number, self)
	
	def create_teams(self, amount_teams):
		splited_teams = self.split_in_teams(self.player_sequence, amount_teams)
		i = 1
		# Se ingresa en orden inverso asi los equipos de menos miembros estan primeros y en ventaja
		for team in splited_teams[::-1]:
			self.board.state.teams.append(Team("Equipo {}".format(i), team))
			i += 1
		# Pongo al jugador inicial de cada equipo.
		for team in self.board.state.teams:
			team.increment_player_counter()
			
		# Marco al equipo activo
		self.board.state.active_team = self.board.state.teams[self.board.state.team_counter]
		self.board.state.inactive_team = self.board.state.teams[1 if self.board.state.team_counter == 0 else 0]
		
	def split_in_teams(self, lst,n):
		return [lst[i::n] for i in range(n)]
	
	def verify_turn(self, uid):		
		if self.board.state.fase_actual == "Set_Reference":
			return (uid in [team.active_player.uid for team in self.board.state.teams])
		if self.board.state.fase_actual == "Intercept/Decrypt":
			is_decriptor = (self.board.state.active_team.belongs(uid) and uid != self.board.state.active_team.active_player.uid and self.board.state.active_team.team_choosen_code is None)
			is_interceptor = (self.board.state.inactive_team.belongs(uid) and self.board.state.active_team.opponent_team_choosen_code is None and self.turncount != 1)
			return is_decriptor or is_interceptor
	
	def getHistory(self, uid):		
		history_text = "*Historial del grupo {}*:\n".format(self.groupName)
		if self.board.state.fase_actual == "Set_Reference":
			history_text += self.board.state.active_team.printHistory(True) if self.board.state.active_team.belongs(uid) else self.board.state.inactive_team.printHistory(True)			
		else:
			history_text += self.board.state.active_team.printHistory(True) if self.board.state.active_team.belongs(uid) else self.board.state.active_team.printHistory()
		return [history_text]

	def myturn_message(self, uid):		
		group_link_name = self.groupName if get_config_data(self, "link") is None else "[{0}]({1})".format(self.groupName, get_config_data(self, "link"))
		active_team = self.board.state.active_team
		inactive_team = self.board.state.inactive_team
		player_team = self.getPlayerTeam(uid)
		if self.board.state.fase_actual == "Set_Reference":
			return player_team.generate_code_message(group_link_name)
		if self.board.state.fase_actual == "Intercept/Decrypt":
			esDesencriptar = (self.board.state.active_team.belongs(uid) and uid != self.board.state.active_team.active_player.uid)
			msg = active_team.generate_decrypt_message(group_link_name) if esDesencriptar else inactive_team.generate_intercept_message(group_link_name, active_team.clue)
			return msg
	def call(self, context):
		import Decrypt.Commands as DecryptCommands
		if self.board is not None:
    			DecryptCommands.command_call(context.bot, self)
	
