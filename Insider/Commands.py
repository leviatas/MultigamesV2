#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging as log
import re

import Insider.Controller as InsiderController
from Utils import get_game, save
from Constants.Config import ADMIN

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

import GamesController

log.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=log.INFO)
logger = log.getLogger(__name__)


async def command_call(bot, game):
    """Recordatorio periódico del estado de la partida."""
    if not game.board:
        return
    st = game.board.state
    fase = st.fase_actual
    if fase == "Preguntas":
        await bot.send_message(
            game.cid,
            "🎭 *Insider en curso* — Fase de Preguntas.\n"
            "Hagan preguntas de sí/no al Guía para adivinar la palabra.\n"
            "El Guía usa `/acerto` cuando alguien acierta, o `/notiempo` si se acaba el tiempo.",
            parse_mode=ParseMode.MARKDOWN
        )
    elif fase == "Juzgar":
        await bot.send_message(
            game.cid,
            "🗳️ *Votación en curso:* ¿el que acertó es el Infiltrado? Voten con los botones.",
            parse_mode=ParseMode.MARKDOWN
        )
    elif fase == "Votar":
        await bot.send_message(
            game.cid,
            "🗳️ *Votación final:* señalen a quién creen que es el Infiltrado.",
            parse_mode=ParseMode.MARKDOWN
        )


def _validar_partida(game):
    return game and game.tipo == "Insider" and game.board


