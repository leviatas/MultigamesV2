from Boardgamebox.Board import Board as BaseBoard
from SpyFall.Boardgamebox.State import State


class Board(BaseBoard):
    def __init__(self, playercount, game):
        self.state = State()
        self.num_players = playercount
        self.cartas = []
        self.discards = []

    def print_board(self, game):
        board = "--- *SpyFall* ---\n"
        board += f"Fase: {self.state.fase_actual}\n"
        board += f"Localidad: {'?' if self.state.localidad else 'Sin asignar'}\n\n"
        board += "--- *Jugadores* ---\n"
        for player in game.player_sequence:
            board += f"• {player.name}\n"
        return board
