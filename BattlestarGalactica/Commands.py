#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Battlestar Galactica — comandos y callbacks (Capa 1)."""

import logging as log
import re

import BattlestarGalactica.Controller as BSGController
from BattlestarGalactica.Constants import Characters, Skills, Loyalty, Locations
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
            "Acción: `/accion` · Crisis: `/crisis` · Tablero: `/estado`",
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
    lineas = [f"{i+1}. {Skills.EMOJI_COLOR[c['color']]} {c['color']} {c['valor']}"
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

    player = game.playerlist[uid]
    if player.en_calabozo:
        await bot.send_message(cid, "Estás en el calabozo y no puedes realizar acciones.")
        return

    acciones = BSGController.ACCIONES_UBICACION.get(player.ubicacion, [])
    ubic = Locations.UBICACIONES.get(player.ubicacion, {}).get("nombre", "—")
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

        await callback.answer("Acción realizada.")
        try:
            await bot.edit_message_text("Acción elegida.", cid, callback.message.message_id)
        except Exception:
            pass

        if accion != "pass":
            await BSGController.ejecutar_accion_ubicacion(bot, game, presser, accion)
        else:
            await bot.send_message(cid, f"{game.playerlist[presser].name} pasa su acción.")
        if not st.ganador:
            await bot.send_message(cid, "Ahora se revela la *Crisis*. Usa `/crisis`.", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"callback_bsg_accion error: {e}")
        try:
            await callback.answer("Error.")
        except Exception:
            pass
        await bot.send_message(ADMIN[0], f"BSG accion error: {e}")


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
    player = game.playerlist[uid]
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
    if st.active_player and st.active_player.uid != uid and uid not in ADMIN:
        await bot.send_message(cid, "Solo el jugador activo (o un admin) revela la crisis.")
        return
    await BSGController.robar_crisis(bot, game)


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
