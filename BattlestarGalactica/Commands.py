#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Battlestar Galactica — comandos y callbacks (Capa 1)."""

import logging as log
import re

import BattlestarGalactica.Controller as BSGController
from BattlestarGalactica.Constants import Characters, Skills, Loyalty, Locations, Space
from Utils import get_game, save
from Constants.Config import ADMIN

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

import GamesController

log.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=log.INFO)
logger = log.getLogger(__name__)


def _validar(game):
    return game and game.tipo == "BattlestarGalactica" and game.board


async def command_call(bot, game):
    if not game.board:
        return
    st = game.board.state
    if st.fase_actual == "En Juego" and st.active_player:
        await bot.send_message(
            game.cid,
            f"🚀 *BSG en curso* — turno de *{st.active_player.name}*.\n"
            "Mover: `/mover` · Acción: `/accion` · Crisis: `/crisis` · Tablero: `/estado` · Mapa: `/mapa`\n"
            "Habilidad: `/habilidad` · Presidente: `/quorum` · Cylons: `/revelar`\n"
            "Presidente/Almirante: `/encarcelar` · `/liberar`",
            parse_mode=ParseMode.MARKDOWN,
        )


async def callback_bsg_pick(update: Update, context: CallbackContext):
    """Selección de personaje."""
    bot = context.bot
    callback = update.callback_query
    presser = callback.from_user.id
    try:
        regex = re.search(r"(-?[0-9]*)\*bsgPick\*([a-z_]*)\*(-?[0-9]*)", callback.data)
        cid = int(regex.group(1))
        key = regex.group(2)
        target_uid = int(regex.group(3))

        game = get_game(cid)
        if not _validar(game):
            await callback.answer("Partida no encontrada.")
            return
        st = game.board.state
        if st.fase_actual != "Seleccion de Personajes":
            await callback.answer("La selección ya terminó.")
            return
        if presser != target_uid:
            await callback.answer("No es tu turno de elegir.")
            return
        if key in st.personajes_elegidos.values():
            await callback.answer("Ese personaje ya fue elegido.")
            return
        if target_uid in st.personajes_elegidos:
            await callback.answer("Ya elegiste personaje.")
            return

        await callback.answer(f"Elegiste {Characters.PERSONAJES[key]['nombre']}")
        try:
            await bot.edit_message_text(
                f"{game.playerlist[target_uid].name} eligió a {Characters.PERSONAJES[key]['nombre']}.",
                cid, callback.message.message_id
            )
        except Exception:
            pass
        await BSGController.asignar_personaje(bot, game, target_uid, key)
    except Exception as e:
        logger.error(f"callback_bsg_pick error: {e}")
        try:
            await callback.answer("Error.")
        except Exception:
            pass
        await bot.send_message(ADMIN[0], f"BSG pick error: {e}")


async def callback_bsg_draw(update: Update, context: CallbackContext):
    """El jugador activo elige el color de la siguiente carta a robar (privado)."""
    bot = context.bot
    callback = update.callback_query
    presser = callback.from_user.id
    try:
        regex = re.search(r"(-?[0-9]*)\*bsgDraw\*([A-Za-z]*)\*(-?[0-9]*)", callback.data)
        cid = int(regex.group(1))
        color = regex.group(2)
        target = int(regex.group(3))
        game = get_game(cid)
        if not _validar(game):
            await callback.answer("Partida no encontrada.")
            return
        st = game.board.state
        if not st.skill_draw or st.skill_draw["uid"] != presser or presser != target:
            await callback.answer("No es tu robo de cartas.")
            return
        if color not in st.skill_draw["pool"]:
            await callback.answer("Color no disponible.")
            return
        await callback.answer(f"Robaste {color}.")
        try:
            await bot.edit_message_reply_markup(presser, callback.message.message_id, reply_markup=None)
        except Exception:
            pass
        await BSGController.elegir_color_skill(bot, game, presser, color)
    except Exception as e:
        logger.error(f"callback_bsg_draw error: {e}")
        try:
            await callback.answer("Error.")
        except Exception:
            pass
        await bot.send_message(ADMIN[0], f"BSG draw error: {e}")


def _esperando_robo(st, uid):
    """True si el jugador activo aún debe elegir sus cartas de Recibir Habilidades."""
    return bool(st.skill_draw and st.active_player and st.active_player.uid == uid
                and st.skill_draw["uid"] == uid)


async def command_lealtad(update: Update, context: CallbackContext):
    """Muestra al jugador su personaje y su lealtad por privado."""
    bot = context.bot
    cid = update.message.chat_id
    uid = update.message.from_user.id
    game = get_game(cid)
    if not _validar(game):
        await bot.send_message(cid, "No hay partida de Battlestar Galactica activa aquí.")
        return
    if uid not in game.playerlist:
        await bot.send_message(uid, "No estás en esta partida.")
        return
    player = game.playerlist[uid]
    pj = Characters.PERSONAJES.get(player.personaje)
    es_cylon = Loyalty.CYLON in player.loyalty_cards
    rol = "🤖 *ERES UN CYLON*" if es_cylon else "🧑 No eres un Cylon (por ahora)"
    nombre_pj = pj["nombre"] if pj else "sin asignar"
    await bot.send_message(
        uid,
        f"{rol}\n\nPersonaje: *{nombre_pj}*\n"
        f"Cartas de lealtad: {len(player.loyalty_cards)}",
        parse_mode=ParseMode.MARKDOWN,
    )


