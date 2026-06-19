#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Battlestar Galactica — Controller (Capa 1: fundamentos + bucle central).

Implementado en esta capa:
- Setup completo: selección de personajes, reparto de lealtad, títulos
  (Presidente/Almirante), recursos y pistas iniciales, manos de habilidad.
- Bucle de turno: Recibir Habilidades → (Acción simplificada) → Crisis.
- Recibir Habilidades fiel al set del personaje: se roba el set completo cada
  turno; los slots fijos se reparten solos y los de elección (p. ej. Apolo,
  Liderazgo/Política) los decide el jugador.
- Chequeos de habilidad con mazo de Destino.
- Fase del Agente Durmiente (distancia 4).
- Salto FTL, condiciones de victoria/derrota.
- Combate espacial posicional: Vipers tripulados, Heavy Raiders, abordaje.
- Daño a Galactica por ubicaciones e iconos de activación Cylon por crisis.

- Cartas de habilidad jugables con /jugar: de acción (Consolidate Power,
  Repair, Maximum Firepower, Launch Scout, Executive Order) y reactivas que se
  arman (Strategic Planning +2 al ataque, Evasive Maneuvers reroll defensivo).
- Habilidades 1/juego de cada personaje y pasivas de los 9 personajes: Adama
  (fuerza 1 positiva), Tyrol (mano 8), Apollo (descartes al azar), Baltar (roba
  carta tras la Crisis), Roslin (roba 2 Crisis y elige 1), Boomer (mira la
  próxima Crisis al final de su turno), Tigh/Zarek (ajustan dificultad de
  ciertas ubicaciones), Helo (repite 1 tirada de ataque/turno), Starbuck (aviso
  de acciones extra al pilotar).

- Acciones de ubicación completas: Comunicaciones reposiciona naves civiles, y
  la Oficina del Presidente roba 1 carta de Quórum y permite robar otra o jugar.
- Quórum (poderes presidenciales): cartas inmediatas/dirigidas y las que
  permanecen en juego — Aceptar la Profecía (+2 al chequeo de Presidente),
  Especialista de Misión (elige destino en el próximo salto), Árbitro (±3 en el
  Camarote del Almirante) y Vicepresidente (único candidato a la Presidencia).

- Súper crisis: al revelarse, el Cylon roba una Súper Crisis a su mano; la juega
  desde Caprica (resuelve sus efectos) o la intercambia en la Nave de
  Resurrección. Mazo y descarte propios.

