#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Battlestar Galactica — Controller (Capa 1: fundamentos + bucle central).

Implementado en esta capa:
- Setup completo: selección de personajes, reparto de lealtad, títulos
  (Presidente/Almirante), recursos y pistas iniciales, manos de habilidad.
- Bucle de turno: Recibir Habilidades → (Acción simplificada) → Crisis.
- Chequeos de habilidad con mazo de Destino.
- Fase del Agente Durmiente (distancia 4).
- Salto FTL, condiciones de victoria/derrota.

Pendiente para capas siguientes (claramente acotado):
- Combate espacial detallado (vipers/raiders/basestars), abordaje.
- Acciones de ubicación completas, Quórum, súper crisis.
- Habilidades específicas de cada personaje y cartas de habilidad con efecto.
- Roster completo de cartas de crisis.
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
from BattlestarGalactica.Constants import Characters, Locations, Skills, Crisis, Loyalty

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
        f"*Habilidad:* {pj['habilidad']}\n"
        f"*Desventaja:* {pj['desventaja']}\n"
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

    # --- Manos de habilidad iniciales ---
    for player in game.playerlist.values():
        _robar_skills(st, player)
        await _dm_mano(bot, player)

    st.fase_actual = "En Juego"
    st.player_counter = 0
    st.active_player = game.player_sequence[0]

    await bot.send_message(
        game.cid,
        "🃏 *Cartas de lealtad repartidas* (revisen su privado).\n\n"
        f"🏛️ Presidente: *{pres.name if pres else '—'}*\n"
        f"🎖️ Almirante: *{alm.name if alm else '—'}*\n\n"
        "La flota parte. ¡Sobrevivan hasta la distancia 8!",
        parse_mode=ParseMode.MARKDOWN,
    )
    await bot.send_message(game.cid, game.board.print_board(game), parse_mode=ParseMode.MARKDOWN)
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


