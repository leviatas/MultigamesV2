#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging as log
import re

import SpyFall.Controller as SpyFallController
from Utils import get_game, save, player_call
from Constants.Config import ADMIN
from SpyFall.Constants.Locations import LISTA_LOCALIDADES

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.ext import CallbackContext

import GamesController

log.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=log.INFO)
logger = log.getLogger(__name__)


def command_call(bot, game):
    """Periodic reminder of game state."""
    if not game.board:
        return
    fase = game.board.state.fase_actual
    if fase == "Interrogando":
        bot.send_message(
            game.cid,
            "🕵️ *SpyFall en curso* — ¡Hay un espía entre ustedes!\n\n"
            "• `/acusar` — Votar quién es el espía\n"
            "• `/adivinar` — (Solo espía) Adivinar la localidad\n"
            "• `/rol` — Ver tu rol en privado",
            parse_mode=ParseMode.MARKDOWN
        )
    elif fase == "Votando":
        votos_faltantes = [
            game.playerlist[uid].name
            for uid in game.playerlist
            if uid not in game.board.state.votos_acusacion
        ]
        if votos_faltantes:
            bot.send_message(
                game.cid,
                f"⏳ *Votación en curso* — Faltan votar:\n" +
                "\n".join(f"• {n}" for n in votos_faltantes),
                parse_mode=ParseMode.MARKDOWN
            )


def command_acusar(update: Update, context: CallbackContext):
    """Start a vote to identify the spy."""
    bot = context.bot
    cid = update.message.chat_id
    uid = update.message.from_user.id

    game = get_game(cid)
    if not game or game.tipo != "SpyFall":
        bot.send_message(cid, "No hay partida de SpyFall activa aquí.")
        return
    if not game.board:
        bot.send_message(cid, "La partida no ha comenzado.")
        return
    if uid not in game.playerlist:
        bot.send_message(cid, "No estás en esta partida.")
        return
    if game.board.state.fase_actual == "Votando":
        bot.send_message(cid, "⚠️ Ya hay una votación en curso.")
        return
    if game.board.state.fase_actual != "Interrogando":
        bot.send_message(cid, "No se puede acusar en este momento.")
        return

    game.board.state.fase_actual = "Votando"
    game.board.state.votos_acusacion = {}
    game.board.state.acusador_uid = uid

    acusador_name = game.playerlist[uid].name

    btns = []
    for p_uid, player in game.playerlist.items():
        datos = f"{cid}*spyfallVoto*{p_uid}*{uid}"
        btns.append([InlineKeyboardButton(f"🔎 {player.name}", callback_data=datos)])

    markup = InlineKeyboardMarkup(btns)
    msg = bot.send_message(
        cid,
        f"🗳️ *{acusador_name}* inicia una votación.\n\n"
        f"¿Quién creen que es el espía? Cada jugador vote una vez:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup
    )
    game.board.state.voto_msg_id = msg.message_id

    save(bot, game.cid)


def callback_spyfall_voto(update: Update, context: CallbackContext):
    """Handle a player's vote for who they think is the spy."""
    bot = context.bot
    callback = update.callback_query
    voter_uid = callback.from_user.id

    try:
        regex = re.search(r"(-?[0-9]*)\*spyfallVoto\*(-?[0-9]*)\*(-?[0-9]*)", callback.data)
        cid = int(regex.group(1))
        accused_uid = int(regex.group(2))

        game = get_game(cid)
        if not game or game.tipo != "SpyFall" or not game.board:
            callback.answer("Partida no encontrada.")
            return

        if game.board.state.fase_actual != "Votando":
            callback.answer("La votación ya terminó.")
            return

        if voter_uid not in game.playerlist:
            callback.answer("No estás en esta partida.")
            return

        if voter_uid in game.board.state.votos_acusacion:
            callback.answer("Ya votaste.")
            return

        accused_player = game.playerlist.get(accused_uid)
        if not accused_player:
            callback.answer("Jugador no encontrado.")
            return

        game.board.state.votos_acusacion[voter_uid] = accused_uid
        voter_name = game.playerlist[voter_uid].name

        callback.answer(f"Votaste por {accused_player.name}")
        bot.send_message(
            cid,
            f"✅ *{voter_name}* votó.",
            parse_mode=ParseMode.MARKDOWN
        )

        # Resolve when everyone has voted
        if len(game.board.state.votos_acusacion) >= len(game.playerlist):
            save(bot, game.cid)
            SpyFallController.resolve_accusation(bot, game)
        else:
            save(bot, game.cid)

    except Exception as e:
        logger.error(f"callback_spyfall_voto error: {e}")
        try:
            callback.answer("Error procesando el voto.")
        except Exception:
            pass
        bot.send_message(ADMIN[0], f"SpyFall voto error: {e}")


