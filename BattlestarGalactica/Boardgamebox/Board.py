from Boardgamebox.Board import Board as BaseBoard
from BattlestarGalactica.Boardgamebox.State import State


class Board(BaseBoard):
    def __init__(self, playercount, game):
        self.state = State()
        self.num_players = playercount
        self.cartas = []
        self.discards = []

    def print_board(self, game):
        st = self.state
        board = "🚀 *Battlestar Galactica*\n"
        board += f"Fase: {st.fase_actual}\n\n"
        board += "*Recursos:*\n"
        board += f"🍞 Comida: {st.comida}   ⛽ Combustible: {st.combustible}\n"
        board += f"🙂 Moral: {st.moral}   👥 Población: {st.poblacion}\n\n"
        board += f"🧭 Distancia: {st.distancia}/{st.objetivo_distancia}   "
        board += f"⏫ Prep. salto: {st.jump_prep}/{st.jump_prep_max}\n\n"
        board += "*Naves:*\n"
        board += f"✈️ Vipers (reserva/espacio/dañados): {st.vipers_reserva}/{st.vipers_espacio}/{st.vipers_danados}\n"
        board += f"👾 Raiders: {st.raiders}   🛸 Basestars: {st.basestars}\n\n"

        pres = game.playerlist.get(st.presidente_uid)
        alm = game.playerlist.get(st.almirante_uid)
        board += f"🏛️ Presidente: {pres.name if pres else '—'}\n"
        board += f"🎖️ Almirante: {alm.name if alm else '—'}\n\n"

        board += "*Jugadores:*\n"
        for player in game.player_sequence:
            marca = "➡️ " if st.active_player == player else "• "
            pj = player.personaje or "?"
            revel = " 🤖" if player.revealed else ""
            board += f"{marca}{player.name} ({pj}){revel}\n"
        return board
