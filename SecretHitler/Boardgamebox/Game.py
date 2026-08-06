import json
from datetime import datetime
from random import shuffle

from SecretHitler.Boardgamebox.Player import Player
from SecretHitler.Boardgamebox.Board import Board
from SecretHitler.Boardgamebox.State import State

class Game(object):
	def __init__(self, cid, initiator, groupName):
		self.playerlist = {}
		self.player_sequence = []
		self.cid = cid
		self.board = None
		self.initiator = initiator
		self.dateinitvote = None
		self.history = []
		self.hiddenhistory = []
		self.is_debugging = False
		self.groupName = groupName
		self.tipo = 'SecretHitler'
		# {guesser_uid: [{"fascists": [uid, ...], "hitler": uid}, ...]} - historial de palpitos de /guess (maximo 2 intentos, el ultimo es definitivo)
		self.guesses = {}
		# {voter_uid: voted_uid} - voto de /mvp, uno por jugador, se puede cambiar hasta el fin de la partida
		self.mvp_votes = {}

	def add_player(self, uid, player):
		if any([True for k,v in self.playerlist.items() if v.name.strip() == player.name.strip()]):
			# Pongo al player con su uid
			self.playerlist[uid] = Player(f'{player.name} {uid}', uid)
		else:
			self.playerlist[uid] = player
	def get_hitler(self):
		for uid in self.playerlist:
			if self.playerlist[uid].role == "Hitler":
				return self.playerlist[uid]

	def get_fascists(self):
		fascists = []
		for uid in self.playerlist:
			if self.playerlist[uid].role == "Fascista":
				fascists.append(self.playerlist[uid])
		return fascists

	def compute_mvp(self):
		# Devuelve el uid con mas votos de /mvp, o None si nadie voto o hay empate.
		votes = getattr(self, "mvp_votes", {})
		tally = {}
		for voter_uid, voted_uid in votes.items():
			if voted_uid in self.playerlist:
				tally[voted_uid] = tally.get(voted_uid, 0) + 1
		if not tally:
			return None
		max_votes = max(tally.values())
		top = [uid for uid, count in tally.items() if count == max_votes]
		if len(top) != 1:
			return None
		return top[0]

	def compute_best_guessers(self):
		# Devuelve el conjunto de uids de Liberales con mas aciertos en el /guess
		# "completo" (fascistas comunes + Hitler). Vacio si ningun liberal adivino.
		hitler = self.get_hitler()
		hitler_uid = hitler.uid if hitler else None
		fascist_uids = {f.uid for f in self.get_fascists()}
		guesses = getattr(self, "guesses", {})

		scores = {}
		for guesser_uid, history in guesses.items():
			if not history:
				continue
			guesser = self.playerlist.get(guesser_uid)
			if guesser is None or guesser.role != "Liberal":
				continue
			guess = history[-1]
			guessed_fascist_uids = [u for u in guess.get("fascists", []) if u in self.playerlist]
			guessed_hitler_uid = guess.get("hitler")
			aciertos = len([u for u in guessed_fascist_uids if u in fascist_uids])
			acierto_hitler = 1 if (guessed_hitler_uid is not None and guessed_hitler_uid == hitler_uid) else 0
			scores[guesser_uid] = aciertos + acierto_hitler

		if not scores:
			return set()
		max_score = max(scores.values())
		return {u for u, s in scores.items() if s == max_score}

	def shuffle_player_sequence(self):
		for uid in self.playerlist:
			self.player_sequence.append(self.playerlist[uid])
		shuffle(self.player_sequence)

	def remove_from_player_sequence(self, Player):
		for p in self.player_sequence:
			if p.uid == Player.uid:
				p.remove(Player)

	def print_roles(self):
		try:
			rtext = ""
			if self.board is None:
				#game was not started yet
				return rtext
			else:
				for p in self.playerlist:
					name = self.playerlist[p].name
					role = self.playerlist[p].role
					preference_rol = self.playerlist[p].preference_rol
					muerto = self.playerlist[p].is_dead					
					rtext += "El rol de %s %sera %s %s" % (name, "(muerto) " if muerto else "", role, ("" if preference_rol == "" else "queria ser " + preference_rol))										
					rtext +=  "\n"
				return rtext
		except Exception as e:
			rtext += str(e)