async def command_mano(update: Update, context: CallbackContext):
    """Muestra la mano de habilidad por privado."""
    bot = context.bot
    cid = update.message.chat_id
    uid = update.message.from_user.id
    game = get_game(cid)
    if not _validar(game):
        await bot.send_message(cid, "No hay partida de Battlestar Galactica activa aquí.")
        return
    if uid not in game.playerlist:
        await bot.send_message(uid, "No estás en esta partida.")
        return
    player = game.playerlist[uid]
    if not player.skill_hand:
        await bot.send_message(uid, "No tienes cartas de habilidad.")
        return
    lineas = [f"{i+1}. {Skills.EMOJI_COLOR[c['color']]} {c['color']} {c['valor']} — _{c.get('nombre','')}_"
              for i, c in enumerate(player.skill_hand)]
    await bot.send_message(uid, "🃏 *Tu mano:*\n" + "\n".join(lineas), parse_mode=ParseMode.MARKDOWN)


async def command_estado(update: Update, context: CallbackContext):
    """Muestra el tablero/estado de la partida."""
    bot = context.bot
    cid = update.message.chat_id
    game = get_game(cid)
    if not _validar(game):
        await bot.send_message(cid, "No hay partida de Battlestar Galactica activa aquí.")
        return
    await bot.send_message(cid, game.board.print_board(game), parse_mode=ParseMode.MARKDOWN)


async def command_mapa(update: Update, context: CallbackContext):
    """Muestra el mapa textual de la flota (ubicaciones y espacio)."""
    bot = context.bot
    cid = update.message.chat_id
    game = get_game(cid)
    if not _validar(game):
        await bot.send_message(cid, "No hay partida de Battlestar Galactica activa aquí.")
        return
    await bot.send_message(cid, game.board.print_map(game), parse_mode=ParseMode.MARKDOWN)


async def command_accion(update: Update, context: CallbackContext):
    """Acción del jugador activo (menú simplificado en esta capa)."""
    bot = context.bot
    cid = update.message.chat_id
    uid = update.message.from_user.id
    game = get_game(cid)
    if not _validar(game):
        await bot.send_message(cid, "No hay partida de Battlestar Galactica activa aquí.")
        return
    st = game.board.state
    if st.fase_actual != "En Juego" or not st.active_player or st.active_player.uid != uid:
        await bot.send_message(cid, "No es tu turno de acción.")
        return
    if _esperando_robo(st, uid):
        await bot.send_message(cid, "Primero elige tus cartas de habilidad (revisa tu privado).")
        return

    player = game.playerlist[uid]
    # En el calabozo solo se permite el intento de fuga (chequeo del Calabozo).
    if player.en_calabozo and player.ubicacion != "brig":
        await bot.send_message(cid, "Estás en el calabozo y no puedes realizar acciones.")
        return

    # Pilotando un Viper tripulado: acciones de piloto en lugar de las de ubicación.
    if getattr(player, "viper_area", None) is not None:
        btns = [[InlineKeyboardButton(BSGController.ETIQUETA_ACCION[a],
                                      callback_data=f"{cid}*bsgAccion*{a}*{uid}")]
                for a in BSGController.ACCIONES_PILOTO]
        await bot.send_message(cid, f"✈️ Pilotas un Viper en *{Space.nombre(player.viper_area)}* — elige tu acción:",
                               reply_markup=InlineKeyboardMarkup(btns), parse_mode=ParseMode.MARKDOWN)
        return

    ubic = Locations.UBICACIONES.get(player.ubicacion, {}).get("nombre", "—")

    # Cylon revelado: acciones de sabotaje según su ubicación Cylon
    if player.revealed:
        acciones = BSGController.ACCIONES_CYLON.get(player.ubicacion, [])
        if not acciones:
            await bot.send_message(cid, f"📍 {ubic}: sin acción Cylon aquí. Usa `/mover` o `/crisis`.",
                                   parse_mode=ParseMode.MARKDOWN)
            return
        btns = [[InlineKeyboardButton(BSGController.ETIQUETA_ACCION_CYLON[a],
                                      callback_data=f"{cid}*bsgCylon*{a}*{uid}")]
                for a in acciones]
        await bot.send_message(cid, f"🤖 *{ubic}* — acción Cylon:",
                               reply_markup=InlineKeyboardMarkup(btns), parse_mode=ParseMode.MARKDOWN)
        return

    if st.ubicacion_averiada(player.ubicacion):
        await bot.send_message(cid, f"🛠️ *{ubic}* está averiada: su acción no está disponible hasta repararla "
                                    f"(usa el Laboratorio de Investigación). Puedes `/mover` o `/crisis`.",
                               parse_mode=ParseMode.MARKDOWN)
        return

    acciones = BSGController.ACCIONES_UBICACION.get(player.ubicacion, [])
    if not acciones:
        await bot.send_message(cid, f"📍 {ubic}: no hay acción disponible aquí. Usa `/crisis`.",
                               parse_mode=ParseMode.MARKDOWN)
        return
    btns = [[InlineKeyboardButton(BSGController.ETIQUETA_ACCION[a],
                                  callback_data=f"{cid}*bsgAccion*{a}*{uid}")]
            for a in acciones]
    btns.append([InlineKeyboardButton("⏭️ Pasar", callback_data=f"{cid}*bsgAccion*pass*{uid}")])
    await bot.send_message(cid, f"📍 *{ubic}* — elige tu acción:",
                           reply_markup=InlineKeyboardMarkup(btns), parse_mode=ParseMode.MARKDOWN)


