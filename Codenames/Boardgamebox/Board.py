from Boardgamebox.Board import Board as BaseBoard
from Codenames.Boardgamebox.State import State


REVEAL_EMOJIS = {
    "rojo":    "🟥",
    "azul":    "🟦",
    "neutral": "⬜",
    "asesino": "💀",
}
KEYCAP = {i: f"{i}⃣" for i in range(1, 26)}


class Board(BaseBoard):
    def __init__(self, playercount, game):
        BaseBoard.__init__(self, playercount, game)
        self.state = State()

    def print_board(self, game):
        board = ""
        if game.is_debugging:
            board += f"--- Fase: {self.state.fase_actual} ---\n"

        board += "🔴 *Rojos restantes:* {r}  |  🔵 *Azules restantes:* {a}\n".format(
            r=self.state.palabras_rojo_restantes,
            a=self.state.palabras_azul_restantes,
        )

        if self.state.pista_actual:
            board += f"*Pista:* `{self.state.pista_actual}` — {self.state.numero_pista}\n"
            board += f"Intentos restantes: {self.state.intentos_restantes}\n"

        board += "\n"
        for i, card in enumerate(self.state.tablero):
            cell = REVEAL_EMOJIS[card["tipo"]] if card["revealed"] else KEYCAP[card["numero"]]
            board += cell + "  "
            if (i + 1) % 5 == 0:
                board = board.rstrip() + "\n"

        board += "\n*Turno:* " + (self.state.turno_actual or "—")
        return board

    def print_spymaster_board(self, game):
        board = "*[VISTA ESPÍA]*\n"
        for i, card in enumerate(self.state.tablero):
            prefix = "✅" if card["revealed"] else ""
            cell = f"{prefix}{REVEAL_EMOJIS[card['tipo']]}*{card['numero']}*"
            board += cell + "  "
            if (i + 1) % 5 == 0:
                board = board.rstrip() + "\n"
        return board