Pendiente para capas siguientes (claramente acotado):
- Roster completo de cartas de crisis con sus efectos de éxito/fracaso.
"""

import logging as log
import random
import re

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from Utils import get_game, save, simple_choose_buttons, player_call
from Constants.Config import ADMIN
from BattlestarGalactica.Boardgamebox.Game import Game
from BattlestarGalactica.Constants import Characters, Locations, Skills, Crisis, Loyalty, Quorum, Space

import GamesController

log.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=log.INFO)
logger = log.getLogger(__name__)


# ===================== SETUP =====================

async def init_game(bot, game):
    try:
        log.info("BSG init_game called")
        game.shuffle_player_sequence()
        st = game.board.state

        # Construir mazos
        st.skill_decks = Skills.construir_todos_los_mazos()
        for color in st.skill_decks:
            random.shuffle(st.skill_decks[color])
        st.skill_discards = {color: [] for color in Skills.COLORES}

        # Mazo de Destino: 2 cartas de cada color, barajadas
        st.destiny_deck = []
        for color in Skills.COLORES:
            for _ in range(2):
                if st.skill_decks[color]:
                    st.destiny_deck.append(st.skill_decks[color].pop())
        random.shuffle(st.destiny_deck)

        # Mazo de crisis
        st.crisis_deck = [dict(c) for c in Crisis.CRISIS_DECK]
        random.shuffle(st.crisis_deck)
        st.crisis_discard = []

        # Mazo de súper crisis (para Cylons revelados)
        st.super_crisis_deck = [dict(c) for c in Crisis.SUPER_CRISIS_DECK]
        random.shuffle(st.super_crisis_deck)

        # Mazo de Quórum (para el Presidente)
        st.quorum_deck = [dict(c) for c in Quorum.QUORUM_DECK]
        random.shuffle(st.quorum_deck)
        st.quorum_discard = []

        # Orden de selección de personajes = orden de jugadores
        st.orden_seleccion = [p.uid for p in game.player_sequence]
        st.indice_seleccion = 0
        st.fase_actual = "Seleccion de Personajes"

        await bot.send_message(
            game.cid,
            "🚀 *¡Comienza Battlestar Galactica!*\n\n"
            "Primero cada jugador elige su personaje, en orden. "
            "Luego se repartirán las cartas de lealtad en privado (¿quién es Cylon?).",
            parse_mode=ParseMode.MARKDOWN,
        )
        await pedir_seleccion_personaje(bot, game)
        await save(bot, game.cid)
    except Exception as e:
        logger.error(f"BSG init_game error: {e}")
        await bot.send_message(ADMIN[0], f"BSG init_game error: {e}")
        raise


async def pedir_seleccion_personaje(bot, game):
    st = game.board.state
    if st.indice_seleccion >= len(st.orden_seleccion):
        await finalizar_setup(bot, game)
        return

    uid = st.orden_seleccion[st.indice_seleccion]
    player = game.playerlist[uid]
    elegidos = set(st.personajes_elegidos.values())

    btns = []
    for tipo in Characters.TIPOS:
        emoji = Characters.EMOJI_TIPO[tipo]
        for key, pj in Characters.personajes_por_tipo(tipo).items():
            if key in elegidos:
                continue
            btns.append([InlineKeyboardButton(
                f"{emoji} {pj['nombre']} ({tipo})",
                callback_data=f"{game.cid}*bsgPick*{key}*{uid}"
            )])

    await bot.send_message(
        game.cid,
        f"🎭 {player_call(player)}, elige tu personaje:",
        reply_markup=InlineKeyboardMarkup(btns),
        parse_mode=ParseMode.MARKDOWN,
    )


async def asignar_personaje(bot, game, uid, key):
    st = game.board.state
    pj = Characters.PERSONAJES[key]
    player = game.playerlist[uid]
    player.personaje = key
    player.tipo = pj["tipo"]
    player.ubicacion = pj["ubicacion"]
    st.personajes_elegidos[uid] = key

    await bot.send_message(
        uid,
        f"{Characters.EMOJI_TIPO[pj['tipo']]} Eres *{pj['nombre']}* ({pj['tipo']}).\n\n"
        f"*Habilidades:*\n{pj['abilities']}\n\n"
        f"📍 Ubicación inicial: {Locations.UBICACIONES[pj['ubicacion']]['nombre']}",
        parse_mode=ParseMode.MARKDOWN,
    )
    st.indice_seleccion += 1
    await pedir_seleccion_personaje(bot, game)


async def finalizar_setup(bot, game):
    st = game.board.state
    st.fase_actual = "Repartiendo Lealtad"

    # --- Construir y repartir mazo de lealtad ---
    num = len(game.playerlist)
    num_bb = sum(1 for p in game.playerlist.values()
                 if p.personaje in ("baltar", "boomer"))
    st.loyalty_deck = Loyalty.construir_mazo_lealtad(num, num_bb)
    random.shuffle(st.loyalty_deck)

    for uid, player in game.playerlist.items():
        pj = Characters.PERSONAJES[player.personaje]
        cantidad = 1 + pj.get("loyalty_extra", 0)
        for _ in range(cantidad):
            if st.loyalty_deck:
                player.loyalty_cards.append(st.loyalty_deck.pop())
        player.is_cylon = Loyalty.CYLON in player.loyalty_cards
        await _dm_lealtad(bot, player)

    # --- Títulos ---
    _asignar_titulos(game)
    pres = game.playerlist.get(st.presidente_uid)
    alm = game.playerlist.get(st.almirante_uid)

    # --- Flota inicial ---
    _colocar_flota_inicial(st)

    # --- Mano inicial de habilidades (regla del juego base) ---
    # Todos los jugadores EXCEPTO el primero roban su set completo de habilidades
    # al empezar (los slots de elección se resuelven al azar en este reparto de
    # setup). El primer jugador robará su mano en su primer turno (su ventaja es
    # jugar primero).
    primer_jugador = game.player_sequence[0]
    for player in game.player_sequence:
        if player.uid == primer_jugador.uid:
            continue
        _robar_skills(st, player)
        await _dm_mano(bot, player)

    st.fase_actual = "En Juego"
    st.player_counter = 0
    st.active_player = primer_jugador

    await bot.send_message(
        game.cid,
        "🃏 *Cartas de lealtad repartidas* (revisen su privado).\n\n"
        f"🏛️ Presidente: *{pres.name if pres else '—'}*\n"
        f"🎖️ Almirante: *{alm.name if alm else '—'}*\n\n"
        "🛸 *Despliegue inicial:* 1 Basestar y 3 Raiders acechan frente a Galactica, "
        "con 2 Vipers en el espacio y 2 naves civiles a proteger.\n\n"
        "La flota parte. ¡Sobrevivan hasta la distancia 8!",
        parse_mode=ParseMode.MARKDOWN,
    )
    await bot.send_message(game.cid, game.board.print_board(game), parse_mode=ParseMode.MARKDOWN)
    await bot.send_message(game.cid, game.board.print_map(game), parse_mode=ParseMode.MARKDOWN)
    await save(bot, game.cid)
    await iniciar_turno(bot, game)


def _asignar_titulos(game):
    st = game.board.state
    uids = [p.uid for p in game.player_sequence]

    # Presidente: Roslin si está; si no, un Político; si no, el primero.
    pres = next((u for u in uids if game.playerlist[u].personaje == "roslin"), None)
    if pres is None:
        pres = next((u for u in uids if game.playerlist[u].tipo == "Politico"), uids[0])
    # Almirante: Adama si está; si no, un Militar; si no, otro distinto al pres.
    alm = next((u for u in uids if game.playerlist[u].personaje == "adama"), None)
    if alm is None:
        alm = next((u for u in uids if game.playerlist[u].tipo == "Militar" and u != pres), None)
    if alm is None:
        alm = next((u for u in uids if u != pres), uids[0])

    st.presidente_uid = pres
    st.almirante_uid = alm
    game.playerlist[pres].titulos.append("Presidente")
    game.playerlist[alm].titulos.append("Almirante")


def _slots_personaje(skill_set):
    """Normaliza un skill_set a una lista de slots; cada slot es la lista de
    colores admitidos (1 color = slot fijo; varios = slot de elección)."""
    return [list(s) if isinstance(s, (list, tuple)) else [s] for s in skill_set]


def _robar_skills(st, player, cantidad=None):
    """Reparte la mano de habilidades del set del personaje (un slot = una carta).
    Los slots fijos dan su color; los de elección se resuelven al azar (reparto
    automático de setup). Si se pasa 'cantidad', limita el número de cartas."""
    pj = Characters.PERSONAJES[player.personaje]
    slots = _slots_personaje(pj["skill_set"])
    if cantidad is not None:
        slots = slots[:cantidad]
    for opciones in slots:
        color = random.choice(opciones)
        carta = _robar_carta_color(st, color)
        if carta:
            player.skill_hand.append(carta)


LIMITE_MANO = 10


def _limite_mano(player):
    """Límite de mano de cartas de habilidad (Tyrol 'Imprudente' tiene 8)."""
    if getattr(player, "personaje", None) == "tyrol":
        return 8
    return LIMITE_MANO


async def _descartar_hasta_limite(bot, game, player):
    """Al final del turno, descarta hasta el límite de 10 cartas de habilidad.
    El motor descarta automáticamente las de menor fuerza (las menos útiles)."""
    limite = _limite_mano(player)
    sobran = len(player.skill_hand) - limite
    if sobran <= 0:
        return
    st = game.board.state
    # Apollo 'Cabezadura': los descartes forzados son al azar (no elige el motor).
    if getattr(player, "personaje", None) == "apollo" and not player.revealed:
        random.shuffle(player.skill_hand)
    else:
        # Ordenar por fuerza ascendente y descartar las más débiles.
        player.skill_hand.sort(key=lambda c: c.get("valor", 0))
    descartadas = [player.skill_hand.pop(0) for _ in range(sobran)]
    for c in descartadas:
        st.skill_discards.setdefault(c["color"], []).append(c)
    await bot.send_message(
        player.uid,
        f"🗑️ Tenías más de {limite} cartas; se descartaron {sobran} "
        f"(las de menor fuerza).",
    )
    await _dm_mano(bot, player)


def _robar_carta_color(st, color):
    if not st.skill_decks.get(color):
        # Rebarajar descartes de ese color
        if st.skill_discards.get(color):
            st.skill_decks[color] = st.skill_discards[color]
            st.skill_discards[color] = []
            random.shuffle(st.skill_decks[color])
    if st.skill_decks.get(color):
        return st.skill_decks[color].pop()
    return None


async def _dm_lealtad(bot, player):
    cartas = player.loyalty_cards
    es_cylon = Loyalty.CYLON in cartas
    es_simp = Loyalty.SIMPATIZANTE in cartas
    if es_cylon:
        txt = ("🤖 *ERES UN CYLON.*\nSabotea a la flota sin que te descubran. "
               "Podrás revelarte más adelante para causar más daño.")
    elif es_simp:
        txt = ("🕵️ Tienes la carta de *Simpatizante*. Su efecto se resolverá en la "
               "Fase del Agente Durmiente.")
    else:
        txt = "🧑 *No eres un Cylon* (por ahora). Ayuda a la flota a sobrevivir."
    await bot.send_message(player.uid, txt, parse_mode=ParseMode.MARKDOWN)


async def _dm_mano(bot, player):
    if not player.skill_hand:
        return
    lineas = [f"{i+1}. {Skills.EMOJI_COLOR[c['color']]} {c['color']} {c['valor']} — _{c.get('nombre','')}_"
              for i, c in enumerate(player.skill_hand)]
    await bot.send_message(
        player.uid,
        "🃏 *Tu mano de habilidad:*\n" + "\n".join(lineas),
        parse_mode=ParseMode.MARKDOWN,
    )


# ===================== BUCLE DE TURNO =====================

async def iniciar_turno(bot, game):
    st = game.board.state
    if st.ganador:
        return
    player = st.active_player

    # Pasivas al inicio del turno
    if not player.revealed:
        if player.personaje == "helo":
            st.reroll_armed = True   # Oficial ECO: 1 repetición de tirada este turno
        elif player.personaje == "starbuck" and getattr(player, "viper_area", None) is not None:
            await bot.send_message(
                game.cid,
                f"✈️ *Piloto Experta*: {player.name} empieza pilotando un Viper y puede tomar acciones extra.",
                parse_mode=ParseMode.MARKDOWN,
            )

    # Paso "Recibir Habilidades": se roba el set completo del personaje. Los slots
    # fijos se reparten solos; los de elección los decide el jugador.
    if player.revealed:
        slots = [list(Skills.COLORES), list(Skills.COLORES)]  # Cylon: 2 cartas a elección
        encabezado = f"🤖 *Turno del Cylon {player.name}*"
    else:
        pj = Characters.PERSONAJES[player.personaje]
        slots = _slots_personaje(pj["skill_set"])
        encabezado = f"🎬 *Turno de {player.name}*"

    st.skill_draw = {"uid": player.uid, "slots": slots}
    await bot.send_message(
        game.cid,
        f"{encabezado} — *Recibir Habilidades*.\n"
        f"{player.name} recibe su set de habilidades (las de elección, en privado)…",
        parse_mode=ParseMode.MARKDOWN,
    )
    await save(bot, game.cid)
    await _procesar_slots_skill(bot, game)


async def _procesar_slots_skill(bot, game):
    """Reparte automáticamente los slots fijos; al llegar a un slot de elección,
    pide el color al jugador. Termina el paso cuando no quedan slots."""
    st = game.board.state
    sd = st.skill_draw
    if not sd:
        return
    player = game.playerlist.get(sd["uid"])
    if not player:
        return
    # Slots fijos consecutivos → se reparten solos.
    while sd["slots"] and len(sd["slots"][0]) == 1:
        color = sd["slots"].pop(0)[0]
        await _entregar_carta_skill(bot, game, player, color)
    if sd["slots"]:
        await save(bot, game.cid)
        await _prompt_color_skill(bot, game)
        return
    st.skill_draw = None
    await _dm_mano(bot, player)
    await save(bot, game.cid)
    await _anunciar_turno(bot, game)


async def _entregar_carta_skill(bot, game, player, color):
    """Roba 1 carta del color dado a la mano del jugador y lo notifica por privado."""
    st = game.board.state
    carta = _robar_carta_color(st, color)
    if carta:
        player.skill_hand.append(carta)
        await bot.send_message(
            player.uid,
            f"➕ Robaste {Skills.EMOJI_COLOR[carta['color']]} {carta['color']} {carta['valor']} "
            f"— _{carta.get('nombre','')}_",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await bot.send_message(player.uid, f"(No quedan cartas de {color}.)")


async def _prompt_color_skill(bot, game):
    """Pide por privado al jugador activo el color del siguiente slot de elección."""
    st = game.board.state
    sd = st.skill_draw
    if not sd or not sd["slots"]:
        return
    player = game.playerlist.get(sd["uid"])
    if not player:
        return
    opciones = sd["slots"][0]
    btns = [[InlineKeyboardButton(
                f"{Skills.EMOJI_COLOR[c]} {c}",
                callback_data=f"{game.cid}*bsgDraw*{c}*{player.uid}")]
            for c in opciones]
    await bot.send_message(
        player.uid,
        f"🃏 *Recibir Habilidades* — te quedan *{len(sd['slots'])}* carta(s).\n"
        f"Elige el tipo de esta carta ({' / '.join(opciones)}):",
        reply_markup=InlineKeyboardMarkup(btns),
        parse_mode=ParseMode.MARKDOWN,
    )


async def elegir_color_skill(bot, game, uid, color):
    """Resuelve un slot de elección con el color elegido y continúa el reparto."""
    st = game.board.state
    sd = st.skill_draw
    if not sd or sd["uid"] != uid or not sd["slots"] or color not in sd["slots"][0]:
        return
    player = game.playerlist[uid]
    sd["slots"].pop(0)
    await _entregar_carta_skill(bot, game, player, color)
    await _procesar_slots_skill(bot, game)


async def _anunciar_turno(bot, game):
    """Anuncia en el grupo las acciones disponibles tras Recibir Habilidades."""
    st = game.board.state
    player = st.active_player
    ubic = Locations.UBICACIONES.get(player.ubicacion, {}).get("nombre", "—")
    if player.revealed:
        await bot.send_message(
            game.cid,
            f"🤖 *{player.name}* recibió sus cartas.\n"
            f"📍 Estás en: *{ubic}*\n\n"
            f"`/mover` y `/accion` para sabotear · luego `/crisis` para *terminar tu turno* "
            f"(los Cylon no roban crisis).\n"
            f"Consulta `/mapa` para ver la flota.",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await bot.send_message(
            game.cid,
            f"🎬 *{player.name}* recibió sus cartas de habilidad.\n"
            f"📍 Estás en: *{ubic}*\n\n"
            f"`/mover` para cambiar de ubicación · `/accion` para la acción de tu ubicación · "
            f"luego `/crisis` para revelar la crisis.\n"
            f"Consulta `/mapa` para ver la flota y dónde está cada jugador.",
            parse_mode=ParseMode.MARKDOWN,
        )


async def avanzar_turno(bot, game):
    st = game.board.state
    if st.ganador:
        return
    # Fin del turno del jugador activo: descartar hasta el límite de mano.
    if st.active_player:
        await _descartar_hasta_limite(bot, game, st.active_player)
    # Los efectos reactivos armados caducan al cambiar de turno.
    st.bonus_actor = None
    st.dado_bonus = 0
    st.evasive_armed = False
    st.reroll_armed = False
    seq = game.player_sequence
    st.player_counter = (st.player_counter + 1) % len(seq)
    st.active_player = seq[st.player_counter]
    await iniciar_turno(bot, game)


# ===================== FLOTA / COMBATE ESPACIAL =====================

# Distribución de carga de las naves civiles (juego base). Cada nave civil
# lleva una carga oculta hasta que es destruida: algunas transportan un recurso
# y otras van vacías.
CIVILES_CARGAS = [
    {"recurso": "combustible", "cantidad": 1},
    {"recurso": "combustible", "cantidad": 1},
    {"recurso": "poblacion", "cantidad": 1},
    {"recurso": "poblacion", "cantidad": 1},
    {"recurso": "moral", "cantidad": 1},
    {"recurso": None, "cantidad": 0},
    {"recurso": None, "cantidad": 0},
    {"recurso": None, "cantidad": 0},
]


def _colocar_flota_inicial(st):
    """Despliega la disposición inicial del juego base sobre las áreas:
    - 1 Viper en cada tubo de lanzamiento (2 en total).
    - 1 Basestar y 3 Raiders como amenaza Cylon en la Proa.
    - 2 Naves civiles en la Popa (con carga oculta); el resto queda en reserva.
    """
    # Vipers: 1 en cada tubo de lanzamiento
    for area_idx in Space.LAUNCH_AREAS:
        if st.vipers_reserva > 0:
            st.vipers_reserva -= 1
            st.areas[area_idx]["vipers"] += 1

    # Amenaza Cylon inicial en la Proa
    st.areas[Space.AREA_PROA]["basestars"].append(0)   # 0 tokens de daño
    st.areas[Space.AREA_PROA]["raiders"] += 3

    # Naves civiles: 2 en la Popa, el resto a la pila de reserva
    pila = [dict(c) for c in CIVILES_CARGAS]
    random.shuffle(pila)
    for _ in range(min(2, len(pila))):
        st.areas[Space.AREA_POPA]["civiles"].append(pila.pop())
    st.civiles_pile = pila


def _d8():
    return random.randint(1, 8)


def _tirar_ataque(st):
    """Tirada de ataque del bando humano. Aplica las pasivas/cartas que afectan
    la tirada: Helo 'Oficial ECO' (repite 1/turno y se queda con la mejor) y
    'Strategic Planning' (Planificación Estratégica, +N armado)."""
    base = random.randint(1, 8)
    if getattr(st, "reroll_armed", False):
        st.reroll_armed = False
        base = max(base, random.randint(1, 8))
    bonus = getattr(st, "dado_bonus", 0)
    if bonus:
        st.dado_bonus = 0
    return base + bonus


# ---- Helpers de áreas y combate posicional ----

def _areas_con(st, tipo):
    """Índices de áreas que contienen al menos una nave del tipo dado
    ('raiders', 'heavy_raiders', 'basestars', 'vipers', 'civiles')."""
    res = []
    for i, a in enumerate(st.areas):
        if tipo in ("raiders", "vipers", "heavy_raiders"):
            cant = a.get(tipo, 0)
        else:
            cant = len(a.get(tipo, []))
        if cant > 0:
            res.append(i)
    return res


async def _lanzar_raider_token(st, area_idx, cantidad=1):
    st.areas[area_idx]["raiders"] += cantidad


async def _danar_basestar(bot, game, area_idx, cantidad=1):
    """Aplica 'cantidad' tokens de daño a una Basestar del área; 3 = destruida."""
    st = game.board.state
    bs = st.areas[area_idx]["basestars"]
    if not bs:
        return
    # Concentrar el daño en la Basestar más dañada del área.
    k = max(range(len(bs)), key=lambda j: bs[j])
    bs[k] += cantidad
    if bs[k] >= 3:
        bs.pop(k)
        await bot.send_message(game.cid, "🛸💀 ¡Basestar destruida!")
    else:
        await bot.send_message(game.cid, f"💥 Impacto en Basestar ({bs[k]}/3) en {Space.nombre(area_idx)}.")


async def _danar_galactica(bot, game, fuente="ataque"):
    """Galactica recibe un token de avería en una ubicación al azar (deshabilita
    su acción). Con las 6 ubicaciones averiadas, Galactica es destruida."""
    st = game.board.state
    disponibles = [k for k in Locations.GALACTICA_DAMAGEABLE if k not in st.galactica_damage]
    if not disponibles:
        await bot.send_message(game.cid, f"🛡️💥 Galactica recibe daño ({fuente}): ya no quedan sistemas operativos.")
        return
    loc = random.choice(disponibles)
    st.galactica_damage.append(loc)
    nombre = Locations.UBICACIONES[loc]["nombre"].split(" (")[0]
    await bot.send_message(
        game.cid,
        f"🛡️💥 *Galactica recibe daño* ({fuente}): se avería *{nombre}* "
        f"({st.total_danos_galactica()}/{st.galactica_danos_max}).",
        parse_mode=ParseMode.MARKDOWN,
    )


async def _reparar_galactica(bot, game, player, loc=None):
    """Repara una ubicación averiada de Galactica (equipo de control de daños)."""
    st = game.board.state
    if not st.galactica_damage:
        await bot.send_message(game.cid, "🔧 No hay sistemas averiados que reparar.")
        return
    if loc is None or loc not in st.galactica_damage:
        loc = st.galactica_damage[0]
    st.galactica_damage.remove(loc)
    nombre = Locations.UBICACIONES[loc]["nombre"].split(" (")[0]
    await bot.send_message(
        game.cid,
        f"🔧 {player.name} repara *{nombre}* "
        f"({st.total_danos_galactica()}/{st.galactica_danos_max} averiadas).",
        parse_mode=ParseMode.MARKDOWN,
    )


# Acciones disponibles por ubicación (clave -> lista de acciones), según el set oficial.
ACCIONES_UBICACION = {
    "ftl": ["jump"],
    "weapons": ["shoot_raider", "shoot_basestar"],
    "command": ["activate_vipers"],
    "communications": ["peek_civiles"],
    "admiral_quarters": ["brig_check"],
    "research": ["draw_eng", "draw_tac", "repair"],
    "hangar": ["launch"],
    "armory": ["armory_attack"],
    "sickbay": [],
    "brig": ["brig_escape"],
    "press_room": ["draw_politics"],
    "president_office": ["draw_quorum"],
    "administration": ["president_check"],
}

# Acciones que requieren elegir un personaje objetivo (abren chequeo de ubicación)
ACCIONES_CON_OBJETIVO = {"brig_check": "brig", "president_check": "president"}

# Acciones que requieren elegir un ÁREA del espacio (Control de Armas) → tipo de nave
ACCIONES_CON_AREA = {"shoot_raider": "raiders", "shoot_basestar": "basestars"}

# Acciones disponibles mientras se pilota un Viper tripulado.
ACCIONES_PILOTO = ["pilot_attack", "pilot_move", "pilot_land"]

# Acción de piloto que requiere elegir un área adyacente.
ACCIONES_PILOTO_AREA = {"pilot_move"}

ETIQUETA_ACCION = {
    "jump": "🌌 Saltar la flota (FTL)",
    "shoot_raider": "🔫 Disparar a un Raider",
    "shoot_basestar": "💥 Disparar a una Basestar",
    "activate_vipers": "✈️ Activar Vipers (atacan Raiders)",
    "peek_civiles": "🔭 Inspeccionar naves civiles",
    "brig_check": "🚔 Enviar a alguien al Calabozo (chequeo)",
    "draw_eng": "🔵 Robar 1 carta de Ingeniería",
    "draw_tac": "🟣 Robar 1 carta de Táctica",
    "repair": "🔧 Reparar un sistema de Galactica",
    "launch": "✈️ Lanzarte en un Viper",
    "armory_attack": "🪖 Atacar a un centurión",
    "draw_politics": "🟡 Robar 2 cartas de Política",
    "draw_quorum": "🏛️ Robar una carta de Quórum",
    "president_check": "🏛️ Dar la Presidencia (chequeo)",
    "pilot_attack": "🔫 Atacar Cylon en tu área",
    "pilot_move": "✈️ Volar a un área adyacente",
    "pilot_land": "🛬 Aterrizar en Galactica",
}


async def ejecutar_accion_ubicacion(bot, game, uid, accion, objetivo=None):
    """Resuelve la acción de ubicación elegida por el jugador activo."""
    st = game.board.state
    player = game.playerlist[uid]

    # Una ubicación averiada no permite usar su acción hasta repararla.
    if st.ubicacion_averiada(player.ubicacion):
        nombre = Locations.UBICACIONES[player.ubicacion]["nombre"].split(" (")[0]
        await bot.send_message(game.cid, f"🛠️ *{nombre}* está averiada: hay que repararla antes de usar su acción.",
                               parse_mode=ParseMode.MARKDOWN)
        return

    if accion == "jump":
        # FTL Control: saltar si el track no está en zona roja (proxy: prep >= 2)
        if st.jump_prep < 2:
            await bot.send_message(game.cid, "El track de salto aún no está listo (necesita avanzar más por crisis).")
            return
        await ejecutar_salto(bot, game, auto=False)
    elif accion == "shoot_raider":
        await _disparar(bot, game, "raider", objetivo)
    elif accion == "shoot_basestar":
        await _disparar(bot, game, "basestar", objetivo)
    elif accion == "activate_vipers":
        # Comando: hasta 2 activaciones de Vipers sin tripular (atacar o mover).
        await _activar_vipers_comando(bot, game)
    elif accion == "peek_civiles":
        lineas = []
        for i, a in enumerate(st.areas):
            for c in a["civiles"]:
                lineas.append(f"{Space.nombre(i)}: {c['recurso'] or 'vacía'}")
        info = "\n".join(lineas) or "ninguna"
        await bot.send_message(uid, f"🔭 Cargas de las naves civiles:\n{info}")
        await bot.send_message(game.cid, f"🔭 {player.name} inspecciona las naves civiles.")
        # Comunicaciones: además, puedes reposicionar una nave civil hacia la
        # retaguardia (Popa), lejos de la amenaza Cylon de la proa.
        btns = [[InlineKeyboardButton(f"🚚 Mover civil de {Space.nombre(i)} a {Space.nombre(_paso_hacia(i, [Space.AREA_POPA]))}",
                                      callback_data=f"{game.cid}*bsgCivil*{i}*{uid}")]
                for i, a in enumerate(st.areas) if a["civiles"] and i != Space.AREA_POPA]
        btns.append([InlineKeyboardButton("✅ No mover", callback_data=f"{game.cid}*bsgCivil*-1*{uid}")])
        await bot.send_message(uid, "🔭 ¿Reposicionar una nave civil?",
                               reply_markup=InlineKeyboardMarkup(btns))
    elif accion == "draw_eng":
        await _robar_color(bot, game, player, Skills.INGENIERIA)
    elif accion == "draw_tac":
        await _robar_color(bot, game, player, Skills.TACTICA)
    elif accion == "repair":
        await _reparar_galactica(bot, game, player)
    elif accion == "launch":
        await _lanzar_piloto(bot, game, player)
    elif accion == "pilot_attack":
        await _pilot_atacar(bot, game, player)
    elif accion == "pilot_move":
        await _pilot_mover(bot, game, player, objetivo)
    elif accion == "pilot_land":
        await _pilot_aterrizar(bot, game, player)
    elif accion == "armory_attack":
        if not st.boarding_party:
            await bot.send_message(game.cid, "No hay centuriones a bordo de Galactica.")
        else:
            r = _tirar_ataque(st)
            if r >= 7:
                _destruir_centurion_avanzado(st)
                await bot.send_message(game.cid, f"🪖 Tirada {r}: ¡centurión destruido! (a bordo: {st.total_centuriones()})")
            else:
                await bot.send_message(game.cid, f"🪖 Tirada {r}: el centurión resiste el fuego.")
    elif accion == "draw_politics":
        await _robar_color(bot, game, player, Skills.POLITICA)
        await _robar_color(bot, game, player, Skills.POLITICA)
    elif accion == "draw_quorum":
        if uid != st.presidente_uid and uid not in ADMIN:
            await bot.send_message(game.cid, "Solo el Presidente puede robar cartas de Quórum.")
            return
        await robar_quorum(bot, game, uid)
        # Oficina del Presidente: tras robar 1, puedes robar otra o jugar una (/quorum).
        btns = [[InlineKeyboardButton("🏛️ Robar otra carta", callback_data=f"{game.cid}*bsgQDraw*{uid}"),
                 InlineKeyboardButton("✅ Terminar", callback_data=f"{game.cid}*bsgQDraw*0")]]
        await bot.send_message(uid, "🏛️ Puedes *robar otra* carta de Quórum o *terminar* (y jugar una con `/quorum`).",
                               reply_markup=InlineKeyboardMarkup(btns), parse_mode=ParseMode.MARKDOWN)
    elif accion in ("brig_check", "president_check"):
        await abrir_chequeo_ubicacion(bot, game, uid, accion, objetivo)
        return  # el chequeo se resuelve aparte; no guardar dos veces
    elif accion == "brig_escape":
        await abrir_chequeo_ubicacion(bot, game, uid, accion, uid)
        return
    else:
        await bot.send_message(game.cid, "Acción no disponible.")
    await save(bot, game.cid)


async def _robar_color(bot, game, player, color):
    carta = _robar_carta_color(game.board.state, color)
    if carta:
        player.skill_hand.append(carta)
    await bot.send_message(game.cid, f"🃏 {player.name} roba 1 carta ({color}).")
    await _dm_mano(bot, player)


# ---- Chequeos de habilidad asociados a una acción de ubicación ----

async def abrir_chequeo_ubicacion(bot, game, actor_uid, accion, objetivo_uid):
    st = game.board.state
    # Determinar ubicación y su check
    player = game.playerlist[actor_uid]
    info = Locations.UBICACIONES.get(player.ubicacion, {})
    check = info.get("check")
    if not check:
        await bot.send_message(game.cid, "Aquí no hay un chequeo disponible.")
        return
    if st.skill_check:
        await bot.send_message(game.cid, "Ya hay un chequeo abierto.")
        return
    efecto = check["efecto"]
    dificultad = check["dificultad"]
    # Poder presidencial "Aceptar la Profecía": +2 al chequeo de Administración.
    if efecto == "president" and st.profecia_pendiente:
        dificultad += 2 * st.profecia_pendiente
        st.profecia_pendiente = 0
    st.skill_check = {
        "ubicacion_accion": efecto,
        "actor_uid": actor_uid,
        "objetivo_uid": objetivo_uid,
        "colores": check["colores"],
        "dificultad": dificultad,
        "aportes": {},
    }
    emojis = " ".join(Skills.EMOJI_COLOR[c] for c in check["colores"])
    obj = game.playerlist.get(objetivo_uid)
    obj_txt = f" sobre *{obj.name}*" if obj and objetivo_uid != actor_uid else ""
    await bot.send_message(
        game.cid,
        f"🎲 *Chequeo de acción*{obj_txt} — dificultad *{dificultad}*.\n"
        f"Colores positivos: {emojis}.\n"
        f"Aporten con `/aportar N` y resuelvan con `/resolver`.",
        parse_mode=ParseMode.MARKDOWN,
    )
    await save(bot, game.cid)
    await _ofrecer_modificador_dificultad(bot, game)


def _buscar_personaje(game, pj):
    """Devuelve el jugador (no revelado) que encarna al personaje dado, o None."""
    for p in game.playerlist.values():
        if getattr(p, "personaje", None) == pj and not p.revealed:
            return p
    return None


async def _ofrecer_modificador_dificultad(bot, game):
    """Ofrece a Tigh (Camarote del Almirante, −3) o Zarek (Administración/Calabozo,
    ±2) modificar la dificultad de un chequeo de acción de ubicación recién abierto."""
    st = game.board.state
    sc = st.skill_check
    if not sc or not sc.get("ubicacion_accion"):
        return
    actor = game.playerlist.get(sc.get("actor_uid"))
    if not actor:
        return
    loc = actor.ubicacion
    if loc == "admiral_quarters":
        tigh = _buscar_personaje(game, "tigh")
        if tigh:
            btns = [[InlineKeyboardButton("➖3 dificultad", callback_data=f"{game.cid}*bsgMod*-3*{tigh.uid}"),
                     InlineKeyboardButton("No usar", callback_data=f"{game.cid}*bsgMod*0*{tigh.uid}")]]
            await bot.send_message(tigh.uid, "🎖️ *Odio a los Cylons*: puedes reducir en 3 la dificultad de este chequeo.",
                                   reply_markup=InlineKeyboardMarkup(btns), parse_mode=ParseMode.MARKDOWN)
        # Poder presidencial "Árbitro": ajusta ±3 los chequeos del Camarote del Almirante.
        arb = game.playerlist.get(st.arbitro_uid)
        if arb and not arb.revealed:
            btns = [[InlineKeyboardButton("➖3", callback_data=f"{game.cid}*bsgMod*-3*{arb.uid}"),
                     InlineKeyboardButton("➕3", callback_data=f"{game.cid}*bsgMod*3*{arb.uid}"),
                     InlineKeyboardButton("No usar", callback_data=f"{game.cid}*bsgMod*0*{arb.uid}")]]
            await bot.send_message(arb.uid, "⚖️ *Árbitro*: puedes mover la dificultad de este chequeo en ±3.",
                                   reply_markup=InlineKeyboardMarkup(btns), parse_mode=ParseMode.MARKDOWN)
    elif loc in ("administration", "brig"):
        zarek = _buscar_personaje(game, "zarek")
        if zarek:
            btns = [[InlineKeyboardButton("➖2", callback_data=f"{game.cid}*bsgMod*-2*{zarek.uid}"),
                     InlineKeyboardButton("➕2", callback_data=f"{game.cid}*bsgMod*2*{zarek.uid}"),
                     InlineKeyboardButton("No usar", callback_data=f"{game.cid}*bsgMod*0*{zarek.uid}")]]
            await bot.send_message(zarek.uid, "🏛️ *Amigos en las Sombras*: puedes modificar la dificultad de este chequeo en ±2.",
                                   reply_markup=InlineKeyboardMarkup(btns), parse_mode=ParseMode.MARKDOWN)


async def aplicar_modificador_dificultad(bot, game, uid, delta):
    """Aplica el ajuste de dificultad de Tigh/Zarek (pasiva) o del Árbitro (poder
    presidencial) al chequeo de acción abierto."""
    st = game.board.state
    sc = st.skill_check
    if not sc or not sc.get("ubicacion_accion"):
        await bot.send_message(uid, "Ya no hay un chequeo de acción abierto.")
        return
    p = game.playerlist.get(uid)
    if not p or p.revealed:
        return
    es_pj = p.personaje in ("tigh", "zarek")
    es_arbitro = uid == st.arbitro_uid
    if not es_pj and not es_arbitro:
        return
    if delta == 0:
        await bot.send_message(uid, "No modificas la dificultad.")
        return
    sc["dificultad"] = max(0, sc["dificultad"] + delta)
    etiqueta = "El Árbitro" if es_arbitro and not es_pj else Characters.PERSONAJES[p.personaje]["nombre"]
    await bot.send_message(
        game.cid,
        f"🎚️ *{etiqueta}* ajusta la dificultad del chequeo en {'+' if delta > 0 else ''}{delta} (ahora *{sc['dificultad']}*).",
        parse_mode=ParseMode.MARKDOWN,
    )
    await save(bot, game.cid)


async def _resolver_chequeo_ubicacion(bot, game, sc, total, exito):
    """Aplica el resultado de un chequeo asociado a una acción de ubicación."""
    st = game.board.state
    efecto = sc["ubicacion_accion"]
    objetivo = game.playerlist.get(sc.get("objetivo_uid"))
    st.skill_check = None
    if not exito:
        await bot.send_message(game.cid, "❌ El chequeo de acción falla; no ocurre nada.")
        await save(bot, game.cid)
        return
    if efecto == "brig" and objetivo:
        objetivo.en_calabozo = True
        objetivo.ubicacion = "brig"
        await bot.send_message(game.cid, f"🚔 *{objetivo.name}* es enviado al Calabozo.", parse_mode=ParseMode.MARKDOWN)
    elif efecto == "president" and objetivo:
        ant = game.playerlist.get(st.presidente_uid)
        if ant and "Presidente" in ant.titulos:
            ant.titulos.remove("Presidente")
        st.presidente_uid = objetivo.uid
        if "Presidente" not in objetivo.titulos:
            objetivo.titulos.append("Presidente")
        # Si era el Vicepresidente, asume la Presidencia y se libera el puesto de VP.
        if objetivo.uid == st.vicepresidente_uid:
            st.vicepresidente_uid = None
        await bot.send_message(game.cid, f"🏛️ *{objetivo.name}* recibe el título de Presidente.", parse_mode=ParseMode.MARKDOWN)
    elif efecto == "escape" and objetivo:
        objetivo.en_calabozo = False
        objetivo.ubicacion = "sickbay"
        await bot.send_message(game.cid, f"🔓 *{objetivo.name}* sale del Calabozo (Enfermería).", parse_mode=ParseMode.MARKDOWN)
    await save(bot, game.cid)


def _paso_hacia(i, objetivos):
    """Área vecina de 'i' que más acerca a algún área objetivo (desempate horario)."""
    if not objetivos:
        return None
    cw = (i + 1) % Space.N_AREAS
    ccw = (i - 1) % Space.N_AREAS
    dcw = min(Space.distancia(cw, j) for j in objetivos)
    dccw = min(Space.distancia(ccw, j) for j in objetivos)
    return cw if dcw <= dccw else ccw


async def mover_civil(bot, game, area_idx):
    """Comunicaciones: mueve una nave civil del área dada un paso hacia la Popa."""
    st = game.board.state
    if area_idx < 0:
        return
    if not (0 <= area_idx < Space.N_AREAS) or not st.areas[area_idx]["civiles"]:
        await bot.send_message(game.cid, "No hay naves civiles que mover en esa área.")
        return
    destino = _paso_hacia(area_idx, [Space.AREA_POPA])
    if destino is None or destino == area_idx:
        return
    civil = st.areas[area_idx]["civiles"].pop()
    st.areas[destino]["civiles"].append(civil)
    await bot.send_message(
        game.cid,
        f"🚚 Una nave civil se reposiciona de {Space.nombre(area_idx)} a {Space.nombre(destino)}.",
    )
    await save(bot, game.cid)


def _quitar_raider(st):
    """Elimina un Raider de alguna área (la primera con Raiders). Devuelve True si lo hizo."""
    objetivos = _areas_con(st, "raiders")
    if not objetivos:
        return False
    st.areas[objetivos[0]]["raiders"] -= 1
    return True


async def _disparar(bot, game, objetivo, area_idx):
    """Galactica (Control de Armas) dispara a un Raider o Basestar en un área."""
    st = game.board.state
    if area_idx is None or not (0 <= area_idx < Space.N_AREAS):
        await bot.send_message(game.cid, "Área inválida.")
        return
    area = st.areas[area_idx]
    if objetivo == "raider":
        if area["raiders"] <= 0:
            await bot.send_message(game.cid, f"No hay Raiders en {Space.nombre(area_idx)}.")
            return
        r = _tirar_ataque(st)
        if r >= 3:   # tabla de combate: Raider destruido con 3-8
            area["raiders"] -= 1
            await bot.send_message(game.cid, f"🔫 Tirada {r}: ¡Raider destruido en {Space.nombre(area_idx)}! (quedan {area['raiders']})")
        else:
            await bot.send_message(game.cid, f"🔫 Tirada {r}: fallo.")
    else:
        if not area["basestars"]:
            await bot.send_message(game.cid, f"No hay Basestars en {Space.nombre(area_idx)}.")
            return
        r = _tirar_ataque(st)
        if r >= 5:   # Galactica vs Basestar: daña con 5-8
            await _danar_basestar(bot, game, area_idx)
        else:
            await bot.send_message(game.cid, f"💥 Tirada {r}: fallo.")


async def _lanzar_viper(bot, game, area_idx=None):
    """Lanza un Viper de la reserva a un tubo de lanzamiento."""
    st = game.board.state
    if st.vipers_reserva <= 0:
        await bot.send_message(game.cid, "No quedan Vipers en la reserva.")
        return False
    if area_idx is None:
        area_idx = min(Space.LAUNCH_AREAS, key=lambda i: st.areas[i]["vipers"])
    st.vipers_reserva -= 1
    st.areas[area_idx]["vipers"] += 1
    await bot.send_message(game.cid, f"✈️ Viper lanzado en {Space.nombre(area_idx)} (en vuelo: {st.total_vipers_espacio()}).")
    return True


# ---- Vipers tripulados (fichas de piloto) ----

def _pilotos_en_area(game, i):
    """Jugadores que pilotan un Viper en el área i."""
    return [p for p in game.playerlist.values() if getattr(p, "viper_area", None) == i]


def total_vipers_tripulados(game):
    return sum(1 for p in game.playerlist.values() if getattr(p, "viper_area", None) is not None)


async def _lanzar_piloto(bot, game, player):
    """El jugador despega en un Viper tripulado desde un tubo de lanzamiento."""
    st = game.board.state
    if getattr(player, "viper_area", None) is not None:
        await bot.send_message(game.cid, "Ya estás pilotando un Viper.")
        return False
    if st.vipers_reserva <= 0:
        await bot.send_message(game.cid, "No quedan Vipers en la reserva.")
        return False
    # Despega por el tubo con menos presencia Cylon.
    area = min(Space.LAUNCH_AREAS,
               key=lambda k: st.areas[k]["raiders"] + st.areas[k].get("heavy_raiders", 0) + len(st.areas[k]["basestars"]))
    st.vipers_reserva -= 1
    player.viper_area = area
    player.ubicacion = None
    await bot.send_message(game.cid, f"✈️ {player.name} despega en un Viper desde {Space.nombre(area)}.")
    return True


async def _pilot_atacar(bot, game, player):
    """El Viper tripulado ataca una nave Cylon de su área (Raider 3+, Heavy 4+, Basestar 6+)."""
    st = game.board.state
    i = player.viper_area
    area = st.areas[i]
    r = _tirar_ataque(st)
    if area["raiders"] > 0:
        if r >= 3:
            area["raiders"] -= 1
            await bot.send_message(game.cid, f"✈️🔫 Tirada {r}: {player.name} derriba un Raider en {Space.nombre(i)} (quedan {area['raiders']}).")
        else:
            await bot.send_message(game.cid, f"✈️ Tirada {r}: {player.name} falla contra el Raider.")
    elif area.get("heavy_raiders", 0) > 0:
        if r >= 4:
            area["heavy_raiders"] -= 1
            await bot.send_message(game.cid, f"✈️🔫 Tirada {r}: {player.name} derriba un Heavy Raider en {Space.nombre(i)}.")
        else:
            await bot.send_message(game.cid, f"✈️ Tirada {r}: {player.name} falla contra el Heavy Raider.")
    elif area["basestars"]:
        if r >= 6:
            await _danar_basestar(bot, game, i)
        else:
            await bot.send_message(game.cid, f"✈️ Tirada {r}: {player.name} no logra dañar la Basestar.")
    else:
        await bot.send_message(game.cid, "No hay naves Cylon en tu área para atacar.")


async def _pilot_mover(bot, game, player, destino):
    """El Viper tripulado vuela a un área adyacente del anillo."""
    i = player.viper_area
    if destino is None or destino not in Space.vecinos(i):
        await bot.send_message(game.cid, "Solo puedes volar a un área adyacente.")
        return
    player.viper_area = destino
    await bot.send_message(game.cid, f"✈️ {player.name} vuela de {Space.nombre(i)} a {Space.nombre(destino)}.")


async def _pilot_aterrizar(bot, game, player):
    """El Viper tripulado aterriza: vuelve a la reserva y el piloto al Hangar."""
    st = game.board.state
    st.vipers_reserva += 1
    player.viper_area = None
    player.ubicacion = "hangar"
    await bot.send_message(game.cid, f"🛬 {player.name} aterriza en la Cubierta de Hangar.")


async def _activar_vipers_comando(bot, game):
    """Hasta 2 activaciones de Vipers sin tripular (atacar Raider o moverse)."""
    st = game.board.state
    if st.total_vipers_espacio() == 0:
        await bot.send_message(game.cid, "No hay Vipers en el espacio para activar.")
        return
    for _ in range(2):
        await _activar_un_viper(bot, game)


async def _activar_un_viper(bot, game):
    """Un Viper ataca un Raider de su área; si no hay, se mueve hacia el más cercano."""
    st = game.board.state
    # 1. Atacar un Raider en un área donde haya Viper y Raider
    for i, a in enumerate(st.areas):
        if a["vipers"] > 0 and a["raiders"] > 0:
            r = _d8()
            if r >= 3:
                a["raiders"] -= 1
                await bot.send_message(game.cid, f"✈️🔫 Tirada {r}: el Viper derriba un Raider en {Space.nombre(i)} (quedan {a['raiders']}).")
            else:
                await bot.send_message(game.cid, f"✈️ Tirada {r}: el Viper falla en {Space.nombre(i)}.")
            return
    # 2. Mover un Viper hacia el Raider más cercano
    objetivos = _areas_con(st, "raiders")
    if not objetivos:
        await bot.send_message(game.cid, "No hay Raiders a los que atacar.")
        return
    for i, a in enumerate(st.areas):
        if a["vipers"] > 0:
            destino = _paso_hacia(i, objetivos)
            if destino is not None and destino != i:
                a["vipers"] -= 1
                st.areas[destino]["vipers"] += 1
                await bot.send_message(game.cid, f"✈️ Un Viper se mueve a {Space.nombre(destino)} para interceptar.")
            return


async def _nuke(bot, game, area_idx=None):
    """Ataque nuclear del Almirante (1 por juego) sobre una Basestar."""
    st = game.board.state
    if st.nuke_usado:
        await bot.send_message(game.cid, "El ataque nuclear ya fue utilizado.")
        return
    objetivos = _areas_con(st, "basestars")
    if not objetivos:
        await bot.send_message(game.cid, "No hay Basestars para atacar.")
        return
    if area_idx is None or area_idx not in objetivos:
        area_idx = objetivos[0]
    st.nuke_usado = True
    area = st.areas[area_idx]
    r = _tirar_ataque(st)
    await bot.send_message(game.cid, f"☢️ *¡ATAQUE NUCLEAR!* Tirada {r} sobre {Space.nombre(area_idx)}.", parse_mode=ParseMode.MARKDOWN)
    if r <= 2:
        await _danar_basestar(bot, game, area_idx, cantidad=2)
    else:
        if area["basestars"]:
            k = max(range(len(area["basestars"])), key=lambda j: area["basestars"][j])
            area["basestars"].pop(k)
            await bot.send_message(game.cid, "🛸💀 ¡Basestar destruida por el ataque nuclear!")
        if r >= 7:
            destr = min(3, area["raiders"])
            area["raiders"] -= destr
            if destr:
                await bot.send_message(game.cid, f"💥 La explosión destruye {destr} Raider(s) en {Space.nombre(area_idx)}.")


async def mover_jugador(bot, game, uid, destino):
    st = game.board.state
    player = game.playerlist[uid]
    if destino not in Locations.UBICACIONES:
        await bot.send_message(game.cid, "Ubicación inválida.")
        return
    player.ubicacion = destino
    await bot.send_message(
        game.cid,
        f"📍 {player.name} se mueve a *{Locations.UBICACIONES[destino]['nombre']}*.",
        parse_mode=ParseMode.MARKDOWN,
    )
    await save(bot, game.cid)


# Iconos de activación Cylon que puede llevar una carta de crisis.
ICONOS_CYLON = {
    "raiders": "Activar Raiders",
    "heavy_raiders": "Activar Heavy Raiders",
    "centuriones": "Activar Centuriones",
    "basestars": "Activar Basestars",
    "launch_raiders": "Lanzar Raiders",
    "launch_heavy": "Lanzar Heavy Raiders",
}


def _iconos_desde_texto(texto):
    """Deriva los iconos de activación Cylon a partir del texto de la crisis
    (las cartas del set indican qué naves se activan/lanzan al pie de la carta)."""
    t = (texto or "").lower()
    iconos = []
    if ("activate heavy raider" in t) or ("activar heavy raider" in t):
        iconos.append("heavy_raiders")
    if ("activate raiders" in t) or ("activar raiders" in t) or ("activa raiders" in t):
        iconos.append("raiders")
    if ("activate basestars" in t) or ("activar basestars" in t):
        iconos.append("basestars")
    if ("activate centurion" in t) or ("activar centurion" in t):
        iconos.append("centuriones")
    if ("launch raiders" in t) or ("lanzar raiders" in t):
        iconos.append("launch_raiders")
    if ("launch" in t and "heavy raider" in t):
        iconos.append("launch_heavy")
    # Quitar duplicados conservando el orden de aparición.
    vistos, salida = set(), []
    for i in iconos:
        if i not in vistos:
            vistos.add(i)
            salida.append(i)
    return salida


# Distribución de iconos de activación que aproxima la del juego base (la mayoría
# de las cartas activan Raiders; algunas Basestars o lanzan refuerzos; pocas
# activan Heavy Raiders o Centuriones). Las cartas físicas llevan estos iconos al
# pie; como no están en los datos, se asignan de forma estable por carta.
_PERFIL_ICONOS = [
    ["raiders"], ["raiders"], ["raiders"], ["raiders"],
    ["basestars"], ["basestars"],
    ["launch_raiders"], ["launch_raiders"],
    ["raiders", "basestars"],
    ["heavy_raiders"],
    ["launch_heavy"],
    ["centuriones"],
]


def _hash_estable(s):
    """Hash determinista (estable entre ejecuciones, a diferencia de hash())."""
    h = 0
    for ch in s or "":
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return h


def _activaciones_para_crisis(crisis):
    """Iconos de activación Cylon de una crisis: si el texto los nombra de forma
    explícita se usan esos; si no, se asigna un perfil estable según la carta."""
    ic = _iconos_desde_texto(crisis.get("texto", ""))
    if ic:
        return ic
    clave = crisis.get("id") or crisis.get("titulo") or crisis.get("texto") or ""
    return list(_PERFIL_ICONOS[_hash_estable(clave) % len(_PERFIL_ICONOS)])


async def _lanzar_raiders_por_basestar(bot, game):
    """Lanzar Raiders: cada Basestar suelta 2 Raiders en su propia área."""
    st = game.board.state
    total = 0
    for a in st.areas:
        for _ in a["basestars"]:
            a["raiders"] += 2
            total += 2
    if total:
        await bot.send_message(game.cid, f"🛸 Las Basestars lanzan {total} Raiders (total: {st.total_raiders()}).")
    else:
        await bot.send_message(game.cid, "🛸 No hay Basestars para lanzar Raiders.")


async def _lanzar_heavy_por_basestar(bot, game):
    """Lanzar Heavy Raiders: cada Basestar suelta 1 Heavy Raider en su área."""
    st = game.board.state
    total = 0
    for i, a in enumerate(st.areas):
        for _ in a["basestars"]:
            a["heavy_raiders"] = a.get("heavy_raiders", 0) + 1
            total += 1
    if total:
        await bot.send_message(game.cid, f"🚁 Las Basestars lanzan {total} Heavy Raider(s) (total: {st.total_heavy_raiders()}).")
    else:
        await bot.send_message(game.cid, "🚁 No hay Basestars para lanzar Heavy Raiders.")


async def activar_naves_cylon(bot, game, iconos):
    """Resuelve la activación Cylon de una crisis según sus iconos. Primero se
    activan las naves existentes (Raiders → Heavy Raiders → Centuriones →
    Basestars) y al final se lanzan refuerzos (Raiders / Heavy Raiders), para que
    las naves recién traídas no actúen en la misma activación."""
    st = game.board.state
    if not iconos:
        return
    desc = ", ".join(ICONOS_CYLON.get(i, i) for i in iconos)
    await bot.send_message(game.cid, f"🤖 *Activación Cylon:* {desc}.", parse_mode=ParseMode.MARKDOWN)

    if "raiders" in iconos:
        await _activar_raiders(bot, game)
        if st.ganador or await _chequear_fin(bot, game):
            return
    if "heavy_raiders" in iconos:
        await _activar_heavy_raiders(bot, game)
        if st.ganador or await _chequear_fin(bot, game):
            return
    if "centuriones" in iconos:
        await _activar_centuriones(bot, game)
        if st.ganador or await _chequear_fin(bot, game):
            return
    if "basestars" in iconos:
        await _activar_basestars(bot, game)
        if st.ganador or await _chequear_fin(bot, game):
            return
    if "launch_raiders" in iconos:
        await _lanzar_raiders_por_basestar(bot, game)
    if "launch_heavy" in iconos:
        await _lanzar_heavy_por_basestar(bot, game)
    await _chequear_fin(bot, game)


async def _activar_raiders(bot, game):
    """Programa de activación de Raiders (reglamento). Si no hay Raiders, cada
    Basestar lanza 2; si no hay nada, no pasa nada."""
    st = game.board.state
    if st.total_raiders() == 0:
        lanzados = 0
        for a in st.areas:
            for _ in a["basestars"]:
                a["raiders"] += 2
                lanzados += 2
        if lanzados:
            await bot.send_message(game.cid, f"🛸 Las Basestars lanzan {lanzados} Raiders.")
        else:
            await bot.send_message(game.cid, "🤖 No hay Raiders ni Basestars: nada que activar.")
        return
    # Activar cada Raider una vez, resolviendo un área a la vez.
    pendientes = [a["raiders"] for a in st.areas]
    for i in range(Space.N_AREAS):
        while pendientes[i] > 0:
            pendientes[i] -= 1
            await _activar_un_raider(bot, game, i)
            if st.ganador:
                return


async def _activar_un_raider(bot, game, i):
    """Programa de un Raider en el área i: atacar Viper → destruir civil →
    moverse hacia la civil más cercana → atacar Galactica."""
    st = game.board.state
    area = st.areas[i]
    if area["raiders"] <= 0:
        return
    # 1. Atacar un Viper tripulado del área (objetivo prioritario: 8 destruido
    #    → piloto a Enfermería; 5-7 dañado → piloto al Hangar).
    pilotos = _pilotos_en_area(game, i)
    if pilotos:
        piloto = random.choice(pilotos)
        r = _d8()
        # Maniobras Evasivas: si están armadas, se repite la tirada con -2
        # (favorece a la defensa) y se consumen.
        if getattr(st, "evasive_armed", False):
            st.evasive_armed = False
            nuevo = max(1, _d8() - 2)
            await bot.send_message(game.cid, f"🌀 Maniobras Evasivas: se repite la tirada ({r} → {nuevo}).")
            r = nuevo
        if r == 8:
            piloto.viper_area = None
            piloto.ubicacion = "sickbay"
            await bot.send_message(game.cid, f"👾 Tirada {r}: ¡el Viper de {piloto.name} es destruido en {Space.nombre(i)}! Va a Enfermería.")
        elif r >= 5:
            piloto.viper_area = None
            piloto.ubicacion = "hangar"
            st.vipers_danados += 1
            await bot.send_message(game.cid, f"👾 Tirada {r}: el Viper de {piloto.name} queda dañado; aterriza en el Hangar.")
        else:
            await bot.send_message(game.cid, f"👾 Tirada {r}: el Raider falla contra el Viper de {piloto.name} en {Space.nombre(i)}.")
        return
    # 2. Atacar un Viper sin tripular en el área (5-7 dañado, 8 destruido)
    if area["vipers"] > 0:
        r = _d8()
        if r == 8:
            area["vipers"] -= 1
            await bot.send_message(game.cid, f"👾 Tirada {r}: ¡Viper destruido en {Space.nombre(i)}!")
        elif r >= 5:
            area["vipers"] -= 1
            st.vipers_danados += 1
            await bot.send_message(game.cid, f"👾 Tirada {r}: Viper dañado en {Space.nombre(i)}.")
        else:
            await bot.send_message(game.cid, f"👾 Tirada {r}: el Raider falla contra el Viper en {Space.nombre(i)}.")
        return
    # 3. Destruir una nave civil en el área (sin tirada)
    if area["civiles"]:
        await _destruir_civil(bot, game, i)
        return
    # 4. Moverse hacia la nave civil más cercana (desempate horario)
    objetivos = _areas_con(st, "civiles")
    if objetivos:
        destino = _paso_hacia(i, objetivos)
        if destino is not None and destino != i:
            area["raiders"] -= 1
            st.areas[destino]["raiders"] += 1   # no se reactiva este turno
            await bot.send_message(game.cid, f"👾 Un Raider avanza de {Space.nombre(i)} a {Space.nombre(destino)}.")
            return
    # 5. Sin naves civiles: atacar Galactica (daña con 8)
    r = _d8()
    if r == 8:
        await _danar_galactica(bot, game, "Raider")
    else:
        await bot.send_message(game.cid, f"👾 Tirada {r}: el Raider no logra dañar Galactica.")


async def _activar_basestars(bot, game):
    """Cada Basestar ataca a Galactica (daña con 4-8)."""
    st = game.board.state
    if st.total_basestars() == 0:
        return
    for a in st.areas:
        for _ in list(a["basestars"]):
            r = _d8()
            if r >= 4:
                await _danar_galactica(bot, game, "Basestar")
                if st.ganador:
                    return
            else:
                await bot.send_message(game.cid, f"🛸 Tirada {r}: la Basestar falla contra Galactica.")


# ---- Heavy Raiders y Partida de Abordaje (centuriones) ----

def _colocar_centurion(st, cantidad=1):
    """Coloca 'cantidad' centuriones en la primera casilla del track de abordaje."""
    for _ in range(cantidad):
        st.boarding_party.append(1)


async def _lanzar_heavy_raider(bot, game, cantidad=1, area_idx=None):
    """Hace aparecer Heavy Raiders en un área (por defecto, la Proa)."""
    st = game.board.state
    if area_idx is None:
        area_idx = Space.AREA_PROA
    st.areas[area_idx]["heavy_raiders"] = st.areas[area_idx].get("heavy_raiders", 0) + cantidad
    await bot.send_message(
        game.cid,
        f"🚁 Aparece(n) {cantidad} Heavy Raider(s) en {Space.nombre(area_idx)} "
        f"(total: {st.total_heavy_raiders()}).",
    )


async def _activar_heavy_raiders(bot, game):
    """Programa de los Heavy Raiders: el que está en un área con tubo de
    lanzamiento accede al hangar, aterriza y desembarca un centurión en el track
    de abordaje (y se retira); el resto avanza un área hacia el tubo más cercano."""
    st = game.board.state
    if st.total_heavy_raiders() == 0:
        return
    # 1. Aterrizajes desde las áreas con acceso al hangar (tubos de lanzamiento)
    for i in Space.LAUNCH_AREAS:
        while st.areas[i].get("heavy_raiders", 0) > 0:
            st.areas[i]["heavy_raiders"] -= 1
            _colocar_centurion(st, 1)
            await bot.send_message(
                game.cid,
                f"🚁 Un Heavy Raider aterriza desde {Space.nombre(i)}: desembarca un "
                f"centurión en Galactica (a bordo: {st.total_centuriones()}).",
            )
            if await _chequear_fin(bot, game):
                return
    # 2. El resto avanza un área hacia el tubo de lanzamiento más cercano
    for i in range(Space.N_AREAS):
        if i in Space.LAUNCH_AREAS:
            continue
        cant = st.areas[i].get("heavy_raiders", 0)
        if cant <= 0:
            continue
        destino = _paso_hacia(i, Space.LAUNCH_AREAS)
        if destino is not None and destino != i:
            st.areas[i]["heavy_raiders"] = 0
            st.areas[destino]["heavy_raiders"] = st.areas[destino].get("heavy_raiders", 0) + cant
            await bot.send_message(
                game.cid,
                f"🚁 {cant} Heavy Raider(s) avanzan de {Space.nombre(i)} a {Space.nombre(destino)}.",
            )


async def _activar_centuriones(bot, game):
    """Programa de la Partida de Abordaje: cada centurión avanza una casilla hacia
    el puente. Al alcanzar la casilla final, los Cylons toman Galactica."""
    st = game.board.state
    if not st.boarding_party:
        return
    st.boarding_party = sorted((p + 1 for p in st.boarding_party), reverse=True)
    cercano = min(st.boarding_party[0], st.boarding_breach)
    await bot.send_message(
        game.cid,
        f"🔺 Los centuriones avanzan por los pasillos de Galactica: {st.total_centuriones()} "
        f"a bordo (el más cercano al puente en la casilla {cercano}/{st.boarding_breach}).",
    )


def _destruir_centurion_avanzado(st):
    """Elimina el centurión más cercano al puente (el de mayor posición). True si lo hizo."""
    if not st.boarding_party:
        return False
    k = max(range(len(st.boarding_party)), key=lambda j: st.boarding_party[j])
    st.boarding_party.pop(k)
    return True


async def _destruir_civil(bot, game, area_idx=None):
    """Destruye una nave civil (de un área concreta o, si no, de un área al azar)."""
    st = game.board.state
    if area_idx is None:
        objetivos = _areas_con(st, "civiles")
        if not objetivos:
            return
        area_idx = random.choice(objetivos)
    area = st.areas[area_idx]
    if not area["civiles"]:
        return
    carga = area["civiles"].pop(random.randrange(len(area["civiles"])))
    if carga["recurso"]:
        await bot.send_message(game.cid, f"🛰️💀 ¡Nave civil destruida en {Space.nombre(area_idx)}! Transportaba {carga['recurso']}.")
        await modificar_recurso(bot, game, carga["recurso"], -carga["cantidad"])
    else:
        await bot.send_message(game.cid, f"🛰️💀 Nave civil destruida en {Space.nombre(area_idx)} (estaba vacía).")


# ===================== SABOTAJE CYLON =====================

# Acciones disponibles para un Cylon revelado, según su ubicación Cylon.
ACCIONES_CYLON = {
    "cylon_fleet": ["launch_raiders", "launch_heavy", "launch_basestar"],
    "caprica": ["play_super_crisis", "sabotage", "board"],
    "resurrection_ship": ["swap_super_crisis", "launch_raiders", "sabotage"],
    "human_fleet": ["sabotage", "board"],
}

ETIQUETA_ACCION_CYLON = {
    "launch_raiders": "👾 Lanzar 2 Raiders",
    "launch_heavy": "🚁 Lanzar un Heavy Raider",
    "launch_basestar": "🛸 Traer una Basestar",
    "sabotage": "🔧💥 Sabotear un recurso (-1)",
    "board": "🔺 Desembarcar un centurión",
    "play_super_crisis": "☠️ Jugar tu Súper Crisis",
    "swap_super_crisis": "♻️ Descartar y robar otra Súper Crisis",
}


async def revelar_cylon(bot, game, uid):
    """Un jugador con carta de Cylon se revela y desata su poder."""
    st = game.board.state
    player = game.playerlist[uid]
    if not player.is_cylon:
        await bot.send_message(uid, "No eres un Cylon. No puedes revelarte.")
        return
    if player.revealed:
        await bot.send_message(uid, "Ya estás revelado.")
        return

    player.revealed = True
    player.en_calabozo = False
    if uid not in st.cylons_revelados:
        st.cylons_revelados.append(uid)
    # Pierde sus títulos humanos
    if uid == st.presidente_uid:
        st.presidente_uid = None
        player.titulos = [t for t in player.titulos if t != "Presidente"]
    if uid == st.almirante_uid:
        st.almirante_uid = None
        player.titulos = [t for t in player.titulos if t != "Almirante"]
    # Si estaba pilotando, abandona el Viper (vuelve a la reserva).
    if getattr(player, "viper_area", None) is not None:
        player.viper_area = None
        st.vipers_reserva += 1
    # Se traslada al lado Cylon
    player.ubicacion = "cylon_fleet"
    player.skill_hand = []

    await bot.send_message(
        game.cid,
        f"🤖 *¡{player.name} se revela como CYLON!* Se traslada a la Flota Cylon.",
        parse_mode=ParseMode.MARKDOWN,
    )

    # Roba una Súper Crisis a su mano (la jugará desde Caprica)
    if st.super_crisis_deck:
        player.super_crisis = st.super_crisis_deck.pop()
        await bot.send_message(game.cid, "☠️ El Cylon roba una *Súper Crisis*…", parse_mode=ParseMode.MARKDOWN)
        await bot.send_message(
            uid,
            f"☠️ *SÚPER CRISIS robada: {player.super_crisis['titulo']}*\n_{player.super_crisis['texto']}_\n\n"
            f"Muévete a *Caprica* y usa `/accion` para *jugarla*. En la *Nave de Resurrección* "
            f"puedes descartarla y robar otra.",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await bot.send_message(game.cid, "☠️ No quedan Súper Crisis en el mazo.")

    await save(bot, game.cid)
    if await _chequear_fin(bot, game):
        return


async def ejecutar_accion_cylon(bot, game, uid, accion):
    """Acción de un Cylon revelado en su turno."""
    st = game.board.state
    player = game.playerlist.get(uid)
    if accion == "play_super_crisis":
        # Caprica: resolver la Súper Crisis que el Cylon tiene en mano.
        if not player or not player.super_crisis:
            await bot.send_message(uid, "No tienes ninguna Súper Crisis en mano.")
            return
        sc = player.super_crisis
        player.super_crisis = None
        st.super_crisis_discard.append(sc)
        await bot.send_message(
            game.cid,
            f"☠️ *SÚPER CRISIS: {sc['titulo']}*\n_{sc['texto']}_",
            parse_mode=ParseMode.MARKDOWN,
        )
        await aplicar_efectos(bot, game, sc.get("efectos", []))
        await save(bot, game.cid)
        await _chequear_fin(bot, game)
        return
    if accion == "swap_super_crisis":
        # Nave de Resurrección: descartar la Súper Crisis actual y robar otra.
        if player and player.super_crisis:
            st.super_crisis_discard.append(player.super_crisis)
            player.super_crisis = None
        if st.super_crisis_deck:
            player.super_crisis = st.super_crisis_deck.pop()
            await bot.send_message(game.cid, "♻️ El Cylon descarta su Súper Crisis y roba otra.")
            await bot.send_message(
                uid,
                f"☠️ *Nueva Súper Crisis: {player.super_crisis['titulo']}*\n_{player.super_crisis['texto']}_",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            await bot.send_message(game.cid, "♻️ El Cylon descarta su Súper Crisis, pero el mazo está vacío.")
        await save(bot, game.cid)
        return
    if accion == "launch_raiders":
        objetivos = _areas_con(st, "basestars")
        area_idx = objetivos[0] if objetivos else Space.AREA_PROA
        st.areas[area_idx]["raiders"] += 2
        await bot.send_message(game.cid, f"👾 El Cylon lanza 2 Raiders en {Space.nombre(area_idx)} (total: {st.total_raiders()}).")
    elif accion == "launch_heavy":
        await _lanzar_heavy_raider(bot, game, 1)
    elif accion == "launch_basestar":
        st.areas[Space.AREA_PROA]["basestars"].append(0)
        await bot.send_message(game.cid, f"🛸 El Cylon trae una Basestar a {Space.nombre(Space.AREA_PROA)} (total: {st.total_basestars()}).")
    elif accion == "sabotage":
        # Sabotea el recurso no nulo más bajo (más dañino)
        recursos = {"comida": st.comida, "combustible": st.combustible,
                    "moral": st.moral, "poblacion": st.poblacion}
        candidatos = {k: v for k, v in recursos.items() if v > 0}
        objetivo = min(candidatos, key=candidatos.get) if candidatos else "moral"
        await modificar_recurso(bot, game, objetivo, -1)
    elif accion == "board":
        _colocar_centurion(st, 1)
        await bot.send_message(game.cid, f"🔺 El Cylon introduce un centurión en Galactica (a bordo: {st.total_centuriones()}).")
    else:
        await bot.send_message(game.cid, "Acción Cylon no disponible.")
    await save(bot, game.cid)


# ===================== HABILIDADES DE PERSONAJE =====================
# Habilidad de "una vez por juego" de cada personaje. Las mecánicas reflejan
# el espíritu de cada habilidad; los textos exactos están en Characters.py
# marcados con VERIFICAR para contrastar con el reglamento.

async def usar_habilidad(bot, game, uid):
    st = game.board.state
    player = game.playerlist.get(uid)
    if not player or not player.personaje:
        return
    if player.habilidad_usada:
        await bot.send_message(uid, "Ya usaste tu habilidad de una vez por juego.")
        return
    if player.revealed:
        await bot.send_message(uid, "Un Cylon revelado no puede usar habilidades humanas.")
        return

    pj = player.personaje
    nombre = Characters.PERSONAJES[pj]["nombre"]
    aplicada = True

    if pj == "baltar":
        cartas = ", ".join(player.loyalty_cards) if player.loyalty_cards else "ninguna"
        await bot.send_message(uid, f"🔎 Tus cartas de lealtad: {cartas}")
        await bot.send_message(game.cid, f"🔎 *{nombre}* analiza información secreta.", parse_mode=ParseMode.MARKDOWN)
    elif pj == "roslin":
        robadas = 0
        for _ in range(2):
            if st.quorum_deck:
                player.quorum_hand.append(st.quorum_deck.pop())
                robadas += 1
        await bot.send_message(game.cid, f"🏛️ *{nombre}* usa su Mandato Ejecutivo y roba {robadas} cartas de Quórum.", parse_mode=ParseMode.MARKDOWN)
    elif pj == "zarek":
        # Tácticas Heterodoxas: pierde 1 población para ganar 1 de otro recurso (el más bajo).
        if st.poblacion <= 1:
            await bot.send_message(uid, "No tienes suficiente población para usar esta habilidad.")
            aplicada = False
        else:
            await modificar_recurso(bot, game, "poblacion", -1)
            otros = {"comida": st.comida, "combustible": st.combustible, "moral": st.moral}
            objetivo = min(otros, key=otros.get)
            await modificar_recurso(bot, game, objetivo, 1)
            await bot.send_message(game.cid, f"🏛️ *{nombre}* usa Tácticas Heterodoxas (−1 población, +1 {objetivo}).", parse_mode=ParseMode.MARKDOWN)
    elif pj == "adama":
        if st.skill_check:
            st.skill_check["bonus"] = st.skill_check.get("bonus", 0) + 3
            await bot.send_message(game.cid, f"🎖️ *{nombre}* usa Cadena de Mando: +3 al chequeo actual.", parse_mode=ParseMode.MARKDOWN)
        else:
            await bot.send_message(uid, "No hay un chequeo abierto para potenciar.")
            aplicada = False
    elif pj == "tigh":
        # Declarar Ley Marcial: entrega el título de Presidente al Almirante.
        alm = st.almirante_uid
        if not alm:
            await bot.send_message(uid, "No hay Almirante al que entregar la Presidencia.")
            aplicada = False
        else:
            ant = game.playerlist.get(st.presidente_uid)
            if ant and "Presidente" in ant.titulos:
                ant.titulos.remove("Presidente")
            st.presidente_uid = alm
            if "Presidente" not in game.playerlist[alm].titulos:
                game.playerlist[alm].titulos.append("Presidente")
            await bot.send_message(game.cid, f"🎖️ *{nombre}* Declara Ley Marcial: la Presidencia pasa al Almirante.", parse_mode=ParseMode.MARKDOWN)
    elif pj == "apollo":
        await _lanzar_viper(bot, game)
        await _activar_un_viper(bot, game)
        await bot.send_message(game.cid, f"✈️ *{nombre}* despega y ataca (habilidad).", parse_mode=ParseMode.MARKDOWN)
    elif pj == "starbuck":
        rep = st.vipers_danados
        st.vipers_reserva += st.vipers_danados
        st.vipers_danados = 0
        _quitar_raider(st)
        await bot.send_message(game.cid, f"✈️ *{nombre}* (Top Gun): repara {rep} Viper(s) y derriba un Raider.", parse_mode=ParseMode.MARKDOWN)
    elif pj == "boomer":
        if _quitar_raider(st):
            await bot.send_message(game.cid, f"✈️ *{nombre}* (Piloto Natural) derriba un Raider.", parse_mode=ParseMode.MARKDOWN)
        else:
            await bot.send_message(uid, "No hay Raiders a los que atacar.")
            aplicada = False
    elif pj == "tyrol":
        rep = st.vipers_danados
        st.vipers_reserva += st.vipers_danados
        st.vipers_danados = 0
        await bot.send_message(game.cid, f"🔧 *{nombre}* (Jefe de Cubierta) repara {rep} Viper(s) dañado(s).", parse_mode=ParseMode.MARKDOWN)
    elif pj == "helo":
        liberados = 0
        for p in game.playerlist.values():
            if p.en_calabozo:
                p.en_calabozo = False
                p.ubicacion = "sickbay"
                liberados += 1
        await bot.send_message(game.cid, f"🩺 *{nombre}* (Brújula Moral) libera a {liberados} preso(s) del calabozo.", parse_mode=ParseMode.MARKDOWN)
    else:
        aplicada = False

    if aplicada:
        player.habilidad_usada = True
        await save(bot, game.cid)
        if await _chequear_fin(bot, game):
            return


# ===================== QUÓRUM =====================

async def robar_quorum(bot, game, uid):
    st = game.board.state
    player = game.playerlist[uid]
    if not st.quorum_deck:
        st.quorum_deck = st.quorum_discard
        st.quorum_discard = []
        random.shuffle(st.quorum_deck)
    if not st.quorum_deck:
        await bot.send_message(game.cid, "No quedan cartas de Quórum.")
        return
    carta = st.quorum_deck.pop()
    player.quorum_hand.append(carta)
    await bot.send_message(game.cid, f"🏛️ El Presidente roba una carta de Quórum.")
    await bot.send_message(uid, f"🏛️ Robaste de Quórum: *{carta['titulo']}* — _{carta['texto']}_", parse_mode=ParseMode.MARKDOWN)


async def jugar_quorum(bot, game, uid, indice):
    st = game.board.state
    player = game.playerlist[uid]
    if uid != st.presidente_uid and uid not in ADMIN:
        await bot.send_message(uid, "Solo el Presidente puede jugar cartas de Quórum.")
        return
    if indice < 1 or indice > len(player.quorum_hand):
        await bot.send_message(uid, "Carta de Quórum inválida.")
        return
    carta = player.quorum_hand.pop(indice - 1)
    await bot.send_message(
        game.cid,
        f"🏛️ *Quórum: {carta['titulo']}*\n_{carta['texto']}_",
        parse_mode=ParseMode.MARKDOWN,
    )

    # Robar cartas de Política para el Presidente (cartas de asignación)
    if carta.get("draw_politics"):
        for _ in range(carta["draw_politics"]):
            await _robar_color(bot, game, player, Skills.POLITICA)

    # Carta con objetivo: esperar selección
    if carta.get("target_efecto"):
        st.quorum_pendiente = carta
        await save(bot, game.cid)
        return  # el resto se resuelve al elegir objetivo

    await aplicar_efectos(bot, game, carta.get("efectos", []))
    if carta.get("keep"):
        await bot.send_message(game.cid, "📌 (Esta carta permanece en juego; su efecto continuo se adjudica según el texto.)")
    else:
        st.quorum_discard.append(carta)
    await save(bot, game.cid)
    await _chequear_fin(bot, game)


async def resolver_quorum_objetivo(bot, game, objetivo_uid):
    """Aplica el efecto de una carta de Quórum dirigida a un objetivo."""
    st = game.board.state
    carta = st.quorum_pendiente
    st.quorum_pendiente = None
    if not carta:
        return
    objetivo = game.playerlist.get(objetivo_uid)
    if not objetivo:
        return
    ef = carta["target_efecto"]
    if ef == "brig":
        objetivo.en_calabozo = True
        objetivo.ubicacion = "brig"
        await bot.send_message(game.cid, f"🚔 *{objetivo.name}* es enviado al Calabozo.", parse_mode=ParseMode.MARKDOWN)
    elif ef == "pardon":
        objetivo.en_calabozo = False
        objetivo.ubicacion = "command"
        await bot.send_message(game.cid, f"🔓 *{objetivo.name}* es indultado y sale del Calabozo.", parse_mode=ParseMode.MARKDOWN)
    elif ef == "mutiny":
        r = _d8()
        if r <= 2:
            await bot.send_message(game.cid, f"🎲 Tirada {r}: el motín fracasa.")
            await modificar_recurso(bot, game, "moral", -1)
        else:
            ant = game.playerlist.get(st.almirante_uid)
            if ant and "Almirante" in ant.titulos:
                ant.titulos.remove("Almirante")
            st.almirante_uid = objetivo.uid
            if "Almirante" not in objetivo.titulos:
                objetivo.titulos.append("Almirante")
            await bot.send_message(game.cid, f"🎲 Tirada {r}: *{objetivo.name}* se vuelve Almirante.", parse_mode=ParseMode.MARKDOWN)
    elif ef == "mugshots":
        cartas = ", ".join(objetivo.loyalty_cards) if objetivo.loyalty_cards else "ninguna"
        await bot.send_message(st.presidente_uid or ADMIN[0],
                               f"🔎 Lealtad de {objetivo.name}: {cartas}")
        await bot.send_message(game.cid, f"🔎 El Presidente revisa la ficha de *{objetivo.name}*.", parse_mode=ParseMode.MARKDOWN)
        r = _d8()
        if r <= 3:
            await bot.send_message(game.cid, f"🎲 Tirada {r}: -1 Moral.")
            await modificar_recurso(bot, game, "moral", -1)
    elif ef == "specialist":
        st.especialista_uid = objetivo.uid
        await bot.send_message(game.cid, f"🧭 *{objetivo.name}* es nombrado Especialista de Misión: elegirá el destino del próximo salto.", parse_mode=ParseMode.MARKDOWN)
    elif ef == "arbitrator":
        st.arbitro_uid = objetivo.uid
        await bot.send_message(game.cid, f"⚖️ *{objetivo.name}* es nombrado Árbitro: podrá ajustar ±3 los chequeos del Camarote del Almirante.", parse_mode=ParseMode.MARKDOWN)
    elif ef == "vicepresident":
        st.vicepresidente_uid = objetivo.uid
        await bot.send_message(game.cid, f"🎖️ *{objetivo.name}* es nombrado Vicepresidente: solo el VP podrá acceder a la Presidencia vía Administración.", parse_mode=ParseMode.MARKDOWN)

    st.quorum_discard.append(carta)
    await save(bot, game.cid)
    await _chequear_fin(bot, game)


# ===================== CRISIS =====================

async def _baltar_intuicion(bot, game):
    """Pasiva de Baltar: tras robar una Crisis roba 1 carta de habilidad
    del tipo que elija (incluso fuera de su set)."""
    st = game.board.state
    ap = st.active_player
    if not ap or getattr(ap, "personaje", None) != "baltar" or ap.revealed:
        return
    if st.play_pending:   # no pisar otro robo de cartas en curso
        return
    st.play_pending = {"tipo": "draw", "uid": ap.uid, "restantes": 1, "label": "Intuición Delirante"}
    btns = [[InlineKeyboardButton(f"{Skills.EMOJI_COLOR[c]} {c}",
                                  callback_data=f"{game.cid}*bsgJugar*cp_{c}*{ap.uid}")]
            for c in Skills.COLORES]
    await bot.send_message(ap.uid, "🔮 *Intuición Delirante* — elige el tipo de carta a robar:",
                           reply_markup=InlineKeyboardMarkup(btns), parse_mode=ParseMode.MARKDOWN)


async def robar_crisis(bot, game):
    st = game.board.state
    if not st.crisis_deck:
        st.crisis_deck = st.crisis_discard
        st.crisis_discard = []
        random.shuffle(st.crisis_deck)
    if not st.crisis_deck:
        await bot.send_message(game.cid, "No quedan cartas de crisis.")
        return

    ap = st.active_player
    # Roslin 'Visiones Religiosas': roba 2 Crisis, elige 1 y la otra va al fondo.
    if (ap and getattr(ap, "personaje", None) == "roslin" and not ap.revealed
            and len(st.crisis_deck) >= 2):
        c0 = st.crisis_deck.pop()
        c1 = st.crisis_deck.pop()
        st.roslin_choice = [c0, c1]
        btns = [
            [InlineKeyboardButton(f"① {c0['titulo']}", callback_data=f"{game.cid}*bsgCrisisSel*0*{ap.uid}")],
            [InlineKeyboardButton(f"② {c1['titulo']}", callback_data=f"{game.cid}*bsgCrisisSel*1*{ap.uid}")],
        ]
        await bot.send_message(
            ap.uid,
            "🔮 *Visiones Religiosas* — robaste 2 Crisis; elige cuál resolver (la otra al fondo):\n\n"
            f"① *{c0['titulo']}*\n_{c0['texto'][:140]}_\n\n"
            f"② *{c1['titulo']}*\n_{c1['texto'][:140]}_",
            reply_markup=InlineKeyboardMarkup(btns), parse_mode=ParseMode.MARKDOWN,
        )
        await bot.send_message(game.cid, "🔮 La Presidenta consulta sus visiones (elige la Crisis en privado)…", parse_mode=ParseMode.MARKDOWN)
        await save(bot, game.cid)
        return

    crisis = st.crisis_deck.pop()
    await _presentar_crisis(bot, game, crisis)


async def resolver_roslin(bot, game, uid, idx):
    """Resuelve la elección de Visiones Religiosas de Roslin."""
    st = game.board.state
    pares = st.roslin_choice
    if not pares or idx not in (0, 1):
        return
    if not st.active_player or st.active_player.uid != uid:
        return
    elegida = pares[idx]
    otra = pares[1 - idx]
    st.crisis_deck.insert(0, otra)   # la descartada va al fondo del mazo
    st.roslin_choice = None
    await _presentar_crisis(bot, game, elegida)


async def _presentar_crisis(bot, game, crisis):
    """Anuncia la Crisis elegida, dispara la pasiva de Baltar y la despacha."""
    st = game.board.state
    st.crisis_actual = crisis

    await bot.send_message(
        game.cid,
        f"⚠️ *CRISIS: {crisis['titulo']}*\n_{crisis['texto']}_",
        parse_mode=ParseMode.MARKDOWN,
    )

    # Baltar 'Intuición Delirante': tras robar una Crisis, roba 1 carta de habilidad a elección.
    await _baltar_intuicion(bot, game)

    if crisis["tipo"] == "chequeo":
        if crisis.get("alternativa"):
            await abrir_decision_crisis(bot, game, crisis)
        else:
            await abrir_chequeo(bot, game, crisis)
    elif crisis["tipo"] == "eleccion":
        await abrir_eleccion(bot, game, crisis)
    elif crisis["tipo"] == "voto":
        await abrir_voto(bot, game, crisis)
    else:
        await aplicar_efectos(bot, game, crisis.get("efectos", []))
        await cerrar_crisis(bot, game, crisis)


def _decisor_uid(game, decisor):
    st = game.board.state
    if decisor == "presidente" and st.presidente_uid:
        return st.presidente_uid
    if decisor == "almirante" and st.almirante_uid:
        return st.almirante_uid
    return st.active_player.uid


# ---- Crisis con opción "OR": el decisor elige chequeo o alternativa ----

async def abrir_decision_crisis(bot, game, crisis):
    st = game.board.state
    st.skill_check = None
    duid = _decisor_uid(game, crisis.get("decisor", "activo"))
    decisor = game.playerlist[duid]
    colores = " ".join(Skills.EMOJI_COLOR[c] for c in crisis["colores"])
    btns = [
        [InlineKeyboardButton(f"🎲 Intentar chequeo (dif. {crisis['dificultad']}) {colores}",
                              callback_data=f"{game.cid}*bsgCrisisOpt*check*{duid}")],
        [InlineKeyboardButton(crisis["alternativa"]["label"],
                              callback_data=f"{game.cid}*bsgCrisisOpt*alt*{duid}")],
    ]
    await bot.send_message(
        game.cid,
        f"🤔 {player_call(decisor)} elige: arriesgar el *chequeo* o tomar la *alternativa*.",
        reply_markup=InlineKeyboardMarkup(btns),
        parse_mode=ParseMode.MARKDOWN,
    )
    await save(bot, game.cid)


async def resolver_decision_crisis(bot, game, opcion):
    st = game.board.state
    crisis = st.crisis_actual
    if not crisis:
        return
    if opcion == "check":
        await abrir_chequeo(bot, game, crisis)
    else:
        alt = crisis.get("alternativa", {})
        await bot.send_message(game.cid, f"🛡️ Se toma la alternativa: *{alt.get('label','')}*", parse_mode=ParseMode.MARKDOWN)
        await aplicar_efectos(bot, game, alt.get("efectos", []))
        await cerrar_crisis(bot, game, crisis)


# ---- Crisis de decisión ----

async def abrir_eleccion(bot, game, crisis):
    st = game.board.state
    duid = _decisor_uid(game, crisis.get("decisor", "activo"))
    decisor = game.playerlist[duid]
    st.skill_check = None
    btns = [[InlineKeyboardButton(op["label"], callback_data=f"{game.cid}*bsgEleccion*{i}*{decisor.uid}")]
            for i, op in enumerate(crisis["opciones"])]
    await bot.send_message(
        game.cid,
        f"🤔 *Decisión* — {player_call(decisor)} debe elegir:",
        reply_markup=InlineKeyboardMarkup(btns),
        parse_mode=ParseMode.MARKDOWN,
    )
    await save(bot, game.cid)


async def resolver_eleccion(bot, game, indice):
    st = game.board.state
    crisis = st.crisis_actual
    if not crisis or indice < 0 or indice >= len(crisis["opciones"]):
        return
    opcion = crisis["opciones"][indice]
    await bot.send_message(game.cid, f"➡️ Se elige: *{opcion['label']}*", parse_mode=ParseMode.MARKDOWN)
    await aplicar_efectos(bot, game, opcion.get("efectos", []))
    await cerrar_crisis(bot, game, crisis)


# ---- Crisis de voto ----

async def abrir_voto(bot, game, crisis):
    st = game.board.state
    st.crisis_vote = {"votos": {}, "n_opciones": len(crisis["opciones"])}
    btns = [[InlineKeyboardButton(op["label"], callback_data=f"{game.cid}*bsgCrisisVoto*{i}*0")]
            for i, op in enumerate(crisis["opciones"])]
    await bot.send_message(
        game.cid,
        "🗳️ *Votación de crisis* — todos los jugadores (no presos ni Cylons revelados) votan. "
        "Gana la mayoría:",
        reply_markup=InlineKeyboardMarkup(btns),
        parse_mode=ParseMode.MARKDOWN,
    )
    await save(bot, game.cid)


def _votantes_validos(game):
    return [p for p in game.playerlist.values() if not p.en_calabozo and not p.revealed]


async def registrar_voto_crisis(bot, game, uid, indice):
    st = game.board.state
    vote = st.crisis_vote
    if not vote:
        return
    player = game.playerlist.get(uid)
    if not player or player.en_calabozo or player.revealed:
        return
    vote["votos"][uid] = indice
    if len(vote["votos"]) >= len(_votantes_validos(game)):
        await resolver_voto_crisis(bot, game)
    else:
        await save(bot, game.cid)


async def resolver_voto_crisis(bot, game):
    st = game.board.state
    crisis = st.crisis_actual
    vote = st.crisis_vote
    st.crisis_vote = None
    if not crisis or not vote:
        return
    conteo = {}
    for idx in vote["votos"].values():
        conteo[idx] = conteo.get(idx, 0) + 1
    if not conteo:
        ganadora = 0
    else:
        maxv = max(conteo.values())
        empatadas = [i for i, c in conteo.items() if c == maxv]
        # Desempate: el Presidente decide; si no, la primera opción.
        ganadora = empatadas[0]
        if len(empatadas) > 1 and st.presidente_uid in vote["votos"]:
            pres_voto = vote["votos"][st.presidente_uid]
            if pres_voto in empatadas:
                ganadora = pres_voto
    opcion = crisis["opciones"][ganadora]
    await bot.send_message(game.cid, f"🗳️ Gana la opción: *{opcion['label']}*", parse_mode=ParseMode.MARKDOWN)
    await aplicar_efectos(bot, game, opcion.get("efectos", []))
    await cerrar_crisis(bot, game, crisis)


async def abrir_chequeo(bot, game, crisis):
    st = game.board.state
    colores = crisis["colores"]
    emojis = " ".join(Skills.EMOJI_COLOR[c] for c in colores)
    st.skill_check = {
        "crisis_id": crisis.get("id", crisis.get("titulo")),
        "colores": colores,
        "dificultad": crisis["dificultad"],
        "aportes": {},   # uid -> lista de cartas
    }
    await bot.send_message(
        game.cid,
        f"🎲 *Chequeo de habilidad* — dificultad *{crisis['dificultad']}*.\n"
        f"Colores positivos: {emojis} ({', '.join(colores)}).\n\n"
        f"Cada jugador puede aportar cartas en privado con `/aportar N` (número de carta de su mano). "
        f"Cuando todos hayan aportado, el Almirante o el jugador activo usa `/resolver`.",
        parse_mode=ParseMode.MARKDOWN,
    )
    await save(bot, game.cid)


# ===================== CARTAS DE HABILIDAD (ACCIÓN) =====================
# Cartas de ACCIÓN: se juegan por su efecto como acción del turno.
CARTAS_ACCION = {"Consolidate Power", "Repair", "Maximum Firepower",
                 "Launch Scout", "Executive Order"}

# Cartas REACTIVAS que se ARMAN en tu turno y se consumen en el siguiente
# disparo/ataque relevante.
CARTAS_ARMABLES = {"Strategic Planning", "Evasive Maneuvers"}

# Conjunto completo de cartas que el comando /jugar puede activar.
CARTAS_JUGABLES = CARTAS_ACCION | CARTAS_ARMABLES

# Cuándo se usan las cartas que no se juegan con /jugar (mensaje informativo).
CUANDO_SE_JUEGAN = {
    "Declare Emergency": "se aporta a un chequeo (reduce su dificultad en 2).",
    "Scientific Research": "se aporta a un chequeo (Ingeniería cuenta en positivo).",
}


async def carta_repair(bot, game, player):
    """Reparación: en Hangar/pilotando arregla hasta 2 Vipers; si no, repara una
    ubicación averiada de Galactica. Devuelve True si tuvo efecto."""
    st = game.board.state
    if player.ubicacion == "hangar" or getattr(player, "viper_area", None) is not None:
        rep = min(2, st.vipers_danados)
        if rep:
            st.vipers_danados -= rep
            st.vipers_reserva += rep
            await bot.send_message(game.cid, f"🔧 {player.name} usa *Reparación*: arregla {rep} Viper(s) dañado(s).", parse_mode=ParseMode.MARKDOWN)
            return True
    loc = player.ubicacion
    if loc in st.galactica_damage:
        await _reparar_galactica(bot, game, player, loc)
        return True
    if st.galactica_damage:
        await _reparar_galactica(bot, game, player)
        return True
    await bot.send_message(player.uid, "🔧 No hay nada que reparar (ni Vipers dañados ni sistemas averiados).")
    return False


async def carta_max_firepower(bot, game, player):
    """Potencia de Fuego Máxima: pilotando, ataca hasta 4 veces en tu área."""
    st = game.board.state
    if getattr(player, "viper_area", None) is None:
        await bot.send_message(player.uid, "Debes estar pilotando un Viper para usar Potencia de Fuego Máxima.")
        return False
    await bot.send_message(game.cid, f"🔫 {player.name} desata *Potencia de Fuego Máxima* (hasta 4 ataques).", parse_mode=ParseMode.MARKDOWN)
    for _ in range(4):
        i = player.viper_area
        a = st.areas[i]
        if a["raiders"] <= 0 and a.get("heavy_raiders", 0) <= 0 and not a["basestars"]:
            break
        await _pilot_atacar(bot, game, player)
        if st.ganador:
            break
    return True


async def carta_draw_color(bot, game, uid, color):
    """Robo de cartas con elección de color (Consolidación de Poder e
    Intuición Delirante de Baltar). Roba 1 carta del color elegido por paso."""
    st = game.board.state
    pp = st.play_pending
    if not pp or pp.get("tipo") != "draw" or pp.get("uid") != uid:
        return
    player = game.playerlist[uid]
    etiqueta = pp.get("label", "Robo de habilidad")
    carta = _robar_carta_color(st, color)
    if carta:
        player.skill_hand.append(carta)
        await bot.send_message(
            uid,
            f"➕ *{etiqueta}*: robaste {Skills.EMOJI_COLOR[carta['color']]} {color} {carta['valor']}.",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await bot.send_message(uid, f"(No quedan cartas de {color}.)")
    pp["restantes"] -= 1
    if pp["restantes"] <= 0:
        st.play_pending = None
        await _dm_mano(bot, player)
    await save(bot, game.cid)


async def carta_strategic_planning(bot, game, player):
    """Planificación Estratégica: arma +2 a tu próxima tirada de ataque."""
    st = game.board.state
    if st.dado_bonus:
        await bot.send_message(player.uid, "Ya tienes una Planificación Estratégica armada.")
        return False
    st.dado_bonus = 2
    await bot.send_message(game.cid, f"📐 {player.name} arma *Planificación Estratégica*: +2 a la próxima tirada de ataque humana.", parse_mode=ParseMode.MARKDOWN)
    return True


async def carta_evasive(bot, game, player):
    """Maniobras Evasivas: arma una repetición (-2) del próximo ataque a un Viper tripulado."""
    st = game.board.state
    if st.evasive_armed:
        await bot.send_message(player.uid, "Ya tienes Maniobras Evasivas armadas.")
        return False
    st.evasive_armed = True
    await bot.send_message(game.cid, f"🌀 {player.name} arma *Maniobras Evasivas*: el próximo ataque a un Viper tripulado se repetirá con −2.", parse_mode=ParseMode.MARKDOWN)
    return True


async def carta_executive_order(bot, game, uid, objetivo_uid):
    """Orden Ejecutiva: concede a otro jugador una acción extra durante este turno."""
    st = game.board.state
    objetivo = game.playerlist.get(objetivo_uid)
    if not objetivo or objetivo_uid == uid:
        await bot.send_message(uid, "Debes elegir a OTRO jugador.")
        return False
    if objetivo.revealed or objetivo.en_calabozo:
        await bot.send_message(uid, "No puedes dar la orden a un Cylon revelado ni a un preso.")
        return False
    st.bonus_actor = objetivo_uid
    await bot.send_message(game.cid, f"📋 {game.playerlist[uid].name} da una *Orden Ejecutiva*: {objetivo.name} recibe una acción extra este turno (`/accion` o `/mover`).", parse_mode=ParseMode.MARKDOWN)
    await bot.send_message(objetivo_uid, "📋 Recibiste una *Orden Ejecutiva*: puedes usar `/accion` o `/mover` durante este turno.", parse_mode=ParseMode.MARKDOWN)
    return True


async def carta_scout_resolve(bot, game, uid, mantener):
    """Explorar: mantiene la próxima Crisis arriba o la manda al fondo del mazo."""
    st = game.board.state
    pp = st.play_pending
    if not pp or pp.get("tipo") != "scout" or pp.get("uid") != uid:
        return
    st.play_pending = None
    if st.crisis_deck and not mantener:
        c = st.crisis_deck.pop()         # cima
        st.crisis_deck.insert(0, c)      # al fondo
        await bot.send_message(game.cid, "🔭 *Lanzar Sonda*: la próxima Crisis se envía al fondo del mazo.", parse_mode=ParseMode.MARKDOWN)
    else:
        await bot.send_message(game.cid, "🔭 *Lanzar Sonda*: la próxima Crisis se mantiene arriba.", parse_mode=ParseMode.MARKDOWN)
    await save(bot, game.cid)


async def aportar_carta(bot, game, uid, indice):
    st = game.board.state
    if not st.skill_check:
        await bot.send_message(uid, "No hay ningún chequeo de habilidad abierto.")
        return
    player = game.playerlist.get(uid)
    if not player or indice < 1 or indice > len(player.skill_hand):
        await bot.send_message(uid, "Número de carta inválido.")
        return
    carta = player.skill_hand.pop(indice - 1)
    st.skill_check["aportes"].setdefault(uid, []).append(carta)
    await bot.send_message(
        uid,
        f"Aportaste {Skills.EMOJI_COLOR[carta['color']]} {carta['color']} {carta['valor']} "
        f"(boca abajo).",
        parse_mode=ParseMode.MARKDOWN,
    )
    await _dm_mano(bot, player)
    await save(bot, game.cid)


async def resolver_chequeo(bot, game):
    st = game.board.state
    sc = st.skill_check
    if not sc:
        await bot.send_message(game.cid, "No hay chequeo abierto.")
        return

    colores = sc["colores"]
    total = 0
    detalle = []
    # Aportes de jugadores
    todas = []
    for uid, cartas in sc["aportes"].items():
        for c in cartas:
            todas.append(c)
    # Habilidades de cartas jugadas en el chequeo (solo aportes de jugadores)
    nombres = [c.get("nombre") for c in todas]
    scientific = "Scientific Research" in nombres   # Ingeniería cuenta en positivo
    declare_emergency = nombres.count("Declare Emergency")
    # Adama 'Líder Inspirador': las cartas de fuerza 1 cuentan en positivo.
    adama_activo = any(getattr(p, "personaje", None) == "adama" and not p.revealed
                       for p in game.playerlist.values())
    # 2 cartas de destino
    destino = _robar_destino(st, 2)
    for c in destino:
        todas.append(c)

    random.shuffle(todas)  # ocultar quién aportó qué
    for c in todas:
        if scientific and c["color"] == Skills.INGENIERIA:
            signo = 1
        elif adama_activo and c["valor"] == 1:
            signo = 1
        else:
            signo = Skills.signo_para_check(c["color"], colores)
        total += signo * c["valor"]
        detalle.append(f"{Skills.EMOJI_COLOR[c['color']]}{'+' if signo>0 else '-'}{c['valor']}")
        st.skill_discards.setdefault(c["color"], []).append(c)

    # Bono de habilidades (p. ej. Cadena de Mando de Adama)
    bonus = sc.get("bonus", 0)
    if bonus:
        total += bonus
        detalle.append(f"⭐{'+' if bonus>0 else ''}{bonus}")

    # Dificultad efectiva (Declare Emergency reduce 2, máx 1 por chequeo)
    dificultad = sc["dificultad"]
    notas = []
    if declare_emergency:
        dificultad -= 2
        notas.append("Declare Emergency −2 dif.")
    if scientific:
        notas.append("Scientific Research: Ingeniería positiva")
    if adama_activo:
        notas.append("Adama: fuerza 1 positiva")

    exito = total >= dificultad
    extra = (" (" + "; ".join(notas) + ")") if notas else ""
    await bot.send_message(
        game.cid,
        f"🎲 Resultado del chequeo: *{total}* vs dificultad *{dificultad}*{extra} → "
        f"{'✅ ÉXITO' if exito else '❌ FRACASO'}\n"
        f"Cartas: {' '.join(detalle) if detalle else '(ninguna)'}",
        parse_mode=ParseMode.MARKDOWN,
    )

    # Chequeo asociado a una acción de ubicación (no es una crisis)
    if sc.get("ubicacion_accion"):
        await _resolver_chequeo_ubicacion(bot, game, sc, total, exito)
        return

    crisis = st.crisis_actual
    st.skill_check = None
    efectos = crisis["exito"] if exito else crisis["fracaso"]
    await aplicar_efectos(bot, game, efectos)
    await cerrar_crisis(bot, game, crisis)


def _robar_destino(st, n):
    cartas = []
    for _ in range(n):
        if not st.destiny_deck:
            # Reconstruir destino con 2 de cada color de los descartes/mazos
            for color in Skills.COLORES:
                for _ in range(2):
                    c = _robar_carta_color(st, color)
                    if c:
                        st.destiny_deck.append(c)
            random.shuffle(st.destiny_deck)
        if st.destiny_deck:
            cartas.append(st.destiny_deck.pop())
    return cartas


async def cerrar_crisis(bot, game, crisis):
    st = game.board.state
    st.crisis_discard.append(crisis)
    st.crisis_actual = None

    # Activación de naves Cylon según los iconos de la crisis. Las cartas nuevas
    # pueden traer la lista explícita en "activaciones"; las heredadas marcan
    # "activar_cylons" y derivamos los iconos del texto de la carta.
    iconos = crisis.get("activaciones")
    if iconos is None and crisis.get("activar_cylons"):
        iconos = _activaciones_para_crisis(crisis)
    if iconos:
        await activar_naves_cylon(bot, game, iconos)
        if await _chequear_fin(bot, game):
            return

    # Avance de preparación de salto por iconos de la crisis
    jump_icons = crisis.get("jump", 0)
    if jump_icons:
        st.jump_prep = min(st.jump_prep_max, st.jump_prep + jump_icons)
        await bot.send_message(
            game.cid,
            f"⏫ Preparación de salto: {st.jump_prep}/{st.jump_prep_max}",
            parse_mode=ParseMode.MARKDOWN,
        )

    # Autojump si el track está lleno
    if st.jump_prep >= st.jump_prep_max:
        await ejecutar_salto(bot, game, auto=True)

    if await _chequear_fin(bot, game):
        return

    # Boomer 'Reconocimiento': al final de su turno mira la próxima Crisis.
    await _boomer_reconocimiento(bot, game)

    await bot.send_message(game.cid, game.board.print_board(game), parse_mode=ParseMode.MARKDOWN)
    await avanzar_turno(bot, game)


async def _boomer_reconocimiento(bot, game):
    """Pasiva de Boomer: al final de su turno mira la carta superior del mazo de
    Crisis y decide dejarla arriba o enviarla al fondo (reusa el flujo de Sonda)."""
    st = game.board.state
    ap = st.active_player
    if not ap or getattr(ap, "personaje", None) != "boomer" or ap.revealed:
        return
    if not st.crisis_deck or st.play_pending:
        return
    st.play_pending = {"tipo": "scout", "uid": ap.uid}
    top = st.crisis_deck[-1]
    btns = [[InlineKeyboardButton("⬆️ Mantener arriba", callback_data=f"{game.cid}*bsgJugar*ls_keep*{ap.uid}"),
             InlineKeyboardButton("⬇️ Enviar al fondo", callback_data=f"{game.cid}*bsgJugar*ls_bottom*{ap.uid}")]]
    await bot.send_message(
        ap.uid,
        f"🔭 *Reconocimiento* — próxima Crisis: *{top['titulo']}*\n_{top['texto'][:160]}_\n¿Mantenerla arriba o enviarla al fondo?",
        reply_markup=InlineKeyboardMarkup(btns), parse_mode=ParseMode.MARKDOWN,
    )


# ===================== EFECTOS / RECURSOS =====================

async def aplicar_efectos(bot, game, efectos):
    st = game.board.state
    for ef in efectos or []:
        tipo = ef.get("tipo")
        if tipo == "recurso":
            await modificar_recurso(bot, game, ef["recurso"], ef["delta"])
        elif tipo == "raiders":
            cant = ef["cantidad"]
            if cant >= 0:
                objetivos = _areas_con(st, "basestars")
                area_idx = objetivos[0] if objetivos else Space.AREA_PROA
                st.areas[area_idx]["raiders"] += cant
                await bot.send_message(game.cid, f"👾 Aparecen {cant} Raiders en {Space.nombre(area_idx)} (total: {st.total_raiders()}).")
            else:
                for _ in range(-cant):
                    if not _quitar_raider(st):
                        break
                await bot.send_message(game.cid, f"🔫 Se eliminan Raiders (total: {st.total_raiders()}).")
        elif tipo == "vipers":
            st.vipers_reserva += ef["cantidad"]
            await bot.send_message(game.cid, f"✈️ Llegan {ef['cantidad']} Vipers a la reserva (total reserva: {st.vipers_reserva}).")
        elif tipo == "basestar":
            for _ in range(ef["cantidad"]):
                st.areas[Space.AREA_PROA]["basestars"].append(0)
            await bot.send_message(game.cid, f"🛸 Aparece(n) {ef['cantidad']} Basestar(s) en {Space.nombre(Space.AREA_PROA)} (total: {st.total_basestars()}).")
        elif tipo == "centuriones":
            delta = ef["delta"]
            if delta >= 0:
                _colocar_centurion(st, delta)
                await bot.send_message(game.cid, f"🔺 Se colocan {delta} centurión/es en el track de abordaje (a bordo: {st.total_centuriones()}).")
            else:
                for _ in range(-delta):
                    if not _destruir_centurion_avanzado(st):
                        break
                await bot.send_message(game.cid, f"🔺 Se eliminan centuriones (a bordo: {st.total_centuriones()}).")
        elif tipo == "heavy_raiders":
            cant = ef["cantidad"]
            if cant >= 0:
                await _lanzar_heavy_raider(bot, game, cant)
            else:
                restantes = -cant
                for a in st.areas:
                    while restantes > 0 and a.get("heavy_raiders", 0) > 0:
                        a["heavy_raiders"] -= 1
                        restantes -= 1
                await bot.send_message(game.cid, f"🚁 Se destruyen Heavy Raiders (total: {st.total_heavy_raiders()}).")
        elif tipo == "jump_prep":
            st.jump_prep = max(0, min(st.jump_prep_max, st.jump_prep + ef["delta"]))
            await bot.send_message(game.cid, f"⏫ Preparación de salto: {st.jump_prep}/{st.jump_prep_max}")
        elif tipo == "activar":
            await activar_naves_cylon(bot, game, ef.get("iconos", []))
        elif tipo == "destruir_civil":
            await _destruir_civil(bot, game)
        elif tipo == "roll":
            r = _d8()
            lo, hi = ef.get("rango", [6, 8])
            ok = lo <= r <= hi
            await bot.send_message(game.cid, f"🎲 Tirada: *{r}* ({'éxito' if ok else 'fallo'} en {lo}-{hi})", parse_mode=ParseMode.MARKDOWN)
            await aplicar_efectos(bot, game, ef["exito"] if ok else ef.get("fracaso", []))
        elif tipo == "mensaje":
            await bot.send_message(game.cid, ef["texto"])
        elif tipo == "prophecy":
            st.profecia_pendiente += 1
            await bot.send_message(
                game.cid,
                "🔮 *Profecía aceptada*: el próximo chequeo de Administración para nombrar "
                "Presidente tendrá +2 de dificultad.",
                parse_mode=ParseMode.MARKDOWN,
            )


async def modificar_recurso(bot, game, recurso, delta):
    st = game.board.state
    actual = getattr(st, recurso)
    nuevo = max(0, actual + delta)
    setattr(st, recurso, nuevo)
    emoji = {"comida": "🍞", "combustible": "⛽", "moral": "🙂", "poblacion": "👥"}.get(recurso, "")
    signo = "+" if delta >= 0 else ""
    await bot.send_message(
        game.cid,
        f"{emoji} {recurso.capitalize()}: {actual} → {nuevo} ({signo}{delta})",
    )


# ===================== SALTO / SLEEPER =====================

async def ejecutar_salto(bot, game, auto=False):
    st = game.board.state
    st.jump_prep = 0
    # La carta de destino del salto avanza 1 o 2 unidades de distancia.
    avance = random.choice([1, 1, 2])
    # Poder presidencial "Especialista de Misión": elige el destino (mejor avance)
    # en este salto y luego cesa en el cargo.
    esp = game.playerlist.get(st.especialista_uid)
    if esp:
        avance = 2
        st.especialista_uid = None
        await bot.send_message(
            game.cid,
            f"🧭 *{esp.name}* (Especialista de Misión) guía el salto y elige el mejor destino.",
            parse_mode=ParseMode.MARKDOWN,
        )
    st.distancia = min(st.objetivo_distancia, st.distancia + avance)

    # Tras el salto: las naves Cylon no siguen a la flota; los Vipers regresan a
    # la reserva. Las naves civiles viajan con la flota (permanecen en sus áreas).
    for a in st.areas:
        st.vipers_reserva += a["vipers"]
        a["vipers"] = 0
        a["raiders"] = 0
        a["heavy_raiders"] = 0
        a["basestars"] = []
    st.vipers_reserva += st.vipers_danados
    st.vipers_danados = 0
    # Los Vipers tripulados regresan al Hangar con la flota.
    for p in game.playerlist.values():
        if getattr(p, "viper_area", None) is not None:
            p.viper_area = None
            p.ubicacion = "hangar"
            st.vipers_reserva += 1

    etiqueta = "AUTOMÁTICO" if auto else "FTL"
    await bot.send_message(
        game.cid,
        f"🌌 *¡SALTO {etiqueta}!* La flota avanza y deja atrás a los Cylons. "
        f"Distancia: *{st.distancia}/{st.objetivo_distancia}*.",
        parse_mode=ParseMode.MARKDOWN,
    )
    # Fase del Agente Durmiente
    if not st.sleeper_hecho and st.distancia >= Loyalty.DISTANCIA_SLEEPER:
        await fase_durmiente(bot, game)


async def fase_durmiente(bot, game):
    st = game.board.state
    st.sleeper_hecho = True
    await bot.send_message(
        game.cid,
        "😴 *Fase del Agente Durmiente* — se reparte una nueva carta de lealtad a cada jugador.",
        parse_mode=ParseMode.MARKDOWN,
    )
    for uid, player in game.playerlist.items():
        pj = Characters.PERSONAJES.get(player.personaje, {})
        # Boomer recibe 2 cartas en la fase durmiente y va al Calabozo
        cantidad = 1 + pj.get("sleeper_extra", 0)
        for _ in range(cantidad):
            if st.loyalty_deck:
                carta = st.loyalty_deck.pop()
                player.loyalty_cards.append(carta)
                if carta == Loyalty.CYLON and not player.is_cylon:
                    player.is_cylon = True
        if pj.get("sleeper_to_brig") and not player.revealed:
            player.en_calabozo = True
            player.ubicacion = "brig"
            await bot.send_message(game.cid, f"🚔 {player.name} es trasladado al Calabozo (Agente Durmiente).")
        await _dm_lealtad(bot, player)


# ===================== FIN DE PARTIDA =====================

async def _chequear_fin(bot, game):
    st = game.board.state
    # Derrota: algún recurso en 0
    for recurso, nombre in [("comida", "Comida"), ("combustible", "Combustible"),
                            ("moral", "Moral"), ("poblacion", "Población")]:
        if getattr(st, recurso) <= 0:
            await terminar(bot, game, "Cylons", f"El recurso *{nombre}* llegó a 0.")
            return True
    # Derrota: los centuriones llegan al puente (casilla final del track)
    if any(p >= st.boarding_breach for p in st.boarding_party):
        await terminar(bot, game, "Cylons", "Los centuriones llegaron al puente: Galactica fue abordada.")
        return True
    # Derrota: Galactica destruida (6 ubicaciones averiadas)
    if st.total_danos_galactica() >= st.galactica_danos_max:
        await terminar(bot, game, "Cylons", "Todos los sistemas de Galactica fueron destruidos.")
        return True
    # Victoria humana
    if st.distancia >= st.objetivo_distancia:
        await terminar(bot, game, "Humanos", "La flota alcanzó la distancia objetivo. ¡Llegaron a Kobol!")
        return True
    return False


async def terminar(bot, game, ganador, razon):
    st = game.board.state
    st.ganador = ganador
    st.razon_fin = razon
    st.fase_actual = "Finalizado"
    await save(bot, game.cid)

    # Revelar Cylons
    cylons = [p.name for p in game.playerlist.values() if p.is_cylon]
    cylon_txt = ", ".join(cylons) if cylons else "ninguno"
    emoji = "🧑‍🚀" if ganador == "Humanos" else "🤖"
    await bot.send_message(
        game.cid,
        f"{emoji} *¡Ganan los {ganador}!*\n\n{razon}\n\n"
        f"🤖 Cylons en la partida: *{cylon_txt}*",
        parse_mode=ParseMode.MARKDOWN,
    )
    await continue_playing(bot, game)


async def continue_playing(bot, game):
    opciones_botones = {
        "Nuevo": "Nuevo partido con nuevos jugadores",
        "Mismos": "Misma partida, mismos jugadores",
    }
    await simple_choose_buttons(
        bot, game.cid, 1, game.cid,
        "chooseendBSG",
        "¿Quieres continuar jugando?",
        opciones_botones,
    )


async def callback_finish_game_buttons_bsg(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    try:
        regex = re.search(r"(-[0-9]*)\*chooseendBSG\*(.*)\*([0-9]*)", callback.data)
        cid, opcion, uid = int(regex.group(1)), regex.group(2), int(regex.group(3))
        try:
            await bot.edit_message_text(f"Has elegido: {opcion}", cid, callback.message.message_id)
        except Exception:
            await bot.edit_message_text(f"Has elegido: {opcion}", uid, callback.message.message_id)

        game = get_game(cid)
        groupName, tipo, modo = game.groupName, game.tipo, game.modo
        players = game.playerlist.copy()

        new_game = Game(cid, uid, groupName, tipo, modo)
        GamesController.games[cid] = new_game

        if opcion == "Nuevo":
            await bot.send_message(
                cid,
                "Cada jugador puede unirse con /join. El iniciador puede escribir /startgame cuando todos estén listos.",
            )
            return

        # Reiniciar con los mismos jugadores
        new_game.playerlist = {}
        for p_uid, old in players.items():
            new_game.add_player(p_uid, old.name)
        new_game.board = None
        new_game.create_board()
        new_game.player_sequence = []
        await init_game(bot, new_game)
    except Exception as e:
        await bot.send_message(ADMIN[0], f'callback_finish_game_buttons_bsg error: {e}')
        await bot.send_message(ADMIN[0], callback.data)
