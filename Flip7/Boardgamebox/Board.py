import random

from Boardgamebox.Board import Board as BaseBoard
from Flip7.Boardgamebox.State import State
from Flip7.Constants.Cards import build_deck, card_display

ESTADO_TXT = {
    "jugando": "",
    "plantado": " (plantado ✋)",
    "congelado": " (congelado ❄️)",
    "reventado": " (reventó 💥)",
    "flip7": " (¡FLIP 7! 🎉)",
}


class Board(BaseBoard):
    def __init__(self, playercount, game):
        self.state = State()
        self.num_players = playercount
        self.cartas = build_deck()
        self.discards = []

    def robar_carta(self):
        if not self.cartas:
            self.cartas = self.discards
            self.discards = []
            random.shuffle(self.cartas)
        return self.cartas.pop()

    def print_board(self, game):
        st = self.state
        board = "--- 🎴 *Flip 7* — Ronda {} ---\n".format(st.ronda)
        board += "Cartas restantes en el mazo: {}\n\n".format(len(self.cartas))
        board += "--- *Jugadores* ---\n"
        for player in game.player_sequence:
            marca = " ⬅️" if st.active_player is not None and st.active_player.uid == player.uid else ""
            estado_txt = ESTADO_TXT.get(player.estado_ronda, "")
            cartas_txt = ", ".join(card_display(n) for n in sorted(player.numeros)) or "-"
            mods_txt = " + mods: {}".format(", ".join(player.modificadores)) if player.modificadores else ""
            sc_txt = " 🍀" if player.tiene_segunda_oportunidad else ""
            board += "• {}{}{}: [{}]{}{} — ronda: {} — total: {}\n".format(
                player.name, estado_txt, marca, cartas_txt, mods_txt, sc_txt,
                player.puntaje_ronda(), player.puntaje_total
            )
        return board
