from Boardgamebox.Player import Player as BasePlayer
from collections import Counter

from BattlestarGalactica.Constants import Characters, Skills, Locations


def _resumen_skill_set(skill_set):
    """Resume el set de habilidad de un personaje en líneas legibles, indicando
    la cantidad por color y si el slot es FIJO o de ELECCIÓN (entre 2+ colores)."""
    fijos = Counter()
    elecciones = Counter()
    for slot in skill_set:
        if isinstance(slot, (list, tuple)):
            elecciones[tuple(slot)] += 1
        else:
            fijos[slot] += 1
    lineas = []
    for color, n in fijos.items():
        emoji = Skills.EMOJI_COLOR.get(color, "")
        lineas.append(f"{emoji} {n}× {color} (fijo)")
    for opciones, n in elecciones.items():
        ops = " o ".join(f"{Skills.EMOJI_COLOR.get(c, '')} {c}" for c in opciones)
        lineas.append(f"🔀 {n}× a elegir entre: {ops}")
    return lineas


class Player(BasePlayer):
    def __init__(self, name, uid):
        BasePlayer.__init__(self, name, uid)
        self.personaje = None          # clave del personaje elegido
        self.tipo = None               # Politico/Militar/Piloto/Apoyo
        self.ubicacion = None          # clave de ubicación actual
        self.titulos = []              # ["Presidente"] / ["Almirante"]
        self.loyalty_cards = []        # lista de strings (cylon/humano/simpatizante)
        self.is_cylon = False          # revelado o no, refleja si tiene carta cylon
        self.revealed = False          # si ya se reveló como Cylon
        self.skill_hand = []           # lista de cartas {color, valor}
        self.skill_choices_pendientes = []  # slots de elección del reparto inicial por decidir
        self.quorum_hand = []          # cartas de Quórum (Presidente)
        self.super_crisis = None       # Súper Crisis en mano (Cylon revelado): se juega en Caprica
        self.en_calabozo = False
        self.habilidad_usada = False   # habilidad de "una vez por juego"
        self.viper_area = None         # índice de área si pilota un Viper (None = en una ubicación)

    def get_private_info(self, game):
        """Información privada del jugador: su personaje y datos iniciales,
        incluyendo qué cartas de habilidad recibe cada turno (color, cantidad y
        si son fijas o a elegir)."""
        pj = Characters.PERSONAJES.get(self.personaje)
        if not pj:
            return ("🚀 *Battlestar Galactica*\n\n"
                    "Todavía no tienes personaje asignado en esta partida.")
        emoji_tipo = Characters.EMOJI_TIPO.get(pj["tipo"], "")
        ubic = Locations.UBICACIONES.get(pj["ubicacion"], {}).get("nombre", pj["ubicacion"])
        lineas = [
            "🚀 *Battlestar Galactica — Tu personaje*",
            "",
            f"{emoji_tipo} *{pj['nombre']}*  ·  _{pj['tipo']}_",
        ]
        if pj.get("titulo"):
            lineas.append(f"🏷️ Título inicial: *{pj['titulo']}*")
        lineas.append(f"📍 Ubicación inicial: {ubic}")
        lineas.append("")
        lineas.append("🃏 *Cartas de habilidad que recibes cada turno:*")
        for l in _resumen_skill_set(pj["skill_set"]):
            lineas.append(f"  • {l}")
        lineas.append(f"  _Total: {len(pj['skill_set'])} cartas por turno._")
        lineas.append("")
        lineas.append("✨ *Habilidades:*")
        lineas.append(pj["abilities"])
        return "\n".join(lineas)

