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
from BattlestarGalactica.Constants import Characters, Locations, Skills, Crisis, Loyalty, Quorum

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

    # En el juego base no se reparte mano inicial: cada jugador roba en el
    # paso de Recibir Habilidades al comienzo de su turno.

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


def _robar_skills(st, player, cantidad=3):
    """Roba 'cantidad' cartas de habilidad de los colores del set del personaje.
    En el juego base se roban 3 por turno, repartidas entre los colores permitidos."""
    pj = Characters.PERSONAJES[player.personaje]
    pool = pj["skill_set"]
    for _ in range(cantidad):
        color = random.choice(pool)
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


# Acciones disponibles por ubicación (clave -> lista de acciones), según el set oficial.
ACCIONES_UBICACION = {
    "ftl": ["jump"],
    "weapons": ["shoot_raider", "shoot_basestar"],
    "command": ["activate_vipers"],
    "communications": ["peek_civiles"],
    "admiral_quarters": ["brig_check"],
    "research": ["draw_eng", "draw_tac"],
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

ETIQUETA_ACCION = {
    "jump": "🌌 Saltar la flota (FTL)",
    "shoot_raider": "🔫 Disparar a un Raider",
    "shoot_basestar": "💥 Disparar a una Basestar",
    "activate_vipers": "✈️ Activar Vipers (atacan Raiders)",
    "peek_civiles": "🔭 Inspeccionar naves civiles",
    "brig_check": "🚔 Enviar a alguien al Calabozo (chequeo)",
    "draw_eng": "🟡 Robar 1 carta de Ingeniería",
    "draw_tac": "🔴 Robar 1 carta de Táctica",
    "launch": "✈️ Lanzarte en un Viper",
    "armory_attack": "🪖 Atacar a un centurión",
    "draw_politics": "🟢 Robar 2 cartas de Política",
    "draw_quorum": "🏛️ Robar una carta de Quórum",
    "president_check": "🏛️ Dar la Presidencia (chequeo)",
}


async def ejecutar_accion_ubicacion(bot, game, uid, accion, objetivo=None):
    """Resuelve la acción de ubicación elegida por el jugador activo."""
    st = game.board.state
    player = game.playerlist[uid]

    if accion == "jump":
        # FTL Control: saltar si el track no está en zona roja (proxy: prep >= 2)
        if st.jump_prep < 2:
            await bot.send_message(game.cid, "El track de salto aún no está listo (necesita avanzar más por crisis).")
            return
        await ejecutar_salto(bot, game, auto=False)
    elif accion == "shoot_raider":
        await _disparar(bot, game, "raider")
    elif accion == "shoot_basestar":
        await _disparar(bot, game, "basestar")
    elif accion == "activate_vipers":
        # Comando: activar hasta 2 Vipers sin tripular para atacar
        await _viper_ataca(bot, game)
        if st.vipers_espacio > 0 and st.raiders > 0:
            await _viper_ataca(bot, game)
    elif accion == "peek_civiles":
        info = ", ".join(c["recurso"] or "vacía" for c in st.civiles) or "ninguna"
        await bot.send_message(uid, f"🔭 Cargas de las naves civiles: {info}")
        await bot.send_message(game.cid, f"🔭 {player.name} inspecciona las naves civiles.")
    elif accion == "draw_eng":
        await _robar_color(bot, game, player, Skills.INGENIERIA)
    elif accion == "draw_tac":
        await _robar_color(bot, game, player, Skills.TACTICA)
    elif accion == "launch":
        await _lanzar_viper(bot, game)
        await bot.send_message(game.cid, f"✈️ {player.name} se lanza en un Viper.")
    elif accion == "armory_attack":
        if st.centuriones <= 0:
            await bot.send_message(game.cid, "No hay centuriones en el track de abordaje.")
        else:
            r = _d8()
            if r >= 7:
                st.centuriones -= 1
                await bot.send_message(game.cid, f"🪖 Tirada {r}: ¡centurión destruido! ({st.centuriones}/{st.centuriones_max})")
            else:
                await bot.send_message(game.cid, f"🪖 Tirada {r}: el centurión resiste.")
    elif accion == "draw_politics":
        await _robar_color(bot, game, player, Skills.POLITICA)
        await _robar_color(bot, game, player, Skills.POLITICA)
    elif accion == "draw_quorum":
        if uid != st.presidente_uid and uid not in ADMIN:
            await bot.send_message(game.cid, "Solo el Presidente puede robar cartas de Quórum.")
            return
        await robar_quorum(bot, game, uid)
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
    st.skill_check = {
        "ubicacion_accion": efecto,
        "actor_uid": actor_uid,
        "objetivo_uid": objetivo_uid,
        "colores": check["colores"],
        "dificultad": check["dificultad"],
        "aportes": {},
    }
    emojis = " ".join(Skills.EMOJI_COLOR[c] for c in check["colores"])
    obj = game.playerlist.get(objetivo_uid)
    obj_txt = f" sobre *{obj.name}*" if obj and objetivo_uid != actor_uid else ""
    await bot.send_message(
        game.cid,
        f"🎲 *Chequeo de acción*{obj_txt} — dificultad *{check['dificultad']}*.\n"
        f"Colores positivos: {emojis}.\n"
        f"Aporten con `/aportar N` y resuelvan con `/resolver`.",
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
        await bot.send_message(game.cid, f"🏛️ *{objetivo.name}* recibe el título de Presidente.", parse_mode=ParseMode.MARKDOWN)
    elif efecto == "escape" and objetivo:
        objetivo.en_calabozo = False
        objetivo.ubicacion = "sickbay"
        await bot.send_message(game.cid, f"🔓 *{objetivo.name}* sale del Calabozo (Enfermería).", parse_mode=ParseMode.MARKDOWN)
    await save(bot, game.cid)


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
        await _viper_ataca(bot, game)
        await bot.send_message(game.cid, f"✈️ *{nombre}* despega y ataca (habilidad).", parse_mode=ParseMode.MARKDOWN)
    elif pj == "starbuck":
        rep = st.vipers_danados
        st.vipers_reserva += st.vipers_danados
        st.vipers_danados = 0
        if st.raiders > 0:
            st.raiders -= 1
        await bot.send_message(game.cid, f"✈️ *{nombre}* (Top Gun): repara {rep} Viper(s) y derriba un Raider.", parse_mode=ParseMode.MARKDOWN)
    elif pj == "boomer":
        if st.raiders > 0:
            st.raiders -= 1
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
    await aplicar_efectos(bot, game, carta.get("efectos", []))
    st.quorum_discard.append(carta)
    await save(bot, game.cid)
    await _chequear_fin(bot, game)


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
    elif crisis["tipo"] == "eleccion":
        await abrir_eleccion(bot, game, crisis)
    elif crisis["tipo"] == "voto":
        await abrir_voto(bot, game, crisis)
    else:
        await aplicar_efectos(bot, game, crisis.get("efectos", []))
        await cerrar_crisis(bot, game, crisis)


# ---- Crisis de decisión ----

async def abrir_eleccion(bot, game, crisis):
    st = game.board.state
    if crisis.get("decisor") == "presidente" and st.presidente_uid:
        decisor = game.playerlist[st.presidente_uid]
    else:
        decisor = st.active_player
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

    # Bono de habilidades (p. ej. Cadena de Mando de Adama)
    bonus = sc.get("bonus", 0)
    if bonus:
        total += bonus
        detalle.append(f"⭐{'+' if bonus>0 else ''}{bonus}")

    exito = total >= sc["dificultad"]
    await bot.send_message(
        game.cid,
        f"🎲 Resultado del chequeo: *{total}* vs dificultad *{sc['dificultad']}* → "
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
            cant = ef["cantidad"]
            st.raiders = max(0, st.raiders + cant)
            if cant >= 0:
                await bot.send_message(game.cid, f"👾 Aparecen {cant} Raiders (total: {st.raiders}).")
            else:
                await bot.send_message(game.cid, f"🔫 Se eliminan {-cant} Raiders (total: {st.raiders}).")
        elif tipo == "vipers":
            st.vipers_reserva += ef["cantidad"]
            await bot.send_message(game.cid, f"✈️ Llegan {ef['cantidad']} Vipers a la reserva (total reserva: {st.vipers_reserva}).")
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
