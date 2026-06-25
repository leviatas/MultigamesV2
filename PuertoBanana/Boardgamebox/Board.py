from Boardgamebox.Board import Board as BaseBoard
from PuertoBanana.Boardgamebox.State import State

BANANAS_VICTORIA = 200


class Board(BaseBoard):
    def __init__(self, playercount, game):
        self.state = State()
        self.num_players = playercount
        self.cartas = []
        self.discards = []

    def print_board(self, game):
        st = self.state
        board = "--- 🍌 *Puerto Banana* ---\n"
        board += f"Fase: {st.fase_actual}\n"
        board += f"Ronda: {st.ronda}\n"
        board += f"Pozo actual: *{st.pozo_actual}* bananas\n\n"
        board += "--- *Jugadores* ---\n"
        for player in game.player_sequence:
            puja = " (ya pujó)" if player.uid in st.last_votes else ""
            marca = " ✗" if player.eliminado_ronda else ""
            board += f"• {player.name}: *{player.bananas}* bananas{puja}{marca}\n"
        return board
