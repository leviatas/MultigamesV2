from Boardgamebox.Board import Board as BaseBoard
from Insider.Boardgamebox.State import State


class Board(BaseBoard):
    def __init__(self, playercount, game):
        self.state = State()
        self.num_players = playercount
        self.cartas = []
        self.discards = []

    def print_board(self, game):
        board = "--- *Insider* ---\n"
        board += f"Fase: {self.state.fase_actual}\n\n"
        board += "--- *Jugadores* ---\n"
        for player in game.player_sequence:
            board += f"• {player.name}\n"
        return board