async def callback_bsg_accion(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    presser = callback.from_user.id
    try:
        regex = re.search(r"(-?[0-9]*)\*bsgAccion\*([a-z0-9_]*)\*(-?[0-9]*)", callback.data)
        cid = int(regex.group(1))
        accion = regex.group(2)
        target = int(regex.group(3))
        game = get_game(cid)
        if not _validar(game):
            await callback.answer("Partida no encontrada.")
            return
        st = game.board.state
        if not st.active_player or st.active_player.uid != presser or presser != target:
            await callback.answer("No es tu acción.")
            return

        # Acción de piloto que requiere elegir un área adyacente → vecinos
        if accion in BSGController.ACCIONES_PILOTO_AREA:
            await callback.answer()
            i = getattr(game.playerlist[presser], "viper_area", None)
            if i is None:
                await bot.send_message(cid, "No estás pilotando un Viper.")
                return
            btns = [[InlineKeyboardButton(Space.nombre(n),
                                          callback_data=f"{cid}*bsgArea*{accion}_{n}*{presser}")]
                    for n in Space.vecinos(i)]
            try:
                await bot.edit_message_text("¿A qué área adyacente vuelas?", cid, callback.message.message_id,
                                            reply_markup=InlineKeyboardMarkup(btns))
            except Exception:
                await bot.send_message(cid, "¿A qué área adyacente vuelas?", reply_markup=InlineKeyboardMarkup(btns))
            return

        # Acciones que requieren elegir un ÁREA del espacio → mostrar botonera de áreas
        if accion in BSGController.ACCIONES_CON_AREA:
            await callback.answer()
            tipo = BSGController.ACCIONES_CON_AREA[accion]
            btns = []
            for i, a in enumerate(st.areas):
                cant = a["raiders"] if tipo == "raiders" else len(a["basestars"])
                if cant > 0:
                    btns.append([InlineKeyboardButton(
                        f"{Space.nombre(i)} ({cant})",
                        callback_data=f"{cid}*bsgArea*{accion}_{i}*{presser}")])
            if not btns:
                await bot.send_message(cid, "No hay objetivos en ningún área.")
                return
            try:
                await bot.edit_message_text("Elige el área a atacar:", cid, callback.message.message_id,
                                            reply_markup=InlineKeyboardMarkup(btns))
            except Exception:
                await bot.send_message(cid, "Elige el área a atacar:", reply_markup=InlineKeyboardMarkup(btns))
            return

        # Acciones que requieren elegir un personaje objetivo → mostrar botonera
        if accion in BSGController.ACCIONES_CON_OBJETIVO:
            await callback.answer()
            btns = []
            for p_uid, p in game.playerlist.items():
                if accion == "brig_check" and (p.en_calabozo or p.revealed):
                    continue
                btns.append([InlineKeyboardButton(p.name, callback_data=f"{cid}*bsgTarget*{accion}*{p_uid}")])
            if not btns:
                await bot.send_message(cid, "No hay objetivos válidos.")
                return
            try:
                await bot.edit_message_text("Elige el objetivo:", cid, callback.message.message_id,
                                            reply_markup=InlineKeyboardMarkup(btns))
            except Exception:
                await bot.send_message(cid, "Elige el objetivo:", reply_markup=InlineKeyboardMarkup(btns))
            return

        await callback.answer("Acción realizada.")
        try:
            await bot.edit_message_text("Acción elegida.", cid, callback.message.message_id)
        except Exception:
            pass

        if accion != "pass":
            await BSGController.ejecutar_accion_ubicacion(bot, game, presser, accion)
        else:
            await bot.send_message(cid, f"{game.playerlist[presser].name} pasa su acción.")
        if not st.ganador and not st.skill_check:
            await bot.send_message(cid, "Ahora se revela la *Crisis*. Usa `/crisis`.", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"callback_bsg_accion error: {e}")
        try:
            await callback.answer("Error.")
        except Exception:
            pass
        await bot.send_message(ADMIN[0], f"BSG accion error: {e}")


async def callback_bsg_area(update: Update, context: CallbackContext):
    """Selección de área del espacio para una acción de Control de Armas."""
    bot = context.bot
    callback = update.callback_query
    presser = callback.from_user.id
    try:
        regex = re.search(r"(-?[0-9]*)\*bsgArea\*([a-z_]+)_([0-9]+)\*(-?[0-9]*)", callback.data)
        cid = int(regex.group(1))
        accion = regex.group(2)
        area_idx = int(regex.group(3))
        target = int(regex.group(4))
        game = get_game(cid)
        if not _validar(game):
            await callback.answer("Partida no encontrada.")
            return
        st = game.board.state
        if not st.active_player or st.active_player.uid != presser or presser != target:
            await callback.answer("No es tu acción.")
            return
        await callback.answer("Área seleccionada.")
        try:
            await bot.edit_message_text(f"{Space.nombre(area_idx)} seleccionada.", cid, callback.message.message_id)
        except Exception:
            pass
        await BSGController.ejecutar_accion_ubicacion(bot, game, presser, accion, objetivo=area_idx)
        if not st.ganador and not st.skill_check:
            await bot.send_message(cid, "Ahora se revela la *Crisis*. Usa `/crisis`.", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"callback_bsg_area error: {e}")
        try:
            await callback.answer("Error.")
        except Exception:
            pass
        await bot.send_message(ADMIN[0], f"BSG area error: {e}")


async def callback_bsg_target(update: Update, context: CallbackContext):
    """Selección de objetivo para una acción de ubicación con chequeo."""
    bot = context.bot
    callback = update.callback_query
    presser = callback.from_user.id
    try:
        regex = re.search(r"(-?[0-9]*)\*bsgTarget\*([a-z0-9_]*)\*(-?[0-9]*)", callback.data)
        cid = int(regex.group(1))
        accion = regex.group(2)
        objetivo = int(regex.group(3))
        game = get_game(cid)
        if not _validar(game):
            await callback.answer("Partida no encontrada.")
            return
        st = game.board.state
        if not st.active_player or st.active_player.uid != presser:
            await callback.answer("No es tu acción.")
            return
        if objetivo not in game.playerlist:
            await callback.answer("Objetivo inválido.")
            return
        await callback.answer("Objetivo elegido.")
        try:
            await bot.edit_message_text(f"Objetivo: {game.playerlist[objetivo].name}", cid, callback.message.message_id)
        except Exception:
            pass
        await BSGController.ejecutar_accion_ubicacion(bot, game, presser, accion, objetivo=objetivo)
    except Exception as e:
        logger.error(f"callback_bsg_target error: {e}")
        try:
            await callback.answer("Error.")
        except Exception:
            pass
        await bot.send_message(ADMIN[0], f"BSG target error: {e}")


async def command_mover(update: Update, context: CallbackContext):
    """El jugador activo elige una ubicación a la que moverse."""
    bot = context.bot
    cid = update.message.chat_id
    uid = update.message.from_user.id
    game = get_game(cid)
    if not _validar(game):
        await bot.send_message(cid, "No hay partida de Battlestar Galactica activa aquí.")
        return
    st = game.board.state
    if st.fase_actual != "En Juego" or not st.active_player or st.active_player.uid != uid:
        await bot.send_message(cid, "No es tu turno.")
        return
    if _esperando_robo(st, uid):
        await bot.send_message(cid, "Primero elige tus cartas de habilidad (revisa tu privado).")
        return
    player = game.playerlist[uid]
    if getattr(player, "viper_area", None) is not None:
        await bot.send_message(cid, "✈️ Estás pilotando un Viper: usa `/accion` para volar a otra área o aterrizar.",
                               parse_mode=ParseMode.MARKDOWN)
        return
    es_cylon_revelado = player.revealed
    btns = []
    for key, info in Locations.UBICACIONES.items():
        if info.get("es_cylon") and not es_cylon_revelado:
            continue
        if not info.get("es_cylon") and es_cylon_revelado:
            continue
        if key == player.ubicacion:
            continue
        btns.append([InlineKeyboardButton(info["nombre"], callback_data=f"{cid}*bsgMover*{key}*{uid}")])
    await bot.send_message(cid, "📍 ¿A dónde quieres moverte?",
                           reply_markup=InlineKeyboardMarkup(btns))


async def callback_bsg_mover(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    presser = callback.from_user.id
    try:
        regex = re.search(r"(-?[0-9]*)\*bsgMover\*([a-z_]*)\*(-?[0-9]*)", callback.data)
        cid = int(regex.group(1))
        destino = regex.group(2)
        target = int(regex.group(3))
        game = get_game(cid)
        if not _validar(game):
            await callback.answer("Partida no encontrada.")
            return
        st = game.board.state
        if not st.active_player or st.active_player.uid != presser or presser != target:
            await callback.answer("No es tu turno.")
            return
        await callback.answer("Te moviste.")
        try:
            await bot.edit_message_text("Movimiento realizado.", cid, callback.message.message_id)
        except Exception:
            pass
        await BSGController.mover_jugador(bot, game, presser, destino)
        await bot.send_message(cid, "Ahora usa `/accion`.", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"callback_bsg_mover error: {e}")
        try:
            await callback.answer("Error.")
        except Exception:
            pass
        await bot.send_message(ADMIN[0], f"BSG mover error: {e}")


async def command_crisis(update: Update, context: CallbackContext):
    """Revela y resuelve la crisis del turno (jugador activo o admin)."""
    bot = context.bot
    cid = update.message.chat_id
    uid = update.message.from_user.id
    game = get_game(cid)
    if not _validar(game):
        await bot.send_message(cid, "No hay partida de Battlestar Galactica activa aquí.")
        return
    st = game.board.state
    if st.fase_actual != "En Juego":
        await bot.send_message(cid, "No es momento de crisis.")
        return
    if st.skill_check:
        await bot.send_message(cid, "Ya hay un chequeo abierto. Resuélvelo con `/resolver`.")
        return
    if st.crisis_actual:
        await bot.send_message(cid, "Ya hay una crisis pendiente de resolver.")
        return
    if st.active_player and st.active_player.uid != uid and uid not in ADMIN:
        await bot.send_message(cid, "Solo el jugador activo (o un admin) revela la crisis.")
        return
    if st.active_player and _esperando_robo(st, st.active_player.uid):
        await bot.send_message(cid, "Primero elige tus cartas de habilidad (revisa tu privado).")
        return
    # Los jugadores Cylon revelados no roban crisis: con esto terminan su turno.
    if st.active_player and st.active_player.revealed:
        await bot.send_message(
            cid, f"🤖 {st.active_player.name} termina su turno (los Cylon no roban crisis)."
        )
        await BSGController.avanzar_turno(bot, game)
        return
    await BSGController.robar_crisis(bot, game)


async def callback_bsg_eleccion(update: Update, context: CallbackContext):
    """El decisor de una crisis de decisión elige una opción."""
    bot = context.bot
    callback = update.callback_query
    presser = callback.from_user.id
    try:
        regex = re.search(r"(-?[0-9]*)\*bsgEleccion\*([0-9]*)\*(-?[0-9]*)", callback.data)
        cid = int(regex.group(1))
        indice = int(regex.group(2))
        decisor = int(regex.group(3))
        game = get_game(cid)
        if not _validar(game):
            await callback.answer("Partida no encontrada.")
            return
        st = game.board.state
        if not st.crisis_actual or st.crisis_actual.get("tipo") != "eleccion":
            await callback.answer("Ya no hay decisión pendiente.")
            return
        if presser != decisor and presser not in ADMIN:
            await callback.answer("No te toca decidir.")
            return
        await callback.answer("Decisión tomada.")
        try:
            await bot.edit_message_text("Decisión tomada.", cid, callback.message.message_id)
        except Exception:
            pass
        await BSGController.resolver_eleccion(bot, game, indice)
    except Exception as e:
        logger.error(f"callback_bsg_eleccion error: {e}")
        try:
            await callback.answer("Error.")
        except Exception:
            pass
        await bot.send_message(ADMIN[0], f"BSG eleccion error: {e}")


async def callback_bsg_crisis_opt(update: Update, context: CallbackContext):
    """El decisor de una crisis con 'OR' elige chequeo o alternativa."""
    bot = context.bot
    callback = update.callback_query
    presser = callback.from_user.id
    try:
        regex = re.search(r"(-?[0-9]*)\*bsgCrisisOpt\*([a-z]*)\*(-?[0-9]*)", callback.data)
        cid = int(regex.group(1))
        opcion = regex.group(2)
        decisor = int(regex.group(3))
        game = get_game(cid)
        if not _validar(game):
            await callback.answer("Partida no encontrada.")
            return
        st = game.board.state
        if not st.crisis_actual or st.crisis_actual.get("tipo") != "chequeo" or not st.crisis_actual.get("alternativa"):
            await callback.answer("Ya no hay decisión pendiente.")
            return
        if st.skill_check:
            await callback.answer("El chequeo ya está abierto.")
            return
        if presser != decisor and presser not in ADMIN:
            await callback.answer("No te toca decidir.")
            return
        await callback.answer("Decisión tomada.")
        try:
            await bot.edit_message_text("Decisión tomada.", cid, callback.message.message_id)
        except Exception:
            pass
        await BSGController.resolver_decision_crisis(bot, game, opcion)
    except Exception as e:
        logger.error(f"callback_bsg_crisis_opt error: {e}")
        try:
            await callback.answer("Error.")
        except Exception:
            pass
        await bot.send_message(ADMIN[0], f"BSG crisis opt error: {e}")


async def callback_bsg_crisis_voto(update: Update, context: CallbackContext):
    """Voto de un jugador en una crisis de voto."""
    bot = context.bot
    callback = update.callback_query
    voter = callback.from_user.id
    try:
        regex = re.search(r"(-?[0-9]*)\*bsgCrisisVoto\*([0-9]*)\*(-?[0-9]*)", callback.data)
        cid = int(regex.group(1))
        indice = int(regex.group(2))
        game = get_game(cid)
        if not _validar(game):
            await callback.answer("Partida no encontrada.")
            return
        st = game.board.state
        if not st.crisis_vote:
            await callback.answer("La votación ya terminó.")
            return
        p = game.playerlist.get(voter)
        if not p:
            await callback.answer("No estás en la partida.")
            return
        if p.en_calabozo or p.revealed:
            await callback.answer("No puedes votar.")
            return
        if voter in st.crisis_vote["votos"]:
            await callback.answer("Ya votaste.")
            return
        await callback.answer("Voto registrado.")
        await BSGController.registrar_voto_crisis(bot, game, voter, indice)
    except Exception as e:
        logger.error(f"callback_bsg_crisis_voto error: {e}")
        try:
            await callback.answer("Error.")
        except Exception:
            pass
        await bot.send_message(ADMIN[0], f"BSG crisis voto error: {e}")


async def command_aportar(update: Update, context: CallbackContext):
    """Aporta una carta de la mano a un chequeo de habilidad (por privado)."""
    bot = context.bot
    uid = update.message.from_user.id
    args = context.args

    # Buscar la partida del jugador (puede escribir desde el privado)
    game = None
    for g in GamesController.games.values():
        if getattr(g, "tipo", None) == "BattlestarGalactica" and uid in getattr(g, "playerlist", {}):
            game = g
            break
    if not game or not game.board:
        await bot.send_message(uid, "No estás en una partida activa de BSG.")
        return
    if not game.board.state.skill_check:
        await bot.send_message(uid, "No hay ningún chequeo de habilidad abierto.")
        return
    if game.playerlist[uid].en_calabozo:
        await bot.send_message(uid, "Estás en el calabozo y no puedes aportar cartas.")
        return
    if not args or not args[0].isdigit():
        await bot.send_message(uid, "Uso: `/aportar N` (N = número de carta de tu mano).", parse_mode=ParseMode.MARKDOWN)
        return
    await BSGController.aportar_carta(bot, game, uid, int(args[0]))


async def command_resolver(update: Update, context: CallbackContext):
    """Resuelve el chequeo de habilidad abierto (Almirante, jugador activo o admin)."""
    bot = context.bot
    cid = update.message.chat_id
    uid = update.message.from_user.id
    game = get_game(cid)
    if not _validar(game):
        await bot.send_message(cid, "No hay partida de Battlestar Galactica activa aquí.")
        return
    st = game.board.state
    if not st.skill_check:
        await bot.send_message(cid, "No hay chequeo abierto.")
        return
    permitido = (uid in ADMIN or uid == st.almirante_uid or
                 (st.active_player and uid == st.active_player.uid))
    if not permitido:
        await bot.send_message(cid, "Solo el Almirante, el jugador activo o un admin pueden resolver.")
        return
    await BSGController.resolver_chequeo(bot, game)


async def callback_bsg_cylon(update: Update, context: CallbackContext):
    """Acción de sabotaje de un Cylon revelado."""
    bot = context.bot
    callback = update.callback_query
    presser = callback.from_user.id
    try:
        regex = re.search(r"(-?[0-9]*)\*bsgCylon\*([a-z0-9_]*)\*(-?[0-9]*)", callback.data)
        cid = int(regex.group(1))
        accion = regex.group(2)
        target = int(regex.group(3))
        game = get_game(cid)
        if not _validar(game):
            await callback.answer("Partida no encontrada.")
            return
        st = game.board.state
        player = game.playerlist.get(presser)
        if not player or not player.revealed or presser != target:
            await callback.answer("No puedes hacer esto.")
            return
        if not st.active_player or st.active_player.uid != presser:
            await callback.answer("No es tu turno.")
            return
        await callback.answer("Sabotaje ejecutado.")
        try:
            await bot.edit_message_text("Acción Cylon ejecutada.", cid, callback.message.message_id)
        except Exception:
            pass
        await BSGController.ejecutar_accion_cylon(bot, game, presser, accion)
        if not st.ganador:
            await bot.send_message(cid, "Usa `/crisis` para *terminar tu turno*.", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"callback_bsg_cylon error: {e}")
        try:
            await callback.answer("Error.")
        except Exception:
            pass
        await bot.send_message(ADMIN[0], f"BSG cylon error: {e}")


async def command_revelar(update: Update, context: CallbackContext):
    """Un Cylon se revela (puede usarse desde el grupo o el privado)."""
    bot = context.bot
    cid = update.message.chat_id
    uid = update.message.from_user.id
    game = get_game(cid)
    if not _validar(game):
        # permitir desde privado: buscar su partida
        for g in GamesController.games.values():
            if getattr(g, "tipo", None) == "BattlestarGalactica" and uid in getattr(g, "playerlist", {}):
                game = g
                break
    if not game or not game.board:
        await bot.send_message(uid, "No estás en una partida activa de BSG.")
        return
    if uid not in game.playerlist:
        await bot.send_message(uid, "No estás en esta partida.")
        return
    await BSGController.revelar_cylon(bot, game, uid)


async def command_habilidad(update: Update, context: CallbackContext):
    """Usa la habilidad de una vez por juego del personaje."""
    bot = context.bot
    cid = update.message.chat_id
    uid = update.message.from_user.id
    game = get_game(cid)
    if not _validar(game):
        for g in GamesController.games.values():
            if getattr(g, "tipo", None) == "BattlestarGalactica" and uid in getattr(g, "playerlist", {}):
                game = g
                break
    if not game or not game.board:
        await bot.send_message(uid, "No estás en una partida activa de BSG.")
        return
    if uid not in game.playerlist:
        await bot.send_message(uid, "No estás en esta partida.")
        return
    await BSGController.usar_habilidad(bot, game, uid)


async def command_quorum(update: Update, context: CallbackContext):
    """El Presidente juega una carta de Quórum de su mano."""
    bot = context.bot
    cid = update.message.chat_id
    uid = update.message.from_user.id
    game = get_game(cid)
    if not _validar(game):
        await bot.send_message(cid, "No hay partida de Battlestar Galactica activa aquí.")
        return
    st = game.board.state
    if uid != st.presidente_uid and uid not in ADMIN:
        await bot.send_message(cid, "Solo el Presidente puede jugar cartas de Quórum.")
        return
    player = game.playerlist[uid]
    if not player.quorum_hand:
        await bot.send_message(cid, "No tienes cartas de Quórum. Róbalas en la Oficina del Presidente.")
        return
    btns = [[InlineKeyboardButton(c["titulo"], callback_data=f"{cid}*bsgQuorum*{i+1}*{uid}")]
            for i, c in enumerate(player.quorum_hand)]
    await bot.send_message(cid, "🏛️ ¿Qué carta de Quórum juegas?", reply_markup=InlineKeyboardMarkup(btns))


async def callback_bsg_quorum(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    presser = callback.from_user.id
    try:
        regex = re.search(r"(-?[0-9]*)\*bsgQuorum\*([0-9]*)\*(-?[0-9]*)", callback.data)
        cid = int(regex.group(1))
        indice = int(regex.group(2))
        ordenante = int(regex.group(3))
        game = get_game(cid)
        if not _validar(game):
            await callback.answer("Partida no encontrada.")
            return
        st = game.board.state
        if presser != ordenante or (presser != st.presidente_uid and presser not in ADMIN):
            await callback.answer("Solo el Presidente.")
            return
        await callback.answer("Carta jugada.")
        try:
            await bot.edit_message_text("Carta de Quórum jugada.", cid, callback.message.message_id)
        except Exception:
            pass
        await BSGController.jugar_quorum(bot, game, presser, indice)
        # Si la carta requiere objetivo, mostrar botonera
        carta = st.quorum_pendiente
        if carta:
            ef = carta.get("target_efecto")
            btns = []
            for p_uid, p in game.playerlist.items():
                if ef == "pardon" and not p.en_calabozo:
                    continue
                if ef == "brig" and (p.en_calabozo or p.revealed):
                    continue
                if ef == "mutiny" and (p_uid == st.almirante_uid or p.revealed):
                    continue
                btns.append([InlineKeyboardButton(p.name, callback_data=f"{cid}*bsgQTarget*x*{p_uid}")])
            if not btns:
                await bot.send_message(cid, "No hay objetivos válidos; la carta se descarta.")
                st.quorum_discard.append(carta); st.quorum_pendiente = None
            else:
                await bot.send_message(cid, "🏛️ Elige el objetivo de la carta de Quórum:",
                                       reply_markup=InlineKeyboardMarkup(btns))
    except Exception as e:
        logger.error(f"callback_bsg_quorum error: {e}")
        try:
            await callback.answer("Error.")
        except Exception:
            pass
        await bot.send_message(ADMIN[0], f"BSG quorum error: {e}")


async def callback_bsg_qtarget(update: Update, context: CallbackContext):
    """Objetivo elegido para una carta de Quórum dirigida."""
    bot = context.bot
    callback = update.callback_query
    presser = callback.from_user.id
    try:
        regex = re.search(r"(-?[0-9]*)\*bsgQTarget\*[a-z]*\*(-?[0-9]*)", callback.data)
        cid = int(regex.group(1))
        objetivo = int(regex.group(2))
        game = get_game(cid)
        if not _validar(game):
            await callback.answer("Partida no encontrada.")
            return
        st = game.board.state
        if presser != st.presidente_uid and presser not in ADMIN:
            await callback.answer("Solo el Presidente.")
            return
        if not st.quorum_pendiente:
            await callback.answer("No hay carta pendiente.")
            return
        if objetivo not in game.playerlist:
            await callback.answer("Objetivo inválido.")
            return
        await callback.answer("Objetivo elegido.")
        try:
            await bot.edit_message_text(f"Objetivo: {game.playerlist[objetivo].name}", cid, callback.message.message_id)
        except Exception:
            pass
        await BSGController.resolver_quorum_objetivo(bot, game, objetivo)
    except Exception as e:
        logger.error(f"callback_bsg_qtarget error: {e}")
        try:
            await callback.answer("Error.")
        except Exception:
            pass
        await bot.send_message(ADMIN[0], f"BSG qtarget error: {e}")


async def command_encarcelar(update: Update, context: CallbackContext):
    """El Presidente o Almirante envía a un jugador (sospechoso) al calabozo."""
    bot = context.bot
    cid = update.message.chat_id
    uid = update.message.from_user.id
    game = get_game(cid)
    if not _validar(game):
        await bot.send_message(cid, "No hay partida de Battlestar Galactica activa aquí.")
        return
    st = game.board.state
    if uid != st.presidente_uid and uid != st.almirante_uid and uid not in ADMIN:
        await bot.send_message(cid, "Solo el Presidente o el Almirante pueden ordenar un arresto.")
        return
    btns = []
    for p_uid, p in game.playerlist.items():
        if p_uid == uid or p.en_calabozo or p.revealed:
            continue
        btns.append([InlineKeyboardButton(p.name, callback_data=f"{cid}*bsgBrig*{p_uid}*{uid}")])
    if not btns:
        await bot.send_message(cid, "No hay jugadores a los que arrestar.")
        return
    await bot.send_message(cid, "🚔 ¿A quién envías al calabozo?", reply_markup=InlineKeyboardMarkup(btns))


async def callback_bsg_brig(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    presser = callback.from_user.id
    try:
        regex = re.search(r"(-?[0-9]*)\*bsgBrig\*(-?[0-9]*)\*(-?[0-9]*)", callback.data)
        cid = int(regex.group(1))
        objetivo = int(regex.group(2))
        ordenante = int(regex.group(3))
        game = get_game(cid)
        if not _validar(game):
            await callback.answer("Partida no encontrada.")
            return
        st = game.board.state
        if presser != ordenante or (presser != st.presidente_uid and presser != st.almirante_uid and presser not in ADMIN):
            await callback.answer("No puedes ordenar esto.")
            return
        p = game.playerlist.get(objetivo)
        if not p:
            await callback.answer("Jugador no encontrado.")
            return
        p.en_calabozo = True
        p.ubicacion = "brig"
        await callback.answer("Arrestado.")
        try:
            await bot.edit_message_text(f"{p.name} fue enviado al calabozo.", cid, callback.message.message_id)
        except Exception:
            pass
        await bot.send_message(cid, f"🚔 *{p.name}* está ahora en el calabozo.", parse_mode=ParseMode.MARKDOWN)
        await save(bot, game.cid)
    except Exception as e:
        logger.error(f"callback_bsg_brig error: {e}")
        try:
            await callback.answer("Error.")
        except Exception:
            pass
        await bot.send_message(ADMIN[0], f"BSG brig error: {e}")


async def command_liberar(update: Update, context: CallbackContext):
    """El Presidente o Almirante libera a un jugador del calabozo."""
    bot = context.bot
    cid = update.message.chat_id
    uid = update.message.from_user.id
    game = get_game(cid)
    if not _validar(game):
        await bot.send_message(cid, "No hay partida de Battlestar Galactica activa aquí.")
        return
    st = game.board.state
    if uid != st.presidente_uid and uid != st.almirante_uid and uid not in ADMIN:
        await bot.send_message(cid, "Solo el Presidente o el Almirante pueden liberar a alguien.")
        return
    btns = []
    for p_uid, p in game.playerlist.items():
        if p.en_calabozo:
            btns.append([InlineKeyboardButton(p.name, callback_data=f"{cid}*bsgFree*{p_uid}*{uid}")])
    if not btns:
        await bot.send_message(cid, "No hay nadie en el calabozo.")
        return
    await bot.send_message(cid, "🔓 ¿A quién liberas?", reply_markup=InlineKeyboardMarkup(btns))


async def callback_bsg_free(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    presser = callback.from_user.id
    try:
        regex = re.search(r"(-?[0-9]*)\*bsgFree\*(-?[0-9]*)\*(-?[0-9]*)", callback.data)
        cid = int(regex.group(1))
        objetivo = int(regex.group(2))
        ordenante = int(regex.group(3))
        game = get_game(cid)
        if not _validar(game):
            await callback.answer("Partida no encontrada.")
            return
        st = game.board.state
        if presser != ordenante or (presser != st.presidente_uid and presser != st.almirante_uid and presser not in ADMIN):
            await callback.answer("No puedes ordenar esto.")
            return
        p = game.playerlist.get(objetivo)
        if not p:
            await callback.answer("Jugador no encontrado.")
            return
        p.en_calabozo = False
        p.ubicacion = "sickbay"
        await callback.answer("Liberado.")
        try:
            await bot.edit_message_text(f"{p.name} fue liberado del calabozo.", cid, callback.message.message_id)
        except Exception:
            pass
        await bot.send_message(cid, f"🔓 *{p.name}* sale del calabozo (Enfermería).", parse_mode=ParseMode.MARKDOWN)
        await save(bot, game.cid)
    except Exception as e:
        logger.error(f"callback_bsg_free error: {e}")
        try:
            await callback.answer("Error.")
        except Exception:
            pass
        await bot.send_message(ADMIN[0], f"BSG free error: {e}")
