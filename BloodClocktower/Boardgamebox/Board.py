# Base Board
from Boardgamebox.Board import Board as BaseBoard
from BloodClocktower.Boardgamebox.State import State

import random
from BloodClocktower.Boardgamebox.State import State
from telegram import ParseMode

class Board(BaseBoard):
    def __init__(self, playercount):
        self.state = State()
        self.num_players = playercount
        
    def print_board(self, game):
        state = game.board.state

        if game.storyteller is None:
            return "¡¡El juego no tiene Storyteller todvia!! Conviertete en él poniendo /storyteller"

        board = ""
        board += f"*Dia {state.day}: {state.phase}*\n"
        jugadores = len(game.player_sequence)
        vivos = game.count_alive()
        votos = game.count_votes()
        board += f"Jugadores {jugadores} vivos {vivos} Votos {votos}"
        board += "💀 Jugador muerto pero con voto\n"
        board += "☠️ Jugador muerto pero sin voto\n"
        board += "\n\n"        
        board += "--- *Orden de jugadores* ---\n"
        for player in game.player_sequence:
            nombre = player.name.replace("_", " ")
            # if self.state.active_player == player:
            #     board += f"*{nombre}* " + u"\u27A1\uFE0F" + " "
            # else:
            dead = ('💀' if player.had_last_vote else '☠️') if player.dead else ""
            board += f"{nombre} {dead}" + u"\u27A1\uFE0F" + " "
        board = board[:-3]
        board += u"\U0001F501"

        return board