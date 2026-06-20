from Boardgamebox.Board import Board as BaseBoard
from BattlestarGalactica.Boardgamebox.State import State
from BattlestarGalactica.Constants import Locations, Space


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


def naves_de_area(area):
    """Devuelve la lista de etiquetas de naves presentes en un área del espacio."""
    piezas = []
    for hits in area["basestars"]:
        extra = f"(daño {hits}/3)" if hits else ""
        piezas.append(f"🛸{extra}")
    if area["raiders"]:
        piezas.append(f"👾×{area['raiders']}")
    if area.get("heavy_raiders"):
        piezas.append(f"🚁×{area['heavy_raiders']}")
    if area["vipers"]:
        piezas.append(f"✈️×{area['vipers']}")
    if area["civiles"]:
        piezas.append(f"🛰️×{len(area['civiles'])}")
    return piezas


def sistemas_averiados(st):
    """Sufijo con los sistemas de Galactica averiados (para el resumen)."""
    if not st.galactica_damage:
        return ""
    nombres = [Locations.UBICACIONES[k]["nombre"].split(" (")[0] for k in st.galactica_damage]
    return "  ⚠️ avería: " + ", ".join(nombres)


def track_abordaje(st):
    """Representa el track de la Partida de Abordaje: una barra de casillas con
    los centuriones que avanzan hacia el puente (casilla final = abordaje)."""
    n = st.boarding_breach
    casillas = ["▫️"] * n
    for pos in st.boarding_party:
        idx = max(0, min(pos, n) - 1)
        casillas[idx] = "🔺"
    barra = "".join(casillas)
    return f"{barra} ({st.total_centuriones()} a bordo)"


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
        tripulados = sum(1 for p in game.playerlist.values() if getattr(p, "viper_area", None) is not None)
        board += (f"✈️ Vipers (espacio/tripulados/reserva/dañados): "
                  f"{st.total_vipers_espacio()}/{tripulados}/{st.vipers_reserva}/{st.vipers_danados}\n")
        board += (f"👾 Raiders: {st.total_raiders()}   🚁 Heavy Raiders: {st.total_heavy_raiders()}   "
                  f"🛸 Basestars: {st.total_basestars()}\n")
        board += f"🛰️ Naves civiles: {st.total_civiles()}\n"
        board += f"🛡️ Daño Galactica: {st.total_danos_galactica()}/{st.galactica_danos_max}{sistemas_averiados(st)}\n"
        board += f"🔺 Abordaje: {track_abordaje(st)}\n\n"

        pres = game.playerlist.get(st.presidente_uid)
        alm = game.playerlist.get(st.almirante_uid)
        board += f"🏛️ Presidente: {pres.name if pres else '—'}\n"
        board += f"🎖️ Almirante: {alm.name if alm else '—'}   ☢️ Ojivas: {st.nukes}\n\n"

        board += "*Jugadores:*\n"
        for player in game.player_sequence:
            marca = "➡️ " if st.active_player == player else "• "
            pj = player.personaje or "?"
            revel = " 🤖" if player.revealed else ""
            board += f"{marca}{player.name} ({pj}){revel}\n"
        return board

    def print_map(self, game):
        """Mapa textual de la flota (espacio por áreas + ubicaciones), sin imágenes.

        Muestra el espacio dividido en las áreas reales (con las naves de cada
        una) y cada nave (Galactica, Colonial One y las localizaciones Cylon) con
        sus ubicaciones y los jugadores presentes en cada una.
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
                averia = " 💥" if key in st.galactica_damage else ""
                quienes = ", ".join(ocupantes.get(key, [])) or "—"
                lineas.append(f"  {icono} {nombre}{averia}: {quienes}")
            return "\n".join(lineas)

        # Vipers tripulados por área (ficha de piloto = nombre del jugador).
        pilotos_area = {}
        for p in game.playerlist.values():
            ar = getattr(p, "viper_area", None)
            if ar is not None:
                pilotos_area.setdefault(ar, []).append(p.name)

        cuerpo = "═════════════ ESPACIO ═════════════\n"
        for meta in Space.AREAS:
            area = st.areas[meta["id"]]
            piezas = naves_de_area(area)
            for nombre_p in pilotos_area.get(meta["id"], []):
                piezas.append(f"🧑‍🚀{nombre_p}")
            tubo = " (tubo)" if meta["launch"] else ""
            cuerpo += f"  {meta['emoji']} {meta['nombre']}{tubo}: {'  '.join(piezas) if piezas else '—'}\n"
        cuerpo += (f"  🅿️ Reserva vipers: {st.vipers_reserva}   "
                   f"🛠️ dañados: {st.vipers_danados}\n")
        cuerpo += f"  🛡️ Daño Galactica: {st.total_danos_galactica()}/{st.galactica_danos_max}\n"
        cuerpo += f"  🔺 Abordaje: {track_abordaje(st)}\n\n"
        cuerpo += "──────────── GALÁCTICA ────────────\n" + _bloque(_GALACTICA) + "\n\n"
        cuerpo += "─────────── COLONIAL ONE ──────────\n" + _bloque(_COLONIAL) + "\n\n"
        cuerpo += "──────── LOCALIZACIONES CYLON ──────\n" + _bloque(_CYLON)

        return "🗺️ *Mapa de la flota*\n```\n" + cuerpo + "\n```"
