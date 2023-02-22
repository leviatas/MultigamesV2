# Base Board
from Boardgamebox.Board import Board as BaseBoard
from BloodClocktower.Boardgamebox.State import State

import random
from BloodClocktower.Boardgamebox.State import State
from telegram import ParseMode

import math
from Utils import player_call


class Board(BaseBoard):
    def __init__(self, playercount):
        self.state = State()
        self.num_players = playercount
    
    def getIndex(self, li, player): 
        for index, x in enumerate(li): 
            if x.uid == player.uid: 
                return index 
        return -1
    	
    def starting_with(self, lst, player):
        index = self.getIndex(lst, player)
        start = index-1 if index is not 0 else len(lst)-1
        for idx in range(len(lst)):
            yield  lst[(idx + start) % len(lst)]
			  
    def print_board(self, game):
        state = game.board.state

        if game.storyteller is None:
            return "¡¡El juego no tiene Storyteller todvia!! Conviertete en él poniendo /storyteller"

        board = ""
        #board += f"Dia {state.day}: {state.phase}\n"
        jugadores = len(game.player_sequence)
        vivos = game.count_alive()
        votos = game.count_votes()
        
        board += f"{state.phase} {state.day}\n"
        board += f"👤 {jugadores} Jugadores\n❤ {vivos} Vivos\n🗳 {votos} Votos totales\n"
        board += "💀 Muerto con voto\n"
        board += "☠️ Muerto sin voto\n\n"
        
        if state.accuser is not None:
            positivos = list(state.votes.values()).count("si")
            necesarios = math.ceil(vivos/2)
            board += f"{state.accuser.name} nominó a {state.defender.name} ({positivos}/{necesarios} votos necesarios para llevarlo al chopping)\n\n"

        lista = game.player_sequence if state.accuser is None else self.starting_with(game.player_sequence, state.defender)
        
        for index, player in enumerate(lista):
            nombre = player.name.replace("_", " ") if state.clock is not index else player_call(player)
            clock = "➡️ " if state.clock == index else ""
            dead = ('💀' if player.had_last_vote else '☠️') if player.dead else ""
            voted = "✋" if player.uid in state.votes and state.votes[player.uid] == "si" else ""
            board += f"{clock}{nombre} {dead} {voted}\n"

        return board
        