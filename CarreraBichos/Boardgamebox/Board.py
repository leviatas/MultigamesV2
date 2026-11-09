from Boardgamebox.Board import Board as BaseBoard
from CarreraBichos.Boardgamebox.State import State


class Board(BaseBoard):
    def __init__(self, playercount, game):
        BaseBoard.__init__(self, playercount, game)
        self.state = State()

    def print_board(self, game):
        from CarreraBichos.Motor import texto_tablero
        return texto_tablero(game)