def _robar_skills(st, player):
    pj = Characters.PERSONAJES[player.personaje]
    for color in pj["skill_set"]:
        carta = _robar_carta_color(st, color)
        if carta:
            player.skill_hand.append(carta)


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
    lineas = [f"{i+1}. {Skills.EMOJI_COLOR[c['color']]} {c['color']} {c['valor']}"
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

    # Recibir habilidades
    _robar_skills(st, player)
    await _dm_mano(bot, player)

    ubic = Locations.UBICACIONES.get(player.ubicacion, {}).get("nombre", "—")
    await bot.send_message(
        game.cid,
        f"🎬 *Turno de {player.name}* (recibió cartas de habilidad).\n"
        f"📍 Estás en: *{ubic}*\n\n"
        f"`/mover` para cambiar de ubicación · `/accion` para la acción de tu ubicación · "
        f"luego `/crisis` para revelar la crisis.",
        parse_mode=ParseMode.MARKDOWN,
    )
    await save(bot, game.cid)


async def avanzar_turno(bot, game):
    st = game.board.state
    if st.ganador:
        return
    seq = game.player_sequence
    st.player_counter = (st.player_counter + 1) % len(seq)
    st.active_player = seq[st.player_counter]
    await iniciar_turno(bot, game)


# ===================== FLOTA / COMBATE ESPACIAL =====================

def _colocar_flota_inicial(st):
    """Despliega vipers iniciales y naves civiles con carga oculta."""
    n_vipers = min(3, st.vipers_reserva)
    st.vipers_reserva -= n_vipers
    st.vipers_espacio += n_vipers

    cargas = [
        {"recurso": "poblacion", "cantidad": 1},
        {"recurso": "poblacion", "cantidad": 1},
        {"recurso": "moral", "cantidad": 1},
        {"recurso": "combustible", "cantidad": 1},
        {"recurso": None, "cantidad": 0},
        {"recurso": None, "cantidad": 0},
    ]
    random.shuffle(cargas)
    st.civiles = cargas
    st.naves_civiles = len(cargas)


def _d8():
    return random.randint(1, 8)


# Acciones disponibles por ubicación (clave -> lista de acciones)
ACCIONES_UBICACION = {
    "weapons": ["shoot_raider", "shoot_basestar"],
    "hangar": ["launch", "repair"],
    "command": ["viper_attack", "repel"],
    "ftl": ["prep"],
    "admiral_quarters": ["jump", "nuke"],
    "research": ["draw2"],
    "press_room": ["draw1"],
    "president_office": ["draw1"],
    "sickbay": ["heal"],
    "brig": [],
}

ETIQUETA_ACCION = {
    "shoot_raider": "🔫 Disparar a un Raider",
    "shoot_basestar": "💥 Disparar a una Basestar",
    "launch": "✈️ Lanzar un Viper",
    "repair": "🔧 Reparar Vipers dañados",
    "viper_attack": "✈️🔫 Viper ataca a un Raider",
    "repel": "🪖 Repeler centuriones (-1)",
    "prep": "⏫ Preparar salto (+1)",
    "jump": "🌌 Ejecutar salto FTL",
    "nuke": "☢️ Ataque nuclear",
    "draw2": "🃏 Robar 2 cartas de habilidad",
    "draw1": "🃏 Robar 1 carta de habilidad",
    "heal": "🩺 Curarse",
}


async def ejecutar_accion_ubicacion(bot, game, uid, accion):
    """Resuelve la acción de ubicación elegida por el jugador activo."""
    st = game.board.state
    player = game.playerlist[uid]

    if accion == "shoot_raider":
        await _disparar(bot, game, "raider")
    elif accion == "shoot_basestar":
        await _disparar(bot, game, "basestar")
    elif accion == "launch":
        await _lanzar_viper(bot, game)
    elif accion == "repair":
        reparados = st.vipers_danados
        st.vipers_reserva += st.vipers_danados
        st.vipers_danados = 0
        await bot.send_message(game.cid, f"🔧 {reparados} Viper(s) reparado(s).")
    elif accion == "viper_attack":
        await _viper_ataca(bot, game)
    elif accion == "repel":
        if st.centuriones > 0:
            st.centuriones -= 1
            await bot.send_message(game.cid, f"🪖 Repeles a los centuriones ({st.centuriones}/{st.centuriones_max}).")
        else:
            await bot.send_message(game.cid, "No hay centuriones a bordo.")
    elif accion == "prep":
        st.jump_prep = min(st.jump_prep_max, st.jump_prep + 1)
        await bot.send_message(game.cid, f"⏫ Preparación de salto: {st.jump_prep}/{st.jump_prep_max}")
    elif accion == "jump":
        if uid != st.almirante_uid and uid not in ADMIN:
            await bot.send_message(game.cid, "Solo el Almirante puede ejecutar el salto.")
            return
        if st.jump_prep < 2:
            await bot.send_message(game.cid, "La preparación de salto aún no es suficiente (mín. 2).")
            return
        await ejecutar_salto(bot, game, auto=False)
    elif accion == "nuke":
        if uid != st.almirante_uid and uid not in ADMIN:
            await bot.send_message(game.cid, "Solo el Almirante puede lanzar el ataque nuclear.")
            return
        await _nuke(bot, game)
    elif accion == "draw2":
        await _robar_n_skills(bot, game, player, 2)
    elif accion == "draw1":
        await _robar_n_skills(bot, game, player, 1)
    elif accion == "heal":
        await bot.send_message(game.cid, f"🩺 {player.name} se recupera en la enfermería.")
    else:
        await bot.send_message(game.cid, "Acción no disponible.")
    await save(bot, game.cid)


async def _robar_n_skills(bot, game, player, n):
    pj = Characters.PERSONAJES[player.personaje]
    colores = pj["skill_set"]
    for i in range(n):
        color = colores[i % len(colores)]
        carta = _robar_carta_color(game.board.state, color)
        if carta:
            player.skill_hand.append(carta)
    await bot.send_message(game.cid, f"🃏 {player.name} roba {n} carta(s) de habilidad.")
    await _dm_mano(bot, player)


async def _disparar(bot, game, objetivo):
    st = game.board.state
    if objetivo == "raider":
        if st.raiders <= 0:
            await bot.send_message(game.cid, "No hay Raiders a los que disparar.")
            return
        r = _d8()
        if r >= 4:
            st.raiders -= 1
            await bot.send_message(game.cid, f"🔫 Tirada {r}: ¡Raider destruido! (quedan {st.raiders})")
        else:
            await bot.send_message(game.cid, f"🔫 Tirada {r}: fallo.")
    else:
        if st.basestars <= 0:
            await bot.send_message(game.cid, "No hay Basestars a las que disparar.")
            return
        r = _d8()
        if r >= 5:
            st.basestar_hits += 1
            await bot.send_message(game.cid, f"💥 Tirada {r}: impacto en Basestar ({st.basestar_hits}/3).")
            if st.basestar_hits >= 3:
                st.basestars -= 1
                st.basestar_hits = 0
                await bot.send_message(game.cid, "🛸💀 ¡Basestar destruida!")
        else:
            await bot.send_message(game.cid, f"💥 Tirada {r}: fallo.")


async def _lanzar_viper(bot, game):
    st = game.board.state
    if st.vipers_reserva <= 0:
        await bot.send_message(game.cid, "No quedan Vipers en la reserva.")
        return
    st.vipers_reserva -= 1
    st.vipers_espacio += 1
    await bot.send_message(game.cid, f"✈️ Viper lanzado (en espacio: {st.vipers_espacio}).")


async def _viper_ataca(bot, game):
    st = game.board.state
    if st.vipers_espacio <= 0:
        await bot.send_message(game.cid, "No hay Vipers en el espacio.")
        return
    if st.raiders <= 0:
        await bot.send_message(game.cid, "No hay Raiders a los que atacar.")
        return
    r = _d8()
    if r >= 4:
        st.raiders -= 1
        await bot.send_message(game.cid, f"✈️🔫 Tirada {r}: el Viper derriba un Raider (quedan {st.raiders}).")
    else:
        await bot.send_message(game.cid, f"✈️ Tirada {r}: el Viper falla.")


async def _nuke(bot, game):
    st = game.board.state
    if st.nuke_usado:
        await bot.send_message(game.cid, "El ataque nuclear ya fue utilizado.")
        return
    if st.basestars <= 0:
        await bot.send_message(game.cid, "No hay Basestars para atacar.")
        return
    st.nuke_usado = True
    st.basestars -= 1
    st.basestar_hits = 0
    await bot.send_message(game.cid, "☢️ *¡ATAQUE NUCLEAR!* Una Basestar es destruida.", parse_mode=ParseMode.MARKDOWN)


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


async def activar_naves_cylon(bot, game):
    """Activa las naves Cylon: basestars lanzan raiders y atacan; raiders combaten."""
    st = game.board.state
    await bot.send_message(game.cid, "🤖 *Se activan las naves Cylon...*", parse_mode=ParseMode.MARKDOWN)

    # Si no hay basestars y pocos raiders, a veces aparece una basestar
    if st.basestars == 0 and st.raiders == 0 and _d8() >= 6:
        st.basestars += 1
        await bot.send_message(game.cid, "🛸 ¡Una Basestar Cylon salta a la zona!")

    # Basestars lanzan raiders
    for _ in range(st.basestars):
        st.raiders += 1
    if st.basestars > 0:
        await bot.send_message(
            game.cid,
            f"🛸 Las Basestars lanzan Raiders (total: {st.raiders}).",
        )

    # Combate Raiders vs Vipers
    combates = min(st.vipers_espacio, st.raiders)
    for _ in range(combates):
        r = _d8()
        if r >= 5:
            st.raiders -= 1
        else:
            st.vipers_espacio -= 1
            st.vipers_danados += 1
    if combates:
        await bot.send_message(
            game.cid,
            f"✈️💥 Combate aéreo — Vipers en espacio: {st.vipers_espacio}, Raiders: {st.raiders}.",
        )

    # Raiders sin oposición atacan naves civiles o abordan Galactica
    excess = max(0, st.raiders - st.vipers_espacio)
    if excess > 0:
        if st.civiles:
            await _destruir_civil(bot, game)
        elif st.vipers_espacio == 0:
            st.centuriones += 1
            await bot.send_message(
                game.cid,
                f"🔺 Sin defensas, los Cylons abordan Galactica (centuriones: {st.centuriones}/{st.centuriones_max}).",
            )

    # Si el espacio quedó despejado de amenazas, los marines recuperan terreno
    if st.raiders == 0 and st.basestars == 0 and st.centuriones > 0:
        st.centuriones -= 1
        await bot.send_message(
            game.cid,
            f"🪖 Espacio despejado: los marines repelen el abordaje (centuriones: {st.centuriones}/{st.centuriones_max}).",
        )


async def _destruir_civil(bot, game):
    st = game.board.state
    if not st.civiles:
        return
    carga = st.civiles.pop(random.randrange(len(st.civiles)))
    st.naves_civiles = len(st.civiles)
    if carga["recurso"]:
        await bot.send_message(game.cid, f"🛰️💀 ¡Nave civil destruida! Transportaba {carga['recurso']}.")
        await modificar_recurso(bot, game, carga["recurso"], -carga["cantidad"])
    else:
        await bot.send_message(game.cid, "🛰️💀 Nave civil destruida (estaba vacía).")


# ===================== SABOTAJE CYLON =====================

# Acciones disponibles para un Cylon revelado, según su ubicación Cylon.
ACCIONES_CYLON = {
    "cylon_fleet": ["launch_raiders", "launch_basestar"],
    "caprica": ["sabotage", "board"],
    "resurrection_ship": ["launch_raiders", "sabotage"],
    "human_fleet": ["sabotage", "board"],
}

ETIQUETA_ACCION_CYLON = {
    "launch_raiders": "👾 Lanzar 2 Raiders",
    "launch_basestar": "🛸 Traer una Basestar",
    "sabotage": "🔧💥 Sabotear un recurso (-1)",
    "board": "🔺 Avanzar abordaje (+1)",
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
    # Se traslada al lado Cylon
    player.ubicacion = "cylon_fleet"
    player.skill_hand = []

    await bot.send_message(
        game.cid,
        f"🤖 *¡{player.name} se revela como CYLON!* Se traslada a la Flota Cylon.",
        parse_mode=ParseMode.MARKDOWN,
    )

    # Desata una súper crisis
    if st.super_crisis_deck:
        sc = st.super_crisis_deck.pop()
        await bot.send_message(
            game.cid,
            f"☠️ *SÚPER CRISIS: {sc['titulo']}*\n_{sc['texto']}_",
            parse_mode=ParseMode.MARKDOWN,
        )
        await aplicar_efectos(bot, game, sc.get("efectos", []))

    await save(bot, game.cid)
    if await _chequear_fin(bot, game):
        return


async def ejecutar_accion_cylon(bot, game, uid, accion):
    """Acción de un Cylon revelado en su turno."""
    st = game.board.state
    if accion == "launch_raiders":
        st.raiders += 2
        await bot.send_message(game.cid, f"👾 El Cylon lanza 2 Raiders (total: {st.raiders}).")
    elif accion == "launch_basestar":
        st.basestars += 1
        await bot.send_message(game.cid, f"🛸 El Cylon trae una Basestar (total: {st.basestars}).")
    elif accion == "sabotage":
        # Sabotea el recurso no nulo más bajo (más dañino)
        recursos = {"comida": st.comida, "combustible": st.combustible,
                    "moral": st.moral, "poblacion": st.poblacion}
        candidatos = {k: v for k, v in recursos.items() if v > 0}
        objetivo = min(candidatos, key=candidatos.get) if candidatos else "moral"
        await modificar_recurso(bot, game, objetivo, -1)
    elif accion == "board":
        st.centuriones = min(st.centuriones_max, st.centuriones + 1)
        await bot.send_message(game.cid, f"🔺 Abordaje Cylon: {st.centuriones}/{st.centuriones_max}")
    else:
        await bot.send_message(game.cid, "Acción Cylon no disponible.")
    await save(bot, game.cid)


# ===================== CRISIS =====================

async def robar_crisis(bot, game):
    st = game.board.state
    if not st.crisis_deck:
        st.crisis_deck = st.crisis_discard
        st.crisis_discard = []
        random.shuffle(st.crisis_deck)
    if not st.crisis_deck:
        await bot.send_message(game.cid, "No quedan cartas de crisis.")
        return
    crisis = st.crisis_deck.pop()
    st.crisis_actual = crisis

    await bot.send_message(
        game.cid,
        f"⚠️ *CRISIS: {crisis['titulo']}*\n_{crisis['texto']}_",
        parse_mode=ParseMode.MARKDOWN,
    )

    if crisis["tipo"] == "chequeo":
        await abrir_chequeo(bot, game, crisis)
    else:
        await aplicar_efectos(bot, game, crisis.get("efectos", []))
        await cerrar_crisis(bot, game, crisis)


async def abrir_chequeo(bot, game, crisis):
    st = game.board.state
    colores = crisis["colores"]
    emojis = " ".join(Skills.EMOJI_COLOR[c] for c in colores)
    st.skill_check = {
        "crisis_id": crisis["id"],
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
    # 2 cartas de destino
    destino = _robar_destino(st, 2)
    for c in destino:
        todas.append(c)

    random.shuffle(todas)  # ocultar quién aportó qué
    for c in todas:
        signo = Skills.signo_para_check(c["color"], colores)
        total += signo * c["valor"]
        detalle.append(f"{Skills.EMOJI_COLOR[c['color']]}{'+' if signo>0 else '-'}{c['valor']}")
        st.skill_discards.setdefault(c["color"], []).append(c)

    crisis = st.crisis_actual
    exito = total >= sc["dificultad"]
    await bot.send_message(
        game.cid,
        f"🎲 Resultado del chequeo: *{total}* vs dificultad *{sc['dificultad']}* → "
        f"{'✅ ÉXITO' if exito else '❌ FRACASO'}\n"
        f"Cartas: {' '.join(detalle) if detalle else '(ninguna)'}",
        parse_mode=ParseMode.MARKDOWN,
    )
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

    # Activación de naves Cylon si la crisis lo indica
    if crisis.get("activar_cylons"):
        await activar_naves_cylon(bot, game)
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

    await bot.send_message(game.cid, game.board.print_board(game), parse_mode=ParseMode.MARKDOWN)
    await avanzar_turno(bot, game)


# ===================== EFECTOS / RECURSOS =====================

async def aplicar_efectos(bot, game, efectos):
    st = game.board.state
    for ef in efectos or []:
        tipo = ef.get("tipo")
        if tipo == "recurso":
            await modificar_recurso(bot, game, ef["recurso"], ef["delta"])
        elif tipo == "raiders":
            st.raiders += ef["cantidad"]
            await bot.send_message(game.cid, f"👾 Aparecen {ef['cantidad']} Raiders (total: {st.raiders}).")
        elif tipo == "basestar":
            st.basestars += ef["cantidad"]
            await bot.send_message(game.cid, f"🛸 Aparece(n) {ef['cantidad']} Basestar(s) (total: {st.basestars}).")
        elif tipo == "centuriones":
            st.centuriones = max(0, st.centuriones + ef["delta"])
            await bot.send_message(game.cid, f"🔺 Centuriones: {st.centuriones}/{st.centuriones_max}")
        elif tipo == "mensaje":
            await bot.send_message(game.cid, ef["texto"])


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
    st.distancia = min(st.objetivo_distancia, st.distancia + avance)

    # Las naves Cylon no siguen a la flota tras el salto; los Vipers regresan.
    st.raiders = 0
    st.basestars = 0
    st.basestar_hits = 0
    st.vipers_reserva += st.vipers_espacio + st.vipers_danados
    st.vipers_espacio = 0
    st.vipers_danados = 0

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
        if st.loyalty_deck:
            carta = st.loyalty_deck.pop()
            player.loyalty_cards.append(carta)
            if carta == Loyalty.CYLON and not player.is_cylon:
                player.is_cylon = True
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
    # Derrota: Galactica tomada por los centuriones
    if st.centuriones >= st.centuriones_max:
        await terminar(bot, game, "Cylons", "Los centuriones tomaron Galactica.")
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