def command_adivinar(update: Update, context: CallbackContext):
    """Spy guesses the location — sends location buttons via DM."""
    bot = context.bot
    cid = update.message.chat_id
    uid = update.message.from_user.id

    game = get_game(cid)
    if not game or game.tipo != "SpyFall":
        bot.send_message(cid, "No hay partida de SpyFall activa aquí.")
        return
    if not game.board:
        bot.send_message(cid, "La partida no ha comenzado.")
        return
    if uid not in game.playerlist:
        bot.send_message(cid, "No estás en esta partida.")
        return
    if game.board.state.fase_actual == "Finalizado":
        bot.send_message(cid, "La partida ya terminó.")
        return

    player = game.playerlist[uid]
    if not player.is_spy:
        bot.send_message(
            uid,
            "Solo el espía puede usar `/adivinar`.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    btns = []
    for idx, localidad in enumerate(LISTA_LOCALIDADES):
        datos = f"{cid}*spyfallAdivinar*{idx}*{uid}"
        btns.append([InlineKeyboardButton(localidad, callback_data=datos)])

    markup = InlineKeyboardMarkup(btns)
    bot.send_message(
        uid,
        "🗺️ *¿Cuál crees que es la localidad?* Elige:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup
    )
    bot.send_message(
        cid,
        f"🕵️ *{player.name}* está adivinando la localidad...",
        parse_mode=ParseMode.MARKDOWN
    )


def callback_spyfall_adivinar(update: Update, context: CallbackContext):
    """Handle the spy's location guess."""
    bot = context.bot
    callback = update.callback_query
    guesser_uid = callback.from_user.id

    try:
        regex = re.search(r"(-?[0-9]*)\*spyfallAdivinar\*([0-9]*)\*(-?[0-9]*)", callback.data)
        cid = int(regex.group(1))
        location_idx = int(regex.group(2))

        if location_idx >= len(LISTA_LOCALIDADES):
            callback.answer("Localidad inválida.")
            return

        guessed_localidad = LISTA_LOCALIDADES[location_idx]

        game = get_game(cid)
        if not game or game.tipo != "SpyFall" or not game.board:
            callback.answer("Partida no encontrada.")
            return

        if game.board.state.fase_actual == "Finalizado":
            callback.answer("La partida ya terminó.")
            return

        if guesser_uid not in game.playerlist:
            callback.answer("No estás en esta partida.")
            return

        player = game.playerlist[guesser_uid]
        if not player.is_spy:
            callback.answer("Solo el espía puede adivinar.")
            return

        callback.answer(f"Adivinaste: {guessed_localidad}")

        real_localidad = game.board.state.localidad
        spy_name = player.name

        bot.send_message(
            cid,
            f"🕵️ *{spy_name}* adivina: *{guessed_localidad}*",
            parse_mode=ParseMode.MARKDOWN
        )

        if guessed_localidad == real_localidad:
            SpyFallController.spy_wins(
                bot, game,
                reason="✅ *¡El espía adivinó la localidad correctamente!*"
            )
        else:
            SpyFallController.non_spy_wins(bot, game, guessed_wrong=True)

    except Exception as e:
        logger.error(f"callback_spyfall_adivinar error: {e}")
        try:
            callback.answer("Error procesando la respuesta.")
        except Exception:
            pass
        bot.send_message(ADMIN[0], f"SpyFall adivinar error: {e}")


def command_rol(update: Update, context: CallbackContext):
    """Show the player their role via DM."""
    bot = context.bot
    cid = update.message.chat_id
    uid = update.message.from_user.id

    game = get_game(cid)
    if not game or game.tipo != "SpyFall":
        bot.send_message(cid, "No hay partida de SpyFall activa aquí.")
        return
    if not game.board:
        bot.send_message(cid, "La partida no ha comenzado.")
        return
    if uid not in game.playerlist:
        bot.send_message(uid, "No estás en esta partida.")
        return

    player = game.playerlist[uid]
    if player.is_spy:
        localidades_list = "\n".join(f"• {loc}" for loc in LISTA_LOCALIDADES)
        bot.send_message(
            uid,
            f"🕵️ *Eres el ESPÍA*\n\nNo conoces la localidad.\n\n"
            f"*Localidades posibles:*\n{localidades_list}",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        bot.send_message(
            uid,
            f"🗺️ *Localidad: {game.board.state.localidad}*\n"
            f"👤 *Tu rol: {player.role}*",
            parse_mode=ParseMode.MARKDOWN
        )
