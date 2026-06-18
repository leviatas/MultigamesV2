from Boardgamebox.Board import Board as BaseBoard
from BattlestarGalactica.Boardgamebox.State import State
from BattlestarGalactica.Constants import Locations


# Iconos por ubicación para el mapa textual (sin imágenes con copyright).
ICONO_UBICACION = {
    "command": "🎯", "ftl": "🚀", "weapons": "🔫", "hangar": "✈️", "armory": "🪖",
    "admiral_quarters": "🎖️", "research": "🔬", "communications": "📡",
    "sickbay": "🏥", "brig": "🔒",
    "press_room": "📰", "president_office": "🏛️", "administration": "📋",
    "caprica": "🌍", "cylon_fleet": "🛸", "human_fleet": "👾", "resurrection_ship": "♻️",
}

# Orden de presentación de cada nave en el mapa.
_GALACTICA = ["command", "ftl", "weapons", "hangar", "armory",
              "admiral_quarters", "research", "communications", "sickbay", "brig"]
_COLONIAL = ["press_room", "president_office", "administration"]
_CYLON = ["caprica", "cylon_fleet", "human_fleet", "resurrection_ship"]


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
        board += f"👾 Raiders: {st.raiders}   🛸 Basestars: {st.basestars}"
        if st.basestars and st.basestar_hits:
            board += f" (impactos: {st.basestar_hits})"
        board += f"\n🛰️ Naves civiles: {len(st.civiles)}   🔺 Centuriones: {st.centuriones}/{st.centuriones_max}\n\n"

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

    def print_map(self, game):
        """Mapa textual de la flota (ubicaciones + espacio), sin imágenes.

        Muestra cada nave (Galactica, Colonial One y las localizaciones Cylon)
        con sus ubicaciones y los jugadores presentes en cada una, además del
        estado del espacio (Vipers, Raiders, Basestars, naves civiles, abordaje).
        """
        st = self.state

        # Ocupantes por ubicación
        ocupantes = {}
        for player in game.playerlist.values():
            if not player.ubicacion:
                continue
            etiqueta = player.name + (" 🤖" if player.revealed else "")
            ocupantes.setdefault(player.ubicacion, []).append(etiqueta)

        def _bloque(claves):
            lineas = []
            for key in claves:
                info = Locations.UBICACIONES.get(key)
                if not info:
                    continue
                nombre = info["nombre"].split(" (")[0]
                icono = ICONO_UBICACION.get(key, "•")
                quienes = ", ".join(ocupantes.get(key, [])) or "—"
                lineas.append(f"  {icono} {nombre}: {quienes}")
            return "\n".join(lineas)

        cuerpo = "═════════════ ESPACIO ═════════════\n"
        cuerpo += (f"  ✈️ Vipers vuelo:{st.vipers_espacio} "
                   f"dañados:{st.vipers_danados} reserva:{st.vipers_reserva}\n")
        cuerpo += f"  👾 Raiders:{st.raiders}   🛸 Basestars:{st.basestars}"
        if st.basestars and st.basestar_hits:
            cuerpo += f" (impactos {st.basestar_hits}/3)"
        cuerpo += (f"\n  🛰️ Naves civiles:{len(st.civiles)}   "
                   f"🔺 Abordaje:{st.centuriones}/{st.centuriones_max}\n\n")
        cuerpo += "──────────── GALÁCTICA ────────────\n" + _bloque(_GALACTICA) + "\n\n"
        cuerpo += "─────────── COLONIAL ONE ──────────\n" + _bloque(_COLONIAL) + "\n\n"
        cuerpo += "──────── LOCALIZACIONES CYLON ──────\n" + _bloque(_CYLON)

        return "🗺️ *Mapa de la flota*\n```\n" + cuerpo + "\n```"
