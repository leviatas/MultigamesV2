from Boardgamebox.Board import Board as BaseBoard
from SecretoCodigo.Boardgamebox.State import State
from SecretoCodigo.render import render_html_to_bytesio


REVEAL_EMOJIS = {
    "rojo":    "🟥",
    "azul":    "🟦",
    "neutral": "⬜",
    "asesino": "💀",
}
DUO_EMOJIS = {
    "agente":  "🟩",
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
            cell = f"{prefix}{REVEAL_EMOJIS[card['tipo']]}*{card['word']}*"
            board += cell + "  "
            if (i + 1) % 5 == 0:
                board = board.rstrip() + "\n"
        return board

    def print_board_duo(self, game):
        st = self.state
        board = ""
        if game.is_debugging:
            board += f"--- Fase: {st.fase_actual} ---\n"

        board += "🤝 *Agentes encontrados:* {a}/{t}  |  ⏳ *Pistas restantes:* {p}\n".format(
            a=st.agentes_revelados, t=st.total_agentes_duo, p=st.pistas_restantes,
        )
        if st.pista_actual:
            board += f"*Pista:* `{st.pista_actual}` — {st.numero_pista}\n"
            board += f"Intentos restantes: {st.intentos_restantes}\n"

        board += "\n"
        for i, card in enumerate(st.tablero):
            cell = "✅" if card["revealed"] else KEYCAP[card["numero"]]
            board += cell + "  "
            if (i + 1) % 5 == 0:
                board = board.rstrip() + "\n"
        return board

    def print_key(self, game, jugador_label):
        st = self.state
        key = st.key_a if jugador_label == "A" else st.key_b
        board = f"*[TU CLAVE — Jugador {jugador_label}]*\n"
        for i, card in enumerate(st.tablero):
            numero = card["numero"]
            prefix = "✅" if card["revealed"] else ""
            cell = f"{prefix}{DUO_EMOJIS[key[numero]]}*{card['word']}*"
            board += cell + "  "
            if (i + 1) % 5 == 0:
                board = board.rstrip() + "\n"
        return board

    # --- Métodos de imagen ---

    def render_board_image(self, game):
        return render_html_to_bytesio(self.state.tablero, mode="public")

    def render_spymaster_image(self, game):
        return render_html_to_bytesio(self.state.tablero, mode="spymaster")

    def render_key_image(self, game, jugador_label):
        key = self.state.key_a if jugador_label == "A" else self.state.key_b
        return render_html_to_bytesio(self.state.tablero, mode="duo_key", key=key)

    def render_duo_board_image(self, game):
        return render_html_to_bytesio(self.state.tablero, mode="duo_public")
