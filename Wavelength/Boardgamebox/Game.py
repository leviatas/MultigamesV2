import json
from datetime import datetime
from random import shuffle, randint

from Boardgamebox.Game import Game as BaseGame
from Wavelength.Boardgamebox.Player import Player
from Wavelength.Boardgamebox.Board import Board
from Wavelength.Boardgamebox.Team import Team
#from Boardgamebox.Board import Board
#from Boardgamebox.State import State
from Utils import get_config_data

class Game(BaseGame):
	def __init__(self, cid, initiator, groupName, tipo = None, modo = None):
		BaseGame.__init__(self, cid, initiator, groupName, tipo, modo)
		self.turncount = 0
		self.code_length = 5
		self.suddenDeath = -1
	# Creacion de player de Say Anything.
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

		# Marco al equipo activo.
		self.board.state.active_team = self.board.state.teams[self.board.state.team_counter]
		self.board.state.active_team.player_counter = 0
		self.board.state.active_team.active_player = self.board.state.active_team.player_sequence[self.board.state.active_team.player_counter]
		self.board.state.inactive_team = self.board.state.teams[1 if self.board.state.team_counter == 0 else 0]

	def split_in_teams(self, lst,n):
		return [lst[i::n] for i in range(n)]

	def verify_turn(self, uid):

		if self.board.state.fase_actual == "Set_Reference" and uid == self.board.state.active_team.active_player.uid:
			return True
		if self.board.state.fase_actual == "Predict" and self.board.state.active_team.belongs(uid) and self.board.state.active_team.active_player.uid != uid:
			return True
		if self.board.state.fase_actual == "Predict_Opp_LR" and self.board.state.inactive_team.belongs(uid):
			return True
		return False

	def myturn_message(self, uid):
		game = self
		group_link_name = "[{0}]({1})".format(game.groupName, get_config_data(game, "link"))
		if game.board.state.fase_actual == "Set_Reference" and uid == game.board.state.active_team.active_player.uid:
			return "Partida: {} de Wavelength tienes que actuar".format(group_link_name)
		if game.board.state.fase_actual == "Predict" and game.board.state.active_team.belongs(uid) and game.board.state.active_team.active_player.uid != uid:
			return "Partida: {} de Wavelength tienes que actuar".format(group_link_name)
		if game.board.state.fase_actual == "Predict_Opp_LR" and game.board.state.inactive_team.belongs(uid):
			return "Partida: {} de Wavelength tienes que actuar".format(group_link_name)
		return "Partida: {} de Wavelength tienes que actuar".format(group_link_name)
	def call(self, context):
		import Wavelength.Commands as WavelengthCommands
		if self.board is not None:
    			WavelengthCommands.command_call(context.bot, self)