async def command_rol(update: Update, context: CallbackContext):
    """Muestra al jugador su rol por privado."""
    bot = context.bot
    cid = update.message.chat_id
    uid = update.message.from_user.id

    game = get_game(cid)
    if not _validar_partida(game):
        await bot.send_message(cid, "No hay partida de Insider activa aquí.")
        return
    if uid not in game.playerlist:
        await bot.send_message(uid, "No estás en esta partida.")
        return

    st = game.board.state
    player = game.playerlist[uid]
    if player.is_guia:
        await bot.send_message(
            uid,
            f"👑 *Eres el GUÍA.*\nLa palabra secreta es: *{st.palabra}*",
            parse_mode=ParseMode.MARKDOWN
        )
    elif player.is_insider:
        await bot.send_message(
            uid,
            f"🕵️ *Eres el INFILTRADO.*\nLa palabra secreta es: *{st.palabra}*",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await bot.send_message(
            uid,
            "👥 *Eres un CIUDADANO.* No conoces la palabra secreta.",
            parse_mode=ParseMode.MARKDOWN
        )


async def command_palabra(update: Update, context: CallbackContext):
    """Reenvía la palabra secreta al Guía o al Infiltrado por privado."""
    bot = context.bot
    cid = update.message.chat_id
    uid = update.message.from_user.id

    game = get_game(cid)
    if not _validar_partida(game):
        await bot.send_message(cid, "No hay partida de Insider activa aquí.")
        return
    if uid not in game.playerlist:
        await bot.send_message(uid, "No estás en esta partida.")
        return

    st = game.board.state
    player = game.playerlist[uid]
    if player.is_guia or player.is_insider:
        await bot.send_message(
            uid,
            f"🔑 La palabra secreta es: *{st.palabra}*",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await bot.send_message(uid, "Solo el Guía y el Infiltrado conocen la palabra.")


async def command_acerto(update: Update, context: CallbackContext):
    """El Guía marca quién adivinó la palabra (muestra botones de jugadores)."""
    bot = context.bot
    cid = update.message.chat_id
    uid = update.message.from_user.id

    game = get_game(cid)
    if not _validar_partida(game):
        await bot.send_message(cid, "No hay partida de Insider activa aquí.")
        return

    st = game.board.state
    if uid != st.guia_uid:
        await bot.send_message(cid, "Solo el Guía puede marcar quién acertó.")
        return
    if st.fase_actual != "Preguntas":
        await bot.send_message(cid, "Solo se puede marcar el acierto durante la fase de Preguntas.")
        return

    btns = []
    for p_uid, player in game.playerlist.items():
        if p_uid == st.guia_uid:
            continue  # el Guía no adivina su propia palabra
        btns.append([InlineKeyboardButton(player.name, callback_data=f"{cid}*insiderAcerto*{p_uid}*{uid}")])

    await bot.send_message(
        cid,
        "👑 *Guía:* ¿quién adivinó la palabra?",
        reply_markup=InlineKeyboardMarkup(btns),
        parse_mode=ParseMode.MARKDOWN
    )


async def callback_insider_acerto(update: Update, context: CallbackContext):
    """Registra al acertador y pasa a la fase de Juzgar."""
    bot = context.bot
    callback = update.callback_query
    presser_uid = callback.from_user.id

    try:
        regex = re.search(r"(-?[0-9]*)\*insiderAcerto\*(-?[0-9]*)\*(-?[0-9]*)", callback.data)
        cid = int(regex.group(1))
        acertador_uid = int(regex.group(2))

        game = get_game(cid)
        if not _validar_partida(game):
            await callback.answer("Partida no encontrada.")
            return

        st = game.board.state
        if presser_uid != st.guia_uid:
            await callback.answer("Solo el Guía elige.")
            return
        if st.fase_actual != "Preguntas":
            await callback.answer("Ya no es momento de marcar el acierto.")
            return
        if acertador_uid not in game.playerlist:
            await callback.answer("Jugador no encontrado.")
            return

        st.acertador_uid = acertador_uid
        await callback.answer("Acierto registrado.")
        try:
            await bot.edit_message_text(
                f"Adivinó la palabra: {game.playerlist[acertador_uid].name}",
                cid, callback.message.message_id
            )
        except Exception:
            pass

        await save(bot, game.cid)
        await InsiderController.start_juzgar(bot, game)
    except Exception as e:
        logger.error(f"callback_insider_acerto error: {e}")
        try:
            await callback.answer("Error procesando la respuesta.")
        except Exception:
            pass
        await bot.send_message(ADMIN[0], f"Insider acerto error: {e}")


async def command_notiempo(update: Update, context: CallbackContext):
    """El Guía declara que se acabó el tiempo y nadie acertó: todos pierden."""
    bot = context.bot
    cid = update.message.chat_id
    uid = update.message.from_user.id

    game = get_game(cid)
    if not _validar_partida(game):
        await bot.send_message(cid, "No hay partida de Insider activa aquí.")
        return

    st = game.board.state
    if uid != st.guia_uid:
        await bot.send_message(cid, "Solo el Guía puede declarar el fin del tiempo.")
        return
    if st.fase_actual != "Preguntas":
        await bot.send_message(cid, "El tiempo solo aplica durante la fase de Preguntas.")
        return

    await InsiderController.todos_pierden(bot, game)


async def callback_insider_juzgar(update: Update, context: CallbackContext):
    """Voto de la fase Juzgar: ¿el que acertó es el infiltrado?"""
    bot = context.bot
    callback = update.callback_query
    voter_uid = callback.from_user.id

    try:
        regex = re.search(r"(-?[0-9]*)\*insiderJuzgar\*(si|no)\*([0-9]*)", callback.data)
        cid = int(regex.group(1))
        voto = regex.group(2)

        game = get_game(cid)
        if not _validar_partida(game):
            await callback.answer("Partida no encontrada.")
            return

        st = game.board.state
        if st.fase_actual != "Juzgar":
            await callback.answer("La votación ya terminó.")
            return
        if voter_uid not in game.playerlist:
            await callback.answer("No estás en esta partida.")
            return
        if voter_uid == st.acertador_uid:
            await callback.answer("El que acertó no vota en esta fase.")
            return
        if voter_uid in st.votos_juzgar:
            await callback.answer("Ya votaste.")
            return

        st.votos_juzgar[voter_uid] = (voto == "si")
        await callback.answer("Voto registrado.")

        elegibles = len(game.playerlist) - 1  # todos menos el acertador
        if len(st.votos_juzgar) >= elegibles:
            await save(bot, game.cid)
            await InsiderController.resolve_juzgar(bot, game)
        else:
            await save(bot, game.cid)
    except Exception as e:
        logger.error(f"callback_insider_juzgar error: {e}")
        try:
            await callback.answer("Error procesando el voto.")
        except Exception:
            pass
        await bot.send_message(ADMIN[0], f"Insider juzgar error: {e}")


async def callback_insider_votar(update: Update, context: CallbackContext):
    """Voto de la fase Votar: señalar al infiltrado."""
    bot = context.bot
    callback = update.callback_query
    voter_uid = callback.from_user.id

    try:
        regex = re.search(r"(-?[0-9]*)\*insiderVotar\*(-?[0-9]*)\*([0-9]*)", callback.data)
        cid = int(regex.group(1))
        accused_uid = int(regex.group(2))

        game = get_game(cid)
        if not _validar_partida(game):
            await callback.answer("Partida no encontrada.")
            return

        st = game.board.state
        if st.fase_actual != "Votar":
            await callback.answer("La votación ya terminó.")
            return
        if voter_uid not in game.playerlist:
            await callback.answer("No estás en esta partida.")
            return
        if voter_uid == st.guia_uid:
            await callback.answer("El Guía no vota en esta fase.")
            return
        if accused_uid not in game.playerlist:
            await callback.answer("Jugador no encontrado.")
            return
        if voter_uid in st.votos_infiltrado:
            await callback.answer("Ya votaste.")
            return

        st.votos_infiltrado[voter_uid] = accused_uid
        await callback.answer(f"Votaste por {game.playerlist[accused_uid].name}")

        elegibles = len(game.playerlist) - 1  # todos menos el Guía
        if len(st.votos_infiltrado) >= elegibles:
            await save(bot, game.cid)
            await InsiderController.resolve_votar(bot, game)
        else:
            await save(bot, game.cid)
    except Exception as e:
        logger.error(f"callback_insider_votar error: {e}")
        try:
            await callback.answer("Error procesando el voto.")
        except Exception:
            pass
        await bot.send_message(ADMIN[0], f"Insider votar error: {e}")


async def callback_insider_desempate(update: Update, context: CallbackContext):
    """El acertador desempata eligiendo al sospechoso."""
    bot = context.bot
    callback = update.callback_query
    presser_uid = callback.from_user.id

    try:
        regex = re.search(r"(-?[0-9]*)\*insiderDesempate\*(-?[0-9]*)\*(-?[0-9]*)", callback.data)
        cid = int(regex.group(1))
        accused_uid = int(regex.group(2))

        game = get_game(cid)
        if not _validar_partida(game):
            await callback.answer("Partida no encontrada.")
            return

        st = game.board.state
        if st.fase_actual != "Desempate":
            await callback.answer("Ya no es momento de desempatar.")
            return
        if presser_uid != st.acertador_uid:
            await callback.answer("Solo quien acertó la palabra decide el desempate.")
            return
        if accused_uid not in st.empate_candidatos:
            await callback.answer("Ese jugador no está empatado.")
            return

        await callback.answer("Decisión registrada.")
        try:
            await bot.edit_message_text(
                f"Decisión del desempate: {game.playerlist[accused_uid].name}",
                cid, callback.message.message_id
            )
        except Exception:
            pass
        await InsiderController.resolver_acusado(bot, game, accused_uid)
    except Exception as e:
        logger.error(f"callback_insider_desempate error: {e}")
        try:
            await callback.answer("Error procesando la decisión.")
        except Exception:
            pass
        await bot.send_message(ADMIN[0], f"Insider desempate error: {e}")
